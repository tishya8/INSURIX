import { createContext, useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";

export const PolicyContext = createContext();

export function PolicyProvider({ children }) {
  const { user } = useAuth();

  const [policies,        setPolicies]   = useState([]);
  const [policyId,        setPolicyId]   = useState(null);
  const [loadingPolicies, setLoading]    = useState(true);
  const [policiesError,   setError]      = useState("");

  useEffect(() => {
    if (!user?.user_id) return;

    setLoading(true);
    setError("");

    fetch(`http://localhost:8000/users/${user.user_id}/policies`)
      .then(res => {
        if (!res.ok) throw new Error("Failed to load policies");
        return res.json();
      })
      .then(data => {
        setPolicies(data);
        const first = data.find(p => p.status === "ACTIVE") || data[0];
        if (first) setPolicyId(String(first.policy_id));
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [user?.user_id]);

  const selectedPolicy = policies.find(p => String(p.policy_id) === policyId) || null;

  return (
    <PolicyContext.Provider value={{
      policies,
      policyId,
      setPolicyId,
      selectedPolicy,
      loadingPolicies,
      policiesError,
    }}>
      {children}
    </PolicyContext.Provider>
  );
}


// import {
//   createContext,
//   useState
// } from "react";

// export const PolicyContext =
//   createContext();

// export function PolicyProvider({
//   children
// }) {

//   const [policyId,
//     setPolicyId] =
//       useState("1");

//   return (
//     <PolicyContext.Provider
//       value={{
//         policyId,
//         setPolicyId
//       }}
//     >
//       {children}
//     </PolicyContext.Provider>
//   );
// }