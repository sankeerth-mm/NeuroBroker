import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
import { api } from "../services/api";
import { wsService } from "../services/websocket";
import { Download, LogOut, Sun, Moon, Radio } from "lucide-react";

export default function TopHeader() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [onlineCount, setOnlineCount] = useState(0);

  useEffect(() => {
    async function fetchCount() {
      try {
        const nodesData = await api.getNodes();
        if (nodesData && nodesData.nodes) {
          const online = nodesData.nodes.filter(n => ["ONLINE", "BUSY"].includes(n.status)).length;
          setOnlineCount(online);
        }
      } catch (e) {}
    }
    fetchCount();

    const updateCount = () => fetchCount();
    wsService.on("node_connected", updateCount);
    wsService.on("node_disconnected", updateCount);
    return () => {
      wsService.off("node_connected", updateCount);
      wsService.off("node_disconnected", updateCount);
    };
  }, []);

  const initials = user?.name
    ? user.name.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2)
    : "CA";

  return (
    <header style={{
      height: "64px",
      background: "var(--bg-header)",
      backdropFilter: "blur(12px)",
      WebkitBackdropFilter: "blur(12px)",
      borderBottom: "1px solid var(--border-color)",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "0 2.25rem",
      position: "sticky",
      top: 0,
      zIndex: 30,
      transition: "background 0.25s ease, border-color 0.25s ease"
    }}>
      {/* Left Header Indicator */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
        <div style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "0.45rem",
          background: theme === "dark" ? "rgba(16, 185, 129, 0.12)" : "#ecfdf5",
          border: theme === "dark" ? "1px solid rgba(16, 185, 129, 0.25)" : "1px solid #a7f3d0",
          color: theme === "dark" ? "#34d399" : "#059669",
          padding: "0.3rem 0.75rem",
          borderRadius: "999px",
          fontSize: "0.72rem",
          fontWeight: 700,
          letterSpacing: "0.06em",
          textTransform: "uppercase"
        }}>
          <span className="pulse-dot" style={{ background: "#10b981", width: "6px", height: "6px" }} />
          <span>COMMAND CENTER - LIVE</span>
        </div>
      </div>

      {/* Right Header Actions */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.85rem" }}>
        
        {/* Light / Dark Mode Toggle Button */}
        <button
          onClick={toggleTheme}
          className="theme-toggle-btn"
          title={`Switch to ${theme === "light" ? "Dark" : "Light"} Mode`}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.45rem",
            padding: "0.4rem 0.8rem",
            borderRadius: "999px",
            fontSize: "0.78rem",
            fontWeight: 600
          }}
        >
          {theme === "light" ? (
            <>
              <Moon size={15} color="#6366f1" />
              <span>Dark Mode</span>
            </>
          ) : (
            <>
              <Sun size={15} color="#f59e0b" />
              <span>Light Mode</span>
            </>
          )}
        </button>

        {/* Nodes Active Pill */}
        <div style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border-color)",
          borderRadius: "999px",
          padding: "0.35rem 0.85rem",
          display: "flex",
          alignItems: "center",
          gap: "0.45rem",
          fontSize: "0.78rem",
          color: "var(--text-muted)"
        }}>
          <span className="pulse-dot" style={{ background: "#10b981", width: "6px", height: "6px" }} />
          <span><strong style={{ color: "var(--text-heading)" }}>{onlineCount}</strong> nodes active</span>
        </div>

        {/* Volunteer Client .ZIP Button */}
        <a
          href={api.getVolunteerClientDownloadUrl()}
          download
          style={{
            background: "var(--bg-card)",
            border: "1px solid var(--border-color)",
            borderRadius: "999px",
            padding: "0.35rem 0.85rem",
            color: "var(--text-heading)",
            fontSize: "0.78rem",
            fontWeight: 600,
            display: "flex",
            alignItems: "center",
            gap: "0.4rem",
            textDecoration: "none",
            transition: "all 0.2s ease"
          }}
        >
          <Download size={13} color="var(--primary)" />
          <span>Client .ZIP</span>
        </a>

        {/* User Avatar Capsule */}
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: "0.55rem",
          padding: "0.2rem 0.6rem 0.2rem 0.25rem",
          borderRadius: "999px",
          background: "var(--bg-card)",
          border: "1px solid var(--border-color)"
        }}>
          <div style={{
            width: "30px",
            height: "30px",
            borderRadius: "50%",
            background: "linear-gradient(135deg, #0066FF, #6366f1)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "0.72rem",
            fontWeight: 800,
            color: "#ffffff"
          }}>
            {initials}
          </div>
          <div style={{ fontSize: "0.76rem", lineHeight: 1.15 }}>
            <div style={{ fontWeight: 700, color: "var(--text-heading)" }}>{user?.name || "Cluster Administrator"}</div>
            <div style={{ fontSize: "0.65rem", color: "var(--text-dim)" }}>{user?.role === "admin" ? "Administrator" : "Researcher"}</div>
          </div>
        </div>

        {/* Logout button */}
        <button
          onClick={logout}
          style={{
            background: "var(--bg-card)",
            border: "1px solid var(--border-color)",
            borderRadius: "50%",
            width: "32px",
            height: "32px",
            color: "var(--text-muted)",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transition: "all 0.2s ease"
          }}
          title="Sign Out"
        >
          <LogOut size={15} />
        </button>

      </div>
    </header>
  );
}
