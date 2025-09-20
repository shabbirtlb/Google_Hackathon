import React from "react";

export default function AnalysisPage({ result, comparative, onClose, onSave }) {
  if (!result) return null;

  const handleSave = () => {
    const entry = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      result,
      comparative,
    };
    onSave(entry);
    alert("✅ Analysis saved!");
  };

  return (
    <div className="fixed inset-0 bg-gray-50 overflow-y-auto p-6 z-40">
      <div className="flex justify-between items-center mb-6">
        <button
          onClick={onClose}
          className="px-4 py-2 rounded-xl border hover:bg-gray-100"
        >
          ← Back
        </button>
        <button
          onClick={handleSave}
          className="px-4 py-2 rounded-xl bg-green-600 text-white hover:bg-green-700"
        >
          💾 Save Analysis
        </button>
      </div>

      <h2 className="text-3xl font-bold mb-6">📊 Full Investment Analysis</h2>

      {/* Company Overview */}
      <section className="mb-8">
        <h3 className="text-xl font-semibold mb-2">🏢 Company Overview</h3>
        <p className="mb-1">{result.company_overview?.description}</p>
        <p><span className="font-medium">Status:</span> {result.company_overview?.status}</p>
        {result.company_overview?.acquisition && (
          <p>
            <span className="font-medium">Acquired by:</span>{" "}
            {result.company_overview.acquisition.buyer} for{" "}
            {result.company_overview.acquisition.price} on{" "}
            {result.company_overview.acquisition.date}
          </p>
        )}
      </section>

      {/* Financial Analysis */}
      <section className="mb-8">
        <h3 className="text-xl font-semibold mb-2">💰 Financial Analysis</h3>
        <ul className="list-disc pl-6 space-y-1">
          <li>Total Funding: ${result.financial_analysis?.total_funding}</li>
          <li>Revenue Estimate: ${result.financial_analysis?.revenue_estimate}</li>
          <li>Funding Efficiency: {result.financial_analysis?.funding_efficiency?.toFixed(2)}x</li>
          <li>Revenue Multiple: {result.financial_analysis?.revenue_multiple}x</li>
          <li>Value per Employee: ${result.financial_analysis?.value_per_employee}</li>
        </ul>
      </section>

      {/* Growth Indicators */}
      <section className="mb-8">
        <h3 className="text-xl font-semibold mb-2">📈 Growth Indicators</h3>
        <p>Growth Score: {result.growth_indicators?.growth_score}/100</p>
        <p>
          Employees: {result.growth_indicators?.team_growth_indicators?.employee_count} |{" "}
          Customers: {result.growth_indicators?.customer_acquisition_metrics?.total_customers}
        </p>
      </section>

      {/* Sector Benchmarks */}
      <section className="mb-8">
        <h3 className="text-xl font-semibold mb-2">📊 Sector Benchmarks</h3>
        {result.sector_benchmarks?.company_vs_sector && (
          <ul className="list-disc pl-6 space-y-1">
            <li>
              Revenue Multiple: Company {result.sector_benchmarks.company_vs_sector.revenue_multiple.company}x 
              vs Sector {result.sector_benchmarks.company_vs_sector.revenue_multiple.sector_median}x → 
              {result.sector_benchmarks.company_vs_sector.revenue_multiple.assessment}
            </li>
            <li>
              Funding Efficiency: Company {result.sector_benchmarks.company_vs_sector.funding_efficiency.company}x 
              vs Sector {result.sector_benchmarks.company_vs_sector.funding_efficiency.sector_median}x → 
              {result.sector_benchmarks.company_vs_sector.funding_efficiency.assessment}
            </li>
          </ul>
        )}
      </section>

      {/* Investment Recommendation */}
      <section className="mb-8">
        <h3 className="text-xl font-semibold mb-2">💡 Investment Recommendation</h3>
        <p className="font-medium">
          Rating: {result.investment_recommendation?.rating} ({result.investment_recommendation?.score}/100)
        </p>
        <p className="mt-2 whitespace-pre-line">
          {result.investment_recommendation?.reasoning}
        </p>
      </section>

      {/* Comparative Analysis */}
      {comparative && (
        <section className="mb-8">
          <h3 className="text-xl font-semibold mb-2">🔍 Comparative Analysis</h3>
          {["inconsistencies","red_flags","pros"].map((key) => (
            <div className="mb-4" key={key}>
              <h4 className="font-medium">{key.charAt(0).toUpperCase() + key.slice(1)}</h4>
              <ul className={`list-disc pl-6 ${key === "inconsistencies" ? "text-red-600" : key === "red_flags" ? "text-orange-600" : "text-green-600"}`}>
                {comparative[key].map((item, idx) => <li key={idx}>{item}</li>)}
              </ul>
            </div>
          ))}
          <p className="mt-3 font-medium">{comparative.investor_takeaway}</p>
        </section>
      )}
    </div>
  );
}