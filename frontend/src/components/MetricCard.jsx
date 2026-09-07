import React from "react";

export default function MetricCard({ title, value, subtitle, icon: Icon, color = "var(--primary)", trend = null }) {
  return (
    <div className="glass-panel" style={{ padding: "1.25rem", position: "relative", overflow: "hidden" }}>
      <div style={{
        position: "absolute",
        top: "-15px",
        right: "-15px",
        width: "80px",
        height: "80px",
        borderRadius: "50%",
        background: color,
        filter: "blur(40px)",
        opacity: 0.15,
        pointerEvents: "none"
      }} />

      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
        <div>
          <div style={{ fontSize: "0.82rem", color: "var(--text-muted)", fontWeight: 500, marginBottom: "0.4rem" }}>
            {title}
          </div>
          <div style={{ fontSize: "1.75rem", fontWeight: 700, color: "#ffffff", letterSpacing: "-0.02em" }}>
            {value}
          </div>
        </div>

        {Icon && (
          <div style={{
            background: `rgba(255, 255, 255, 0.05)`,
            border: "1px solid var(--border-color)",
            padding: "0.6rem",
            borderRadius: "10px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: color
          }}>
            <Icon size={20} />
          </div>
        )}
      </div>

      {(subtitle || trend) && (
        <div style={{ marginTop: "0.65rem", fontSize: "0.78rem", color: "var(--text-dim)", display: "flex", alignItems: "center", gap: "0.4rem" }}>
          {subtitle && <span>{subtitle}</span>}
          {trend && <span style={{ color: trend > 0 ? "var(--accent-emerald)" : "var(--accent-rose)", fontWeight: 600 }}>{trend}</span>}
        </div>
      )}
    </div>
  );
}
