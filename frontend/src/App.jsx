import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import { AuthProvider, useAuth }   from "./context/AuthContext";
import { PolicyProvider }          from "./components/PolicyContext";

import Sidebar     from "./components/Sidebar";
import LoginPage   from "./pages/LoginPage";
import ChatPage    from "./pages/ChatPage";
import ClaimsPage  from "./pages/ClaimsPage";
import PolicyPage  from "./pages/PolicyPage";

import "./index.css";

function ProtectedLayout() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{
        minHeight: "100vh", display: "flex",
        alignItems: "center", justifyContent: "center",
        background: "#0F172A", color: "#475569",
        fontSize: 14, fontFamily: "Inter, sans-serif",
      }}>
        Loading…
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;

  return (
    <PolicyProvider>
      <div className="app-container">
        <Sidebar />
        <div className="content">
          <Routes>
            <Route path="/"         element={<ChatPage />} />
            <Route path="/policies" element={<PolicyPage />} />
            <Route path="/claims"   element={<ClaimsPage />} />
          </Routes>
        </div>
      </div>
    </PolicyProvider>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/*"     element={<ProtectedLayout />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;