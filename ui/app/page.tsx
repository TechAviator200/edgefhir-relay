"use client";

import { useEffect, useState, useCallback } from "react";
import { JsonView, darkStyles } from "react-json-view-lite";
import "react-json-view-lite/dist/index.css";

const API = "/api";

interface Status {
  phase: string;
  connectivity_on: boolean;
  outbox_count: number;
  last_decision: Record<string, unknown> | null;
  last_fhir_bundle: Record<string, unknown> | null;
  last_updated: number | null;
}

export default function Dashboard() {
  const [status, setStatus] = useState<Status | null>(null);
  const [history, setHistory] = useState<Record<string, unknown>[]>([]);
  const [mode, setMode] = useState("normal");
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"summary" | "structured">("summary");

  const poll = useCallback(async () => {
    try {
      const [sRes, hRes, mRes] = await Promise.all([
        fetch(`${API}/status`),
        fetch(`${API}/history`),
        fetch(`${API}/mode`),
      ]);
      if (sRes.ok) setStatus(await sRes.json());
      if (hRes.ok) {
        const h = await hRes.json();
        setHistory(h.series ?? []);
      }
      if (mRes.ok) {
        const m = await mRes.json();
        setMode(m.mode ?? "normal");
      }
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Fetch failed");
    }
  }, []);

  useEffect(() => {
    poll();
    const id = setInterval(poll, 2000);
    return () => clearInterval(id);
  }, [poll]);

  const post = async (path: string) => {
    try {
      await fetch(`${API}${path}`, { method: "POST" });
      await poll();
    } catch {}
  };

  const latestVitals = history.length > 0 ? history[history.length - 1] : null;

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-bold">EdgeFHIR Relay Dashboard</h1>

      {error && (
        <div className="bg-red-900/50 border border-red-700 rounded p-3 text-sm">
          {error}
        </div>
      )}

      {/* Status Cards */}
      <div className="grid grid-cols-4 gap-4">
        <Card label="Phase" value={status?.phase ?? "—"} />
        <Card
          label="Connectivity"
          value={status?.connectivity_on ? "ONLINE" : "OFFLINE"}
          color={status?.connectivity_on ? "text-green-400" : "text-red-400"}
        />
        <Card label="Outbox" value={String(status?.outbox_count ?? 0)} />
        <Card label="Mode" value={mode} />
      </div>

      {/* Controls */}
      <div className="flex flex-wrap gap-2">
        <Btn onClick={() => post("/connectivity/on")} label="Connectivity ON" />
        <Btn onClick={() => post("/connectivity/off")} label="Connectivity OFF" />
        <Btn onClick={() => post("/flush")} label="Flush Outbox" />
        <span className="w-px bg-gray-700" />
        <Btn onClick={() => post("/simulate/normal")} label="Normal" />
        <Btn onClick={() => post("/simulate/desat")} label="Desat" />
        <Btn onClick={() => post("/simulate/fever")} label="Fever" />
        <Btn onClick={() => post("/simulate/tachy")} label="Tachy" />
      </div>

      {/* Latest Vitals */}
      <Section title="Latest Vitals">
        {latestVitals ? (
          <div className="grid grid-cols-5 gap-3">
            <Metric label="HR" value={latestVitals.hr} unit="bpm" />
            <Metric label="SpO2" value={latestVitals.spo2} unit="%" />
            <Metric label="Temp" value={latestVitals.temp_c} unit="°C" />
            <Metric label="RR" value={latestVitals.rr} unit="/min" />
            <Metric label="Motion" value={latestVitals.motion ?? "—"} unit="" />
          </div>
        ) : (
          <p className="text-gray-500 text-sm">No vitals yet</p>
        )}
      </Section>

      {/* View Toggle */}
      <div className="flex gap-1">
        <button
          onClick={() => setViewMode("summary")}
          className={`px-3 py-1.5 rounded text-sm transition-colors ${
            viewMode === "summary"
              ? "bg-blue-600 text-white"
              : "bg-gray-700 text-gray-300 hover:bg-gray-600"
          }`}
        >
          Summary
        </button>
        <button
          onClick={() => setViewMode("structured")}
          className={`px-3 py-1.5 rounded text-sm transition-colors ${
            viewMode === "structured"
              ? "bg-blue-600 text-white"
              : "bg-gray-700 text-gray-300 hover:bg-gray-600"
          }`}
        >
          Structured (JSON)
        </button>
      </div>

      {/* Decision */}
      <Section title="Last Decision">
        {viewMode === "structured" ? (
          status?.last_decision ? (
            <pre className="bg-gray-900 rounded p-3 text-sm overflow-auto max-h-48">
              {JSON.stringify(status.last_decision, null, 2)}
            </pre>
          ) : (
            <p className="text-gray-500 text-sm">No decision yet</p>
          )
        ) : (
          <DecisionSummary decision={status?.last_decision ?? null} />
        )}
      </Section>

      {/* FHIR Bundle */}
      <Section title="Last FHIR Bundle">
        {viewMode === "structured" ? (
          status?.last_fhir_bundle ? (
            <div className="bg-gray-900 rounded p-3 overflow-auto max-h-96 text-sm">
              <JsonView
                data={status.last_fhir_bundle}
                style={darkStyles}
                shouldExpandNode={(level) => level < 2}
              />
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No bundle yet</p>
          )
        ) : (
          <BundleSummary bundle={status?.last_fhir_bundle ?? null} />
        )}
      </Section>
    </div>
  );
}

function Card({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="text-xs text-gray-400 uppercase tracking-wide">{label}</div>
      <div className={`text-lg font-mono font-semibold mt-1 ${color ?? "text-white"}`}>
        {value}
      </div>
    </div>
  );
}

function Btn({ onClick, label }: { onClick: () => void; label: string }) {
  return (
    <button
      onClick={onClick}
      className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded text-sm transition-colors"
    >
      {label}
    </button>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-2">
        {title}
      </h2>
      {children}
    </div>
  );
}

function Metric({ label, value, unit }: { label: string; value: unknown; unit: string }) {
  return (
    <div className="bg-gray-800 rounded p-3 text-center">
      <div className="text-xs text-gray-400">{label}</div>
      <div className="text-lg font-mono">
        {String(value)} <span className="text-xs text-gray-500">{unit}</span>
      </div>
    </div>
  );
}

function DecisionSummary({ decision }: { decision: Record<string, unknown> | null }) {
  if (!decision) return <p className="text-gray-500 text-sm">No decision yet</p>;

  const triage = String(decision.triage ?? "—");
  const nextAction = String(decision.next_action ?? "—");
  const confidence = typeof decision.confidence === "number" ? decision.confidence : 0;
  const reasons = Array.isArray(decision.reasons) ? decision.reasons : [];

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-3 gap-3">
        <Card label="Triage" value={triage} />
        <Card label="Next Action" value={nextAction} />
        <Card label="Confidence" value={`${Math.round(confidence * 100)}%`} />
      </div>
      {reasons.length > 0 && (
        <ul className="list-disc list-inside text-sm text-gray-300 bg-gray-900 rounded p-3 space-y-1">
          {reasons.map((r, i) => (
            <li key={i}>{String(r)}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function BundleSummary({ bundle }: { bundle: Record<string, unknown> | null }) {
  if (!bundle) return <p className="text-gray-500 text-sm">No bundle yet</p>;

  const bundleType = String(bundle.type ?? "—");
  const timestamp = String(bundle.timestamp ?? "—");
  const entries = Array.isArray(bundle.entry) ? bundle.entry : [];

  const typeCounts: Record<string, number> = {};
  for (const entry of entries) {
    const res = (entry as Record<string, unknown>)?.resource as Record<string, unknown> | undefined;
    const rt = String(res?.resourceType ?? "Unknown");
    typeCounts[rt] = (typeCounts[rt] ?? 0) + 1;
  }

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-3 gap-3">
        <Card label="Bundle Type" value={bundleType} />
        <Card label="Entries" value={String(entries.length)} />
        <Card label="Timestamp" value={timestamp.split("T")[0] ?? timestamp} />
      </div>
      {Object.keys(typeCounts).length > 0 && (
        <div className="bg-gray-900 rounded p-3 text-sm">
          <div className="text-xs text-gray-400 uppercase tracking-wide mb-2">Resources</div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(typeCounts).map(([type, count]) => (
              <span key={type} className="bg-gray-800 rounded px-2 py-1 font-mono">
                {type} <span className="text-gray-400">x{count}</span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
