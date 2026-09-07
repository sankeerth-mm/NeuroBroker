import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { Cpu, Lock, Mail, ArrowRight, ShieldCheck, UserCheck } from "lucide-react";

export default function Login({ onSwitchToRegister }) {
  const { login, register } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
    } catch (err) {
      setError(err.message || "Failed to login");
    } finally {
      setLoading(false);
    }
  };

  // Quick 1-Click Demo Login
  const handleQuickDemo = async (role = "admin") => {
    setError("");
    setLoading(true);
    const demoEmail = role === "admin" ? "admin@neurobroker.org" : "user@neurobroker.org";
    const demoPass = "AdminPassword123!";
    try {
      await login(demoEmail, demoPass);
    } catch (err) {
      // If user doesn't exist yet, auto-register demo account
      try {
        await register(role === "admin" ? "Admin User" : "Demo Researcher", demoEmail, demoPass, role);
      } catch (regErr) {
        setError(regErr.message);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: "1.5rem"
    }}>
      <div className="glass-panel" style={{
        width: "100%",
        maxWidth: "440px",
        padding: "2.5rem 2rem",
        boxShadow: "var(--shadow-neon), var(--shadow-glass)"
      }}>
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "2rem" }}>
          <div style={{
            background: "var(--primary-gradient)",
            width: "52px",
            height: "52px",
            borderRadius: "14px",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 0 20px rgba(56, 189, 248, 0.4)",
            marginBottom: "1rem"
          }}>
            <Cpu size={28} color="#ffffff" />
          </div>
          <h1 style={{ fontSize: "1.6rem", fontWeight: 800, color: "#ffffff" }}>
            Neuro<span style={{ color: "var(--primary)" }}>Broker</span>
          </h1>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "0.3rem" }}>
            Volunteer Distributed Deep Learning Engine
          </p>
        </div>

        {error && (
          <div style={{
            background: "rgba(244, 63, 94, 0.15)",
            border: "1px solid rgba(244, 63, 94, 0.3)",
            color: "#f43f5e",
            padding: "0.75rem",
            borderRadius: "8px",
            fontSize: "0.85rem",
            marginBottom: "1.25rem"
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1.1rem" }}>
          <div>
            <label style={{ display: "block", fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "0.4rem", fontWeight: 500 }}>
              Email Address
            </label>
            <div style={{ position: "relative" }}>
              <input
                type="email"
                required
                className="form-input"
                placeholder="researcher@university.edu"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                style={{ paddingLeft: "2.5rem" }}
              />
              <Mail size={16} color="var(--text-dim)" style={{ position: "absolute", left: "0.85rem", top: "50%", transform: "translateY(-50%)" }} />
            </div>
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "0.4rem", fontWeight: 500 }}>
              Password
            </label>
            <div style={{ position: "relative" }}>
              <input
                type="password"
                required
                className="form-input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={{ paddingLeft: "2.5rem" }}
              />
              <Lock size={16} color="var(--text-dim)" style={{ position: "absolute", left: "0.85rem", top: "50%", transform: "translateY(-50%)" }} />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary"
            style={{ width: "100%", justifyContent: "center", marginTop: "0.5rem", padding: "0.8rem" }}
          >
            {loading ? "Authenticating..." : "Sign In to Dashboard"}
            <ArrowRight size={16} />
          </button>
        </form>

        {/* Quick Demo Section */}
        <div style={{ marginTop: "1.75rem", paddingTop: "1.5rem", borderTop: "1px solid var(--border-color)" }}>
          <div style={{ fontSize: "0.75rem", color: "var(--text-dim)", textAlign: "center", marginBottom: "0.8rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            1-Click Demo Evaluation Login
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
            <button
              onClick={() => handleQuickDemo("admin")}
              type="button"
              className="btn-secondary"
              style={{ fontSize: "0.8rem", justifyContent: "center", padding: "0.55rem" }}
            >
              <ShieldCheck size={15} color="var(--accent-cyan)" />
              <span>Admin Demo</span>
            </button>
            <button
              onClick={() => handleQuickDemo("user")}
              type="button"
              className="btn-secondary"
              style={{ fontSize: "0.8rem", justifyContent: "center", padding: "0.55rem" }}
            >
              <UserCheck size={15} color="var(--accent-emerald)" />
              <span>User Demo</span>
            </button>
          </div>
        </div>

        <div style={{ textAlign: "center", marginTop: "1.5rem", fontSize: "0.82rem", color: "var(--text-muted)" }}>
          Don't have an account?{" "}
          <span
            onClick={onSwitchToRegister}
            style={{ color: "var(--primary)", fontWeight: 600, cursor: "pointer" }}
          >
            Register Here
          </span>
        </div>
      </div>
    </div>
  );
}
