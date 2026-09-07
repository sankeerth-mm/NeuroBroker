const host = typeof window !== "undefined" && window.location.hostname ? window.location.hostname : "127.0.0.1";
const API_BASE = `http://${host}:8000`;

function getHeaders(isJson = true) {
  const token = localStorage.getItem("nb_token");
  const headers = {};
  if (isJson) {
    headers["Content-Type"] = "application/json";
  }
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

export const api = {
  // Auth
  async login(email, password) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Login failed" }));
      throw new Error(err.detail || "Invalid credentials");
    }
    return res.json();
  },

  async register(name, email, password, role = "user") {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password, role }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Registration failed" }));
      throw new Error(err.detail || "Registration failed");
    }
    return res.json();
  },

  async getMe() {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error("Unauthorized");
    return res.json();
  },

  // Nodes
  async getNodes() {
    const res = await fetch(`${API_BASE}/api/nodes`, { headers: getHeaders() });
    if (!res.ok) throw new Error("Failed to fetch nodes");
    return res.json();
  },

  async getNodeHistory(nodeId) {
    const res = await fetch(`${API_BASE}/api/nodes/${nodeId}/history`, { headers: getHeaders() });
    if (!res.ok) return [];
    return res.json();
  },

  getVolunteerClientDownloadUrl() {
    return `${API_BASE}/api/nodes/client/download`;
  },

  // Datasets
  async getDatasets() {
    const res = await fetch(`${API_BASE}/api/datasets`, { headers: getHeaders() });
    if (!res.ok) throw new Error("Failed to fetch datasets");
    return res.json();
  },

  uploadWithProgress(url, formData, onProgress) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", url);
      const token = localStorage.getItem("nb_token");
      if (token) {
        xhr.setRequestHeader("Authorization", `Bearer ${token}`);
      }

      if (xhr.upload && onProgress) {
        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            const percent = Math.round((event.loaded / event.total) * 100);
            onProgress(percent, event.loaded, event.total);
          }
        };
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText));
          } catch (e) {
            resolve(xhr.responseText);
          }
        } else {
          try {
            const err = JSON.parse(xhr.responseText);
            reject(new Error(err.detail || "Upload failed"));
          } catch (e) {
            reject(new Error(`Upload failed with status ${xhr.status}`));
          }
        }
      };

      xhr.onerror = () => reject(new Error("Network error during upload"));
      xhr.send(formData);
    });
  },

  async uploadDataset(formData, onProgress) {
    return this.uploadWithProgress(`${API_BASE}/api/datasets/upload`, formData, onProgress);
  },

  // Models
  async getModelPackages() {
    const res = await fetch(`${API_BASE}/api/models`, { headers: getHeaders() });
    if (!res.ok) throw new Error("Failed to fetch model packages");
    return res.json();
  },

  async uploadModelPackage(formData, onProgress) {
    return this.uploadWithProgress(`${API_BASE}/api/models/upload`, formData, onProgress);
  },

  getFinalModelDownloadUrl(jobId) {
    return `${API_BASE}/api/models/jobs/${jobId}/final`;
  },

  // Jobs
  async getJobs() {
    const res = await fetch(`${API_BASE}/api/jobs`, { headers: getHeaders() });
    if (!res.ok) throw new Error("Failed to fetch jobs");
    return res.json();
  },

  async getJobDetail(jobId) {
    const res = await fetch(`${API_BASE}/api/jobs/${jobId}`, { headers: getHeaders() });
    if (!res.ok) throw new Error("Job not found");
    return res.json();
  },

  async createJob(jobData) {
    const res = await fetch(`${API_BASE}/api/jobs`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(jobData),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Failed to create job" }));
      throw new Error(err.detail || "Job creation failed");
    }
    return res.json();
  },

  async startJob(jobId) {
    const res = await fetch(`${API_BASE}/api/jobs/${jobId}/start`, {
      method: "POST",
      headers: getHeaders(),
    });
    return res.json();
  },

  async stopJob(jobId) {
    const res = await fetch(`${API_BASE}/api/jobs/${jobId}/stop`, {
      method: "POST",
      headers: getHeaders(),
    });
    return res.json();
  },

  async pauseJob(jobId) {
    const res = await fetch(`${API_BASE}/api/jobs/${jobId}/pause`, {
      method: "POST",
      headers: getHeaders(),
    });
    return res.json();
  },

  async resumeJob(jobId) {
    const res = await fetch(`${API_BASE}/api/jobs/${jobId}/resume`, {
      method: "POST",
      headers: getHeaders(),
    });
    return res.json();
  },

  async getJobRounds(jobId) {
    const res = await fetch(`${API_BASE}/api/jobs/${jobId}/rounds`, { headers: getHeaders() });
    if (!res.ok) return [];
    return res.json();
  },

  async getJobTasks(jobId) {
    const res = await fetch(`${API_BASE}/api/jobs/${jobId}`, { headers: getHeaders() });
    if (!res.ok) return [];
    const data = await res.json();
    return data.tasks || [];
  },

  async getJobReport(jobId) {
    const res = await fetch(`${API_BASE}/api/jobs/${jobId}/report`, { headers: getHeaders() });
    return res.json();
  },

  // Admin
  async getAdminStats() {
    const res = await fetch(`${API_BASE}/api/admin/stats`, { headers: getHeaders() });
    if (!res.ok) throw new Error("Admin access required");
    return res.json();
  },

  async getSystemLogs(level = "", component = "") {
    let url = `${API_BASE}/api/admin/logs?limit=100`;
    if (level) url += `&level=${level}`;
    if (component) url += `&component=${component}`;
    const res = await fetch(url, { headers: getHeaders() });
    return res.json();
  },

  async getSchedulerDecisions(jobId = "") {
    let url = `${API_BASE}/api/admin/scheduler-decisions?limit=100`;
    if (jobId) url += `&job_id=${jobId}`;
    const res = await fetch(url, { headers: getHeaders() });
    return res.json();
  },
};
