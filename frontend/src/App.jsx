import { useState, useEffect } from "react";
import axios from "axios";
import { AlertTriangle, CheckCircle, XCircle, RefreshCw, Terminal, Brain, Wrench, FileText } from "lucide-react";

const API = "http://127.0.0.1:8080";

const RiskBadge = ({ level }) => {
  const colors = {
    low: "bg-green-100 text-green-800",
    medium: "bg-yellow-100 text-yellow-800",
    high: "bg-red-100 text-red-800"
  };
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-bold uppercase ${colors[level] || colors.medium}`}>
      {level}
    </span>
  );
};

const StatusBadge = ({ approved }) => {
  if (approved === null || approved === undefined)
    return <span className="px-2 py-1 rounded-full text-xs font-bold bg-yellow-100 text-yellow-800">⏳ Awaiting Approval</span>;
  if (approved)
    return <span className="px-2 py-1 rounded-full text-xs font-bold bg-green-100 text-green-800">✅ Approved</span>;
  return <span className="px-2 py-1 rounded-full text-xs font-bold bg-red-100 text-red-800">❌ Rejected</span>;
};

export default function App() {
  const [incidents, setIncidents] = useState([]);
  const [active, setActive] = useState(null);
  const [loading, setLoading] = useState(false);
  const [triggerLoading, setTriggerLoading] = useState(false);

  const fetchIncidents = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/incidents`);
      setIncidents(res.data.incidents);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => { fetchIncidents(); }, []);

  const triggerIncident = async () => {
    setTriggerLoading(true);
    setActive(null);
    try {
      const res = await axios.post(`${API}/incidents/trigger-async`);
      setActive(res.data);
      await fetchIncidents();
    } catch (e) {
      alert("Error triggering incident: " + e.message);
    }
    setTriggerLoading(false);
  };

  const approveAction = async (incident_id, approved) => {
    try {
      await axios.post(`${API}/incidents/${incident_id}/approve`, {
        incident_id,
        approved,
        approved_by: "human_operator"
      });
      setActive(prev => prev ? { ...prev, approved } : null);
      await fetchIncidents();
    } catch (e) {
      alert("Error: " + e.message);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 font-mono">
      {/* Header */}
      <div className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-teal-400">⚡ NOC AGENT</h1>
          <p className="text-xs text-gray-500">Explainable Agentic Incident Response</p>
        </div>
        <button
          onClick={triggerIncident}
          disabled={triggerLoading}
          className="flex items-center gap-2 bg-teal-600 hover:bg-teal-500 disabled:opacity-50 px-4 py-2 rounded text-sm font-bold transition"
        >
          <RefreshCw size={14} className={triggerLoading ? "animate-spin" : ""} />
          {triggerLoading ? "Running Agent..." : "Trigger BGP Incident"}
        </button>
      </div>

      <div className="grid grid-cols-12 gap-0 h-[calc(100vh-65px)]">

        {/* Left: Audit Log */}
        <div className="col-span-3 border-r border-gray-800 overflow-y-auto">
          <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between">
            <span className="text-xs text-gray-400 uppercase tracking-wider">Audit Log</span>
            <span className="text-xs bg-gray-800 px-2 py-1 rounded">{incidents.length}</span>
          </div>
          {loading && <p className="text-xs text-gray-500 p-4">Loading...</p>}
          {incidents.map((inc) => (
            <div
              key={inc.id}
              onClick={() => setActive(inc)}
              className="px-4 py-3 border-b border-gray-800 cursor-pointer hover:bg-gray-900 transition"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold text-teal-400">{inc.incident_id}</span>
                <StatusBadge approved={inc.approved} />
              </div>
              <p className="text-xs text-gray-400 truncate">
                {inc.hypothesis?.cause || "Processing..."}
              </p>
              <p className="text-xs text-gray-600 mt-1">{inc.created_at?.slice(0, 16)}</p>
            </div>
          ))}
          {incidents.length === 0 && !loading && (
            <p className="text-xs text-gray-600 p-4 text-center">No incidents yet.<br/>Click "Trigger BGP Incident"</p>
          )}
        </div>

        {/* Right: Detail Panel */}
        <div className="col-span-9 overflow-y-auto p-6">
          {!active ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-600">
              <AlertTriangle size={48} className="mb-4 opacity-30" />
              <p className="text-sm">Trigger an incident or select one from the audit log</p>
            </div>
          ) : (
            <div className="space-y-6 max-w-4xl">

              {/* Incident Header */}
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-white">{active.incident_id}</h2>
                  <p className="text-xs text-gray-500">BGP_SESSION_DOWN · core-router-zurich-01</p>
                </div>
                <StatusBadge approved={active.approved} />
              </div>

              {/* Step 1: Observation */}
              <div className="bg-gray-900 rounded-lg border border-gray-800 p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Terminal size={16} className="text-teal-400" />
                  <span className="text-sm font-bold text-teal-400">STEP 1 — OBSERVE</span>
                </div>
                <pre className="text-xs text-gray-300 whitespace-pre-wrap leading-relaxed">
                  {active.observe_output || active.observation_summary || "Observation data not available"}
                </pre>
              </div>

              {/* Step 2: Hypothesis */}
              {active.hypothesis && (
                <div className="bg-gray-900 rounded-lg border border-gray-800 p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Brain size={16} className="text-purple-400" />
                    <span className="text-sm font-bold text-purple-400">STEP 2 — HYPOTHESIZE (Claude)</span>
                    <span className="ml-auto text-xs bg-purple-900 text-purple-300 px-2 py-1 rounded">
                      {Math.round((active.hypothesis.confidence || 0) * 100)}% confidence
                    </span>
                  </div>
                  <p className="text-sm text-white font-bold mb-3">{active.hypothesis.cause}</p>
                  <div className="space-y-1 mb-3">
                    {(active.hypothesis.evidence || []).map((e, i) => (
                      <p key={i} className="text-xs text-gray-300">• {e}</p>
                    ))}
                  </div>
                  <div className="border-t border-gray-700 pt-3">
                    <p className="text-xs text-gray-400 italic">{active.hypothesis.reasoning}</p>
                  </div>
                </div>
              )}

              {/* Step 3: Remediation */}
              {active.remediation && (
                <div className="bg-gray-900 rounded-lg border border-gray-800 p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Wrench size={16} className="text-orange-400" />
                    <span className="text-sm font-bold text-orange-400">STEP 3 — REMEDIATE (Claude)</span>
                    <span className="ml-auto">
                      <RiskBadge level={active.remediation.risk_level} />
                    </span>
                  </div>
                  <p className="text-sm text-white mb-3">{active.remediation.description}</p>

                  <div className="mb-3">
                    <p className="text-xs text-gray-500 mb-1 uppercase tracking-wider">Commands</p>
                    {(active.remediation.commands || []).map((cmd, i) => (
                      <div key={i} className="bg-gray-950 rounded px-3 py-1 text-xs text-green-400 font-mono mb-1">
                        $ {cmd}
                      </div>
                    ))}
                  </div>

                  <div>
                    <p className="text-xs text-gray-500 mb-1 uppercase tracking-wider">Rollback</p>
                    {(active.remediation.rollback_commands || []).map((cmd, i) => (
                      <div key={i} className="bg-gray-950 rounded px-3 py-1 text-xs text-red-400 font-mono mb-1">
                        $ {cmd}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Step 4: Human Approval */}
              {active.remediation?.requires_approval && (
                <div className="bg-gray-900 rounded-lg border border-yellow-800 p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <FileText size={16} className="text-yellow-400" />
                    <span className="text-sm font-bold text-yellow-400">STEP 4 — HUMAN APPROVAL REQUIRED</span>
                  </div>

                  {active.approved === null || active.approved === undefined ? (
                    <div className="flex gap-3">
                      <button
                        onClick={() => approveAction(active.incident_id, true)}
                        className="flex items-center gap-2 bg-green-700 hover:bg-green-600 px-4 py-2 rounded text-sm font-bold transition"
                      >
                        <CheckCircle size={16} /> Approve & Execute
                      </button>
                      <button
                        onClick={() => approveAction(active.incident_id, false)}
                        className="flex items-center gap-2 bg-red-800 hover:bg-red-700 px-4 py-2 rounded text-sm font-bold transition"
                      >
                        <XCircle size={16} /> Reject
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <StatusBadge approved={active.approved} />
                      <span className="text-xs text-gray-400">by human_operator</span>
                    </div>
                  )}
                </div>
              )}

            </div>
          )}
        </div>
      </div>
    </div>
  );
}