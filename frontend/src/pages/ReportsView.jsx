import React, { useState, useEffect } from "react";
import { api } from "../services/api";
import { 
  FileText, 
  Download, 
  Layers, 
  CheckCircle, 
  Clock, 
  Cpu, 
  RefreshCw, 
  HardDrive 
} from "lucide-react";

export default function ReportsView() {
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchJobs = async () => {
    try {
      const allJobs = await api.getJobs();
      setJobs(allJobs || []);
      if (allJobs.length > 0) {
        selectJob(allJobs[0]);
      }
    } catch (e) {
      console.error("Failed to load jobs:", e);
    } finally {
      setLoading(false);
    }
  };

  const selectJob = async (job) => {
    setSelectedJob(job);
    try {
      const rep = await api.getJobReport(job.id);
      setReport(rep);
    } catch (e) {
      console.error("Failed to fetch report:", e);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const downloadJsonReport = () => {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `neurobroker_job_${selectedJob.id}_report.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="app-container animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: "1.75rem" }}>
      {/* Header */}
      <div className="glass-panel" style={{ padding: "1.75rem 2rem", borderLeft: "4px solid var(--primary)" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div>
            <h1 style={{ fontSize: "1.4rem", fontWeight: 800, color: "#ffffff", display: "flex", alignItems: "center", gap: "0.6rem" }}>
              <FileText size={24} color="var(--primary)" />
              Training Audit Reports & Model Artifacts
            </h1>
            <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
              Download comprehensive training logs, final PyTorch `.pth` model weights, and node contribution breakdowns.
            </p>
          </div>
          <button onClick={fetchJobs} className="btn-secondary" title="Refresh">
            <RefreshCw size={15} />
          </button>
        </div>
      </div>

      {jobs.length === 0 ? (
        <div className="glass-panel" style={{ textAlign: "center", padding: "4rem", color: "var(--text-muted)" }}>
          <FileText size={44} color="var(--text-dim)" style={{ marginBottom: "0.75rem" }} />
          <h3 style={{ color: "#ffffff", fontWeight: 700 }}>No Training Reports Generated</h3>
          <p style={{ fontSize: "0.85rem", marginTop: "0.25rem" }}>
            Run a training job to generate audit reports and download final models.
          </p>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: "1.5rem" }}>
          {/* Left: Jobs List */}
          <div className="glass-panel" style={{ padding: "1.25rem" }}>
            <h3 style={{ fontSize: "0.95rem", fontWeight: 700, color: "#ffffff", marginBottom: "1rem" }}>
              Training Jobs History
            </h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
              {jobs.map((j) => {
                const isSelected = selectedJob?.id === j.id;
                return (
                  <div
                    key={j.id}
                    onClick={() => selectJob(j)}
                    style={{
                      background: isSelected ? "rgba(56, 189, 248, 0.15)" : "rgba(255, 255, 255, 0.02)",
                      border: isSelected ? "1px solid rgba(56, 189, 248, 0.4)" : "1px solid var(--border-color)",
                      borderRadius: "8px",
                      padding: "0.85rem",
                      cursor: "pointer",
                      transition: "all 0.2s ease"
                    }}
                  >
                    <div style={{ fontWeight: 600, color: "#ffffff", fontSize: "0.9rem" }}>{j.name}</div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-dim)", marginTop: "0.2rem", display: "flex", justifyContent: "space-between" }}>
                      <span>{j.job_code}</span>
                      <span className={`status-pill ${j.status === "COMPLETED" ? "status-online" : "status-offline"}`} style={{ fontSize: "0.65rem", padding: "0.1rem 0.4rem" }}>
                        {j.status}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right: Selected Report Details */}
          {report && (
            <div className="glass-panel" style={{ padding: "1.75rem", display: "flex", flexDirection: "column", gap: "1.25rem" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", borderBottom: "1px solid var(--border-color)", paddingBottom: "1rem" }}>
                <div>
                  <h2 style={{ fontSize: "1.2rem", fontWeight: 700, color: "#ffffff" }}>
                    {report.job_summary?.name} ({report.job_summary?.job_code})
                  </h2>
                  <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
                    Status: <strong style={{ color: "var(--accent-emerald)" }}>{report.job_summary?.status}</strong> • Duration: {report.job_summary?.total_duration_sec?.toFixed(1)}s
                  </div>
                </div>

                <div style={{ display: "flex", gap: "0.6rem" }}>
                  <button onClick={downloadJsonReport} className="btn-secondary">
                    <Download size={14} />
                    <span>Download JSON Report</span>
                  </button>

                  <a
                    href={api.getFinalModelDownloadUrl(selectedJob.id)}
                    download
                    className="btn-primary"
                    style={{ textDecoration: "none" }}
                  >
                    <Download size={14} />
                    <span>Final Model (.pth)</span>
                  </a>
                </div>
              </div>

              {/* Summary Stats */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1rem" }}>
                <div style={{ background: "rgba(255, 255, 255, 0.02)", padding: "0.85rem", borderRadius: "8px", border: "1px solid var(--border-color)" }}>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>Final Convergence Accuracy</div>
                  <div style={{ fontSize: "1.3rem", fontWeight: 700, color: "var(--accent-emerald)", marginTop: "0.25rem" }}>
                    {report.job_summary?.final_accuracy?.toFixed(2)}%
                  </div>
                </div>

                <div style={{ background: "rgba(255, 255, 255, 0.02)", padding: "0.85rem", borderRadius: "8px", border: "1px solid var(--border-color)" }}>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>Final Cross-Entropy Loss</div>
                  <div style={{ fontSize: "1.3rem", fontWeight: 700, color: "var(--primary)", marginTop: "0.25rem" }}>
                    {report.job_summary?.final_loss?.toFixed(4)}
                  </div>
                </div>

                <div style={{ background: "rgba(255, 255, 255, 0.02)", padding: "0.85rem", borderRadius: "8px", border: "1px solid var(--border-color)" }}>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>Total Federated Rounds</div>
                  <div style={{ fontSize: "1.3rem", fontWeight: 700, color: "var(--accent-purple)", marginTop: "0.25rem" }}>
                    {report.job_summary?.rounds_completed} / {report.job_summary?.max_rounds}
                  </div>
                </div>
              </div>

              {/* Node Contributions Table */}
              <div>
                <h4 style={{ fontSize: "0.95rem", fontWeight: 600, color: "#ffffff", marginBottom: "0.75rem" }}>
                  Volunteer Node Compute Contributions
                </h4>
                <div style={{ overflowX: "auto" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.82rem" }}>
                    <thead>
                      <tr style={{ borderBottom: "1px solid var(--border-color)", color: "var(--text-dim)", textTransform: "uppercase", fontSize: "0.7rem" }}>
                        <th style={{ padding: "0.5rem" }}>Node ID</th>
                        <th style={{ padding: "0.5rem" }}>Tasks Completed</th>
                        <th style={{ padding: "0.5rem" }}>Samples Trained</th>
                        <th style={{ padding: "0.5rem" }}>Compute Duration (s)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(report.node_contributions || {}).map(([nodeId, stats]) => (
                        <tr key={nodeId} style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.04)" }}>
                          <td style={{ padding: "0.6rem 0.5rem", fontWeight: 600, color: "#ffffff" }}>{nodeId}</td>
                          <td style={{ padding: "0.6rem 0.5rem" }}>{stats.tasks_completed}</td>
                          <td style={{ padding: "0.6rem 0.5rem" }}>{stats.samples} samples</td>
                          <td style={{ padding: "0.6rem 0.5rem" }}>{stats.training_time?.toFixed(1)}s</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
