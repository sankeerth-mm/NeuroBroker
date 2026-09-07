import React, { useState, useEffect } from "react";
import { api } from "../services/api";
import { wsService } from "../services/websocket";
import MetricCard from "../components/MetricCard";
import { 
  Activity, 
  Layers, 
  PlayCircle, 
  Server, 
  CheckCircle2, 
  XCircle, 
  ArrowUpRight, 
  ShieldCheck, 
  HardDrive, 
  Clock, 
  Download, 
  Plus 
} from "lucide-react";

export default function UserDashboard({ setActiveTab, setSelectedJobId }) {
  const [jobs, setJobs] = useState([]);
  const [nodes, setNodes] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    try {
      const [jobsData, nodesData] = await Promise.all([
        api.getJobs(),
        api.getNodes(),
      ]);
      setJobs(jobsData || []);
      setNodes(nodesData.nodes || []);
    } catch (e) {
      console.error("Dashboard fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();

    const handleJobChange = () => fetchDashboardData();
    const handleNodeChange = () => fetchDashboardData();

    wsService.on("job_status_change", handleJobChange);
    wsService.on("round_completed", handleJobChange);
    wsService.on("node_connected", handleNodeChange);
    wsService.on("node_disconnected", handleNodeChange);

    return () => {
      wsService.off("job_status_change", handleJobChange);
      wsService.off("round_completed", handleJobChange);
      wsService.off("node_connected", handleNodeChange);
      wsService.off("node_disconnected", handleNodeChange);
    };
  }, []);

  const runningJobs = jobs.filter((j) => ["TRAINING", "SCHEDULING", "PARTITIONING", "AGGREGATING", "QUEUED"].includes(j.status));
  const completedJobs = jobs.filter((j) => j.status === "COMPLETED");
  const failedJobs = jobs.filter((j) => j.status === "FAILED");
  const onlineNodes = nodes.filter((n) => ["ONLINE", "BUSY"].includes(n.status));

  const avgReliability = nodes.length > 0
    ? (nodes.reduce((acc, n) => acc + (n.reliability_score || 1.0), 0) / nodes.length) * 100
    : 100;

  const handleViewJob = (jobId) => {
    setSelectedJobId(jobId);
    setActiveTab("training");
  };

  return (
    <div className="app-container animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: "1.75rem" }}>
      {/* Welcome Banner */}
      <div className="glass-panel" style={{
        padding: "1.75rem 2rem",
        background: "linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.7) 100%)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        borderLeft: "4px solid var(--primary)"
      }}>
        <div>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 700, color: "#ffffff" }}>
            Federated Training Compute Brokerage Dashboard
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.88rem", marginTop: "0.25rem" }}>
            Orchestrating resource-aware dataset partitioning and FedAvg weight aggregation across volunteer nodes.
          </p>
        </div>

        <div style={{ display: "flex", gap: "0.75rem" }}>
          <button 
            onClick={() => setActiveTab("create_job")} 
            className="btn-primary"
          >
            <Plus size={16} />
            <span>New Training Job</span>
          </button>
          <a
            href={api.getVolunteerClientDownloadUrl()}
            download
            className="btn-secondary"
            style={{ textDecoration: "none" }}
          >
            <Download size={16} />
            <span>Volunteer Client</span>
          </a>
        </div>
      </div>

      {/* Top Metrics Row */}
      <div className="grid-cols-4">
        <MetricCard
          title="Total Training Jobs"
          value={jobs.length}
          subtitle={`${runningJobs.length} active in cluster`}
          icon={Layers}
          color="var(--primary)"
        />
        <MetricCard
          title="Connected Volunteers"
          value={onlineNodes.length}
          subtitle={`${nodes.length} registered total`}
          icon={Server}
          color="var(--accent-emerald)"
        />
        <MetricCard
          title="Completed Jobs"
          value={completedJobs.length}
          subtitle={`${failedJobs.length} failed jobs`}
          icon={CheckCircle2}
          color="var(--accent-cyan)"
        />
        <MetricCard
          title="Fleet Reliability"
          value={`${avgReliability.toFixed(0)}%`}
          subtitle="Dynamic trust score average"
          icon={ShieldCheck}
          color="var(--accent-purple)"
        />
      </div>

      {/* Main Content: Jobs Table & Fleet Preview */}
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "1.5rem" }}>
        {/* Left: Training Jobs List */}
        <div className="glass-panel" style={{ padding: "1.5rem" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.25rem" }}>
            <h2 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#ffffff", display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <Activity size={18} color="var(--primary)" />
              Training Jobs Overview
            </h2>
            <button 
              onClick={() => setActiveTab("create_job")} 
              className="btn-secondary" 
              style={{ fontSize: "0.78rem", padding: "0.35rem 0.75rem" }}
            >
              + Create Job
            </button>
          </div>

          {jobs.length === 0 ? (
            <div style={{ textAlign: "center", padding: "3rem 1rem", color: "var(--text-muted)" }}>
              <Layers size={36} color="var(--text-dim)" style={{ marginBottom: "0.75rem" }} />
              <div style={{ fontWeight: 600, color: "var(--text-main)" }}>No training jobs created yet</div>
              <p style={{ fontSize: "0.85rem", marginTop: "0.25rem" }}>
                Upload a model package and dataset to launch your first distributed training run.
              </p>
              <button 
                onClick={() => setActiveTab("create_job")} 
                className="btn-primary" 
                style={{ marginTop: "1rem", fontSize: "0.85rem" }}
              >
                Launch First Job
              </button>
            </div>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.85rem" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border-color)", color: "var(--text-dim)", textTransform: "uppercase", fontSize: "0.72rem", letterSpacing: "0.05em" }}>
                    <th style={{ padding: "0.75rem 0.5rem" }}>Job</th>
                    <th style={{ padding: "0.75rem 0.5rem" }}>Status</th>
                    <th style={{ padding: "0.75rem 0.5rem" }}>Round</th>
                    <th style={{ padding: "0.75rem 0.5rem" }}>Accuracy</th>
                    <th style={{ padding: "0.75rem 0.5rem" }}>Loss</th>
                    <th style={{ padding: "0.75rem 0.5rem", textAlign: "right" }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.map((job) => {
                    const isRunning = ["TRAINING", "SCHEDULING", "PARTITIONING", "AGGREGATING"].includes(job.status);
                    const progress = job.max_rounds > 0 ? (job.current_round / job.max_rounds) * 100 : 0;
                    
                    return (
                      <tr key={job.id} style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.04)" }}>
                        <td style={{ padding: "0.85rem 0.5rem" }}>
                          <div style={{ fontWeight: 600, color: "#ffffff" }}>{job.name}</div>
                          <div style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>{job.job_code}</div>
                        </td>
                        <td style={{ padding: "0.85rem 0.5rem" }}>
                          <span className={`status-pill ${isRunning ? "status-busy" : job.status === "COMPLETED" ? "status-online" : "status-offline"}`}>
                            {isRunning && <span className="pulse-dot" style={{ background: "#38bdf8" }} />}
                            {job.status}
                          </span>
                        </td>
                        <td style={{ padding: "0.85rem 0.5rem" }}>
                          <div style={{ fontWeight: 500 }}>
                            {job.current_round} / {job.max_rounds}
                          </div>
                          <div className="progress-bar-container" style={{ width: "70px", marginTop: "0.25rem" }}>
                            <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
                          </div>
                        </td>
                        <td style={{ padding: "0.85rem 0.5rem", fontWeight: 600, color: job.global_accuracy > 0 ? "var(--accent-emerald)" : "var(--text-dim)" }}>
                          {job.global_accuracy > 0 ? `${job.global_accuracy.toFixed(2)}%` : "—"}
                        </td>
                        <td style={{ padding: "0.85rem 0.5rem", color: "var(--text-muted)" }}>
                          {job.global_loss > 0 ? job.global_loss.toFixed(4) : "—"}
                        </td>
                        <td style={{ padding: "0.85rem 0.5rem", textAlign: "right" }}>
                          <button
                            onClick={() => handleViewJob(job.id)}
                            className="btn-secondary"
                            style={{ padding: "0.35rem 0.75rem", fontSize: "0.78rem" }}
                          >
                            <span>Live View</span>
                            <ArrowUpRight size={14} />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Right: Connected Volunteer Fleet Mini List */}
        <div className="glass-panel" style={{ padding: "1.5rem" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.25rem" }}>
            <h2 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#ffffff", display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <Server size={18} color="var(--accent-emerald)" />
              Volunteer Fleet
            </h2>
            <button 
              onClick={() => setActiveTab("admin")} 
              className="btn-secondary" 
              style={{ fontSize: "0.78rem", padding: "0.35rem 0.65rem" }}
            >
              All Nodes
            </button>
          </div>

          {nodes.length === 0 ? (
            <div style={{ textAlign: "center", padding: "2rem 1rem", color: "var(--text-muted)" }}>
              <Server size={32} color="var(--text-dim)" style={{ marginBottom: "0.5rem" }} />
              <div style={{ fontSize: "0.85rem", fontWeight: 600 }}>No volunteer nodes connected</div>
              <p style={{ fontSize: "0.75rem", marginTop: "0.25rem" }}>
                Run <code>python demo.py</code> or start a remote volunteer worker.
              </p>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              {nodes.slice(0, 5).map((node) => {
                const isOnline = ["ONLINE", "BUSY"].includes(node.status);
                return (
                  <div
                    key={node.id}
                    style={{
                      background: "rgba(255, 255, 255, 0.03)",
                      border: "1px solid var(--border-color)",
                      borderRadius: "10px",
                      padding: "0.85rem",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between"
                    }}
                  >
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: "0.45rem" }}>
                        <span style={{ fontWeight: 600, fontSize: "0.85rem", color: "#ffffff" }}>{node.node_id}</span>
                        <span className={`status-pill ${node.status === "BUSY" ? "status-busy" : isOnline ? "status-online" : "status-offline"}`} style={{ fontSize: "0.65rem", padding: "0.15rem 0.5rem" }}>
                          {node.status}
                        </span>
                      </div>
                      <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
                        {node.gpu_name !== "CPU Only" ? node.gpu_name : `${node.cpu_cores} Core CPU`} • Rel: {(node.reliability_score * 100).toFixed(0)}%
                      </div>
                    </div>

                    <div style={{ textAlign: "right", fontSize: "0.75rem" }}>
                      <div style={{ color: "var(--text-dim)" }}>CPU: {node.cpu_usage.toFixed(0)}%</div>
                      <div style={{ color: "var(--text-dim)" }}>RAM: {node.ram_usage_percent.toFixed(0)}%</div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
