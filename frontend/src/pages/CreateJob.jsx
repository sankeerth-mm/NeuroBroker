import React, { useState, useEffect } from "react";
import { api } from "../services/api";
import { 
  PlayCircle, 
  Upload, 
  Layers, 
  Database, 
  Sliders, 
  CheckCircle, 
  ArrowRight, 
  Sparkles,
  Info 
} from "lucide-react";

export default function CreateJob({ setActiveTab, setSelectedJobId }) {
  const [name, setName] = useState("MNIST Federated DL Demo");
  const [description, setDescription] = useState("Broker-orchestrated CNN classification training across heterogeneous volunteer nodes");
  
  const [modelPackages, setModelPackages] = useState([]);
  const [selectedModelId, setSelectedModelId] = useState("");
  
  const [datasets, setDatasets] = useState([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState("");
  
  // Hyperparameters
  const [maxRounds, setMaxRounds] = useState(5);
  const [localEpochs, setLocalEpochs] = useState(2);
  const [batchSize, setBatchSize] = useState(32);
  const [learningRate, setLearningRate] = useState(0.01);
  const [targetAccuracy, setTargetAccuracy] = useState(90.0);
  const [minVolunteerNodes, setMinVolunteerNodes] = useState(2);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // File uploads
  const [modelFile, setModelFile] = useState(null);
  const [datasetFile, setDatasetFile] = useState(null);
  const [uploadMode, setUploadMode] = useState(false);

  useEffect(() => {
    async function loadArtifacts() {
      try {
        const [models, dsets] = await Promise.all([
          api.getModelPackages(),
          api.getDatasets(),
        ]);
        setModelPackages(models || []);
        setDatasets(dsets || []);
        if (models.length > 0) setSelectedModelId(models[0].id);
        if (dsets.length > 0) setSelectedDatasetId(dsets[0].id);
      } catch (e) {
        console.error("Failed to load models/datasets:", e);
      }
    }
    loadArtifacts();
  }, []);

  const [uploadStatus, setUploadStatus] = useState("");
  const [uploadPercent, setUploadPercent] = useState(0);

  const handleLaunch = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    setUploadStatus("Preparing files...");
    setUploadPercent(0);

    try {
      let modelId = selectedModelId;
      let datasetId = selectedDatasetId;

      // Handle direct file uploads if provided
      if (modelFile) {
        setUploadStatus(`Uploading Model Package (${(modelFile.size / (1024 * 1024)).toFixed(1)} MB)...`);
        const mData = new FormData();
        mData.append("name", modelFile.name.replace(".zip", ""));
        mData.append("file", modelFile);
        const mRes = await api.uploadModelPackage(mData, (pct, loaded, total) => {
          setUploadPercent(pct);
          setUploadStatus(`Uploading Model Package: ${pct}% (${(loaded / (1024 * 1024)).toFixed(1)} / ${(total / (1024 * 1024)).toFixed(1)} MB)`);
        });
        modelId = mRes.id;
      }

      if (datasetFile) {
        const sizeGb = (datasetFile.size / (1024 * 1024 * 1024)).toFixed(2);
        setUploadStatus(`Uploading Dataset (${sizeGb} GB)...`);
        const dData = new FormData();
        dData.append("name", datasetFile.name.replace(/\.[^/.]+$/, ""));
        dData.append("file", datasetFile);
        dData.append("dataset_type", datasetFile.name.endsWith(".csv") ? "csv_classification" : "image_classification");
        const dRes = await api.uploadDataset(dData, (pct, loaded, total) => {
          setUploadPercent(pct);
          const loadedStr = total > 1024 * 1024 * 1024
            ? `${(loaded / (1024 * 1024 * 1024)).toFixed(2)} / ${(total / (1024 * 1024 * 1024)).toFixed(2)} GB`
            : `${(loaded / (1024 * 1024)).toFixed(1)} / ${(total / (1024 * 1024)).toFixed(1)} MB`;
          setUploadStatus(`Uploading Dataset: ${pct}% (${loadedStr})`);
        });
        datasetId = dRes.id;
      }

      if (!modelId || !datasetId) {
        throw new Error("Please select or upload both a Model Package and a Dataset.");
      }

      setUploadStatus("Initializing training job & scheduling cluster...");

      // Create Training Job
      const jobData = {
        name,
        description,
        model_package_id: parseInt(modelId),
        dataset_id: parseInt(datasetId),
        max_rounds: parseInt(maxRounds),
        local_epochs: parseInt(localEpochs),
        batch_size: parseInt(batchSize),
        learning_rate: parseFloat(learningRate),
        target_accuracy: parseFloat(targetAccuracy),
        min_volunteer_nodes: parseInt(minVolunteerNodes),
      };

      const createdJob = await api.createJob(jobData);
      
      // Auto-start job
      await api.startJob(createdJob.id);

      // Navigate to live training view
      setSelectedJobId(createdJob.id);
      setActiveTab("training");
    } catch (err) {
      setError(err.message || "Failed to create training job");
    } finally {
      setLoading(false);
      setUploadStatus("");
    }
  };

  return (
    <div className="app-container animate-fade-in" style={{ maxWidth: "1000px" }}>
      <div className="glass-panel" style={{ padding: "2rem" }}>
        {/* Header */}
        <div style={{ borderBottom: "1px solid var(--border-color)", paddingBottom: "1.25rem", marginBottom: "1.75rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
            <div style={{
              background: "var(--primary-gradient)",
              padding: "0.5rem",
              borderRadius: "8px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center"
            }}>
              <PlayCircle size={20} color="#ffffff" />
            </div>
            <div>
              <h1 style={{ fontSize: "1.35rem", fontWeight: 700, color: "#ffffff" }}>
                Configure & Launch Training Job
              </h1>
              <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginTop: "0.15rem" }}>
                Select neural model architecture, dataset, and federated hyperparameter constraints.
              </p>
            </div>
          </div>
        </div>

        {error && (
          <div style={{
            background: "rgba(244, 63, 94, 0.15)",
            border: "1px solid rgba(244, 63, 94, 0.3)",
            color: "#f43f5e",
            padding: "0.85rem",
            borderRadius: "8px",
            fontSize: "0.85rem",
            marginBottom: "1.5rem"
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleLaunch} style={{ display: "flex", flexDirection: "column", gap: "1.75rem" }}>
          {/* Job Details */}
          <div>
            <h3 style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--primary)", marginBottom: "0.85rem" }}>
              1. Job Information
            </h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
              <div>
                <label style={{ display: "block", fontSize: "0.78rem", color: "var(--text-muted)", marginBottom: "0.35rem" }}>
                  Job Name
                </label>
                <input
                  type="text"
                  required
                  className="form-input"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: "0.78rem", color: "var(--text-muted)", marginBottom: "0.35rem" }}>
                  Description / Research Notes
                </label>
                <input
                  type="text"
                  className="form-input"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>
            </div>
          </div>

          {/* Model & Dataset Selection */}
          <div>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.85rem" }}>
              <h3 style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--primary)" }}>
                2. Model Package & Dataset
              </h3>
              <button
                type="button"
                onClick={() => setUploadMode(!uploadMode)}
                className="btn-secondary"
                style={{ fontSize: "0.75rem", padding: "0.3rem 0.6rem" }}
              >
                {uploadMode ? "Use Preloaded Artifacts" : "+ Upload Custom Files"}
              </button>
            </div>

            {!uploadMode ? (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                <div>
                  <label style={{ display: "block", fontSize: "0.78rem", color: "var(--text-muted)", marginBottom: "0.35rem" }}>
                    Select Model Package (.zip)
                  </label>
                  <select
                    className="form-input"
                    value={selectedModelId}
                    onChange={(e) => setSelectedModelId(e.target.value)}
                  >
                    {modelPackages.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.name} ({m.framework})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={{ display: "block", fontSize: "0.78rem", color: "var(--text-muted)", marginBottom: "0.35rem" }}>
                    Select Dataset
                  </label>
                  <select
                    className="form-input"
                    value={selectedDatasetId}
                    onChange={(e) => setSelectedDatasetId(e.target.value)}
                  >
                    {datasets.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name} ({d.total_samples} samples, {d.dataset_type})
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            ) : (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                <div style={{
                  border: "2px dashed var(--border-color)",
                  borderRadius: "10px",
                  padding: "1.25rem",
                  textAlign: "center",
                  background: "rgba(255, 255, 255, 0.02)"
                }}>
                  <Upload size={24} color="var(--primary)" style={{ marginBottom: "0.5rem" }} />
                  <div style={{ fontSize: "0.82rem", fontWeight: 600 }}>Custom Model Package (.zip)</div>
                  <input
                    type="file"
                    accept=".zip"
                    onChange={(e) => setModelFile(e.target.files[0])}
                    style={{ marginTop: "0.5rem", fontSize: "0.75rem" }}
                  />
                </div>

                <div style={{
                  border: "2px dashed var(--border-color)",
                  borderRadius: "10px",
                  padding: "1.25rem",
                  textAlign: "center",
                  background: "rgba(255, 255, 255, 0.02)"
                }}>
                  <Database size={24} color="var(--accent-cyan)" style={{ marginBottom: "0.5rem" }} />
                  <div style={{ fontSize: "0.82rem", fontWeight: 600 }}>Custom Dataset (.zip or .csv)</div>
                  <input
                    type="file"
                    accept=".zip,.csv"
                    onChange={(e) => setDatasetFile(e.target.files[0])}
                    style={{ marginTop: "0.5rem", fontSize: "0.75rem" }}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Hyperparameters */}
          <div>
            <h3 style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--primary)", marginBottom: "0.85rem" }}>
              3. Hyperparameters & Convergence Criteria
            </h3>
            
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1rem" }}>
              <div>
                <label style={{ display: "block", fontSize: "0.78rem", color: "var(--text-muted)", marginBottom: "0.35rem" }}>
                  Max Federated Rounds: <span style={{ color: "#ffffff", fontWeight: 600 }}>{maxRounds}</span>
                </label>
                <input
                  type="range"
                  min="1"
                  max="20"
                  value={maxRounds}
                  onChange={(e) => setMaxRounds(e.target.value)}
                  style={{ width: "100%" }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.78rem", color: "var(--text-muted)", marginBottom: "0.35rem" }}>
                  Local Epochs per Round: <span style={{ color: "#ffffff", fontWeight: 600 }}>{localEpochs}</span>
                </label>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={localEpochs}
                  onChange={(e) => setLocalEpochs(e.target.value)}
                  style={{ width: "100%" }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.78rem", color: "var(--text-muted)", marginBottom: "0.35rem" }}>
                  Batch Size: <span style={{ color: "#ffffff", fontWeight: 600 }}>{batchSize}</span>
                </label>
                <select
                  className="form-input"
                  value={batchSize}
                  onChange={(e) => setBatchSize(e.target.value)}
                >
                  <option value="16">16</option>
                  <option value="32">32 (Default)</option>
                  <option value="64">64</option>
                  <option value="128">128</option>
                </select>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.78rem", color: "var(--text-muted)", marginBottom: "0.35rem" }}>
                  Learning Rate (SGD)
                </label>
                <input
                  type="number"
                  step="0.001"
                  className="form-input"
                  value={learningRate}
                  onChange={(e) => setLearningRate(e.target.value)}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.78rem", color: "var(--text-muted)", marginBottom: "0.35rem" }}>
                  Target Accuracy (%): <span style={{ color: "#ffffff", fontWeight: 600 }}>{targetAccuracy}%</span>
                </label>
                <input
                  type="number"
                  min="10"
                  max="100"
                  className="form-input"
                  value={targetAccuracy}
                  onChange={(e) => setTargetAccuracy(e.target.value)}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.78rem", color: "var(--text-muted)", marginBottom: "0.35rem" }}>
                  Min Volunteer Workers
                </label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  className="form-input"
                  value={minVolunteerNodes}
                  onChange={(e) => setMinVolunteerNodes(e.target.value)}
                />
              </div>
            </div>
          </div>

          {loading && (
            <div style={{ background: "rgba(56, 189, 248, 0.08)", border: "1px solid rgba(56, 189, 248, 0.3)", borderRadius: "8px", padding: "0.85rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.82rem", color: "var(--primary)", fontWeight: 600, marginBottom: "0.4rem" }}>
                <span>{uploadStatus || "Initializing..."}</span>
                {uploadPercent > 0 && <span>{uploadPercent}%</span>}
              </div>
              {uploadPercent > 0 && (
                <div className="progress-bar-container" style={{ height: "6px" }}>
                  <div className="progress-bar-fill" style={{ width: `${uploadPercent}%` }} />
                </div>
              )}
            </div>
          )}

          {/* Submit */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", paddingTop: "1rem", borderTop: "1px solid var(--border-color)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.78rem", color: "var(--text-dim)" }}>
              <Info size={15} color="var(--primary)" />
              The scheduler will automatically select optimal volunteers based on live CPU, RAM, GPU, and network metrics.
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary"
              style={{ padding: "0.8rem 1.8rem", fontSize: "0.95rem" }}
            >
              {loading ? (uploadStatus ? "Uploading..." : "Initializing...") : "Start Distributed Training"}
              <ArrowRight size={18} />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
