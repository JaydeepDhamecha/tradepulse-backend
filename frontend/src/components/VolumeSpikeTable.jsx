import { useEffect, useState } from "react";
import API from "../api/axios";

export default function VolumeSpikeTable({ date }) {
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const params = date ? { date } : {};
    API.get("/api/stocks/volume-spike/", { params })
      .then((r) => setStocks((r.data.results ?? r.data).slice(0, 15)))
      .catch(() => setStocks([]))
      .finally(() => setLoading(false));
  }, [date]);

  return (
    <div className="rounded-2xl border border-gray-800 bg-gray-900 p-6">
      <h2 className="mb-4 text-lg font-semibold text-white">
        Volume Spikes
      </h2>

      {loading ? (
        <RowsSkeleton />
      ) : stocks.length === 0 ? (
        <p className="py-8 text-center text-sm text-gray-500">No data available.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-xs uppercase text-gray-500">
                <th className="pb-3 pr-4">Symbol</th>
                <th className="pb-3 pr-4 text-right">Volume</th>
                <th className="pb-3 pr-4 text-right">Spike Ratio</th>
                <th className="pb-3 text-right">Close</th>
              </tr>
            </thead>
            <tbody>
              {stocks.map((s) => {
                const ratio = parseFloat(s.volume_spike_ratio);
                return (
                  <tr
                    key={s.id}
                    className="border-b border-gray-800/50 last:border-0"
                  >
                    <td className="py-2.5 pr-4 font-medium text-white">
                      {s.symbol}
                    </td>
                    <td className="py-2.5 pr-4 text-right font-mono text-gray-300">
                      {Number(s.volume).toLocaleString("en-IN")}
                    </td>
                    <td
                      className={`py-2.5 pr-4 text-right font-mono font-semibold ${
                        ratio >= 2 ? "text-orange-400" : "text-gray-300"
                      }`}
                    >
                      {ratio.toFixed(2)}x
                    </td>
                    <td className="py-2.5 text-right font-mono text-gray-300">
                      {parseFloat(s.close).toFixed(2)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function RowsSkeleton() {
  return (
    <div className="space-y-3">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="flex gap-4">
          <div className="h-4 w-20 animate-pulse rounded bg-gray-800" />
          <div className="h-4 flex-1 animate-pulse rounded bg-gray-800" />
          <div className="h-4 w-16 animate-pulse rounded bg-gray-800" />
          <div className="h-4 w-16 animate-pulse rounded bg-gray-800" />
        </div>
      ))}
    </div>
  );
}
