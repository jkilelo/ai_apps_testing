
import React, { useState } from 'react';
import { profileData } from '../services/geminiService';

const DataProfiler: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<any>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleProfile = async () => {
    if (!file) return;

    setLoading(true);
    setReport(null);

    try {
      // For demonstration, we simulate reading a chunk of the file
      const reader = new FileReader();
      reader.onload = async (event) => {
        const text = event.target?.result as string;
        const sample = text.slice(0, 5000); // Send first 5k characters
        const result = await profileData(file.name, sample);
        setReport(result);
        setLoading(false);
      };
      reader.readAsText(file);
    } catch (error) {
      console.error(error);
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-8 rounded-xl border border-slate-200 shadow-sm text-center">
        <div className="max-w-md mx-auto">
          <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-4">
            <i className="fas fa-file-csv text-2xl text-blue-500"></i>
          </div>
          <h2 className="text-xl font-bold text-slate-900 mb-2">Data Profiling Engine</h2>
          <p className="text-sm text-slate-500 mb-6">Upload a CSV or JSON dataset to generate comprehensive AI insights and quality reports.</p>
          
          <label className="block">
            <input 
              type="file" 
              accept=".csv,.json"
              onChange={handleFileChange}
              className="block w-full text-sm text-slate-500 file:mr-4 file:py-2.5 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer" 
            />
          </label>

          {file && (
            <button
              onClick={handleProfile}
              disabled={loading}
              className={`mt-6 w-full py-3 rounded-xl font-bold transition-all ${
                loading 
                ? 'bg-slate-100 text-slate-400' 
                : 'bg-slate-900 text-white hover:bg-black'
              }`}
            >
              {loading ? <i className="fas fa-spinner fa-spin mr-2"></i> : null}
              {loading ? 'Analyzing Dataset...' : 'Generate Profile Report'}
            </button>
          )}
        </div>
      </div>

      {report && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-in fade-in slide-in-from-bottom-4">
          <div className="md:col-span-1 space-y-6">
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <h3 className="text-sm font-semibold uppercase tracking-widest text-slate-400 mb-4">Overview</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-slate-600">Rows</span>
                  <span className="font-mono font-bold">{report.stats.rows.toLocaleString()}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-slate-600">Columns</span>
                  <span className="font-mono font-bold">{report.stats.columns}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-slate-600">Missing Values</span>
                  <span className={`font-mono font-bold ${report.stats.missingValues > 0 ? 'text-rose-500' : 'text-emerald-500'}`}>
                    {report.stats.missingValues}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-slate-600">Duplicates</span>
                  <span className="font-mono font-bold">{report.stats.duplicateRows}</span>
                </div>
              </div>
            </div>

            <div className="bg-rose-50 border border-rose-100 p-6 rounded-xl">
              <h3 className="text-rose-900 font-semibold mb-3 flex items-center gap-2">
                <i className="fas fa-triangle-exclamation"></i>
                Anomalies
              </h3>
              <ul className="space-y-2">
                {report.anomalies.map((a: string, i: number) => (
                  <li key={i} className="text-xs text-rose-800 leading-relaxed">• {a}</li>
                ))}
              </ul>
            </div>
          </div>

          <div className="md:col-span-2">
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm h-full">
              <h3 className="text-sm font-semibold uppercase tracking-widest text-slate-400 mb-4">AI-Generated Insights</h3>
              <div className="space-y-4">
                {report.insights.map((insight: string, i: number) => (
                  <div key={i} className="flex gap-4 p-4 bg-slate-50 rounded-lg border border-slate-100">
                    <div className="shrink-0 w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center text-blue-600 font-bold text-sm">
                      {i + 1}
                    </div>
                    <p className="text-sm text-slate-700 leading-relaxed">{insight}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DataProfiler;
