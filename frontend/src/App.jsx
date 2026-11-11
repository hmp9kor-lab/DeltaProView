import React, { useState, useEffect } from "react";
import axios from "axios";
import {
  GitCompareArrows,
  Download,
  RotateCcw,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  FileSpreadsheet,
  Layers,
} from "lucide-react";

import "./App.css";

const api = axios.create({
  baseURL: "/api",
});

function App() {
  // Configuration data
  const [configData, setConfigData] = useState([]);

  // Selection states
  const [selectedPS, setSelectedPS] = useState("");
  const [selectedPSL2, setSelectedPSL2] = useState("");
  const [selectedMethod, setSelectedMethod] = useState("");

  // Revision states
  const [selectedRevisions, setSelectedRevisions] = useState([]);

  // Application states
  const [loadingConfig, setLoadingConfig] = useState(true);
  const [loadingCompare, setLoadingCompare] = useState(false);

  const [error, setError] = useState("");
  const [downloadBlob, setDownloadBlob] = useState(null);

  // ----------------------------------
  // Load configuration from backend
  // ----------------------------------

  useEffect(() => {
    let mounted = true;

    const loadConfig = async () => {
      try {
        const response = await api.get("/config");

        const data = response.data;

        let configurations = [];

        if (Array.isArray(data)) {
          configurations = data;
        } else if (Array.isArray(data?.config)) {
          configurations = data.config;
        } else if (Array.isArray(data?.data)) {
          configurations = data.data;
        } else {
          throw new Error("Invalid configuration response");
        }

        if (mounted) {
          setConfigData(configurations);
        }
      } catch (err) {
        console.error("Configuration loading failed:", err);

        if (mounted) {
          setConfigData([]);
        }
      } finally {
        if (mounted) {
          setLoadingConfig(false);
        }
      }
    };

    loadConfig();

    return () => {
      mounted = false;
    };
  }, []);

  // ----------------------------------
  // Resolve cascading dropdown options
  // ----------------------------------

  const level1Options = Array.isArray(configData)
    ? configData
    : [];

  const selectedL1 = level1Options.find(
    (item) => item.name === selectedPS
  );

  const level2Options = selectedL1?.children || [];

  const selectedL2 = level2Options.find(
    (item) => item.name === selectedPSL2
  );

  const level3Options = selectedL2?.children || [];

  const selectedMethodObj = level3Options.find(
    (item) => item.name === selectedMethod
  );

  const revisions = selectedMethodObj?.revisions || [];

  // ----------------------------------
  // Handle process selection
  // ----------------------------------

  const handlePSChange = (value) => {
    setSelectedPS(value);
    setSelectedPSL2("");
    setSelectedMethod("");
    setSelectedRevisions([]);
    setDownloadBlob(null);
    setError("");
  };

  const handlePSL2Change = (value) => {
    setSelectedPSL2(value);
    setSelectedMethod("");
    setSelectedRevisions([]);
    setDownloadBlob(null);
    setError("");
  };

  const handleMethodChange = (value) => {
    setSelectedMethod(value);
    setSelectedRevisions([]);
    setDownloadBlob(null);
    setError("");
  };

  // ----------------------------------
  // Revision selection
  // ----------------------------------

  const handleToggleRevision = (revision) => {
    setError("");
    setDownloadBlob(null);

    setSelectedRevisions((previous) => {
      const alreadySelected = previous.some(
        (item) => item.id === revision.id
      );

      if (alreadySelected) {
        return previous.filter(
          (item) => item.id !== revision.id
        );
      }

      if (previous.length >= 2) {
        return [previous[1], revision];
      }

      return [...previous, revision];
    });
  };

  // ----------------------------------
  // Compare revisions
  // ----------------------------------

  const handleCompare = async () => {
    if (!selectedMethodObj || selectedRevisions.length !== 2) {
      return;
    }

    setLoadingCompare(true);
    setError("");
    setDownloadBlob(null);

    const sorted = [...selectedRevisions].sort(
      (a, b) => parseFloat(a.version) - parseFloat(b.version)
    );

    const [oldRev, newRev] = sorted;

    try {
      const response = await api.post(
        "/compare",
        {
          page_id: selectedMethodObj.pub_id,
          rev1_id: newRev.id,
          rev2_id: oldRev.id,
          method_name: selectedMethod,
          versions_text: `${newRev.version} and ${oldRev.version}`,
        },
        {
          responseType: "blob",
        }
      );

      const blob = new Blob([response.data], {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      });

      setDownloadBlob(blob);
    } catch (err) {
      console.error("Comparison failed:", err);

      setError(
        "Comparison failed. Please check the backend connection and try again."
      );
    } finally {
      setLoadingCompare(false);
    }
  };

  // ----------------------------------
  // Download Excel report
  // ----------------------------------

  const handleDownload = () => {
    if (!downloadBlob) return;

    const url = window.URL.createObjectURL(downloadBlob);

    const link = document.createElement("a");

    link.href = url;

    link.download = `DeltaProView_${selectedMethod
      .split(" ")[0]
      .replace(/[^a-zA-Z0-9_-]/g, "")}.xlsx`;

    document.body.appendChild(link);

    link.click();

    document.body.removeChild(link);

    window.URL.revokeObjectURL(url);
  };

  // ----------------------------------
  // Reset application
  // ----------------------------------

  const handleReset = () => {
    setSelectedPS("");
    setSelectedPSL2("");
    setSelectedMethod("");
    setSelectedRevisions([]);
    setDownloadBlob(null);
    setError("");
  };

  // ----------------------------------
  // UI
  // ----------------------------------

  return (
    <div className="app-container">

      {/* HEADER */}

      <header className="app-header">

        <div className="header-inner">

          <div className="brand-section">

            <div className="bosch-brand">
              BOSCH
            </div>

            <div className="brand-divider"></div>

            <div className="application-title">
              <h1>DeltaProView</h1>
              <span>Compass Version Comparer</span>
            </div>

          </div>

          <div className="header-right">
            <span className="version-label">POC v1.0</span>
          </div>

        </div>

      </header>

      {/* MAIN CONTENT */}

      <main className="main-content">

        <div className="page-heading">

          <div>
            <div className="eyebrow">PROCESS ENGINEERING</div>

            <h2>Version Comparison</h2>

            <p>
              Select a process, choose two revisions and
              generate an Excel comparison report.
            </p>
          </div>

          <button
            className="reset-button"
            onClick={handleReset}
          >
            <RotateCcw size={16} />
            Reset
          </button>

        </div>

        {/* PROCESS SELECTION */}

        <section className="content-card">

          <div className="section-heading">

            <div className="section-icon">
              <Layers size={20} />
            </div>

            <div>
              <h3>Process Selection</h3>
              <p>Select the process hierarchy</p>
            </div>

          </div>

          <div className="selection-grid">

            {/* LEVEL 1 */}

            <div className="form-group">

              <label>PS Process Landscape</label>

              <select
                value={selectedPS}
                onChange={(e) => handlePSChange(e.target.value)}
                disabled={loadingConfig || level1Options.length === 0}
              >

                <option value="">
                  {loadingConfig
                    ? "Loading..."
                    : "-- Select Process Landscape --"}
                </option>

                {level1Options.map((item) => (
                  <option key={item.pub_id} value={item.name}>
                    {item.name}
                  </option>
                ))}

              </select>

            </div>

            {/* LEVEL 2 */}

            <div className="form-group">

              <label>PS Processes</label>

              <select
                value={selectedPSL2}
                onChange={(e) => handlePSL2Change(e.target.value)}
                disabled={!selectedPS}
              >

                <option value="">-- Select Process --</option>

                {level2Options.map((item) => (
                  <option key={item.pub_id} value={item.name}>
                    {item.name}
                  </option>
                ))}

              </select>

            </div>

            {/* LEVEL 3 */}

            <div className="form-group">

              <label>PS Methods</label>

              <select
                value={selectedMethod}
                onChange={(e) => handleMethodChange(e.target.value)}
                disabled={!selectedPSL2}
              >

                <option value="">-- Select Method --</option>

                {level3Options.map((item) => (
                  <option key={item.pub_id} value={item.name}>
                    {item.name}
                  </option>
                ))}

              </select>

            </div>

          </div>

          {!loadingConfig && level1Options.length === 0 && (
            <div className="connection-notice">
              <AlertCircle size={17} />

              <span>
                Backend not connected. Process options will
                appear here once the backend is available.
              </span>
            </div>
          )}

        </section>

        {/* REVISION SELECTION */}

        {selectedMethod && (

          <section className="content-card">

            <div className="section-heading">

              <div className="section-icon red-icon">
                <FileSpreadsheet size={20} />
              </div>

              <div>
                <h3>Select Revisions</h3>
                <p>
                  Choose exactly two versions to compare.
                </p>
              </div>

              <div className="selection-count">
                {selectedRevisions.length} / 2 Selected
              </div>

            </div>

            {revisions.length > 0 ? (

              <div className="revision-list">

                {revisions.map((revision) => {

                  const checked = selectedRevisions.some(
                    (item) => item.id === revision.id
                  );

                  return (

                    <label
                      key={revision.id}
                      className={`revision-item ${
                        checked ? "revision-selected" : ""
                      }`}
                    >

                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => handleToggleRevision(revision)}
                      />

                      <span className="revision-name">
                        Version {revision.version}
                      </span>

                      <span className="revision-id">
                        ID: {revision.id}
                      </span>

                    </label>

                  );
                })}

              </div>

            ) : (

              <div className="empty-state">
                No revisions are available for this method.
              </div>

            )}

            {/* ACTION BUTTONS */}

            {revisions.length > 0 && (

              <div className="action-area">

                <div className="action-info">

                  {selectedRevisions.length === 2
                    ? "Two revisions selected. Ready to compare."
                    : "Select two revisions to continue."}

                </div>

                <div className="action-buttons">

                  <button
                    className="compare-button"
                    onClick={handleCompare}
                    disabled={
                      selectedRevisions.length !== 2 ||
                      loadingCompare
                    }
                  >

                    {loadingCompare ? (
                      <RefreshCw size={17} className="spin" />
                    ) : (
                      <GitCompareArrows size={17} />
                    )}

                    {loadingCompare
                      ? "Comparing..."
                      : "Compare Revisions"}

                  </button>

                  {downloadBlob && (

                    <button
                      className="download-button"
                      onClick={handleDownload}
                    >

                      <Download size={17} />
                      Download Excel

                    </button>

                  )}

                </div>

              </div>

            )}

            {/* ERROR MESSAGE */}

            {error && (

              <div className="error-message">

                <AlertCircle size={18} />

                <span>{error}</span>

              </div>

            )}

            {/* SUCCESS MESSAGE */}

            {downloadBlob && (

              <div className="success-message">

                <CheckCircle2 size={18} />

                <span>
                  Comparison completed successfully.
                  Your Excel report is ready.
                </span>

              </div>

            )}

          </section>

        )}

      </main>

      {/* FOOTER */}

      <footer className="app-footer">

        <div className="footer-inner">

          <span>
            © Robert Bosch GmbH {new Date().getFullYear()}
          </span>

          <span>
            DeltaProView | Compass Version Comparer
          </span>

        </div>

      </footer>

    </div>
  );
}

export default App;