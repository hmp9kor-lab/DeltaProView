import React from "react";

export const BoschHeader = () => {
  return (
    <header style={{ backgroundColor: "#ffffff", borderBottom: "1px solid #D1D5DB" }}>
      {/* Bosch Ribbon */}
      <div className="bosch-ribbon" />
      <div style={{ padding: "15px 30px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          {/* Dynamic reference: Put your Bosch logo inside frontend/public/Bosch_logo.png */}
          <img 
            src="/Bosch_logo.png" 
            alt="Bosch" 
            style={{ height: "30px", width: "auto", display: "block" }} 
            onError={(e) => { e.target.style.display = 'none'; }} // Gracefully hides if file is missing
          />
          <span style={{ fontSize: "22px", fontWeight: "bold", color: "#1F2937", letterSpacing: "-0.5px" }}>
            DeltaProView
          </span>
          <span style={{ color: "#D1D5DB", fontSize: "18px" }}>|</span>
          <span style={{ color: "#4B5563", fontSize: "13px", fontWeight: "600" }}>
            Compass Version Comparer
          </span>
        </div>
      </div>
    </header>
  );
};
