
import React, { useState } from 'react';
import { checkDataQuality } from '../services/geminiService';

const QualityChecker: React.FC = () => {
  const [data, setData] = useState('');
  const [rules, setRules] = useState('1. Email must be valid\n2. Date cannot be in the future\n3. Value must be positive');
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<any>(null);

  const handleCheck = async () => {
    if (!data.trim()) return;
    setLoading(true);
    setReport(null);

    try {
      const result = await checkDataQuality(data, rules);
      setReport(result);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h3 className="text-sm font-semibold text-slate-400 uppercase mb-3">Input Data Snippet</h3>
            <textarea
              value={data}
              onChange={(e) => setData(e.target.value)}
              placeholder="Paste CSV rows or JSON objects here..."
              className="w-full h-48 p-4 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono focus:ring-2 focus:ring-indigo-500 transition-all outline-none"
            />
          </div>
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h3 className="text-sm font-semibold text-slate-400 uppercase mb-3">Validation Rules</h3>
            <textarea
              value={rules}
              onChange={(e) => setRules(e.target.value)}
              placeholder="Define validation rules..."
              className="w-full h-32 p-4 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 transition-all outline-none"
            />
          </div>
          <button
            onClick={handleCheck}
            disabled={loading || !data}
            className={`w-full py-4 rounded-xl font-bold shadow-lg transition-all ${
              loading || !data 
              ? 'bg-slate-100 text-slate-400' 
              : 'bg-indigo-600 text-white hover:bg-indigo-700 active:scale-[0.98]'
            }`}
          >
            {loading ? <i className="fas fa-spinner fa-spin mr-2"></i> : <i className="fas fa-shield-check mr-2"></i>}
            Run Quality Audit
          </button>
        </div>

        <div className="space-y-6">
          {report ? (
            <>
              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                <h3 className="text-sm font-semibold text-slate-400 uppercase mb-6">Quality Score</h3>
                <div className="flex items-center gap-8">
                  <div className="relative w-24 h-24">
                    <svg className="w-full h-full" viewBox="0 0 36 36">
                      <path
                        className="text-slate-100"
                        strokeDasharray="100, 100"
                        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="3"
                      />
                      <path
                        className={report.score > 80 ? 'text-emerald-500' : report.score > 50 ? 'text-amber-500' : 'text-rose-500'}
                        strokeDasharray={`${report.score}, 100`}
                        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="3"
                        strokeLinecap="round"
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center font-bold text-xl">
                      {report.score}%
                    </div>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-900">Overall Data Integrity</p>
                    <p className="text-xs text-slate-500">Based on {report.violations.length} checked criteria.</p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm min-h-[300px]">
                <h3 className="text-sm font-semibold text-slate-400 uppercase mb-4">Rule Violations</h3>
                <div className="space-y-3">
                  {report.violations.length === 0 ? (
                    <div className="py-12 text-center text-slate-400 italic">No violations found!</div>
                  ) : (
                    report.violations.map((v: any, i: number) => (
                      <div key={i} className="flex items-start gap-4 p-4 rounded-lg border border-slate-100 bg-slate-50/50">
                        <div className={`mt-1 shrink-0 w-2 h-2 rounded-full ${
                          v.severity === 'high' ? 'bg-rose-500' : v.severity === 'medium' ? 'bg-amber-500' : 'bg-blue-500'
                        }`}></div>
                        <div>
                          <p className="text-xs font-bold text-slate-500 uppercase tracking-tighter mb-1">{v.rule}</p>
                          <p className="text-sm text-slate-800">{v.issue}</p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="bg-slate-50 border-2 border-dashed border-slate-200 rounded-xl flex items-center justify-center h-full min-h-[400px]">
              <div className="text-center p-8">
                <i className="fas fa-file-shield text-4xl text-slate-200 mb-4"></i>
                <p className="text-slate-400 text-sm">Results will appear here after audit</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default QualityChecker;
