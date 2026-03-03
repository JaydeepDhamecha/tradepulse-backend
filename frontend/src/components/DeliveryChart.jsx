import { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import API from "../api/axios";

export default function DeliveryChart({ date }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const params = date ? { date } : {};
    API.get("/api/stocks/top-delivery/", { params })
      .then((r) => {
        const rows = (r.data.results ?? r.data).slice(0, 10).map((s) => ({
          symbol: s.symbol,
          delivery: parseFloat(s.delivery_percentage),
        }));
        setData(rows);
      })
      .catch(() => setData([]))
      .finally(() => setLoading(false));
  }, [date]);

  return (
    <div className="rounded-2xl border border-gray-800 bg-gray-900 p-6">
      <h2 className="mb-4 text-lg font-semibold text-white">
        Delivery % (Top 10)
      </h2>
      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-700 border-t-emerald-400" />
        </div>
      ) : data.length === 0 ? (
        <p className="py-16 text-center text-sm text-gray-500">No data.</p>
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
              unit="%"
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1f2937",
                border: "1px solid #374151",
                borderRadius: "0.5rem",
                fontSize: "0.8rem",
              }}
              labelStyle={{ color: "#f3f4f6" }}
              formatter={(v) => [`${v.toFixed(1)}%`, "Delivery"]}
            />
            <Bar dataKey="delivery" radius={[6, 6, 0, 0]}>
              {data.map((_, i) => (
                <Cell key={i} fill={i < 3 ? "#34d399" : "#6ee7b7"} fillOpacity={0.8} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
