import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import GlobalMarketCard from "../components/GlobalMarketCard";
import MarketBiasSummary from "../components/MarketBiasSummary";
import AIInsightBox from "../components/AIInsightBox";
import SignalsTable from "../components/SignalsTable";
import DeliveryTable from "../components/DeliveryTable";
import VolumeSpikeTable from "../components/VolumeSpikeTable";
import DeliveryChart from "../components/DeliveryChart";
import OIChangeChart from "../components/OIChangeChart";
import VolumeSpikeChart from "../components/VolumeSpikeChart";

export default function Dashboard() {
  const { logout } = useAuth();
  const [selectedDate, setSelectedDate] = useState("");

  return (
    <div className="min-h-screen bg-gray-950">
      {/* Header */}
      <header className="sticky top-0 z-10 border-b border-gray-800 bg-gray-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
          <h1 className="text-xl font-bold tracking-tight text-white">
            TradePulse <span className="text-emerald-400">AI</span>
          </h1>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-1.5 text-sm text-gray-200 outline-none transition focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
              />
              {selectedDate && (
                <button
                  onClick={() => setSelectedDate("")}
                  className="rounded-lg bg-gray-800 px-3 py-1.5 text-xs text-gray-400 transition hover:bg-gray-700 hover:text-white"
                  title="Clear date — show latest"
                >
                  Latest
                </button>
              )}
            </div>
            <button
              onClick={logout}
              className="rounded-lg bg-gray-800 px-4 py-1.5 text-sm text-gray-300 transition hover:bg-gray-700 hover:text-white"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="mx-auto max-w-7xl space-y-6 px-4 py-6 sm:px-6">
        {/* ── Top: Global Markets ── */}
        <GlobalMarketCard date={selectedDate} />

        {/* ── Middle: Bias + AI Insight ── */}
        <div className="grid gap-6 lg:grid-cols-3">
          <MarketBiasSummary date={selectedDate} />
          <div className="lg:col-span-2">
            <AIInsightBox date={selectedDate} />
          </div>
        </div>

        {/* ── Charts ── */}
        <div className="grid gap-6 lg:grid-cols-3">
          <DeliveryChart date={selectedDate} />
          <OIChangeChart date={selectedDate} />
          <VolumeSpikeChart date={selectedDate} />
        </div>

        {/* ── Tables ── */}
        <SignalsTable date={selectedDate} />

        <div className="grid gap-6 lg:grid-cols-2">
          <DeliveryTable date={selectedDate} />
          <VolumeSpikeTable date={selectedDate} />
        </div>
      </main>
    </div>
  );
}
