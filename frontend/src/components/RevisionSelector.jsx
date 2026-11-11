import React from "react";

export const RevisionSelector = ({ revisions, selected, onToggle }) => {
  if (revisions.length === 0) return null;

  return (
    <div className="card">
      <div className="card-title-container">
        <div className="indicator red" />
        <h3>2. Select Exactly 2 Revisions</h3>
      </div>
      <div className="revision-list">
        {revisions.map((rev) => {
          const isSelected = selected.some((s) => s.id === rev.id);
          return (
            <div
              key={rev.id}
              onClick={() => onToggle(rev)}
              className={`revision-item ${isSelected ? "selected" : ""}`}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <input
                  type="checkbox"
                  checked={isSelected}
                  readOnly
                  style={{ accentColor: "#007A99", cursor: "pointer" }}
                />
                <span style={{ fontSize: "14px", fontWeight: "600" }}>Version {rev.version}</span>
              </div>
              <span style={{ fontSize: "12px", color: "#9CA3AF", fontFamily: "monospace" }}>Page ID: {rev.id}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
