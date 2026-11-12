import axios from "axios";

// Relative base URL: Vite's dev proxy forwards /api/* to the FastAPI backend (127.0.0.1:8000)
const api = axios.create({
  baseURL: "/api",
  timeout: 120000, // Confluence fetches + Excel generation can be slow
});

// Pull a readable message out of any axios error, including blob error bodies
const extractErrorMessage = async (err) => {
  const data = err?.response?.data;

  if (data instanceof Blob) {
    const text = await data.text();
    try {
      return JSON.parse(text).detail || text;
    } catch {
      return text;
    }
  }

  if (data?.detail) {
    return typeof data.detail === "string"
      ? data.detail
      : JSON.stringify(data.detail);
  }

  if (err?.code === "ECONNABORTED") {
    return "The request timed out. Please try again.";
  }

  if (!err?.response) {
    return "Cannot reach the backend. Make sure it is running on port 8000.";
  }

  return err.message || "Unexpected error";
};

export const fetchConfig = async () => {
  try {
    const response = await api.get("/config");
    return response.data;
  } catch (err) {
    throw new Error(await extractErrorMessage(err));
  }
};

export const runComparison = async (
  pageId,
  rev1Id,
  rev2Id,
  methodName,
  versionsText
) => {
  try {
    const response = await api.post(
      "/compare",
      {
        page_id: pageId,
        rev1_id: rev1Id,
        rev2_id: rev2Id,
        method_name: methodName,
        versions_text: versionsText,
      },
      { responseType: "blob" }
    );
    return response.data; // Blob (.xlsx)
  } catch (err) {
    throw new Error(await extractErrorMessage(err));
  }
};

export default api;