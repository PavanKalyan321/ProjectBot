"use client";

import React, { useState, useRef } from "react";
import {
  startContinuousDOMScan,
  generateScanReport,
  getMostReliableMultiplier,
  exportScanResults,
  type ScanResult,
} from "@/lib/iframe-dom-scanner";

interface IframeDOMScannerProps {
  iframeRef: React.RefObject<HTMLIFrameElement>;
  onScanComplete?: (results: ScanResult[], report: string) => void;
}

export default function IframeDOMScanner({
  iframeRef,
  onScanComplete,
}: IframeDOMScannerProps) {
  const [isScanning, setIsScanning] = useState(false);
  const [scanResults, setScanResults] = useState<ScanResult[]>([]);
  const [report, setReport] = useState("");
  const [liveUpdates, setLiveUpdates] = useState<ScanResult | null>(null);
  const updateCountRef = useRef(0);

  const handleStartScan = async () => {
    setIsScanning(true);
    setScanResults([]);
    setReport("");
    setLiveUpdates(null);
    updateCountRef.current = 0;

    try {
      const results = await startContinuousDOMScan(
        iframeRef,
        10, // 10 seconds
        (update) => {
          setLiveUpdates(update);
          updateCountRef.current++;
        }
      );

      setScanResults(results);
      const generatedReport = generateScanReport(results);
      setReport(generatedReport);
      onScanComplete?.(results, generatedReport);
    } catch (error) {
      console.error("Scan error:", error);
      setReport(`Error during scan: ${error}`);
    } finally {
      setIsScanning(false);
    }
  };

  const handleExportJSON = () => {
    const json = exportScanResults(scanResults);
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `iframe-scan-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportReport = () => {
    const blob = new Blob([report], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `iframe-scan-report-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const mostReliable = scanResults.length > 0 ? getMostReliableMultiplier(scanResults) : null;

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-lg p-6 space-y-4">
      <div className="space-y-2">
        <h3 className="text-lg font-bold text-white">Iframe DOM Scanner</h3>
        <p className="text-slate-400 text-sm">
          Continuously captures iframe DOM for 10 seconds to identify multiplier elements
        </p>
      </div>

      {/* Control Section */}
      <div className="flex gap-3 flex-wrap">
        <button
          onClick={handleStartScan}
          disabled={isScanning}
          className={`px-4 py-2 rounded font-medium text-sm transition-colors ${
            isScanning
              ? "bg-slate-600 text-slate-400 cursor-not-allowed"
              : "bg-blue-600 hover:bg-blue-700 text-white"
          }`}
        >
          {isScanning ? "Scanning... (10s)" : "Start 10s Scan"}
        </button>

        {scanResults.length > 0 && (
          <>
            <button
              onClick={handleExportJSON}
              className="px-4 py-2 rounded font-medium text-sm bg-green-600 hover:bg-green-700 text-white transition-colors"
            >
              Export JSON
            </button>
            <button
              onClick={handleExportReport}
              className="px-4 py-2 rounded font-medium text-sm bg-purple-600 hover:bg-purple-700 text-white transition-colors"
            >
              Export Report
            </button>
          </>
        )}
      </div>

      {/* Live Update Section */}
      {isScanning && liveUpdates && (
        <div className="bg-slate-800/50 border border-slate-700 rounded p-4">
          <p className="text-xs text-slate-400 mb-2">
            Live Update #{updateCountRef.current} - {liveUpdates.timestamp}
          </p>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-slate-400">Elements Found</p>
              <p className="text-white font-bold text-lg">{liveUpdates.elements.length}</p>
            </div>
            <div>
              <p className="text-slate-400">Multiplier Elements</p>
              <p className="text-green-400 font-bold text-lg">
                {liveUpdates.multiplierElements.length}
              </p>
            </div>
            <div>
              <p className="text-slate-400">Numeric Patterns</p>
              <p className="text-blue-400 font-bold text-lg">
                {liveUpdates.numericPatterns.length}
              </p>
            </div>
          </div>
          {liveUpdates.numericPatterns.length > 0 && (
            <div className="mt-3 pt-3 border-t border-slate-700">
              <p className="text-xs text-slate-400 mb-2">Values Found:</p>
              <p className="text-white font-mono text-sm">
                {liveUpdates.numericPatterns.map(p => `${p.value.toFixed(2)}x`).join(", ")}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Most Reliable Section */}
      {mostReliable && (
        <div className="bg-green-500/10 border border-green-500/30 rounded p-4">
          <p className="text-xs text-green-400 uppercase tracking-wider mb-2">Most Reliable Multiplier</p>
          <div className="flex items-center gap-4">
            <div className="text-4xl font-bold text-green-400">
              {mostReliable.value.toFixed(2)}x
            </div>
            <div className="space-y-1">
              <p className="text-white">Frequency: {mostReliable.frequency} occurrences</p>
              <p className="text-slate-400 text-sm">
                Confidence: {(mostReliable.confidence * 100).toFixed(0)}%
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Report Display Section */}
      {report && (
        <div className="bg-slate-950 border border-slate-700 rounded overflow-hidden">
          <div className="bg-slate-800/50 px-4 py-3 border-b border-slate-700">
            <p className="text-sm font-mono text-slate-300">Scan Report</p>
          </div>
          <div className="p-4 overflow-x-auto max-h-96 overflow-y-auto">
            <pre className="text-xs text-slate-300 font-mono whitespace-pre-wrap break-words">
              {report}
            </pre>
          </div>
        </div>
      )}

      {/* Summary Stats */}
      {scanResults.length > 0 && (
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="bg-slate-800/30 border border-slate-700 rounded p-3">
            <p className="text-slate-400">Total Scans</p>
            <p className="text-white font-bold text-lg">{scanResults.length}</p>
          </div>
          <div className="bg-slate-800/30 border border-slate-700 rounded p-3">
            <p className="text-slate-400">Duration</p>
            <p className="text-white font-bold text-lg">{(scanResults.length * 0.5).toFixed(1)}s</p>
          </div>
        </div>
      )}
    </div>
  );
}
