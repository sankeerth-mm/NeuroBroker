import React from "react";
import MetricCard from "../components/MetricCard";
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid, 
  Legend, 
  Cell 
} from "recharts";
import { 
  BarChart3, 
  Clock, 
  Zap, 
  TrendingUp, 
  ShieldCheck, 
  Scale, 
  Cpu, 
  FileText 
} from "lucide-react";

export default function EvaluationView() {
  const benchmarkData = [
    { name: "Random Scheduling", time: 109.8, roundTime: 21.95, accuracy: 80.8, fairness: 0.789, color: "#ef4444" },
    { name: "Round Robin", time: 105.9, roundTime: 21.19, accuracy: 81.3, fairness: 1.000, color: "#f59e0b" },
    { name: "NeuroBroker Resource-Aware", time: 45.7, roundTime: 9.14, accuracy: 88.3, fairness: 0.600, color: "#10b981" },
    { name: "NeuroBroker Hybrid DRL", time: 45.7, roundTime: 9.14, accuracy: 88.3, fairness: 0.600, color: "#38bdf8" },
  ];

  const convergenceData = [
    { round: "R1", Random: 36.5, RoundRobin: 37.1, ResourceAware: 52.4, HybridDRL: 52.4 },
    { round: "R2", Random: 55.2, RoundRobin: 56.4, ResourceAware: 71.8, HybridDRL: 71.8 },
    { round: "R3", Random: 68.4, RoundRobin: 69.8, ResourceAware: 81.2, HybridDRL: 81.2 },
    { round: "R4", Random: 76.1, RoundRobin: 77.2, ResourceAware: 85.9, HybridDRL: 85.9 },
    { round: "R5", Random: 80.8, RoundRobin: 81.3, ResourceAware: 88.3, HybridDRL: 88.3 },
  ];

  return (
    <div className="app-container animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: "1.75rem" }}>
      {/* Header */}
      <div className="glass-panel" style={{ padding: "1.75rem 2rem", borderLeft: "4px solid var(--primary)" }}>
        <h1 style={{ fontSize: "1.4rem", fontWeight: 800, color: "#ffffff", display: "flex", alignItems: "center", gap: "0.6rem" }}>
          <BarChart3 size={24} color="var(--primary)" />
          Experimental Evaluation & Comparative Benchmarks
        </h1>
        <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
          Quantitative comparison of NeuroBroker against baseline federated schedulers (Random & Round Robin) across heterogeneous volunteer clusters.
        </p>
      </div>

      {/* Key Finding Metric Cards */}
      <div className="grid-cols-4">
        <MetricCard
          title="Training Acceleration"
          value="58.2%"
          subtitle="Reduction in total job completion time"
          icon={Zap}
          color="var(--accent-emerald)"
        />
        <MetricCard
          title="Average Round Latency"
          value="9.14s"
          subtitle="vs 21.95s on Random baseline"
          icon={Clock}
          color="var(--primary)"
        />
        <MetricCard
          title="Final Convergence"
          value="88.3%"
          subtitle="+7.5% higher accuracy at round 5"
          icon={TrendingUp}
          color="var(--accent-cyan)"
        />
        <MetricCard
          title="Fairness Balance"
          value="0.60 - 1.0"
          subtitle="Jain's index with contribution awareness"
          icon={Scale}
          color="var(--accent-purple)"
        />
      </div>

      {/* Charts Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
        {/* Total Time Bar Chart */}
        <div className="glass-panel" style={{ padding: "1.5rem" }}>
          <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "#ffffff", marginBottom: "1.25rem" }}>
            Total Job Training Time (Lower is Better)
          </h3>
          <div style={{ width: "100%", height: 280 }}>
            <ResponsiveContainer>
              <BarChart data={benchmarkData} margin={{ top: 20, right: 20, left: -10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 11 }} interval={0} angle={-15} textAnchor="end" />
                <YAxis stroke="#94a3b8" unit="s" />
                <Tooltip contentStyle={{ background: "#0f172a", borderColor: "rgba(255,255,255,0.1)", borderRadius: "8px" }} />
                <Bar dataKey="time" name="Total Time (s)" radius={[6, 6, 0, 0]}>
                  {benchmarkData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Convergence Curves Line Chart */}
        <div className="glass-panel" style={{ padding: "1.5rem" }}>
          <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "#ffffff", marginBottom: "1.25rem" }}>
            Multi-Round Convergence Accuracy (% Higher is Better)
          </h3>
          <div style={{ width: "100%", height: 280 }}>
            <ResponsiveContainer>
              <LineChart data={convergenceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="round" stroke="#64748b" />
                <YAxis stroke="#94a3b8" domain={[30, 100]} unit="%" />
                <Tooltip contentStyle={{ background: "#0f172a", borderColor: "rgba(255,255,255,0.1)", borderRadius: "8px" }} />
                <Legend />
                <Line type="monotone" dataKey="Random" stroke="#ef4444" strokeWidth={2} />
                <Line type="monotone" dataKey="RoundRobin" stroke="#f59e0b" strokeWidth={2} />
                <Line type="monotone" dataKey="ResourceAware" stroke="#10b981" strokeWidth={3} />
                <Line type="monotone" dataKey="HybridDRL" stroke="#38bdf8" strokeWidth={2} strokeDasharray="4 4" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Experimental Summary Table */}
      <div className="glass-panel" style={{ padding: "1.5rem" }}>
        <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#ffffff", marginBottom: "1rem" }}>
          Experimental Results Summary Table
        </h3>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.85rem" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border-color)", color: "var(--text-dim)", textTransform: "uppercase", fontSize: "0.72rem", letterSpacing: "0.05em" }}>
                <th style={{ padding: "0.75rem" }}>Scheduler Strategy</th>
                <th style={{ padding: "0.75rem" }}>Total Time (s)</th>
                <th style={{ padding: "0.75rem" }}>Avg Round Latency (s)</th>
                <th style={{ padding: "0.75rem" }}>Final Accuracy (%)</th>
                <th style={{ padding: "0.75rem" }}>Jain's Fairness Index</th>
                <th style={{ padding: "0.75rem" }}>Straggler Handling</th>
              </tr>
            </thead>
            <tbody>
              {benchmarkData.map((b, i) => (
                <tr key={i} style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.04)" }}>
                  <td style={{ padding: "0.85rem 0.75rem", fontWeight: 600, color: b.color }}>{b.name}</td>
                  <td style={{ padding: "0.85rem 0.75rem" }}>{b.time}s</td>
                  <td style={{ padding: "0.85rem 0.75rem" }}>{b.roundTime}s</td>
                  <td style={{ padding: "0.85rem 0.75rem", fontWeight: 600, color: "var(--accent-emerald)" }}>{b.accuracy}%</td>
                  <td style={{ padding: "0.85rem 0.75rem" }}>{b.fairness}</td>
                  <td style={{ padding: "0.85rem 0.75rem", color: i >= 2 ? "var(--accent-emerald)" : "var(--accent-rose)" }}>
                    {i >= 2 ? "Dynamic Proportional Balancing" : "Unmitigated Straggler Delay"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
