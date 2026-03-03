import { useEffect, useState } from "react";
import API from "../api/axios";

const biasConfig = {
  BULLISH: { color: "text-emerald-400", bg: "bg-emerald-500/10", icon: "\u25B2" },
  BEARISH: { color: "text-red-400", bg: "bg-red-500/10", icon: "\u25BC" },
  NEUTRAL: { color: "text-yellow-400", bg: "bg-yellow-500/10", icon: "\u25C6" },
};

export default function MarketBiasSummary() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    API.get("/api/global-market/latest/")
      .then((r) => setData(r.data))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="animate-pulse rounded-2xl border border-gray-800 bg-gray-900 p-6">
        <div className="h-5 w-36 rounded bg-gray-800" />
        <div className="mt-4 h-12 w-40 rounded bg-gray-800" />
      </div>
    );
  }

  const bias = data?.market_bias || "NEUTRAL";
  const cfg = biasConfig[bias] || biasConfig.NEUTRAL;

  return (
    <div className="rounded-2xl border border-gray-800 bg-gray-900 p-6">
      <h2 className="mb-3 text-lg font-semibold text-white">Market Bias</h2>
      <div
        className={`inline-flex items-center gap-2 rounded-xl px-5 py-3 text-2xl font-bold ${cfg.bg} ${cfg.color}`}
      >
        <span>{cfg.icon}</span>
        <span>{bias}</span>
      </div>
      {data?.date && (
        <p className="mt-3 text-xs text-gray-500">As of {data.date}</p>
      )}
    </div>
  );
}
