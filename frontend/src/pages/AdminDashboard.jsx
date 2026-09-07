import React, { useState, useEffect } from "react";
import { api } from "../services/api";
import { wsService } from "../services/websocket";
import MetricCard from "../components/MetricCard";
import { 
  Server, 
  Cpu, 
  HardDrive, 
  ShieldAlert, 
  Activity, 
  Wifi, 
  Terminal, 
  RefreshCw, 
  Users, 
  Layers 
} from "lucide-react";

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [nodes, setNodes] = useState([]);
  const [logs, setLogs] = useState([]);
  const [logFilter, setLogFilter] = useState("ALL");
  const [loading, setLoading] = useState(true);

  const fetchAdminData = async () => {
    try {
      const [statsData, nodesData, logsData] = await Promise.all([
        api.getAdminStats().catch(() => null),
        api.getNodes(),
        api.getSystemLogs(),
      ]);
      setStats(statsData);
      setNodes(nodesData.nodes || []);
      setLogs(logsData || []);
    } catch (err) {
      console.error("Admin fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAdminData();

    const handleNodeChange = () => fetchAdminData();
    const handleTelemetry = (data) => {
      setNodes((prev) =>
        prev.map((n) =>
          n.node_id === data.node_id
            ? { ...n, cpu_usage: data.cpu_usage, ram_usage_percent: data.ram_usage_percent, gpu_usage_percent: data.gpu_usage_percent, latency_ms: data.latency_ms, status: data.status }
            : n
        )
      );
    };

    wsService.on("node_connected", handleNodeChange);
    wsService.on("node_disconnected", handleNodeChange);
    wsService.on("node_telemetry", handleTelemetry);

    return () => {
      wsService.off("node_connected", handleNodeChange);
      wsService.off("node_disconnected", handleNodeChange);
      wsService.off("node_telemetry", handleTelemetry);
    };
  }, []);

  const filteredLogs = logs.filter((l) => logFilter === "ALL" || l.level === logFilter);

  return (
    <div className="app-container animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: "1.75rem" }}>
      {/* Admin Title */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 800, color: "#ffffff" }}>
            Admin Cluster & Volunteer Fleet Management
          </h1>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
            Live telemetry monitoring, anomaly detection, hardware capabilities, and cluster logs.
          </p>
        </div>
        <button onClick={fetchAdminData} className="btn-secondary">
          <RefreshCw size={15} />
          <span>Refresh Fleet</span>
        </button>
      </div>

      {/* Overview Metric Cards */}
      <div className="grid-cols-4">
        <MetricCard
          title="Total Registered Nodes"
          value={nodes.length}
          subtitle={`${nodes.filter(n => n.status !== "OFFLINE").length} active/online`}
          icon={Server}
          color="var(--primary)"
        />
        <MetricCard
          title="Cluster Compute Capability"
          value={`${nodes.reduce((acc, n) => acc + (n.overall_capability_score || 1.0), 0).toFixed(1)} pts`}
          subtitle="Normalized benchmark capacity"
          icon={Cpu}
          color="var(--accent-cyan)"
        />
        <MetricCard
          title="Unhealthy / Anomalies"
          value={nodes.filter(n => n.status === "UNHEALTHY").length}
          subtitle="Hardware or network degradation"
          icon={ShieldAlert}
          color="var(--accent-rose)"
        />
        <MetricCard
          title="Average Fleet Trust"
          value={stats ? `${(stats.avg_node_reliability * 100).toFixed(0)}%` : "98%"}
          subtitle="Dynamic reliability score"
          icon={Activity}
          color="var(--accent-emerald)"
        />
      </div>

      {/* Volunteer Nodes Hardware Fleet Grid */}
      <div>
        <h2 style={{ fontSize: "1.15rem", fontWeight: 700, color: "#ffffff", marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <Server size={18} color="var(--primary)" />
          Connected Volunteer Worker Fleet
        </h2>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: "1.25rem" }}>
          {nodes.map((node) => {
            const isOnline = ["ONLINE", "BUSY"].includes(node.status);
            const isUnhealthy = node.status === "UNHEALTHY";
            
            return (
              <div 
                key={node.id} 
                className="glass-panel" 
                style={{ 
                  padding: "1.25rem",
                  borderLeft: isUnhealthy ? "4px solid var(--accent-rose)" : node.status === "BUSY" ? "4px solid var(--primary)" : isOnline ? "4px solid var(--accent-emerald)" : "4px solid var(--text-dim)"
                }}
              >
                {/* Node Title & Status Pill */}
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.75rem" }}>
                  <div>
                    <span style={{ fontSize: "1.1rem", fontWeight: 700, color: "#ffffff" }}>{node.node_id}</span>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>{node.hostname || "volunteer-node"}</div>
                  </div>
                  <span className={`status-pill ${isUnhealthy ? "status-unhealthy" : node.status === "BUSY" ? "status-busy" : isOnline ? "status-online" : "status-offline"}`}>
                    {isOnline && <span className="pulse-dot" style={{ background: isUnhealthy ? "#f59e0b" : node.status === "BUSY" ? "#38bdf8" : "#10b981" }} />}
                    {node.status}
                  </span>
                </div>

                {/* Specs List */}
                <div style={{ fontSize: "0.78rem", display: "flex", flexDirection: "column", gap: "0.4rem", color: "var(--text-muted)" }}>
                  <div>
                    <strong>GPU:</strong> <span style={{ color: "var(--text-main)" }}>{node.gpu_name}</span> {node.gpu_memory_total_mb > 0 && `(${(node.gpu_memory_total_mb / 1024).toFixed(1)} GB)`}
                  </div>
                  <div>
                    <strong>CPU:</strong> <span style={{ color: "var(--text-main)" }}>{node.cpu_cores} Cores</span> ({node.cpu_name || "CPU"})
                  </div>
                  <div>
                    <strong>RAM:</strong> <span style={{ color: "var(--text-main)" }}>{(node.ram_total_mb / 1024).toFixed(1)} GB Total</span>
                  </div>
                  <div>
                    <strong>Network:</strong> <span style={{ color: "var(--text-main)" }}>{node.network_download_mbps.toFixed(0)} Mbps</span> • Latency: {node.latency_ms.toFixed(1)}ms
                  </div>
                  <div>
                    <strong>Reliability Score:</strong> <strong style={{ color: "var(--accent-emerald)" }}>{(node.reliability_score * 100).toFixed(0)}%</strong> (Tasks: {node.tasks_completed} ok, {node.tasks_failed} fail)
                  </div>
                </div>

                {/* Telemetry Progress Bars */}
                <div style={{ marginTop: "1rem", paddingTop: "0.75rem", borderTop: "1px solid var(--border-color)", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.72rem", color: "var(--text-muted)", marginBottom: "0.2rem" }}>
                      <span>CPU Utilization</span>
                      <span>{node.cpu_usage.toFixed(0)}%</span>
                    </div>
                    <div className="progress-bar-container">
                      <div className="progress-bar-fill" style={{ width: `${node.cpu_usage}%`, background: node.cpu_usage > 85 ? "var(--accent-rose)" : "var(--primary-gradient)" }} />
                    </div>
                  </div>

                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.72rem", color: "var(--text-muted)", marginBottom: "0.2rem" }}>
                      <span>RAM Utilization</span>
                      <span>{node.ram_usage_percent.toFixed(0)}%</span>
                    </div>
                    <div className="progress-bar-container">
                      <div className="progress-bar-fill" style={{ width: `${node.ram_usage_percent}%`, background: node.ram_usage_percent > 85 ? "var(--accent-rose)" : "var(--secondary-gradient)" }} />
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Real-Time System Log Explorer */}
      <div className="glass-panel" style={{ padding: "1.5rem" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.25rem" }}>
          <h2 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#ffffff", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <Terminal size={18} color="var(--accent-cyan)" />
            Broker Server & Cluster System Logs
          </h2>

          <div style={{ display: "flex", gap: "0.4rem" }}>
            {["ALL", "INFO", "WARNING", "ERROR"].map((lvl) => (
              <button
                key={lvl}
                onClick={() => setLogFilter(lvl)}
                className="btn-secondary"
                style={{
                  padding: "0.25rem 0.65rem",
                  fontSize: "0.75rem",
                  background: logFilter === lvl ? "rgba(56, 189, 248, 0.2)" : "transparent",
                  borderColor: logFilter === lvl ? "var(--primary)" : "var(--border-color)"
                }}
              >
                {lvl}
              </button>
            ))}
          </div>
        </div>

        <div style={{
          background: "rgba(0, 0, 0, 0.4)",
          border: "1px solid var(--border-color)",
          borderRadius: "10px",
          padding: "1rem",
          maxHeight: "300px",
          overflowY: "auto",
          fontFamily: "JetBrains Mono, monospace",
          fontSize: "0.78rem",
          display: "flex",
          flexDirection: "column",
          gap: "0.4rem"
        }}>
          {filteredLogs.length === 0 ? (
            <div style={{ color: "var(--text-dim)" }}>No logs matching filter.</div>
          ) : (
            filteredLogs.map((l) => {
              const color = l.level === "ERROR" ? "#f43f5e" : l.level === "WARNING" ? "#fbbf24" : "#94a3b8";
              return (
                <div key={l.id} style={{ display: "flex", gap: "0.75rem", alignItems: "flex-start" }}>
                  <span style={{ color: "var(--text-dim)" }}>{new Date(l.timestamp).toLocaleTimeString()}</span>
                  <span style={{ color, fontWeight: 600, minWidth: "60px" }}>[{l.level}]</span>
                  <span style={{ color: "var(--primary)", minWidth: "90px" }}>[{l.component}]</span>
                  <span style={{ color: "#f1f5f9" }}>{l.message}</span>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
