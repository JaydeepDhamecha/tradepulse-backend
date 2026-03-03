import { useEffect, useState } from "react";
import API from "../api/axios";

const typeBadge = {
  BUY: "bg-emerald-500/15 text-emerald-400",
  SELL: "bg-red-500/15 text-red-400",
  HOLD: "bg-yellow-500/15 text-yellow-400",
};

export default function SignalsTable() {
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    const params = filter ? { signal_type: filter } : {};
    API.get("/api/stocks/intraday-signals/", { params })
      .then((r) => setSignals(r.data.results ?? r.data))
      .catch(() => setSignals([]))
      .finally(() => setLoading(false));
  }, [filter]);

  return (
    <div className="rounded-2xl border border-gray-800 bg-gray-900 p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Intraday Signals</h2>
        <div className="flex gap-1">
          {["", "BUY", "SELL", "HOLD"].map((f) => (
            <button
              key={f}
              onClick={() => { setLoading(true); setFilter(f); }}
              className={`rounded-lg px-3 py-1 text-xs font-medium transition ${
                filter === f
                  ? "bg-emerald-600 text-white"
                  : "bg-gray-800 text-gray-400 hover:text-white"
              }`}
            >
              {f || "All"}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <TableSkeleton cols={4} />
      ) : signals.length === 0 ? (
        <p className="py-8 text-center text-sm text-gray-500">No signals found.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-xs uppercase text-gray-500">
                <th className="pb-3 pr-4">Symbol</th>
                <th className="pb-3 pr-4">Signal</th>
                <th className="pb-3 pr-4 text-right">Confidence</th>
                <th className="pb-3">Reasoning</th>
              </tr>
            </thead>
            <tbody>
              {signals.map((s) => (
                <tr
                  key={s.id}
                  className="border-b border-gray-800/50 last:border-0"
                >
                  <td className="py-3 pr-4 font-medium text-white">
                    {s.symbol}
                  </td>
                  <td className="py-3 pr-4">
                    <span
                      className={`rounded-md px-2.5 py-1 text-xs font-semibold ${typeBadge[s.signal_type] || ""}`}
                    >
                      {s.signal_type}
                    </span>
                  </td>
                  <td className="py-3 pr-4 text-right font-mono text-gray-300">
                    {parseFloat(s.confidence_score).toFixed(1)}%
                  </td>
                  <td className="max-w-xs truncate py-3 text-gray-400">
                    {s.reasoning_summary}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function TableSkeleton({ cols }) {
  return (
    <div className="space-y-3">
      {[1, 2, 3, 4, 5].map((r) => (
        <div key={r} className="flex gap-4">
          {Array.from({ length: cols }).map((_, i) => (
            <div key={i} className="h-4 flex-1 animate-pulse rounded bg-gray-800" />
          ))}
        </div>
      ))}
    </div>
  );
}
