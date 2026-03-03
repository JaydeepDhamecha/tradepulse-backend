"""
Management command: run_daily_market_update

Runs the full TradePulse daily pipeline for a given date:

  1. Fetch NSE bhavcopy          → Stock model
  2. Calculate OI change         → Stock.oi_change
  3. Calculate volume spike      → Stock.volume_spike_ratio
  4. Fetch global market data    → GlobalMarket model
  5. Calculate market bias       → GlobalMarket.market_bias
  6. Generate intraday signals   → IntradaySignal model
  7. Generate AI insight         → Insight model (via Claude API)
  8. Log success
  9. Idempotent (safe to run twice)

Usage:
  python manage.py run_daily_market_update
  python manage.py run_daily_market_update --date 2025-06-15
"""

import logging
import time
from datetime import date, timedelta

from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run the full daily market analytics pipeline (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            type=str,
            default=None,
            help="Target date in YYYY-MM-DD format. Defaults to today.",
        )
        parser.add_argument(
            "--skip-ai",
            action="store_true",
            default=False,
            help="Skip AI insight generation (useful if no API key).",
        )
        parser.add_argument(
            "--backfill",
            type=int,
            default=0,
            help="Number of past trading days to backfill before running "
                 "today's pipeline. Needed for OI change & volume spike "
                 "calculations which require historical data. "
                 "Example: --backfill 25 loads 25 past days first.",
        )

    def handle(self, *args, **options):
        target_date = self._resolve_date(options["date"])
        backfill_days = options["backfill"]

        # ── Backfill historical data if requested ────────────────
        if backfill_days > 0:
            self._run_backfill(target_date, backfill_days)

        start_time = time.time()

        self.stdout.write("")
        self.stdout.write(self.style.NOTICE(
            f"{'=' * 50}"
        ))
        self.stdout.write(self.style.NOTICE(
            f"  TradePulse AI — Daily Pipeline"
        ))
        self.stdout.write(self.style.NOTICE(
            f"  Date: {target_date}"
        ))
        self.stdout.write(self.style.NOTICE(
            f"{'=' * 50}"
        ))
        self.stdout.write("")

        logger.info("=== Starting daily pipeline for %s ===", target_date)

        # ── Step 1: Fetch NSE bhavcopy & update Stock data ───────
        #    Returns (rows, actual_date). On holidays/weekends the
        #    actual_date may differ — all subsequent steps use it.
        bhavcopy_result = self._run_step(
            step=1,
            label="Fetch NSE bhavcopy",
            func=self._step_bhavcopy,
            target_date=target_date,
        )
        bhavcopy_rows, trading_date = bhavcopy_result

        if trading_date != target_date:
            self.stdout.write(self.style.WARNING(
                f"         → {target_date} is a holiday/weekend. "
                f"Using last trading day: {trading_date}"
            ))

        # ── Steps 2–7 use the actual trading date ────────────────

        # ── Step 2: Calculate OI change ──────────────────────────
        oi_updated = self._run_step(
            step=2,
            label="Calculate OI change",
            func=self._step_oi_change,
            target_date=trading_date,
        )

        # ── Step 3: Calculate volume spike ───────────────────────
        vol_updated = self._run_step(
            step=3,
            label="Calculate volume spike",
            func=self._step_volume_spike,
            target_date=trading_date,
        )

        # ── Step 4: Fetch global market data ─────────────────────
        gm_status = self._run_step(
            step=4,
            label="Fetch global market data",
            func=self._step_global_market,
            target_date=trading_date,
        )

        # ── Step 5: Calculate market bias ────────────────────────
        bias = self._run_step(
            step=5,
            label="Calculate market bias",
            func=self._step_market_bias,
            target_date=trading_date,
        )

        # ── Step 6: Generate intraday signals ────────────────────
        signals = self._run_step(
            step=6,
            label="Generate intraday signals",
            func=self._step_signals,
            target_date=trading_date,
        )

        # ── Step 7: Generate AI insight ──────────────────────────
        if options["skip_ai"]:
            ai_status = "skipped (--skip-ai flag)"
            self.stdout.write(f"  [7/8] Generate AI insight ... {ai_status}")
        else:
            ai_status = self._run_step(
                step=7,
                label="Generate AI insight",
                func=self._step_ai_insight,
                target_date=trading_date,
                critical=False,
            )

        # ── Step 8: Summary & logging ────────────────────────────
        elapsed = time.time() - start_time

        self.stdout.write("")
        self.stdout.write(self.style.NOTICE("  Summary:"))
        self.stdout.write(f"    Requested date     : {target_date}")
        self.stdout.write(f"    Trading date used  : {trading_date}")
        self.stdout.write(f"    Bhavcopy rows      : {bhavcopy_rows}")
        self.stdout.write(f"    OI change updated  : {oi_updated}")
        self.stdout.write(f"    Volume spike updated: {vol_updated}")
        self.stdout.write(f"    Global market      : {gm_status}")
        self.stdout.write(f"    Market bias        : {bias}")
        self.stdout.write(f"    Signals generated  : {signals}")
        self.stdout.write(f"    AI insight         : {ai_status}")
        self.stdout.write(f"    Elapsed time       : {elapsed:.1f}s")
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"  Daily pipeline completed successfully for {trading_date}."
        ))
        self.stdout.write("")

        logger.info(
            "Daily pipeline completed for %s (requested=%s) in %.1fs — "
            "bhavcopy=%s, oi=%s, vol=%s, gm=%s, bias=%s, signals=%s, ai=%s",
            trading_date, target_date, elapsed,
            bhavcopy_rows, oi_updated, vol_updated,
            gm_status, bias, signals, ai_status,
        )

    # ── Helper: backfill historical data ──────────────────────────
    def _run_backfill(self, end_date: date, num_days: int):
        """
        Load bhavcopy-only data for the past *num_days* trading days
        (skipping weekends) so that OI change and volume spike have
        historical data to compute against.
        """
        from stocks.services import fetch_and_store_bhavcopy

        self.stdout.write("")
        self.stdout.write(self.style.NOTICE(
            f"  Backfilling {num_days} trading days of historical data..."
        ))

        # Build list of dates to backfill (walk backwards, skip weekends)
        dates = []
        d = end_date - timedelta(days=1)
        while len(dates) < num_days:
            if d.weekday() < 5:  # Mon-Fri
                dates.append(d)
            d -= timedelta(days=1)

        # Process oldest first
        dates.reverse()

        for i, bf_date in enumerate(dates, 1):
            self.stdout.write(
                f"    [{i}/{num_days}] {bf_date} ...", ending=" "
            )
            try:
                rows, actual = fetch_and_store_bhavcopy(bf_date)
                if actual != bf_date:
                    self.stdout.write(self.style.SUCCESS(
                        f"{rows} rows (used {actual})"
                    ))
                else:
                    self.stdout.write(self.style.SUCCESS(f"{rows} rows"))
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f"skipped ({exc})"))

        self.stdout.write(self.style.SUCCESS(
            f"  Backfill complete ({num_days} days)."
        ))
        self.stdout.write("")

    # ── Helper: resolve date ─────────────────────────────────────
    @staticmethod
    def _resolve_date(date_str: str | None) -> date:
        if date_str:
            try:
                return date.fromisoformat(date_str)
            except ValueError:
                raise CommandError(
                    f"Invalid date format: '{date_str}'. Use YYYY-MM-DD."
                )
        return date.today()

    # ── Helper: run a pipeline step with logging ─────────────────
    def _run_step(self, step: int, label: str, func, target_date: date,
                  critical: bool = True):
        """
        Execute a pipeline step, log the result, and handle errors.

        If critical=True, a failure raises CommandError.
        If critical=False, a failure is logged but the pipeline continues.
        """
        self.stdout.write(f"  [{step}/8] {label} ...", ending=" ")
        try:
            result = func(target_date)
            # For bhavcopy step, display just the row count
            if isinstance(result, tuple):
                display = str(result[0])
            else:
                display = str(result)
            self.stdout.write(self.style.SUCCESS(display))
            return result
        except Exception as exc:
            if critical:
                self.stdout.write(self.style.ERROR(f"FAILED"))
                logger.exception("Step %d (%s) failed for %s", step, label, target_date)
                raise CommandError(
                    f"Step {step} ({label}) failed: {exc}"
                ) from exc
            else:
                msg = f"failed ({exc})"
                self.stdout.write(self.style.WARNING(msg))
                logger.warning(
                    "Step %d (%s) failed for %s: %s",
                    step, label, target_date, exc, exc_info=True,
                )
                return msg

    # ── Pipeline steps ───────────────────────────────────────────

    @staticmethod
    def _step_bhavcopy(target_date: date) -> tuple[int, date]:
        from stocks.services import fetch_and_store_bhavcopy
        rows, actual_date = fetch_and_store_bhavcopy(target_date)
        return rows, actual_date

    @staticmethod
    def _step_oi_change(target_date: date) -> int:
        from stocks.services import calculate_oi_change_for_date
        return calculate_oi_change_for_date(target_date)

    @staticmethod
    def _step_volume_spike(target_date: date) -> int:
        from stocks.services import calculate_volume_spike_for_date
        return calculate_volume_spike_for_date(target_date)

    @staticmethod
    def _step_global_market(target_date: date) -> str:
        from global_market.services import fetch_global_market_data
        gm = fetch_global_market_data(target_date)
        return f"OK (id={gm.pk})" if gm else "no data"

    @staticmethod
    def _step_market_bias(target_date: date) -> str:
        from global_market.services import calculate_market_bias_for_date
        bias = calculate_market_bias_for_date(target_date)
        return bias or "N/A"

    @staticmethod
    def _step_signals(target_date: date) -> int:
        from stocks.services import generate_signals_for_date
        return generate_signals_for_date(target_date)

    @staticmethod
    def _step_ai_insight(target_date: date) -> str:
        from insights.services import generate_daily_insight
        insight = generate_daily_insight(target_date)
        if insight:
            return f"generated (id={insight.pk})"
        return "skipped (no data)"
