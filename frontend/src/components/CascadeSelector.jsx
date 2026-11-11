import React from "react";

export const CascadeSelector = ({ methods, selectedMethod, onSelectMethod }) => {
  return (
    <div className="card">
      <div className="card-title-container">
        <div className="indicator blue" />
        <h3>1. Select Process Method</h3>
      </div>
      <div style={{ marginTop: "15px" }}>
        <label style={{ display: "block", fontSize: "12px", fontWeight: "bold", color: "#9CA3AF", textTransform: "uppercase", marginBottom: "8px" }}>
          PS Method
        </label>
        <select
          value={selectedMethod}
          onChange={(e) => onSelectMethod(e.target.value)}
          className="select-box"
        >
          <option value="">-- Select a Method --</option>
          {methods.map((m) => (
            <option key={m.pub_id} value={m.name}>
              {m.name}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
};
