import React from "react";
import { 
  Cpu, 
  Activity, 
  PlusCircle, 
  Layers, 
  Radio, 
  BarChart3, 
  FileText, 
  Zap 
} from "lucide-react";

export default function Sidebar({ activeTab, setActiveTab, user }) {
  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: Activity },
    { id: "create_job", label: "Create Job", icon: PlusCircle },
    { id: "training", label: "Live Execution", icon: Layers, liveBadge: true },
    { id: "admin", label: "Fleet Telemetry", icon: Radio },
    { id: "scheduler", label: "Scheduler Engine", icon: Cpu },
    { id: "evaluation", label: "Benchmarks", icon: BarChart3 },
    { id: "reports", label: "Reports", icon: FileText },
  ].filter((item) => !item.adminOnly || user?.role === "admin");

  return (
    <aside style={{
      width: "240px",
      minWidth: "240px",
      background: "var(--bg-sidebar)",
      borderRight: "1px solid var(--border-color)",
      display: "flex",
      flexDirection: "column",
      justifyContent: "space-between",
      padding: "1.25rem 1rem",
      height: "100vh",
      position: "sticky",
      top: 0,
      zIndex: 40,
      transition: "background 0.25s ease, border-color 0.25s ease"
    }}>
      <div>
        {/* Logo Brand */}
        <div 
          onClick={() => setActiveTab("dashboard")}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.75rem",
            padding: "0.5rem 0.5rem 1.25rem 0.5rem",
            cursor: "pointer",
            borderBottom: "1px solid var(--border-color)"
          }}
        >
          <div style={{
            background: "linear-gradient(135deg, #0066FF 0%, #38bdf8 100%)",
            width: "36px",
            height: "36px",
            borderRadius: "10px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 4px 12px rgba(0, 102, 255, 0.3)"
          }}>
            <Cpu size={20} color="#ffffff" />
          </div>
          <div>
            <div style={{ fontSize: "1.15rem", fontWeight: 800, letterSpacing: "-0.02em", color: "var(--text-heading)", lineHeight: 1.1 }}>
              Neuro<span style={{ color: "var(--primary)" }}>Broker</span>
            </div>
            <div style={{ fontSize: "0.6rem", color: "var(--text-dim)", fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", marginTop: "0.15rem" }}>
              Enterprise Compute Mesh
            </div>
          </div>
        </div>

        {/* Workspace Nav Header */}
        <div style={{
          fontSize: "0.66rem",
          fontWeight: 800,
          color: "var(--text-dim)",
          letterSpacing: "0.12em",
          textTransform: "uppercase",
          padding: "1.25rem 0.75rem 0.5rem 0.75rem"
        }}>
          Workspace
        </div>

        {/* Navigation items */}
        <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                style={{
                  background: isActive ? "rgba(0, 102, 255, 0.08)" : "transparent",
                  color: isActive ? "var(--primary)" : "var(--text-muted)",
                  border: isActive ? "1px solid rgba(0, 102, 255, 0.2)" : "1px solid transparent",
                  borderRadius: "10px",
                  padding: "0.6rem 0.85rem",
                  fontSize: "0.85rem",
                  fontWeight: isActive ? 700 : 500,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  transition: "all 0.15s ease",
                  textAlign: "left"
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "0.65rem" }}>
                  <Icon size={16} color={isActive ? "var(--primary)" : "var(--text-dim)"} />
                  <span>{item.label}</span>
                </div>
                {item.liveBadge && (
                  <span className="pulse-dot" style={{ background: "#10b981", width: "6px", height: "6px" }} />
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Bottom Sidebar Box: Mesh Health */}
      <div style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border-color)",
        borderRadius: "12px",
        padding: "0.85rem 1rem"
      }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.4rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", fontSize: "0.72rem", color: "var(--text-muted)" }}>
            <Zap size={13} color="var(--primary)" />
            <span>Mesh health</span>
          </div>
          <span style={{
            fontSize: "0.65rem",
            fontWeight: 700,
            color: "#059669",
            background: "#ecfdf5",
            padding: "0.15rem 0.5rem",
            borderRadius: "999px",
            border: "1px solid #a7f3d0"
          }}>
            Operational
          </span>
        </div>
        <div style={{ fontSize: "1.25rem", fontWeight: 800, color: "var(--text-heading)", marginBottom: "0.4rem" }}>
          99.98%
        </div>
        <div className="progress-bar-container" style={{ height: "4px" }}>
          <div className="progress-bar-fill" style={{ width: "99.98%", background: "linear-gradient(90deg, #10b981, #06b6d4)" }} />
        </div>
      </div>
    </aside>
  );
}
