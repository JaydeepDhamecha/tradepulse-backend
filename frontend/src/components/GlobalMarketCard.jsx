import { useEffect, useState } from "react";
import API from "../api/axios";

const indicators = [
  { key: "gift_nifty_change", label: "GIFT Nifty" },
  { key: "dow_jones_change", label: "Dow Jones" },
  { key: "nasdaq_change", label: "Nasdaq" },
];

export default function GlobalMarketCard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    API.get("/api/global-market/latest/")
      .then((r) => setData(r.data))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <CardSkeleton />;
  if (!data) return <EmptyCard />;

  return (
    <div className="rounded-2xl border border-gray-800 bg-gray-900 p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Global Markets</h2>
        <span className="text-xs text-gray-500">{data.date}</span>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {indicators.map(({ key, label }) => {
          const val = data[key] != null ? parseFloat(data[key]) : null;
          return (
            <div key={key} className="text-center">
              <p className="text-xs text-gray-400">{label}</p>
              {val != null ? (
                <p
                  className={`mt-1 text-xl font-bold ${val >= 0 ? "text-emerald-400" : "text-red-400"}`}
                >
                  {val >= 0 ? "+" : ""}
                  {val.toFixed(2)}%
                </p>
              ) : (
                <p className="mt-1 text-xl font-bold text-gray-600">--</p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function CardSkeleton() {
  return (
    <div className="animate-pulse rounded-2xl border border-gray-800 bg-gray-900 p-6">
      <div className="mb-4 h-5 w-32 rounded bg-gray-800" />
      <div className="grid grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex flex-col items-center gap-2">
            <div className="h-3 w-16 rounded bg-gray-800" />
            <div className="h-6 w-20 rounded bg-gray-800" />
          </div>
        ))}
      </div>
    </div>
  );
}

function EmptyCard() {
  return (
    <div className="rounded-2xl border border-gray-800 bg-gray-900 p-6 text-center text-sm text-gray-500">
      No global market data available.
    </div>
  );
}
