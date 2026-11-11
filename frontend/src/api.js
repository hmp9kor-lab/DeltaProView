import axios from "axios";

const api = axios.create({
  baseURL: "/api",
});

export const fetchConfig = async () => {
  const response = await api.get("/config");
  return response.data;
};

export const runComparison = async (pageId, rev1Id, rev2Id, methodName, versionsText) => {
  const response = await api.post("/compare", {
    page_id: pageId,
    rev1_id: rev1Id,
    rev2_id: rev2Id,
    method_name: methodName,
    versions_text: versionsText,
  }, {
    responseType: "blob", 
  });
  return response.data;
};
