import { Link } from "react-router-dom";
import { useContext } from "react";

import { PolicyContext }
  from "../components/PolicyContext";

import PolicyCard
  from "./PolicyCard";

function Sidebar() {

  const {
    policyId,
    setPolicyId
  } = useContext(PolicyContext);

  return (
    <div
      style={{
        width: "280px",
        background: "#1f2937",
        color: "white",
        padding: "20px",
        minHeight: "100vh",
        position: "sticky",
        top: 0,
      }}
    >
      <h2
        style={{
          marginBottom: "30px",
        }}
      >
        INSURIX
      </h2>

      <div
        style={{
          marginBottom: "25px",
          padding: "12px",
          background: "#374151",
          borderRadius: "10px",
        }}
      >
        <strong>Current Session</strong>
        <br />
        user_01
      </div>

      <h4
        style={{
          marginBottom: "10px",
        }}
      >
        Policies
      </h4>

      <PolicyCard
        policyId="CAR-101"
        title="Toyota Camry"
        selected={policyId === "1"}
        onClick={() =>
          setPolicyId("1")
        }
      />

      <PolicyCard
        policyId="BIKE-101"
        title="Honda CB300R"
        selected={policyId === "2"}
        onClick={() =>
          setPolicyId("2")
        }
      />

      <hr
        style={{
          margin: "20px 0",
          borderColor: "#374151",
        }}
      />

      <ul
        style={{
          listStyle: "none",
          padding: 0,
        }}
      >
        <li style={{ marginBottom: "15px" }}>
          <Link
            to="/"
            style={{
              color: "white",
              textDecoration: "none",
            }}
          >
            Policy Assistant
          </Link>
        </li>

        <li style={{ marginBottom: "15px" }}>
          <Link
            to="/claims"
            style={{
              color: "white",
              textDecoration: "none",
            }}
          >
            Claims
          </Link>
        </li>

        <li style={{ marginBottom: "15px" }}>
          <Link
            to="/policies"
            style={{
              color: "white",
              textDecoration: "none",
            }}
          >
            Policies
          </Link>
        </li>
      </ul>
    </div>
  );
}

export default Sidebar;