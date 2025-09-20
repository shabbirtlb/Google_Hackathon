import React, { useState, useEffect } from "react";

export default function SavedAnalysisPage({ onBack }) {
  const [saved, setSaved] = useState([]);

  useEffect(() => {
    const data = JSON.parse(localStorage.getItem("savedAnalyses") || "[]");
    setSaved(data);
  }, []);

  const clearAll = () => {
    localStorage.removeItem("savedAnalyses");
    setSaved([]);
  };

  return (
    <div className="fixed inset-0 bg-gray-50 overflow-y-auto p-6 z-40">
      <div className="flex justify-between items-center mb-6">
        <button
          onClick={onBack}
          className="px-4 py-2 rounded-xl border hover:bg-gray-100"
        >
          ← Back
        </button>
        <button
          onClick={clearAll}
          className="px-4 py-2 rounded-xl bg-red-600 text-white hover:bg-red-700"
        >
          🗑 Clear All
        </button>
      </div>

      <h2 className="text-2xl font-bold mb-6">💾 Saved Analyses</h2>

      {saved.length === 0 ? (
        <p>No saved analyses yet.</p>
      ) : (
        <ul className="space-y-4">
          {saved.map((item) => (
            <li key={item.id} className="bg-white p-4 rounded-xl shadow">
              <p className="text-sm text-gray-500 mb-2">
                Saved on {new Date(item.timestamp).toLocaleString()}
              </p>
              <p className="font-semibold">
                {item.result?.company_overview?.description?.slice(0, 80)}...
              </p>
              <p className="text-xs text-gray-600">
                Rating: {item.result?.investment_recommendation?.rating} (
                {item.result?.investment_recommendation?.score}/100)
              </p>
              <details className="mt-2">
                <summary className="cursor-pointer text-blue-600">
                  View full JSON
                </summary>
                <pre className="text-xs bg-gray-100 p-2 mt-2 rounded overflow-x-auto">
                  {JSON.stringify(item, null, 2)}
                </pre>
              </details>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
