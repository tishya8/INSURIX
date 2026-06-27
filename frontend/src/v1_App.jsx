import { BrowserRouter, Routes, Route } from "react-router-dom";

import Sidebar from "./components/Sidebar";

import ChatPage from "./pages/ChatPage";
import ClaimsPage from "./pages/ClaimsPage";
import PolicyPage from "./pages/PolicyPage";

import "./index.css";

function App() {
  return (
    <BrowserRouter>
      <div className="app-container">

        <Sidebar />

        <div className="content">
          <Routes>
            <Route path="/" element={<ChatPage />} />
            <Route path="/claims" element={<ClaimsPage />} />
            <Route path="/policies" element={<PolicyPage />} />
          </Routes>
        </div>

      </div>
    </BrowserRouter>
  );
}

export default App;