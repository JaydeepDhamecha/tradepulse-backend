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

  return (
    <div className="min-h-screen bg-gray-950">
      {/* Header */}
      <header className="sticky top-0 z-10 border-b border-gray-800 bg-gray-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
          <h1 className="text-xl font-bold tracking-tight text-white">
            TradePulse <span className="text-emerald-400">AI</span>
          </h1>
          <button
            onClick={logout}
            className="rounded-lg bg-gray-800 px-4 py-1.5 text-sm text-gray-300 transition hover:bg-gray-700 hover:text-white"
          >
            Logout
          </button>
        </div>
      </header>

      {/* Content */}
      <main className="mx-auto max-w-7xl space-y-6 px-4 py-6 sm:px-6">
        {/* ── Top: Global Markets ── */}
        <GlobalMarketCard />

        {/* ── Middle: Bias + AI Insight ── */}
        <div className="grid gap-6 lg:grid-cols-3">
          <MarketBiasSummary />
          <div className="lg:col-span-2">
            <AIInsightBox />
          </div>
        </div>

        {/* ── Charts ── */}
        <div className="grid gap-6 lg:grid-cols-3">
          <DeliveryChart />
          <OIChangeChart />
          <VolumeSpikeChart />
        </div>

        {/* ── Tables ── */}
        <SignalsTable />

        <div className="grid gap-6 lg:grid-cols-2">
          <DeliveryTable />
          <VolumeSpikeTable />
        </div>
      </main>
    </div>
  );
}
