import React from "react";

export const BoschFooter = () => {
  return (
    <footer style={{ backgroundColor: "#ffffff", borderTop: "1px solid #D1D5DB", marginTop: "auto" }}>
      <div style={{ padding: "12px 30px", display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "11px", color: "#888888" }}>
        <div>© Robert Bosch GmbH {new Date().getFullYear()}</div>
        <div style={{ fontWeight: "600", color: "#4B5563" }}>DeltaProView - Standalone POC v1.0</div>
      </div>
      <div className="bosch-ribbon" />
    </footer>
  );
};
