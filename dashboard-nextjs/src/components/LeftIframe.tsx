"use client";

import React, { useState, useRef, useEffect } from "react";
import { Play, Pause, Send, X, Activity, Clock, AlertCircle } from "lucide-react";
import { extractMultiplierViaXPath } from "@/lib/iframe-extractor";
import IframeDOMScanner from "./IframeDOMScanner";
import {
  testAllMethods,
  extractMultiplierMultiMethod,
  setupMutationObserver,
  sendPostMessage,
  accessWindowObject,
  callIframeFunction,
  searchIframeText,
  simulateClick,
  interceptConsole,
  watchStorage,
  observePerformance,
} from "@/lib/iframe-communication";

interface LeftIframeProps {
  multiplier?: number;
  status?: "AWAITING" | "RUNNING" | "CRASHED";
  onBet?: (stake: number, target: number) => void;
  onCancelBet?: () => void;
  onPause?: () => void;
  onResume?: () => void;
  onMultiplierChange?: (multiplier: number) => void;
}

interface MonitorLog {
  id: string;
  timestamp: string;
  category: "lifecycle" | "network" | "message" | "interaction";
  type: "info" | "success" | "warning" | "error";
  message: string;
  data?: any;
}

interface PerformanceMetrics {
  duration: number;
  transferSize: number;
  dns: number;
  tcp: number;
  ttfb: number;
}

export default function LeftIframe({
  multiplier = 1.0,
  status = "AWAITING",
  onBet,
  onCancelBet,
  onPause,
  onResume,
  onMultiplierChange,
}: LeftIframeProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  const [stake, setStake] = useState("25");
  const [targetMultiplier, setTargetMultiplier] = useState("2.0");
  const [isPaused, setIsPaused] = useState(false);

  // Monitoring states
  const [logs, setLogs] = useState<MonitorLog[]>([]);
  const [isIframeLoaded, setIsIframeLoaded] = useState(false);
  const [hasPostMessage, setHasPostMessage] = useState(false);
  const [performance, setPerformance] = useState<PerformanceMetrics | null>(null);
  const [visibility, setVisibility] = useState(0);
  const [lastMultiplier, setLastMultiplier] = useState(1.0);
  const [peakMultiplier, setPeakMultiplier] = useState(1.0);
  const [showScanner, setShowScanner] = useState(false);
  const [scannerResults, setScannerResults] = useState<any>(null);
  const [communicationMethods, setCommunicationMethods] = useState<any>(null);
  const [bestMethod, setBestMethod] = useState<string>("");

  // Add log helper
  const addLog = (
    category: MonitorLog["category"],
    type: MonitorLog["type"],
    message: string,
    data?: any
  ) => {
    const log: MonitorLog = {
      id: Math.random().toString(36),
      timestamp: new Date().toLocaleTimeString(),
      category,
      type,
      message,
      data,
    };
    console.log("Adding log:", log);
    setLogs(prev => [...prev.slice(-50), log]); // Keep last 50 logs
    console.log(`[${log.category}] ${log.type.toUpperCase()} - ${log.message}`, data || "");
  };

  

  // Monitor multiplier changes
  useEffect(() => {
    // Detect round start
    if (multiplier > 1.0 && lastMultiplier <= 1.0 && status === "RUNNING") {
      addLog("interaction", "success", `🎮 ROUND STARTED at 1.00x`);
      setLastMultiplier(multiplier);
      setPeakMultiplier(multiplier);
      onMultiplierChange?.(multiplier);
    }
    // Detect round end (crash)
    else if (status === "CRASHED" && multiplier !== lastMultiplier) {
      addLog("interaction", "error", `💥 ROUND ENDED at ${multiplier.toFixed(2)}x`);
      setLastMultiplier(multiplier);
      onMultiplierChange?.(multiplier);
    }
    // Track peak during flight
    else if (multiplier > peakMultiplier && status === "RUNNING") {
      setPeakMultiplier(multiplier);
      addLog("interaction", "info", `📈 Multiplier: ${multiplier.toFixed(2)}x`);
      onMultiplierChange?.(multiplier);
    }
    // Normal update
    else if (multiplier !== lastMultiplier) {
      setLastMultiplier(multiplier);
      onMultiplierChange?.(multiplier);
    }
  }, [multiplier, status, lastMultiplier, peakMultiplier, onMultiplierChange]);

  // Test all communication methods on iframe load
  useEffect(() => {
    if (!isIframeLoaded) return;

    const testCommunicationMethods = async () => {
      addLog("interaction", "info", "🔬 Testing all 10 communication methods...");

      try {
        // Test all methods
        const results = await testAllMethods(iframeRef);
        setCommunicationMethods(results);

        // Log results
        Object.entries(results).forEach(([method, result]: [string, any]) => {
          const status = result.success ? "✅" : "❌";
          const duration = result.duration ? `${result.duration.toFixed(0)}ms` : "N/A";
          addLog(
            "interaction",
            result.success ? "success" : "warning",
            `${status} ${method}: ${result.success ? "Works" : "Failed"} (${duration})`
          );
        });

        // Find best working method
        const bestWorking = Object.entries(results).find(
          ([_, result]: [string, any]) => result.success
        );

        if (bestWorking) {
          setBestMethod(bestWorking[0]);
          addLog(
            "interaction",
            "success",
            `🏆 Best method: ${bestWorking[0]} (fastest working)`
          );
        }

        // Try multi-method extraction
        const multiResult = await extractMultiplierMultiMethod(iframeRef);
        if (multiResult.value) {
          addLog(
            "interaction",
            "success",
            `📊 Multi-method extraction: ${multiResult.value.toFixed(2)}x via ${multiResult.method}`
          );
        }
      } catch (err) {
        addLog("interaction", "error", `❌ Communication test error: ${String(err)}`);
      }
    };

    // Run after a small delay to ensure iframe is ready
    const timer = setTimeout(testCommunicationMethods, 1000);

    return () => clearTimeout(timer);
  }, [isIframeLoaded]);

  // PostMessage-based continuous multiplier extraction (BEST METHOD)
  useEffect(() => {
    if (!isIframeLoaded) return;

    const extractInterval = setInterval(async () => {
      try {
        // Try PostMessage first (your best method - postMessage works!)
        const result = await sendPostMessage(iframeRef, {
          type: "GET_MULTIPLIER"
        }, "https://demo.aviatrix.bet", 2000);

        if (result.success && result.data?.multiplier !== undefined) {
          const extractedValue = parseFloat(result.data.multiplier);

          // Update multiplier if it changed and is valid
          if (extractedValue !== lastMultiplier && !isNaN(extractedValue) && extractedValue > 0) {
            addLog("interaction", "success", `📡 PostMessage: ${extractedValue.toFixed(2)}x`);
            onMultiplierChange?.(extractedValue);
          }
        }
      } catch (err) {
        // Silently fail - don't spam logs
      }
    }, 1000); // Extract every 1 second

    return () => clearInterval(extractInterval);
  }, [isIframeLoaded, lastMultiplier, onMultiplierChange]);

  // XPath-based multiplier extraction from iframe (FALLBACK)
  useEffect(() => {
    if (!isIframeLoaded) return;

    const extractInterval = setInterval(async () => {
      const result = await extractMultiplierViaXPath(
        iframeRef,
        '//*[@id="root"]/div[1]/div[3]/div[2]/div[2]'
      );

      if (result.multiplier !== null && result.multiplier !== lastMultiplier) {
        addLog("interaction", "info", `📡 XPath extraction: ${result.multiplier.toFixed(2)}x (confidence: ${(result.confidence * 100).toFixed(0)}%)`);
      }
    }, 500); // Extract every 500ms during active game

    return () => clearInterval(extractInterval);
  }, [isIframeLoaded, lastMultiplier]);

  const handleBet = () => {
    onBet?.(parseFloat(stake), parseFloat(targetMultiplier));
  };

  const handleCancel = () => {
    onCancelBet?.();
  };

  const handlePause = () => {
    setIsPaused(!isPaused);
    if (!isPaused) {
      onPause?.();
    } else {
      onResume?.();
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case "RUNNING":
        return "text-green-500";
      case "CRASHED":
        return "text-red-500";
      default:
        return "text-yellow-500";
    }
  };

  const getStatusBg = () => {
    switch (status) {
      case "RUNNING":
        return "bg-green-500/10 border-green-500/30";
      case "CRASHED":
        return "bg-red-500/10 border-red-500/30";
      default:
        return "bg-yellow-500/10 border-yellow-500/30";
    }
  };

  // MONITOR: Iframe lifecycle events
  useEffect(() => {
    const iframe = iframeRef.current;
    if (!iframe) return;

    const startTime = window.performance.now();
    addLog("lifecycle", "info", "🚀 Initializing iframe");

    const handleLoad = () => {
      const loadTime = Math.round(window.performance.now() - startTime);
      setIsIframeLoaded(true);
      addLog("lifecycle", "success", `✅ Iframe loaded successfully in ${loadTime}ms`);

      // Get performance metrics
      setTimeout(() => {
        const perfEntries = window.performance.getEntriesByType("resource") as PerformanceResourceTiming[];
        const iframeEntry = perfEntries.find(e =>
          e.name.includes("aviatrix.bet")
        );

        if (iframeEntry) {
          const metrics: PerformanceMetrics = {
            duration: Math.round(iframeEntry.duration),
            transferSize: iframeEntry.transferSize
              ? Math.round(iframeEntry.transferSize / 1024)
              : 0,
            dns: Math.round(
              iframeEntry.domainLookupEnd - iframeEntry.domainLookupStart
            ),
            tcp: Math.round(iframeEntry.connectEnd - iframeEntry.connectStart),
            ttfb: Math.round(
              iframeEntry.responseStart - iframeEntry.requestStart
            ),
          };

          setPerformance(metrics);
          addLog("network", "info", "📊 Performance metrics captured", metrics);
        }
      }, 100);
    };

    const handleError = (e: ErrorEvent) => {
      addLog("lifecycle", "error", `❌ Iframe error: ${e.message}`);
    };

    iframe.addEventListener("load", handleLoad);
    iframe.addEventListener("error", handleError);

    return () => {
      iframe.removeEventListener("load", handleLoad);
      iframe.removeEventListener("error", handleError);
    };
  }, []);

  // MONITOR: postMessage communication
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      // Check if message is from Aviator
      if (event.origin !== "https://demo.aviatrix.bet") return;

      setHasPostMessage(true);
      console.log("Received postMessage:", event.data);
      addLog("message", "success", `📨 Received: ${event.data?.type || "unknown"}`, event.data);
    };

    window.addEventListener("message", handleMessage);

    // Try sending test messages after iframe loads
    const testTimer = setTimeout(() => {
      const iframe = iframeRef.current;
      if (iframe?.contentWindow && isIframeLoaded) {
        const testMessages = [
          { type: "INIT", client: "dashboard", timestamp: Date.now() },
          { type: "HANDSHAKE" },
          { type: "GET_STATE" },
          { type: "SUBSCRIBE", events: ["multiplier", "status"] },
        ];

        testMessages.forEach((msg, idx) => {
          setTimeout(() => {
            iframe.contentWindow!.postMessage(msg, "https://demo.aviatrix.bet");
            addLog("message", "info", `📤 Sent: ${msg.type}`, msg);
          }, (idx + 1) * 1000);
        });
      }
    }, 2000);

    return () => {
      window.removeEventListener("message", handleMessage);
      clearTimeout(testTimer);
    };
  }, [isIframeLoaded]);

  // MONITOR: Iframe visibility
  useEffect(() => {
    const iframe = iframeRef.current;
    if (!iframe) return;

    const observer = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          const ratio = Math.round(entry.intersectionRatio * 100);
          setVisibility(ratio);

          if (entry.isIntersecting && ratio === 100) {
            addLog("interaction", "info", "👁️ Iframe fully visible");
          } else if (!entry.isIntersecting) {
            addLog("interaction", "warning", "👁️ Iframe not visible");
          }
        });
      },
      { threshold: [0, 0.5, 1.0] }
    );

    observer.observe(iframe);
    return () => observer.disconnect();
  }, []);

  // MONITOR: Iframe resize
  useEffect(() => {
    const iframe = iframeRef.current;
    if (!iframe) return;

    const resizeObserver = new ResizeObserver(entries => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        addLog(
          "interaction",
          "info",
          `📐 Resized to ${Math.round(width)}x${Math.round(height)}`
        );
      }
    });

    resizeObserver.observe(iframe);
    return () => resizeObserver.disconnect();
  }, []);

  // Helper to get log icon
  const getLogIcon = (type: MonitorLog["type"]) => {
    switch (type) {
      case "info": return "🔵";
      case "success": return "✅";
      case "warning": return "⚠️";
      case "error": return "🔴";
    }
  };

  // Helper to get category color
  const getCategoryColor = (category: MonitorLog["category"]) => {
    switch (category) {
      case "network": return "text-blue-400";
      case "message": return "text-green-400";
      case "lifecycle": return "text-purple-400";
      case "interaction": return "text-yellow-400";
    }
  };

  return (
    <div className="h-full w-full bg-gradient-to-br from-slate-900 to-slate-800 flex flex-col">
      {/* Top Header */}
      <div className="bg-black/40 border-b border-slate-700 px-6 py-4">
        <h2 className="text-2xl font-bold text-white mb-1">Aviator Bot Controller</h2>
        <p className="text-slate-400 text-sm">Live game monitoring and manual controls</p>
      </div>

      {/* Main Content - Two Columns */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Side - Controls (25%) */}
        <div className="w-1/4 bg-slate-800/30 border-r border-slate-700 overflow-y-auto p-6 space-y-6">
          {/* Multiplier Display */}
          <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
            <p className="text-slate-400 text-xs uppercase tracking-wider mb-3">Current Multiplier</p>
            <div className="text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-blue-500 font-mono">
              {multiplier.toFixed(2)}x
            </div>
          </div>

          {/* Status Badge */}
          <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
            <p className="text-slate-400 text-xs uppercase tracking-wider mb-3">Bot Status</p>
            <div className={`flex items-center gap-2 px-4 py-3 rounded-lg border ${getStatusBg()}`}>
              <div className={`w-3 h-3 rounded-full ${getStatusColor().replace("text-", "bg-")}`} />
              <span className={`font-semibold text-sm ${getStatusColor()}`}>{status}</span>
            </div>
          </div>

          {/* Controls */}
          <div className="space-y-4 border-t border-slate-700 pt-6">
            {/* Stake Input */}
            <div>
              <label className="block text-xs uppercase tracking-wider text-slate-300 font-medium mb-2">Stake ($)</label>
              <input
                type="number"
                value={stake}
                onChange={(e) => setStake(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded border border-slate-600 bg-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                placeholder="25"
                disabled={status === "RUNNING"}
              />
            </div>

            {/* Target Multiplier */}
            <div>
              <label className="block text-xs uppercase tracking-wider text-slate-300 font-medium mb-2">Target</label>
              <input
                type="number"
                step="0.01"
                value={targetMultiplier}
                onChange={(e) => setTargetMultiplier(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded border border-slate-600 bg-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                placeholder="2.0"
                disabled={status === "RUNNING"}
              />
            </div>

            {/* Action Button */}
            {status !== "RUNNING" ? (
              <button
                onClick={handleBet}
                className="w-full py-2 px-4 bg-green-600 hover:bg-green-700 text-white font-semibold text-sm rounded transition-colors flex items-center justify-center gap-2"
              >
                <Send size={16} />
                Place Bet
              </button>
            ) : (
              <button
                onClick={handleCancel}
                className="w-full py-2 px-4 bg-red-600 hover:bg-red-700 text-white font-semibold text-sm rounded transition-colors flex items-center justify-center gap-2"
              >
                <X size={16} />
                Cancel
              </button>
            )}

            {/* Pause/Resume */}
            <button
              onClick={handlePause}
              className={`w-full py-2 px-4 text-sm font-semibold rounded transition-colors flex items-center justify-center gap-2 ${
                isPaused
                  ? "bg-blue-600 hover:bg-blue-700 text-white"
                  : "bg-slate-700 hover:bg-slate-600 text-white"
              }`}
            >
              {isPaused ? <Play size={16} /> : <Pause size={16} />}
              {isPaused ? "Resume" : "Pause"}
            </button>
          </div>

          {/* Status Info */}
          <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-3 text-xs text-slate-400">
            <strong>Status:</strong> Bot is {isPaused ? "paused" : "active"}
          </div>
        </div>

        {/* Right Side - Game Screen (75%) */}
        <div className="flex-1 flex gap-6 overflow-hidden p-6">
          {/* Phone Frame - Left */}
          <div className="flex-1 flex items-center justify-center relative">
            <div className="flex flex-col rounded-3xl border-8 border-slate-900 bg-black shadow-2xl overflow-hidden h-full relative">
              {/* Phone Status Bar */}
              <div className="bg-black px-6 py-2 flex justify-between items-center text-white text-xs shrink-0">
                <span>9:41</span>
                <span>📶 📡 🔋</span>
              </div>

              {/* Iframe Container */}
              <div className="flex-1 bg-slate-800 overflow-hidden flex items-center justify-center relative">
                <iframe
                  ref={iframeRef}
                  src="https://demo.aviatrix.bet/?cid=cricazaprod&isDemo=true&lang=en&sessionToken="
                  className="border-none"
                  style={{ width: "500px", height: "500px" }}
                  title="Aviator Game"
                  sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-modals"
                />

                {/* Floating Multiplier Display */}
                <div className="absolute top-4 right-4 bg-black/80 backdrop-blur-sm border border-green-500/50 rounded-lg px-3 py-2 pointer-events-none">
                  <p className="text-green-400 text-sm font-bold font-mono">
                    {multiplier.toFixed(2)}x
                  </p>
                </div>
              </div>

              {/* Phone Home Indicator */}
              <div className="bg-black h-6 flex justify-center items-end pb-1 shrink-0">
                <div className="w-32 h-1 bg-slate-700 rounded-full"></div>
              </div>
            </div>
          </div>

          {/* Right Panel - Monitoring & Logs */}
          <div className="w-1/5 flex flex-col gap-4 overflow-hidden">
            {/* Multiplier Display */}
            <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-3">
              <p className="text-slate-400 text-xs uppercase tracking-wider mb-2">Live Multiplier</p>
              <div className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-blue-500 font-mono">
                {multiplier.toFixed(2)}x
              </div>
              {peakMultiplier > 1.0 && (
                <p className="text-slate-400 text-xs mt-1">Peak: {peakMultiplier.toFixed(2)}x</p>
              )}
            </div>

            {/* Status Bar */}
            <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg border border-slate-700 text-xs">
              <div className="flex items-center gap-2">
                {isIframeLoaded ? (
                  <Activity className="w-3 h-3 text-green-500 animate-pulse" />
                ) : (
                  <Activity className="w-3 h-3 text-slate-500" />
                )}
                <span className="text-white">
                  {isIframeLoaded ? "Connected" : "Loading..."}
                </span>
              </div>
              <div className="text-slate-400">
                {hasPostMessage ? "✓ msg" : "✗ msg"}
              </div>
            </div>

            {/* Communication Methods Results */}
            {communicationMethods && (
              <div className="p-3 bg-blue-500/10 rounded-lg border border-blue-500/30 text-xs">
                <p className="text-blue-400 font-semibold mb-2">Communication Methods</p>
                <div className="space-y-1">
                  {Object.entries(communicationMethods).map(([method, result]: [string, any]) => (
                    <div key={method} className="flex justify-between items-center text-xs">
                      <span className="text-slate-400">{method}</span>
                      <span className={result.success ? "text-green-400" : "text-red-400"}>
                        {result.success ? "✅" : "❌"}
                      </span>
                    </div>
                  ))}
                  {bestMethod && (
                    <div className="mt-2 pt-2 border-t border-blue-500/30">
                      <p className="text-blue-300 font-semibold">🏆 Best: {bestMethod}</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Performance Metrics */}
            {performance && (
              <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-700 text-xs">
                <p className="text-slate-300 font-semibold mb-2">Performance</p>
                <div className="space-y-1">
                  <div className="flex justify-between text-slate-400">
                    <span>DNS:</span>
                    <span className="text-white">{performance.dns}ms</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>TCP:</span>
                    <span className="text-white">{performance.tcp}ms</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>TTFB:</span>
                    <span className="text-white">{performance.ttfb}ms</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Duration:</span>
                    <span className="text-white">{performance.duration}ms</span>
                  </div>
                </div>
              </div>
            )}

            {/* Event Log / Scanner Toggle */}
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs uppercase tracking-wider text-slate-300 font-semibold">
                {showScanner ? "DOM Scanner" : "Event Log"}
              </h3>
              <button
                onClick={() => setShowScanner(!showScanner)}
                className="text-xs px-2 py-1 rounded bg-slate-700 hover:bg-slate-600 text-slate-300 transition-colors"
              >
                {showScanner ? "Logs" : "Scanner"}
              </button>
            </div>

            {/* Event Log - Scrollable */}
            {!showScanner && (
              <div className="flex-1 flex flex-col min-h-0">
                <div className="flex-1 p-3 bg-slate-950 rounded-lg border border-slate-700 overflow-y-auto">
                  {logs.length === 0 ? (
                    <p className="text-slate-500 text-xs">No events</p>
                  ) : (
                    logs.slice(-20).reverse().map(log => (
                      <div key={log.id} className="text-slate-400 text-xs mb-1 truncate hover:truncate-none">
                        <span>{getLogIcon(log.type)}</span>
                        <span className="ml-1">{log.message}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {/* DOM Scanner Component */}
            {showScanner && (
              <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
                <IframeDOMScanner
                  iframeRef={iframeRef}
                  onScanComplete={(results, report) => {
                    setScannerResults({ results, report });
                    addLog("interaction", "success", `✅ DOM Scan complete: ${results.length} snapshots captured`);
                  }}
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
