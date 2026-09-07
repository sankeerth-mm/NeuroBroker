import React, { useState, useEffect } from "react";
import { api } from "../services/api";
import { wsService } from "../services/websocket";
import MetricCard from "../components/MetricCard";
import { 
  ResponsiveContainer, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid, 
  Legend 
} from "recharts";
import { 
  Layers, 
  Activity, 
  Play, 
  Pause, 
  Square, 
  Download, 
  Server, 
  CheckCircle, 
  AlertTriangle, 
  Clock, 
  TrendingUp, 
  Terminal, 
  RefreshCw 
} from "lucide-react";

export default function TrainingView({ selectedJobId, setSelectedJobId, setActiveTab }) {
  const [job, setJob] = useState(null);
  const [rounds, setRounds] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [logs, setLogs] = useState([]);
  const [decisions, setDecisions] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchJobData = async () => {
    if (!selectedJobId) {
      // Find latest job if none explicitly selected
      try {
        const allJobs = await api.getJobs();
        if (allJobs.length > 0) {
          setSelectedJobId(allJobs[0].id);
          return;
        }
      } catch (e) {}
      setLoading(false);
      return;
    }

    try {
      const [detail, roundList, taskList, decs] = await Promise.all([
        api.getJobDetail(selectedJobId),
        api.getJobRounds(selectedJobId),
        api.getJobTasks(selectedJobId),
        api.getSchedulerDecisions(selectedJobId),
      ]);
      setJob(detail);
      setRounds(roundList || []);
      setTasks(taskList || []);
      setDecisions(decs || []);
    } catch (e) {
      console.error("Error fetching job details:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobData();

    // WebSocket listeners for real-time live training
    const handleRoundCompleted = (data) => {
      if (data.job_id === selectedJobId) {
        fetchJobData();
        addLog(`[AGGREGATOR] Round ${data.round} Completed! Global Acc: ${data.accuracy.toFixed(2)}%, Loss: ${data.loss.toFixed(4)}`);
      }
    };

    const handleTaskProgress = (data) => {
      if (data.job_id === selectedJobId) {
        setTasks((prev) =>
          prev.map((t) =>
            t.id === data.task_id
              ? { ...t, current_epoch: data.epoch, current_loss: data.loss, current_accuracy: data.accuracy, progress_percent: data.progress_percent, status: "RUNNING" }
              : t
          )
        );
      }
    };

    const handleTaskComplete = (data) => {
      if (data.job_id === selectedJobId) {
        setTasks((prev) =>
          prev.map((t) =>
            t.id === data.task_id
              ? { ...t, status: "COMPLETED", progress_percent: 100, current_loss: data.loss, current_accuracy: data.accuracy }
              : t
          )
        );
        addLog(`[NODE ${data.node_id}] Completed local training. Acc: ${data.accuracy.toFixed(2)}% in ${data.training_time.toFixed(1)}s`);
      }
    };

    const handleStatusChange = (data) => {
      if (data.job_id === selectedJobId) {
        setJob((prev) => (prev ? { ...prev, status: data.status } : prev));
        addLog(`[ORCHESTRATOR] Job state changed -> ${data.status}`);
      }
    };

    wsService.on("round_completed", handleRoundCompleted);
    wsService.on("task_progress", handleTaskProgress);
    wsService.on("task_completed", handleTaskComplete);
    wsService.on("job_status_change", handleStatusChange);

    return () => {
      wsService.off("round_completed", handleRoundCompleted);
      wsService.off("task_progress", handleTaskProgress);
      wsService.off("task_completed", handleTaskComplete);
      wsService.off("job_status_change", handleStatusChange);
    };
  }, [selectedJobId]);

  const addLog = (msg) => {
    const time = new Date().toLocaleTimeString();
    setLogs((prev) => [`[${time}] ${msg}`, ...prev.slice(0, 40)]);
  };

  const handleAction = async (action) => {
    try {
      if (action === "pause") await api.pauseJob(selectedJobId);
      if (action === "resume") await api.resumeJob(selectedJobId);
      if (action === "stop") await api.stopJob(selectedJobId);
      fetchJobData();
    } catch (err) {
      alert(`Action failed: ${err.message}`);
    }
  };

  if (!selectedJobId || !job) {
    return (
      <div className="app-container animate-fade-in" style={{ textAlign: "center", padding: "4rem 1rem" }}>
        <Layers size={48} color="var(--text-dim)" style={{ marginBottom: "1rem" }} />
        <h2 style={{ color: "#ffffff", fontWeight: 700 }}>No Active Job Selected</h2>
        <p style={{ color: "var(--text-muted)", marginTop: "0.5rem" }}>
          Select or launch a training job from the dashboard.
        </p>
        <button onClick={() => setActiveTab("create_job")} className="btn-primary" style={{ marginTop: "1.25rem" }}>
          Create New Job
        </button>
      </div>
    );
  }

  const isRunning = ["TRAINING", "SCHEDULING", "PARTITIONING", "AGGREGATING", "QUEUED"].includes(job.status);
  const isCompleted = job.status === "COMPLETED";

  // Prepare chart data
  const chartData = rounds.map((r) => ({
    round: `R${r.round_number}`,
    accuracy: Number(r.accuracy.toFixed(2)),
    loss: Number(r.loss.toFixed(4)),
  }));

  // Current round tasks
  const currentRoundTasks = tasks.filter((t) => t.round_number === job.current_round || tasks.length <= 5);

  return (
    <div className="app-container animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Job Header Bar */}
      <div className="glass-panel" style={{ padding: "1.5rem 2rem", borderLeft: "4px solid var(--primary)" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
              <h1 style={{ fontSize: "1.4rem", fontWeight: 800, color: "#ffffff" }}>{job.name}</h1>
              <span className={`status-pill ${isRunning ? "status-busy" : isCompleted ? "status-online" : "status-offline"}`}>
                {isRunning && <span className="pulse-dot" style={{ background: "#38bdf8" }} />}
                {job.status}
              </span>
            </div>
            <div style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginTop: "0.3rem", display: "flex", gap: "1.25rem" }}>
              <span>Job ID: <strong style={{ color: "var(--text-main)" }}>{job.job_code}</strong></span>
              <span>Model: <strong style={{ color: "var(--text-main)" }}>{job.model_package?.name || "PyTorch Model"}</strong></span>
              <span>Dataset: <strong style={{ color: "var(--text-main)" }}>{job.dataset?.name || "Dataset"}</strong></span>
            </div>
          </div>

          {/* Action Buttons */}
          <div style={{ display: "flex", gap: "0.6rem" }}>
            {isRunning && (
              <>
                {job.status === "PAUSED" ? (
                  <button onClick={() => handleAction("resume")} className="btn-secondary" style={{ color: "var(--accent-emerald)" }}>
                    <Play size={16} /> Resume
                  </button>
                ) : (
                  <button onClick={() => handleAction("pause")} className="btn-secondary" style={{ color: "var(--accent-amber)" }}>
                    <Pause size={16} /> Pause
                  </button>
                )}
                <button onClick={() => handleAction("stop")} className="btn-danger">
                  <Square size={16} /> Stop
                </button>
              </>
            )}

            {isCompleted && (
              <a
                href={api.getFinalModelDownloadUrl(job.id)}
                download
                className="btn-primary"
                style={{ textDecoration: "none" }}
              >
                <Download size={16} />
                <span>Download Final Model (.pth)</span>
              </a>
            )}

            <button onClick={fetchJobData} className="btn-secondary" title="Refresh">
              <RefreshCw size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* Top Training KPIs */}
      <div className="grid-cols-4">
        <MetricCard
          title="Current Federated Round"
          value={`${job.current_round} / ${job.max_rounds}`}
          subtitle={`${((job.current_round / job.max_rounds) * 100).toFixed(0)}% rounds completed`}
          icon={Layers}
          color="var(--primary)"
        />
        <MetricCard
          title="Global Accuracy"
          value={`${job.global_accuracy.toFixed(2)}%`}
          subtitle={`Target: ${job.target_accuracy}%`}
          icon={TrendingUp}
          color="var(--accent-emerald)"
        />
        <MetricCard
          title="Global Loss"
          value={job.global_loss.toFixed(4)}
          subtitle="Cross-Entropy loss across nodes"
          icon={Activity}
          color="var(--accent-cyan)"
        />
        <MetricCard
          title="Estimated Remaining"
          value={job.estimated_remaining_seconds > 0 ? `${job.estimated_remaining_seconds.toFixed(0)}s` : isCompleted ? "Completed" : "Calculating..."}
          subtitle={`Total elapsed: ${job.total_training_time_seconds.toFixed(0)}s`}
          icon={Clock}
          color="var(--accent-purple)"
        />
      </div>

      {/* Main Row: Live Training Charts & Volunteer Worker Nodes Table */}
      <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: "1.5rem" }}>
        {/* Left: Convergence Curves Chart */}
        <div className="glass-panel" style={{ padding: "1.5rem" }}>
          <h2 style={{ fontSize: "1.05rem", fontWeight: 700, color: "#ffffff", marginBottom: "1.25rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <TrendingUp size={18} color="var(--primary)" />
            Global Model Convergence Curves
          </h2>

          {chartData.length === 0 ? (
            <div style={{ textAlign: "center", padding: "4rem 1rem", color: "var(--text-muted)", fontSize: "0.85rem" }}>
              Waiting for Round 1 FedAvg aggregation metrics...
            </div>
          ) : (
            <div style={{ width: "100%", height: 260 }}>
              <ResponsiveContainer>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="round" stroke="#64748b" />
                  <YAxis yAxisId="left" stroke="#38bdf8" domain={[0, 100]} />
                  <YAxis yAxisId="right" orientation="right" stroke="#f43f5e" />
                  <Tooltip contentStyle={{ background: "#0f172a", borderColor: "rgba(255,255,255,0.1)", borderRadius: "8px" }} />
                  <Legend />
                  <Line yAxisId="left" type="monotone" dataKey="accuracy" name="Accuracy (%)" stroke="#38bdf8" strokeWidth={3} dot={{ r: 4 }} />
                  <Line yAxisId="right" type="monotone" dataKey="loss" name="Loss" stroke="#f43f5e" strokeWidth={2} strokeDasharray="3 3" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Right: Real-Time Event Log Terminal */}
        <div className="glass-panel" style={{ padding: "1.5rem", display: "flex", flexDirection: "column" }}>
          <h2 style={{ fontSize: "1.05rem", fontWeight: 700, color: "#ffffff", marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <Terminal size={18} color="var(--accent-emerald)" />
            Live Training Stream
          </h2>

          <div style={{
            flex: 1,
            background: "rgba(0, 0, 0, 0.4)",
            border: "1px solid var(--border-color)",
            borderRadius: "8px",
            padding: "0.75rem",
            overflowY: "auto",
            maxHeight: "240px",
            fontSize: "0.75rem",
            fontFamily: "JetBrains Mono, monospace",
            display: "flex",
            flexDirection: "column",
            gap: "0.35rem"
          }}>
            {logs.length === 0 ? (
              <div style={{ color: "var(--text-dim)" }}>Listening to WebSocket telemetry stream...</div>
            ) : (
              logs.map((log, idx) => (
                <div key={idx} style={{ color: log.includes("Error") ? "#f43f5e" : log.includes("Completed") ? "#34d399" : "#e2e8f0" }}>
                  {log}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Volunteer Worker Node Progress Table */}
      <div className="glass-panel" style={{ padding: "1.5rem" }}>
        <h2 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#ffffff", marginBottom: "1.25rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <Server size={18} color="var(--accent-purple)" />
          Volunteer Node Local Training Tasks
        </h2>

        {tasks.length === 0 ? (
          <div style={{ textAlign: "center", padding: "2.5rem", color: "var(--text-muted)", fontSize: "0.85rem" }}>
            Tasks will be assigned to selected volunteer nodes when training begins.
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.85rem" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border-color)", color: "var(--text-dim)", textTransform: "uppercase", fontSize: "0.72rem", letterSpacing: "0.05em" }}>
                  <th style={{ padding: "0.75rem" }}>Volunteer Node</th>
                  <th style={{ padding: "0.75rem" }}>Round</th>
                  <th style={{ padding: "0.75rem" }}>Status</th>
                  <th style={{ padding: "0.75rem" }}>Epoch Progress</th>
                  <th style={{ padding: "0.75rem" }}>Local Loss</th>
                  <th style={{ padding: "0.75rem" }}>Local Acc</th>
                  <th style={{ padding: "0.75rem" }}>Samples</th>
                </tr>
              </thead>
              <tbody>
                {tasks.slice(0, 10).map((t) => (
                  <tr key={t.id} style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.04)" }}>
                    <td style={{ padding: "0.85rem 0.75rem" }}>
                      <strong style={{ color: "#ffffff" }}>{t.node_id}</strong>
                    </td>
                    <td style={{ padding: "0.85rem 0.75rem" }}>Round {t.round_number}</td>
                    <td style={{ padding: "0.85rem 0.75rem" }}>
                      <span className={`status-pill ${t.status === "COMPLETED" ? "status-online" : t.status === "RUNNING" ? "status-busy" : "status-offline"}`}>
                        {t.status}
                      </span>
                    </td>
                    <td style={{ padding: "0.85rem 0.75rem", minWidth: "150px" }}>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "0.2rem" }}>
                        Epoch {t.current_epoch} / {t.local_epochs} ({t.progress_percent.toFixed(0)}%)
                      </div>
                      <div className="progress-bar-container">
                        <div className="progress-bar-fill" style={{ width: `${t.progress_percent}%` }} />
                      </div>
                    </td>
                    <td style={{ padding: "0.85rem 0.75rem" }}>{t.current_loss > 0 ? t.current_loss.toFixed(4) : "—"}</td>
                    <td style={{ padding: "0.85rem 0.75rem", fontWeight: 600, color: t.current_accuracy > 0 ? "var(--accent-emerald)" : "var(--text-dim)" }}>
                      {t.current_accuracy > 0 ? `${t.current_accuracy.toFixed(2)}%` : "—"}
                    </td>
                    <td style={{ padding: "0.85rem 0.75rem" }}>{t.samples_processed || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
