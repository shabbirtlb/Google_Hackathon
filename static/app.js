import React, { useState, useEffect } from "react";
import AnalysisPage from "./AnalysisPage";
import SavedAnalysisPage from "./SavedAnalysisPage";
import "./App.css"; // Your styles here


// --- Weights Config Modal ---
const WeightsConfigModal = ({ currentWeights, onClose, onSave }) => {
  const [weights, setWeights] = useState(currentWeights || {});

  const handleChange = (field, value) => {
    setWeights({ ...weights, [field]: parseInt(value, 10) || 0 });
  };

  const saveWeights = async () => {
    await fetch("/weights", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(weights),
    });
    alert("Weights updated!");
    onSave(weights);
    onClose();
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h3>Adjust Report Weights</h3>
        {["financial", "growth", "market", "risk"].map((field) => (
          <div key={field}>
            <label>{field}</label>
            <input
              type="number"
              value={weights[field]}
              onChange={(e) => handleChange(field, e.target.value)}
            />
          </div>
        ))}
        <div className="modal-actions">
          <button onClick={onClose}>Cancel</button>
          <button onClick={saveWeights}>Save</button>
        </div>
      </div>
    </div>
  );
};

// Filter Component
const Filters = ({ filters, setFilters, onApply }) => {
  return (
    <div className="filters">
      <input
        type="text"
        placeholder="Search by company name"
        value={filters.query}
        onChange={(e) => setFilters({ ...filters, query: e.target.value })}
      />
      <input
        type="number"
        placeholder="Min team size"
        value={filters.teamMin}
        onChange={(e) => setFilters({ ...filters, teamMin: e.target.value })}
      />
      <input
        type="number"
        placeholder="Max team size"
        value={filters.teamMax}
        onChange={(e) => setFilters({ ...filters, teamMax: e.target.value })}
      />
      <button onClick={onApply}>Apply Filters</button>
    </div>
  );
};

// Company Card Component
const CompanyCard = ({ company, onAnalyze }) => {
  const { name, logo, description } = company;
  return (
    <div className="company-card">
      <img src={logo || "/default-logo.png"} alt={name} />
      <h3>{name}</h3>
      <p>{description}</p>
      <button onClick={() => onAnalyze(company)}>Analyze</button>
    </div>
  );
};

// Analyze Modal Component
const AnalyzePanel = ({ company, onClose, analysisResult }) => {
  if (!company) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <button className="close-btn" onClick={onClose}>
          &times;
        </button>
        <h2>Analysis: {company.name}</h2>
        {analysisResult ? (
          <div className="scrollable-results">
            <pre>{JSON.stringify(analysisResult, null, 2)}</pre>
          </div>
        ) : (
          <p>Loading analysis...</p>
        )}
      </div>
    </div>
  );
};

// Main App
const App = () => {
  const [dataset, setDataset] = useState([]);
  const [filters, setFilters] = useState({
    query: "",
    teamMin: "",
    teamMax: "",
  });
  const [filteredData, setFilteredData] = useState([]);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [view, setView] = useState("home"); // home, analysis, saved

  useEffect(() => {
    // Load dataset (could be from API or JSON)
    fetch("/data/companies.json")
      .then((res) => res.json())
      .then((data) => {
        setDataset(data);
        setFilteredData(data);
      });
  }, []);

  const applyFilters = () => {
    let data = [...dataset];
    if (filters.query) {
      data = data.filter((c) =>
        c.name.toLowerCase().includes(filters.query.toLowerCase())
      );
    }
    if (filters.teamMin) {
      data = data.filter((c) => c.teamSize >= parseInt(filters.teamMin));
    }
    if (filters.teamMax) {
      data = data.filter((c) => c.teamSize <= parseInt(filters.teamMax));
    }
    setFilteredData(data);
  };

  const handleAnalyze = (company) => {
    setSelectedCompany(company);
    setAnalysisResult(null);
    // Simulate fetch analysis
    setTimeout(() => {
      // Replace with actual API call
      setAnalysisResult({
        overview: company.description,
        financials: { revenue: "N/A", growth: "N/A" },
      });
    }, 1000);
  };

  const closeModal = () => setSelectedCompany(null);

  return (
<div className="app">
      <header>
        <h1>Company Analyzer</h1>
        <nav>
          <button onClick={() => setView("home")}>Home</button>
          <button onClick={() => setView("analysis")}>Analysis</button>
          <button onClick={() => setView("saved")}>Saved Analysis</button>
          <button onClick={() => setShowWeightsModal(true)}>Adjust Weights</button>
        </nav>
      </header>

      {view === "home" && (
        <>
          {/* filters */}
          <div className="company-grid">
            {filteredData.map((company) => (
              <div key={company.id} className="company-card">
                <h3>{company.name}</h3>
                <p>{company.description}</p>
                <button onClick={() => handleAnalyze(company)}>Analyze</button>
              </div>
            ))}
          </div>
        </>
      )}

      {view === "analysis" && <AnalysisPage />}
      {view === "saved" && <SavedAnalysisPage />}

      {selectedCompany && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h2>Analysis: {selectedCompany.name}</h2>
            {analysisResult ? (
              <pre>{JSON.stringify(analysisResult, null, 2)}</pre>
            ) : (
              <p>Loading analysis...</p>
            )}
            <button onClick={closeModal}>Close</button>
          </div>
        </div>
      )}

      {showWeightsModal && (
        <WeightsConfigModal
          currentWeights={weights}
          onClose={() => setShowWeightsModal(false)}
          onSave={setWeights}
        />
      )}
    </div>
  );
};

export default App;
