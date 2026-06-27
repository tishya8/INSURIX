import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";

import App from "./App.jsx";

import { AuthProvider } from "./context/AuthContext";
import { PolicyProvider } from "./components/PolicyContext";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <AuthProvider>
      <PolicyProvider>
        <App />
      </PolicyProvider>
    </AuthProvider>
  </StrictMode>
);