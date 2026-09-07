import React, { createContext, useContext, useState, useEffect } from "react";
import { api } from "../services/api";
import { wsService } from "../services/websocket";

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("nb_token"));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadUser() {
      if (token) {
        try {
          const u = await api.getMe();
          setUser(u);
          wsService.connect(u.id);
        } catch (err) {
          console.error("Token verification failed:", err);
          logout();
        }
      }
      setLoading(false);
    }
    loadUser();
  }, [token]);

  const login = async (email, password) => {
    const res = await api.login(email, password);
    localStorage.setItem("nb_token", res.access_token);
    setToken(res.access_token);
    setUser(res.user);
    wsService.connect(res.user.id);
    return res.user;
  };

  const register = async (name, email, password, role = "user") => {
    const res = await api.register(name, email, password, role);
    localStorage.setItem("nb_token", res.access_token);
    setToken(res.access_token);
    setUser(res.user);
    wsService.connect(res.user.id);
    return res.user;
  };

  const logout = () => {
    localStorage.removeItem("nb_token");
    setToken(null);
    setUser(null);
    wsService.disconnect();
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
