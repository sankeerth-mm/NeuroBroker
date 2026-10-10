import React, { useState } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { ThemeProvider } from "./context/ThemeContext";
import Sidebar from "./components/Sidebar";
import TopHeader from "./components/TopHeader";
import Login from "./pages/Login";
import Register from "./pages/Register";
import UserDashboard from "./pages/UserDashboard";
import CreateJob from "./pages/CreateJob";
import TrainingView from "./pages/TrainingView";
import AdminDashboard from "./pages/AdminDashboard";
import SchedulerExplainer from "./pages/SchedulerExplainer";
import EvaluationView from "./pages/EvaluationView";
import ReportsView from "./pages/ReportsView";

function MainApp() {
  const { user, loading } = useAuth();
  const [authMode, setAuthMode] = useState("login"); // 'login' or 'register'
  const [activeTab, setActiveTab] = useState("dashboard");
  const [selectedJobId, setSelectedJobId] = useState(null);

  if (loading) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--primary)" }}>
        <div style={{ textAlign: "center" }}>
          <div className="pulse-dot" style={{ background: "var(--primary)", width: "16px", height: "16px", margin: "0 auto 1rem" }} />
          <div style={{ fontWeight: 600, letterSpacing: "0.05em" }}>INITIALIZING NEUROBROKER...</div>
        </div>
      </div>
    );
  }

  if (!user) {
    return authMode === "login" ? (
      <Login onSwitchToRegister={() => setAuthMode("register")} />
    ) : (
      <Register onSwitchToLogin={() => setAuthMode("login")} />
    );
  }

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "var(--bg-primary)" }}>
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} user={user} />
      
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        <TopHeader />
        
        <main style={{ flex: 1, padding: "1.75rem 2.25rem 3rem 2.25rem", overflowY: "auto" }}>
          {activeTab === "dashboard" && (
            <UserDashboard setActiveTab={setActiveTab} setSelectedJobId={setSelectedJobId} />
          )}
          {activeTab === "create_job" && (
            <CreateJob setActiveTab={setActiveTab} setSelectedJobId={setSelectedJobId} />
          )}
          {activeTab === "training" && (
            <TrainingView selectedJobId={selectedJobId} setSelectedJobId={setSelectedJobId} setActiveTab={setActiveTab} />
          )}
          {activeTab === "admin" && <AdminDashboard />}
          {activeTab === "scheduler" && <SchedulerExplainer />}
          {activeTab === "evaluation" && <EvaluationView />}
          {activeTab === "reports" && <ReportsView />}
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <MainApp />
      </AuthProvider>
    </ThemeProvider>
  );
}
