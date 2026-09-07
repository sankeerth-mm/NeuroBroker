import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { Cpu, Lock, Mail, User, ArrowRight } from "lucide-react";

export default function Register({ onSwitchToLogin }) {
  const { register } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("user");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(name, email, password, role);
    } catch (err) {
      setError(err.message || "Registration failed");
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
        maxWidth: "460px",
        padding: "2.5rem 2rem",
        boxShadow: "var(--shadow-neon), var(--shadow-glass)"
      }}>
        <div style={{ textAlign: "center", marginBottom: "1.75rem" }}>
          <div style={{
            background: "var(--primary-gradient)",
            width: "50px",
            height: "50px",
            borderRadius: "14px",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 0 20px rgba(56, 189, 248, 0.4)",
            marginBottom: "0.75rem"
          }}>
            <Cpu size={26} color="#ffffff" />
          </div>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 800, color: "#ffffff" }}>
            Create Account
          </h1>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
            Join NeuroBroker Distributed DL Cluster
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
              Full Name
            </label>
            <div style={{ position: "relative" }}>
              <input
                type="text"
                required
                className="form-input"
                placeholder="Dr. Samantha Vance"
                value={name}
                onChange={(e) => setName(e.target.value)}
                style={{ paddingLeft: "2.5rem" }}
              />
              <User size={16} color="var(--text-dim)" style={{ position: "absolute", left: "0.85rem", top: "50%", transform: "translateY(-50%)" }} />
            </div>
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "0.4rem", fontWeight: 500 }}>
              Email Address
            </label>
            <div style={{ position: "relative" }}>
              <input
                type="email"
                required
                className="form-input"
                placeholder="svance@university.edu"
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
                minLength={6}
                className="form-input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={{ paddingLeft: "2.5rem" }}
              />
              <Lock size={16} color="var(--text-dim)" style={{ position: "absolute", left: "0.85rem", top: "50%", transform: "translateY(-50%)" }} />
            </div>
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "0.4rem", fontWeight: 500 }}>
              Role
            </label>
            <select
              className="form-input"
              value={role}
              onChange={(e) => setRole(e.target.value)}
            >
              <option value="user">Researcher / Student (User)</option>
              <option value="admin">Cluster Administrator</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary"
            style={{ width: "100%", justifyContent: "center", marginTop: "0.5rem", padding: "0.8rem" }}
          >
            {loading ? "Creating Account..." : "Complete Registration"}
            <ArrowRight size={16} />
          </button>
        </form>

        <div style={{ textAlign: "center", marginTop: "1.5rem", fontSize: "0.82rem", color: "var(--text-muted)" }}>
          Already have an account?{" "}
          <span
            onClick={onSwitchToLogin}
            style={{ color: "var(--primary)", fontWeight: 600, cursor: "pointer" }}
          >
            Sign In
          </span>
        </div>
      </div>
    </div>
  );
}
