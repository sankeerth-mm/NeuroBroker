import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { api } from "../services/api";
import { wsService } from "../services/websocket";
import { 
  Cpu, 
  Layers, 
  PlayCircle, 
  Activity, 
  ShieldAlert, 
  HelpCircle, 
  BarChart3, 
  FileText, 
  Download, 
  LogOut, 
  User, 
  Server 
} from "lucide-react";

export default function Navbar({ activeTab, setActiveTab }) {
  const { user, logout } = useAuth();
  const [onlineCount, setOnlineCount] = useState(0);

  useEffect(() => {
    async function fetchStats() {
      try {
        const nodesData = await api.getNodes();
        setOnlineCount(nodesData.online_count || 0);
      } catch (e) {}
    }
    fetchStats();

    const handleNodeUpdate = () => fetchStats();
    wsService.on("node_connected", handleNodeUpdate);
    wsService.on("node_disconnected", handleNodeUpdate);
    wsService.on("node_registered", handleNodeUpdate);

    return () => {
      wsService.off("node_connected", handleNodeUpdate);
      wsService.off("node_disconnected", handleNodeUpdate);
      wsService.off("node_registered", handleNodeUpdate);
    };
  }, []);

  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: Activity },
    { id: "create_job", label: "Create Training", icon: PlayCircle },
    { id: "training", label: "Live Training", icon: Layers },
    { id: "admin", label: "Fleet & Nodes", icon: Server },
    { id: "scheduler", label: "Scheduler Explainer", icon: HelpCircle },
    { id: "evaluation", label: "Benchmarks", icon: BarChart3 },
    { id: "reports", label: "Reports", icon: FileText },
  ];

  return (
    <nav style={{
      background: "rgba(9, 13, 22, 0.85)",
      backdropFilter: "blur(20px)",
      borderBottom: "1px solid var(--border-color)",
      position: "sticky",
      top: 0,
      zIndex: 50,
      padding: "0.75rem 1.5rem"
    }}>
      <div style={{
        maxWidth: "1440px",
        margin: "0 auto",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "1.5rem"
      }}>
        {/* Brand Logo */}
        <div 
          onClick={() => setActiveTab("dashboard")}
          style={{ display: "flex", alignItems: "center", gap: "0.75rem", cursor: "pointer" }}
        >
          <div style={{
            background: "var(--primary-gradient)",
            width: "38px",
            height: "38px",
            borderRadius: "10px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 0 15px rgba(56, 189, 248, 0.4)"
          }}>
            <Cpu size={22} color="#ffffff" />
          </div>
          <div>
            <div style={{ fontSize: "1.25rem", fontWeight: 800, letterSpacing: "-0.02em", color: "#f8fafc" }}>
              Neuro<span style={{ color: "var(--primary)" }}>Broker</span>
            </div>
            <div style={{ fontSize: "0.68rem", color: "var(--text-muted)", letterSpacing: "0.05em", textTransform: "uppercase" }}>
              Compute Brokerage Engine
            </div>
          </div>
        </div>

        {/* Navigation Links */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                style={{
                  background: isActive ? "rgba(56, 189, 248, 0.12)" : "transparent",
                  color: isActive ? "var(--primary)" : "var(--text-muted)",
                  border: isActive ? "1px solid rgba(56, 189, 248, 0.3)" : "1px solid transparent",
                  padding: "0.45rem 0.85rem",
                  borderRadius: "8px",
                  fontSize: "0.88rem",
                  fontWeight: isActive ? 600 : 500,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.45rem",
                  transition: "all 0.15s ease"
                }}
              >
                <Icon size={16} />
                {item.label}
              </button>
            );
          })}
        </div>

        {/* Right Section: Node Count, Download Client, User Info */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.9rem" }}>
          {/* Online Fleet Badge */}
          <div 
            onClick={() => setActiveTab("admin")}
            className="status-pill status-online" 
            style={{ cursor: "pointer", fontSize: "0.72rem" }}
            title="Connected volunteer computers ready for distributed training"
          >
            <span className="pulse-dot" style={{ background: "#10b981" }} />
            {onlineCount} Nodes Online
          </div>

          {/* Download Volunteer Client Button */}
          <a
            href={api.getVolunteerClientDownloadUrl()}
            download
            className="btn-secondary"
            style={{ textDecoration: "none", fontSize: "0.82rem", padding: "0.45rem 0.85rem" }}
            title="Download the standalone Python program to run on remote volunteer lab computers"
          >
            <Download size={14} color="var(--primary)" />
            <span>Volunteer Client (.zip)</span>
          </a>

          {/* User Badge & Logout */}
          <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
            <div style={{ textAlign: "right", fontSize: "0.78rem" }}>
              <div style={{ fontWeight: 600, color: "var(--text-main)" }}>{user?.name || "User"}</div>
              <div style={{ color: "var(--text-dim)", textTransform: "uppercase", fontSize: "0.68rem" }}>
                {user?.role || "user"}
              </div>
            </div>
            <button 
              onClick={logout} 
              className="btn-secondary" 
              style={{ padding: "0.45rem", borderRadius: "8px" }}
              title="Logout"
            >
              <LogOut size={15} />
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
