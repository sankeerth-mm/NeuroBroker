import React, { useState, useEffect } from "react";
import { api } from "../services/api";
import { 
  HelpCircle, 
  CheckCircle, 
  XCircle, 
  Cpu, 
  HardDrive, 
  Activity, 
  Wifi, 
  Clock, 
  ShieldCheck, 
  Scale, 
  RefreshCw 
} from "lucide-react";

export default function SchedulerExplainer() {
  const [decisions, setDecisions] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState("");
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [allJobs, allDecs] = await Promise.all([
        api.getJobs(),
        api.getSchedulerDecisions(selectedJobId),
      ]);
      setJobs(allJobs || []);
      setDecisions(allDecs || []);
      if (!selectedJobId && allJobs.length > 0) {
        setSelectedJobId(allJobs[0].id);
      }
    } catch (e) {
      console.error("Failed to load scheduler decisions:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [selectedJobId]);

  return (
    <div className="app-container animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: "1.75rem" }}>
      {/* Header */}
      <div className="glass-panel" style={{ padding: "1.75rem 2rem", borderLeft: "4px solid var(--primary)" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div>
            <h1 style={{ fontSize: "1.4rem", fontWeight: 800, color: "#ffffff", display: "flex", alignItems: "center", gap: "0.6rem" }}>
              <HelpCircle size={24} color="var(--primary)" />
              Intelligent Scheduler Explainability Engine
            </h1>
            <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
              Transparent mathematical justifications and multi-objective scoring breakdowns for every worker assignment.
            </p>
          </div>

          <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
            <select
              className="form-input"
              style={{ width: "200px", padding: "0.45rem 0.8rem", fontSize: "0.85rem" }}
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
            >
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.job_code} - {j.name}
                </option>
              ))}
            </select>

            <button onClick={fetchData} className="btn-secondary" title="Refresh">
              <RefreshCw size={15} />
            </button>
          </div>
        </div>
      </div>

      {/* Decision Cards List */}
      {decisions.length === 0 ? (
        <div className="glass-panel" style={{ textAlign: "center", padding: "3.5rem", color: "var(--text-muted)" }}>
          <Scale size={40} color="var(--text-dim)" style={{ marginBottom: "0.75rem" }} />
          <h3 style={{ color: "#ffffff", fontWeight: 700 }}>No Scheduling Decisions Recorded</h3>
          <p style={{ fontSize: "0.85rem", marginTop: "0.25rem" }}>
            When a distributed training job executes rounds, all multi-objective scores and natural language justifications are logged here.
          </p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          {decisions.map((dec) => {
            const isSelected = dec.is_selected;
            return (
              <div 
                key={dec.id} 
                className="glass-panel" 
                style={{ 
                  padding: "1.5rem",
                  borderLeft: isSelected ? "4px solid var(--accent-emerald)" : "4px solid var(--accent-rose)",
                  background: isSelected ? "rgba(15, 23, 42, 0.75)" : "rgba(15, 23, 42, 0.5)"
                }}
              >
                <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: "1rem" }}>
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                      <span style={{ fontSize: "1.15rem", fontWeight: 700, color: "#ffffff" }}>{dec.node_id}</span>
                      <span className={`status-pill ${isSelected ? "status-online" : "status-offline"}`}>
                        {isSelected ? <CheckCircle size={13} /> : <XCircle size={13} />}
                        {isSelected ? "Selected for Round" : "Unselected / Fallback"}
                      </span>
                      <span style={{ fontSize: "0.78rem", color: "var(--text-dim)" }}>
                        Round {dec.round_number}
                      </span>
                    </div>

                    <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
                      Composite Score: <strong style={{ color: "var(--primary)", fontSize: "0.95rem" }}>{dec.overall_score.toFixed(3)}</strong>
                    </div>
                  </div>

                  <div style={{ textAlign: "right", fontSize: "0.78rem", color: "var(--text-dim)" }}>
                    {new Date(dec.timestamp).toLocaleTimeString()}
                  </div>
                </div>

                {/* Score Breakdown Metrics Grid */}
                <div style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))",
                  gap: "0.75rem",
                  marginBottom: "1.25rem",
                  padding: "0.85rem",
                  background: "rgba(255, 255, 255, 0.02)",
                  borderRadius: "8px",
                  border: "1px solid var(--border-color)",
                  fontSize: "0.78rem"
                }}>
                  <div>
                    <span style={{ color: "var(--text-dim)", display: "block" }}>CPU Score</span>
                    <strong style={{ color: "#f8fafc" }}>{(dec.cpu_score * 100).toFixed(0)}%</strong>
                  </div>
                  <div>
                    <span style={{ color: "var(--text-dim)", display: "block" }}>RAM Score</span>
                    <strong style={{ color: "#f8fafc" }}>{(dec.ram_score * 100).toFixed(0)}%</strong>
                  </div>
                  <div>
                    <span style={{ color: "var(--text-dim)", display: "block" }}>GPU Score</span>
                    <strong style={{ color: "#f8fafc" }}>{(dec.gpu_score * 100).toFixed(0)}%</strong>
                  </div>
                  <div>
                    <span style={{ color: "var(--text-dim)", display: "block" }}>Network</span>
                    <strong style={{ color: "#f8fafc" }}>{(dec.network_score * 100).toFixed(0)}%</strong>
                  </div>
                  <div>
                    <span style={{ color: "var(--text-dim)", display: "block" }}>Reliability</span>
                    <strong style={{ color: "var(--accent-emerald)" }}>{(dec.reliability_score * 100).toFixed(0)}%</strong>
                  </div>
                  <div>
                    <span style={{ color: "var(--text-dim)", display: "block" }}>Fairness</span>
                    <strong style={{ color: "var(--accent-purple)" }}>{(dec.fairness_score * 100).toFixed(0)}%</strong>
                  </div>
                  <div>
                    <span style={{ color: "var(--text-dim)", display: "block" }}>Transfer Est.</span>
                    <strong style={{ color: "#f8fafc" }}>{dec.estimated_transfer_time_sec.toFixed(1)}s</strong>
                  </div>
                  <div>
                    <span style={{ color: "var(--text-dim)", display: "block" }}>Train Est.</span>
                    <strong style={{ color: "#f8fafc" }}>{dec.estimated_training_time_sec.toFixed(1)}s</strong>
                  </div>
                </div>

                {/* Natural Language Rationale */}
                <div style={{
                  background: "rgba(0, 0, 0, 0.3)",
                  borderRadius: "8px",
                  padding: "0.85rem 1rem",
                  fontSize: "0.82rem",
                  fontFamily: "JetBrains Mono, monospace",
                  whiteSpace: "pre-line",
                  color: isSelected ? "#38bdf8" : "#94a3b8",
                  lineHeight: "1.6"
                }}>
                  {dec.rationale}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
