const BASE = "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

export const askPolicy = (policyId, question) =>
  request("/chat", {
    method: "POST",
    body: JSON.stringify({ policy_id: Number(policyId), question }),
  });

export const getUserPolicies = (userId) =>
  request(`/users/${userId}/policies`);

export const createClaim = (policyId, incidentType, description) =>
  request("/claims", {
    method: "POST",
    body: JSON.stringify({
      policy_id:     Number(policyId),
      incident_type: incidentType,
      description,
    }),
  });

export const getClaimStatus = (claimId) =>
  request(`/claims/${claimId}`);


// import axios from "axios";

// const BASE_URL = "http://127.0.0.1:8000";

// export const askPolicy = async (policyId, question) => {
//   const response = await axios.post(
//     `${BASE_URL}/chat`,
//     {
//       policy_id: Number(policyId),
//       question: question,
//     }
//   );

//   return response.data;
// };