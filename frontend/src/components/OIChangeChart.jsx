import { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import API from "../api/axios";

export default function OIChangeChart() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    API.get("/api/stocks/top-delivery/")
      .then((r) => {
        const rows = (r.data.results ?? r.data)
          .filter((s) => s.oi_change != null)
          .sort((a, b) => Math.abs(b.oi_change) - Math.abs(a.oi_change))
          .slice(0, 10)
          .map((s) => ({
            symbol: s.symbol,
            oi_change: Number(s.oi_change),
          }));
        setData(rows);
      })
      .catch(() => setData([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="rounded-2xl border border-gray-800 bg-gray-900 p-6">
      <h2 className="mb-4 text-lg font-semibold text-white">
        OI Change (Top 10)
      </h2>
      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-700 border-t-blue-400" />
        </div>
      ) : data.length === 0 ? (
        <p className="py-16 text-center text-sm text-gray-500">No OI data.</p>
      ) : (
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
            <XAxis
              dataKey="symbol"
              tick={{ fill: "#9ca3af", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: "#9ca3af", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) =>
                Math.abs(v) >= 1_000_000
                  ? `${(v / 1_000_000).toFixed(1)}M`
                  : Math.abs(v) >= 1_000
                    ? `${(v / 1_000).toFixed(0)}K`
                    : v
              }
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1f2937",
                border: "1px solid #374151",
                borderRadius: "0.5rem",
                fontSize: "0.8rem",
              }}
              labelStyle={{ color: "#f3f4f6" }}
              formatter={(v) => [Number(v).toLocaleString("en-IN"), "OI Change"]}
            />
            <Bar dataKey="oi_change" radius={[6, 6, 0, 0]}>
              {data.map((entry, i) => (
                <Cell
                  key={i}
                  fill={entry.oi_change >= 0 ? "#60a5fa" : "#f87171"}
                  fillOpacity={0.8}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
