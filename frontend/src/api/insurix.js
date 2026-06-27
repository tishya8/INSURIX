import axios from "axios";

const BASE_URL = "http://127.0.0.1:8000";

export const askPolicy = async (policyId, question) => {
  const response = await axios.post(
    `${BASE_URL}/chat`,
    {
      policy_id: Number(policyId),
      question: question,
    }
  );

  return response.data;
};