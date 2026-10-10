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
  RefreshCw,
  Trash2
} from "lucide-react";

export default function TrainingView({ selectedJobId, setSelectedJobId, setActiveTab }) {
  const [job, setJob] = useState(null);
  const [allJobs, setAllJobs] = useState([]);
  const [rounds, setRounds] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [logs, setLogs] = useState([]);
  const [decisions, setDecisions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionError, setActionError] = useState("");

  const fetchJobData = async () => {
    try {
      const jobList = await api.getJobs();
      setAllJobs(jobList || []);
      
      let targetId = selectedJobId;
      if (!targetId && jobList && jobList.length > 0) {
        targetId = jobList[0].id;
        setSelectedJobId(targetId);
      }

      if (!targetId) {
        setLoading(false);
        return;
      }

      const detail = await api.getJobDetail(targetId);
      const [roundList, taskList, decs] = await Promise.all([
        api.getJobRounds(targetId).catch(() => []),
        api.getJobTasks(targetId).catch(() => []),
        api.getSchedulerDecisions(targetId).catch(() => []),
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
      if (Number(data.job_id) === Number(selectedJobId)) {
        fetchJobData();
        addLog(`[AGGREGATOR] Round ${data.round} Completed! Global Acc: ${data.accuracy.toFixed(2)}%, Loss: ${data.loss.toFixed(4)}`);
      }
    };

    const handleTaskProgress = (data) => {
      if (Number(data.job_id) === Number(selectedJobId)) {
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
      if (Number(data.job_id) === Number(selectedJobId)) {
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
      if (Number(data.job_id) === Number(selectedJobId)) {
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
    setActionError("");
    try {
      if (action === "pause") {
        setJob((prev) => (prev ? { ...prev, status: "PAUSED" } : prev));
        await api.pauseJob(selectedJobId);
      } else if (action === "resume") {
        setJob((prev) => (prev ? { ...prev, status: "TRAINING" } : prev));
        await api.resumeJob(selectedJobId);
      } else if (action === "stop") {
        setJob((prev) => (prev ? { ...prev, status: "CANCELLED" } : prev));
        await api.stopJob(selectedJobId);
      } else if (action === "start") {
        setJob((prev) => (prev ? { ...prev, status: "QUEUED" } : prev));
        await api.startJob(selectedJobId);
      }
      setTimeout(fetchJobData, 600);
    } catch (err) {
      setActionError(err.message || "Training action failed");
      fetchJobData();
    }
  };

  const handleDeleteJob = async () => {
    if (!job) return;
    if (!window.confirm(`Are you sure you want to delete job "${job.name}" (${job.job_code})?`)) {
      return;
    }
    setActionError("");
    try {
      await api.deleteJob(selectedJobId);
    } catch (err) {
      if (err.message && err.message.includes("not found")) {
        // Already removed
      } else {
        setActionError(err.message || "Failed to delete training job");
      }
    } finally {
      setSelectedJobId(null);
      setActiveTab("dashboard");
    }
  };

  const handleDownload = async () => {
    setActionError("");
    try {
      await api.downloadFinalModel(job.id, job.name);
    } catch (err) {
      setActionError(err.message || "Model download failed");
    }
  };

  const handleQuickLaunchDemoJob = async () => {
    setActionError("");
    try {
      const models = await api.getModelPackages();
      const datasets = await api.getDatasets();
      if (!models.length || !datasets.length) {
        setActiveTab("create_job");
        return;
      }
      const newJob = await api.createJob({
        name: "Federated DL Training Job",
        model_package_id: models[0].id,
        dataset_id: datasets[0].id,
        max_rounds: 5,
        local_epochs: 2,
        batch_size: 16,
        learning_rate: 0.01,
        target_accuracy: 95.0,
        min_volunteer_nodes: 1,
      });
      await api.startJob(newJob.id);
      setSelectedJobId(newJob.id);
      setTimeout(fetchJobData, 500);
    } catch (err) {
      setActionError(err.message || "Failed to launch training job");
    }
  };

  if (!selectedJobId || !job) {
    return (
      <div className="app-container animate-fade-in" style={{ textAlign: "center", padding: "4rem 1rem", maxWidth: "600px", margin: "0 auto" }}>
        <Layers size={48} color="var(--primary)" style={{ marginBottom: "1rem" }} />
        <h2 style={{ color: "#ffffff", fontWeight: 700, fontSize: "1.4rem" }}>No Active Job Selected</h2>
        <p style={{ color: "var(--text-muted)", marginTop: "0.5rem", fontSize: "0.9rem" }}>
          {allJobs.length > 0
            ? "Select a training job below or launch a new federated training job."
            : "No training jobs available yet. Create a new job or launch a quick demo job."}
        </p>

        {allJobs.length > 0 && (
          <div style={{ marginTop: "1.25rem" }}>
            <select
              className="form-input"
              style={{ fontSize: "0.9rem", padding: "0.6rem 1rem", width: "100%", background: "rgba(15, 23, 42, 0.9)" }}
              value={selectedJobId || ""}
              onChange={(e) => {
                const id = Number(e.target.value);
                setSelectedJobId(id);
              }}
            >
              <option value="" disabled>-- Select a Training Job --</option>
              {allJobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.job_code} - {j.name} ({j.status})
                </option>
              ))}
            </select>
          </div>
        )}

        <div style={{ display: "flex", gap: "0.8rem", justifyContent: "center", marginTop: "1.5rem" }}>
          <button onClick={() => setActiveTab("create_job")} className="btn-primary">
            Create New Job
          </button>
          <button onClick={handleQuickLaunchDemoJob} className="btn-secondary">
            Quick Launch Job
          </button>
        </div>
      </div>
    );
  }

  const isRunning = ["TRAINING", "SCHEDULING", "PARTITIONING", "AGGREGATING", "QUEUED", "PAUSED"].includes(job.status);
  const isCompleted = job.status === "COMPLETED";
  const isStopped = ["CANCELLED", "FAILED"].includes(job.status);
  const hasModelWeights = (job.current_round > 0) || isCompleted;

  // Compute Dynamic Overall Progress % incorporating completed rounds & live epoch task progress
  const currentRoundTasks = tasks.filter(t => t.round_number === job.current_round);
  const avgTaskPct = currentRoundTasks.length > 0 
    ? (currentRoundTasks.reduce((sum, t) => sum + (t.progress_percent || 0), 0) / currentRoundTasks.length)
    : 0;

  const completedRounds = isCompleted 
    ? job.max_rounds 
    : Math.max(0, (job.current_round || 1) - (["TRAINING", "SCHEDULING", "PARTITIONING"].includes(job.status) ? 1 : 0));

  const overallProgressPct = isCompleted 
    ? 100 
    : job.max_rounds > 0 
      ? Math.min(99, Math.round(((completedRounds + (avgTaskPct / 100)) / job.max_rounds) * 100))
      : 0;

  // Stages for the Pipeline Progress Stepper
  const stages = [
    { key: "QUEUED", label: "Queued" },
    { key: "SCHEDULING", label: "Node Selection" },
    { key: "PARTITIONING", label: "Data Partitioning" },
    { key: "TRAINING", label: "Local Training" },
    { key: "AGGREGATING", label: "FedAvg Aggregation" },
    { key: "COMPLETED", label: "Completed" },
  ];

  const getCurrentStageIndex = (status) => {
    switch (status) {
      case "QUEUED": return 0;
      case "SCHEDULING": return 1;
      case "PARTITIONING": return 2;
      case "TRAINING": return 3;
      case "AGGREGATING": return 4;
      case "COMPLETED": return 5;
      default: return 3;
    }
  };

  const currentStageIdx = getCurrentStageIndex(job.status);

  // Prepare chart data
  const chartData = rounds.map((r) => ({
    round: `R${r.round_number}`,
    accuracy: Number(r.accuracy.toFixed(2)),
    loss: Number(r.loss.toFixed(4)),
  }));

  return (
    <div className="app-container animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {actionError && (
        <div style={{ color: "var(--accent-rose)", fontSize: "0.82rem", padding: "0.75rem 1rem", border: "1px solid rgba(244, 63, 94, 0.35)", borderRadius: "8px", background: "rgba(244, 63, 94, 0.1)", display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <AlertTriangle size={16} />
          <span>{actionError}</span>
        </div>
      )}

      {/* Job Header Bar */}
      <div className="glass-panel" style={{ padding: "1.5rem 2rem", borderLeft: "4px solid var(--primary)" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
              <h1 style={{ fontSize: "1.4rem", fontWeight: 800, color: "var(--text-heading)" }}>{job.name}</h1>
              <span className={`status-pill ${isRunning ? "status-busy" : isCompleted ? "status-online" : "status-offline"}`}>
                {isRunning && <span className="pulse-dot" style={{ background: "#38bdf8" }} />}
                {job.status}
              </span>
            </div>
            <div style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginTop: "0.3rem", display: "flex", gap: "1.25rem", alignItems: "center", flexWrap: "wrap" }}>
              <span>Job Code: <strong style={{ color: "var(--text-main)" }}>{job.job_code}</strong></span>
              <span>Model: <strong style={{ color: "var(--text-main)" }}>{job.model_package?.name || "PyTorch Architecture"}</strong></span>
              <span>Dataset: <strong style={{ color: "var(--text-main)" }}>{job.dataset?.name || "Dataset"}</strong></span>
            </div>
          </div>

          {/* Action Buttons & Job Selector */}
          <div style={{ display: "flex", gap: "0.6rem", alignItems: "center", flexWrap: "wrap" }}>
            {allJobs.length > 1 && (
              <select
                className="form-input"
                style={{ fontSize: "0.82rem", padding: "0.45rem 0.75rem", width: "auto", background: "rgba(15, 23, 42, 0.9)" }}
                value={selectedJobId}
                onChange={(e) => setSelectedJobId(Number(e.target.value))}
              >
                {allJobs.map((j) => (
                  <option key={j.id} value={j.id}>
                    {j.job_code} - {j.name} ({j.status})
                  </option>
                ))}
              </select>
            )}

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

            {isStopped && (
              <button onClick={() => handleAction("start")} className="btn-primary" style={{ background: "var(--primary-gradient)" }}>
                <Play size={16} /> Start Training
              </button>
            )}

            {/* DOWNLOAD MODEL BUTTON */}
            {hasModelWeights && (
              <button
                onClick={handleDownload}
                className="btn-primary"
                style={{
                  background: "linear-gradient(135deg, #059669, #10b981)",
                  boxShadow: "0 4px 14px rgba(16, 185, 129, 0.35)",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  padding: "0.55rem 1.1rem"
                }}
              >
                <Download size={16} />
                <span>Download Model (.pth)</span>
              </button>
            )}

            <button onClick={handleDeleteJob} className="btn-danger" title="Delete Training Job" style={{ padding: "0.45rem 0.8rem", display: "inline-flex", alignItems: "center", gap: "0.4rem" }}>
              <Trash2 size={16} />
              <span>Delete</span>
            </button>

            <button onClick={fetchJobData} className="btn-secondary" title="Refresh Telemetry">
              <RefreshCw size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* 1. OVERALL TRAINING PROGRESS CARD WITH PIPELINE STEPPER        */}
      {/* ------------------------------------------------------------- */}
      <div className="glass-panel" style={{ padding: "1.5rem 2rem", background: "linear-gradient(180deg, rgba(15, 23, 42, 0.8), rgba(30, 41, 59, 0.6))" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem", flexWrap: "wrap", gap: "0.5rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
            <Activity size={20} color="var(--primary)" />
            <h2 style={{ fontSize: "1.1rem", fontWeight: 800, color: "var(--text-heading)" }}>
              Current Training Progress
            </h2>
          </div>
          <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--primary)" }}>
            Round {job.current_round} of {job.max_rounds} ({overallProgressPct}% Completed)
          </div>
        </div>

        {/* Overall Progress Bar */}
        <div style={{ background: "rgba(255, 255, 255, 0.08)", borderRadius: "999px", height: "12px", overflow: "hidden", position: "relative", marginBottom: "1.5rem" }}>
          <div 
            style={{
              width: `${overallProgressPct}%`,
              height: "100%",
              background: isCompleted ? "linear-gradient(90deg, #10b981, #34d399)" : "linear-gradient(90deg, #0066FF, #38bdf8)",
              borderRadius: "999px",
              transition: "width 0.5s ease-in-out"
            }}
          />
        </div>

        {/* Stage Stepper Workflow */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: "0.5rem", textAlign: "center" }}>
          {stages.map((st, idx) => {
            const isDone = idx < currentStageIdx || isCompleted;
            const isCurrent = idx === currentStageIdx && !isCompleted;

            return (
              <div 
                key={st.key}
                style={{
                  background: isCurrent ? "rgba(56, 189, 248, 0.15)" : isDone ? "rgba(16, 185, 129, 0.1)" : "rgba(255, 255, 255, 0.03)",
                  border: isCurrent ? "1px solid #38bdf8" : isDone ? "1px solid rgba(16, 185, 129, 0.4)" : "1px solid var(--border-color)",
                  borderRadius: "8px",
                  padding: "0.65rem 0.4rem",
                  transition: "all 0.25s ease"
                }}
              >
                <div style={{
                  fontSize: "0.7rem",
                  fontWeight: 800,
                  color: isCurrent ? "#38bdf8" : isDone ? "#34d399" : "var(--text-dim)",
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                  marginBottom: "0.2rem"
                }}>
                  Step {idx + 1}
                </div>
                <div style={{
                  fontSize: "0.78rem",
                  fontWeight: 700,
                  color: isCurrent ? "#ffffff" : isDone ? "#e2e8f0" : "var(--text-muted)"
                }}>
                  {st.label}
                </div>
                {isCurrent && (
                  <div style={{ display: "inline-block", width: "6px", height: "6px", borderRadius: "50%", background: "#38bdf8", marginTop: "0.3rem" }} className="pulse-dot" />
                )}
                {isDone && (
                  <CheckCircle size={12} color="#34d399" style={{ marginTop: "0.3rem" }} />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Top Training KPIs */}
      <div className="grid-cols-4">
        <MetricCard
          title="Current Federated Round"
          value={`${job.current_round} / ${job.max_rounds}`}
          subtitle={`${overallProgressPct}% overall progress`}
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

      {/* Main Row: Live Training Charts & Event Terminal */}
      <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: "1.5rem" }}>
        {/* Left: Convergence Curves Chart */}
        <div className="glass-panel" style={{ padding: "1.5rem" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.25rem" }}>
            <h2 style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--text-heading)", display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <TrendingUp size={18} color="var(--primary)" />
              Global Model Convergence Curves
            </h2>
            {hasModelWeights && (
              <button onClick={handleDownload} className="btn-secondary" style={{ fontSize: "0.75rem", padding: "0.3rem 0.75rem" }}>
                <Download size={13} /> Download Weights (.pth)
              </button>
            )}
          </div>

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
          <h2 style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--text-heading)", marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <Terminal size={18} color="var(--accent-emerald)" />
            Live Training Telemetry Stream
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

      {/* ------------------------------------------------------------- */}
      {/* 3. VOLUNTEER WORKER NODE TASKS & ONLINE/OFFLINE STATUS TABLE    */}
      {/* ------------------------------------------------------------- */}
      <div className="glass-panel" style={{ padding: "1.5rem" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.25rem" }}>
          <h2 style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-heading)", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <Server size={18} color="var(--accent-purple)" />
            Volunteer Node Training Execution & Online/Offline Status
          </h2>
          <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
            Real-time local batch progress reported via WebSocket
          </span>
        </div>

        {tasks.length === 0 ? (
          <div style={{ textAlign: "center", padding: "2.5rem", color: "var(--text-muted)", fontSize: "0.85rem" }}>
            Tasks will be assigned to selected volunteer nodes when training begins.
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.85rem" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border-color)", color: "var(--text-dim)", textTransform: "uppercase", fontSize: "0.72rem", letterSpacing: "0.05em" }}>
                  <th style={{ padding: "0.75rem" }}>Node ID</th>
                  <th style={{ padding: "0.75rem" }}>Node Presence</th>
                  <th style={{ padding: "0.75rem" }}>Task Round</th>
                  <th style={{ padding: "0.75rem" }}>Task Status</th>
                  <th style={{ padding: "0.75rem" }}>Epoch Progress (%)</th>
                  <th style={{ padding: "0.75rem" }}>Local Loss</th>
                  <th style={{ padding: "0.75rem" }}>Local Acc</th>
                  <th style={{ padding: "0.75rem" }}>Processed Samples</th>
                </tr>
              </thead>
              <tbody>
                {tasks.slice(0, 15).map((t) => (
                  <tr key={t.id} style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.04)" }}>
                    <td style={{ padding: "0.85rem 0.75rem" }}>
                      <strong style={{ color: "var(--text-heading)", fontFamily: "JetBrains Mono, monospace" }}>{t.node_id}</strong>
                    </td>

                    {/* NODE PRESENCE (ONLINE / OFFLINE BADGE) */}
                    <td style={{ padding: "0.85rem 0.75rem" }}>
                      <span className={`status-pill ${t.status === "FAILED" || t.status === "TIMEOUT" ? "status-offline" : t.status === "RUNNING" ? "status-busy" : "status-online"}`}>
                        <span className="pulse-dot" style={{ background: t.status === "FAILED" ? "#f43f5e" : t.status === "RUNNING" ? "#38bdf8" : "#10b981" }} />
                        {t.status === "FAILED" || t.status === "TIMEOUT" ? "OFFLINE / TIMEOUT" : "ONLINE"}
                      </span>
                    </td>

                    <td style={{ padding: "0.85rem 0.75rem" }}>Round {t.round_number}</td>

                    <td style={{ padding: "0.85rem 0.75rem" }}>
                      <span className={`status-pill ${t.status === "COMPLETED" ? "status-online" : t.status === "RUNNING" ? "status-busy" : "status-offline"}`}>
                        {t.status}
                      </span>
                    </td>

                    <td style={{ padding: "0.85rem 0.75rem", minWidth: "170px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "0.25rem" }}>
                        <span>Epoch {t.current_epoch || 0} / {t.local_epochs}</span>
                        <strong style={{ color: "var(--text-heading)" }}>{t.progress_percent.toFixed(0)}%</strong>
                      </div>
                      <div className="progress-bar-container">
                        <div className="progress-bar-fill" style={{ width: `${t.progress_percent}%`, background: t.status === "COMPLETED" ? "#10b981" : "var(--primary-gradient)" }} />
                      </div>
                    </td>

                    <td style={{ padding: "0.85rem 0.75rem", fontFamily: "JetBrains Mono, monospace" }}>
                      {t.current_loss > 0 ? t.current_loss.toFixed(4) : "—"}
                    </td>

                    <td style={{ padding: "0.85rem 0.75rem", fontWeight: 600, color: t.current_accuracy > 0 ? "var(--accent-emerald)" : "var(--text-dim)", fontFamily: "JetBrains Mono, monospace" }}>
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
