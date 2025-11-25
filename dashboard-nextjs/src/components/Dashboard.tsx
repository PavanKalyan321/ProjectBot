"use client";

import React, { useEffect, useState, useRef } from "react";
import LeftIframe from "./LeftIframe";
import RightIframe from "./RightIframe";
import { getCurrentRound, getLiveStats, getRecentRounds, logMultiplier, createRound } from "@/lib/api";
import { initSocket, onLiveUpdate, onStatsUpdate, requestUpdate } from "@/lib/socket";
import { extractMultiplier } from "@/lib/iframe-extractor";
import type { MultiplierExtractionResult } from "@/lib/iframe-extractor";

interface ModelPrediction {
  model_id: string;
  name: string;
  prediction: number;
  confidence: number;
}

interface LiveData {
  currentRound: any;
  liveStats: any;
  recentRounds: any[];
  multiplier: number;
  status: "AWAITING" | "RUNNING" | "CRASHED";
}

const BOT_ID = "demo_bot_001";
const SESSION_ID = "demo_session_" + Date.now();

export default function Dashboard() {
  const leftIframeRef = useRef<any>(null);

  const [liveData, setLiveData] = useState<LiveData>({
    currentRound: null,
    liveStats: null,
    recentRounds: [],
    multiplier: 1.0,
    status: "AWAITING",
  });

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [demoMode, setDemoMode] = useState(false);
  const [currentRoundId, setCurrentRoundId] = useState<number | null>(null);
  const [roundNumber, setRoundNumber] = useState(1);
  const [lastLoggedMultiplier, setLastLoggedMultiplier] = useState(1.0);
  const [extractionMethod, setExtractionMethod] = useState<string>("auto");
  const [extractionConfidence, setExtractionConfidence] = useState<number>(0);

  // Initialize data on mount
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        console.log("🚀 Dashboard: Starting initial data load...");
        setIsLoading(true);
        // const [roundData, statsData, roundsData] = await Promise.all([
        //   getCurrentRound(),
        //   getLiveStats(),
        //   getRecentRounds(20),
        // ]);

        // console.log("✅ Dashboard: Data loaded successfully", {
        //   roundData,
        //   statsData,
        //   roundsCount: roundsData?.length || 0,
        // });

        // setLiveData((prev) => ({
        //   ...prev,
        //   currentRound: roundData,
        //   liveStats: statsData,
        //   recentRounds: roundsData || [],
        //   multiplier: roundData?.actual_multiplier || 1.0,
        // }));

        setError(null);
      } catch (err) {
        console.error("❌ Dashboard: Failed to load initial data:", err);
        setError("Failed to connect to backend");
      } finally {
        setIsLoading(false);
      }
    };

    loadInitialData();
  }, []);

  // Initialize Socket.IO
  useEffect(() => {
    console.log("🔌 Dashboard: Initializing WebSocket connection...");
    const socket = initSocket();

    socket.on("connect", () => {
      console.log("✅ Dashboard: Connected to WebSocket");
      setIsConnected(true);
      requestUpdate();
    });

    socket.on("disconnect", () => {
      console.log("⚠️ Dashboard: Disconnected from WebSocket");
      setIsConnected(false);
    });

    onLiveUpdate((data) => {
      console.log("📊 Dashboard: Live update received", {
        multiplier: data.actual_multiplier,
        status: data.status,
      });
      setLiveData((prev) => ({
        ...prev,
        currentRound: data,
        multiplier: data.actual_multiplier || prev.multiplier,
        status: data.status || prev.status,
      }));
    });

    onStatsUpdate((data) => {
      console.log("📈 Dashboard: Stats update received", data);
      setLiveData((prev) => ({
        ...prev,
        liveStats: data,
      }));
    });

    return () => {
      // Socket is kept alive but cleanup if needed
    };
  }, []);

  // Auto-refresh data periodically
  // useEffect(() => {
  //   console.log("⏱️ Dashboard: Starting periodic data refresh (every 5 seconds)...");
  //   const interval = setInterval(async () => {
  //     try {
  //       const [roundData, statsData] = await Promise.all([getCurrentRound(), getLiveStats()]);

  //       if (roundData) {
  //         console.log("🔄 Dashboard: Periodic refresh completed", {
  //           multiplier: roundData.actual_multiplier,
  //           status: roundData.status,
  //         });
  //         setLiveData((prev) => ({
  //           ...prev,
  //           currentRound: roundData,
  //           liveStats: statsData,
  //           multiplier: roundData.actual_multiplier || prev.multiplier,
  //         }));
  //       }
  //     } catch (err) {
  //       console.error("⚠️ Dashboard: Periodic refresh failed:", err);
  //     }
  //   }, 5000); // Refresh every 5 seconds

  //   return () => clearInterval(interval);
  // }, []);

  const handleBet = (stake: number, target: number) => {
    console.log("💰 Dashboard: User action - Placing bet", { stake, target, timestamp: new Date().toISOString() });
    // This would typically emit to the backend via Socket.IO
  };

  const handleCancelBet = () => {
    console.log("❌ Dashboard: User action - Canceling bet", { timestamp: new Date().toISOString() });
    // Emit cancel event
  };

  const handlePause = () => {
    console.log("⏸️ Dashboard: User action - Pausing bot", { timestamp: new Date().toISOString() });
    // Emit pause event
  };

  const handleResume = () => {
    console.log("▶️ Dashboard: User action - Resuming bot", { timestamp: new Date().toISOString() });
    // Emit resume event
  };

  const handleMultiplierChange = (newMultiplier: number) => {
    console.log("📊 Dashboard: Multiplier changed", { newMultiplier, timestamp: new Date().toISOString() });
    // Update live data with new multiplier
    setLiveData(prev => ({
      ...prev,
      multiplier: newMultiplier,
    }));
  };

  // Log multiplier changes to database
  useEffect(() => {
    // Only log if multiplier has changed and is not the same as last logged
    if (liveData.multiplier === lastLoggedMultiplier) return;

    const logToDatabase = async () => {
      try {
        // If round just started, create a new round record
        if (liveData.status === "RUNNING" && liveData.multiplier === 1.0 && lastLoggedMultiplier === 1.0) {
          const roundResult = await createRound({
            bot_id: BOT_ID,
            round_number: roundNumber,
            stake_value: 25.0,
            strategy_name: "custom",
            game_name: "aviator",
            platform_code: "demo",
            session_id: SESSION_ID,
          });

          if (roundResult?.round_id) {
            console.log(`✅ Round created: ${roundResult.round_id}`);
            setCurrentRoundId(roundResult.round_id);
          }
        }

        // Log the multiplier
        if (currentRoundId) {
          const result = await logMultiplier({
            bot_id: BOT_ID,
            multiplier: Math.round(liveData.multiplier * 100) / 100, // Round to 2 decimals
            round_id: currentRoundId,
            is_crash: liveData.status === "CRASHED",
            game_name: "aviator",
            platform_code: "demo",
            timestamp: new Date().toISOString(),
          });

          if (result?.status === "success") {
            console.log(`💾 Multiplier ${liveData.multiplier.toFixed(2)}x logged: ${result.record_id}`);
            setLastLoggedMultiplier(liveData.multiplier);
          }
        }
      } catch (err) {
        console.error("❌ Error logging multiplier:", err);
      }
    };

    // Debounce logging to avoid too many requests
    const timer = setTimeout(logToDatabase, 300);
    return () => clearTimeout(timer);
  }, [liveData.multiplier, liveData.status, currentRoundId, lastLoggedMultiplier, roundNumber]);

  // Handle round end - increment round number
  useEffect(() => {
    if (liveData.status === "CRASHED" && lastLoggedMultiplier > 1.0) {
      console.log(`🏁 Round ended at ${lastLoggedMultiplier.toFixed(2)}x`);
      setRoundNumber(prev => prev + 1);
      setCurrentRoundId(null);
      setLastLoggedMultiplier(1.0);
    }
  }, [liveData.status, lastLoggedMultiplier]);

  // Iframe extraction - extracts real multiplier from game iframe
  useEffect(() => {
    // Only start extraction if we have an iframe ref and demo mode is on
    if (!leftIframeRef.current || !demoMode) return;

    console.log("🔍 Dashboard: Starting iframe multiplier extraction...");

    // Try to extract multiplier from iframe every 300ms
    const extractionInterval = setInterval(async () => {
      try {
        // Get iframe reference from LeftIframe component
        const iframeElement = leftIframeRef.current?.querySelector("iframe");
        if (!iframeElement) return;

        // Extract multiplier (will try multiple methods)
        const result = await extractMultiplier(
          { current: iframeElement } as React.RefObject<HTMLIFrameElement>,
          "auto"
        );

        if (result.multiplier !== null && result.confidence > 0.7) {
          // Only log if multiplier actually changed
          if (result.multiplier !== liveData.multiplier) {
            console.log(
              `📊 Extracted: ${result.multiplier.toFixed(2)}x via ${result.method} (${(result.confidence * 100).toFixed(0)}%)`
            );
            setExtractionMethod(result.method);
            setExtractionConfidence(result.confidence);

            // Update state with extracted multiplier
            setLiveData(prev => ({
              ...prev,
              multiplier: result.multiplier!,
            }));
          }
        }
      } catch (err) {
        // Silently fail - extraction methods have fallbacks
      }
    }, 300); // Check every 300ms

    return () => clearInterval(extractionInterval);
  }, [demoMode, liveData.multiplier]);

  // Demo mode - simulates live multiplier changes
  useEffect(() => {
    if (!demoMode || isConnected) return;

    let timeoutId: NodeJS.Timeout;
    const simulateRound = () => {
      // Start round
      setLiveData(prev => ({
        ...prev,
        status: "RUNNING",
        multiplier: 1.0,
      }));

      let currentMultiplier = 1.0;
      let tickCount = 0;

      const tickInterval = setInterval(() => {
        tickCount++;
        // Simulate multiplier increase
        currentMultiplier += Math.random() * 0.15 + 0.05; // Random increase between 0.05 and 0.20

        setLiveData(prev => ({
          ...prev,
          multiplier: currentMultiplier,
        }));

        // Random crash between 5-15 ticks
        if (tickCount > 5 && Math.random() < 0.15) {
          clearInterval(tickInterval);
          setLiveData(prev => ({
            ...prev,
            status: "CRASHED",
            multiplier: currentMultiplier,
          }));

          // Wait 2 seconds before next round
          timeoutId = setTimeout(simulateRound, 2000);
        }
      }, 500); // Update every 500ms
    };

    simulateRound();

    return () => {
      clearTimeout(timeoutId);
    };
  }, [demoMode, isConnected]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 to-slate-900">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 border-b border-slate-700 px-6 py-4 sticky top-0 z-50">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Aviator Bot Dashboard</h1>
            <p className="text-slate-400 text-sm">Real-time monitoring and AI predictions</p>
          </div>

          <div className="flex items-center gap-4">
            {/* Demo Mode Toggle */}
            <button
              onClick={() => setDemoMode(!demoMode)}
              className={`px-3 py-1 text-xs font-semibold rounded transition-colors ${
                demoMode
                  ? "bg-blue-600 text-white"
                  : "bg-slate-700 text-slate-300 hover:bg-slate-600"
              }`}
            >
              {demoMode ? "🎮 Demo ON" : "🎮 Demo OFF"}
            </button>

            {/* Connection Status */}
            <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 border border-slate-700">
              <div
                className={`w-2 h-2 rounded-full ${
                  isConnected || demoMode ? "bg-green-500 animate-pulse" : "bg-red-500"
                }`}
              />
              <span className="text-sm text-slate-300">
                {isConnected ? "Connected" : demoMode ? "Demo Mode" : "Disconnected"}
              </span>
            </div>

            {/* Last Updated */}
            <div className="text-right">
              <p className="text-xs text-slate-400">Last Updated</p>
              <p className="text-sm text-white font-mono" suppressHydrationWarning>
                {new Date().toLocaleTimeString()}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="h-[calc(100vh-80px)] flex flex-col lg:flex-row gap-4 p-4">
        {/* Left Iframe - Bot Controller */}
        <div className="flex-1 rounded-lg border border-slate-700 overflow-hidden shadow-lg">
          {isLoading ? (
            <div className="w-full h-full flex items-center justify-center bg-slate-800">
              <p className="text-slate-400">Loading...</p>
            </div>
          ) : (
            <div ref={leftIframeRef}>
              <LeftIframe
                multiplier={liveData.multiplier}
                status={liveData.status}
                onBet={handleBet}
                onCancelBet={handleCancelBet}
                onPause={handlePause}
                onResume={handleResume}
                onMultiplierChange={handleMultiplierChange}
              />
            </div>
          )}
        </div>

        {/* Right Iframe - Analytics */}
        <div className="w-1/5 rounded-lg border border-slate-700 overflow-hidden shadow-lg">
          {isLoading ? (
            <div className="w-full h-full flex items-center justify-center bg-slate-800">
              <p className="text-slate-400">Loading...</p>
            </div>
          ) : (
            <RightIframe
              models={liveData.currentRound?.models || []}
              actualMultiplier={liveData.currentRound?.actual_multiplier || 0}
              ensemble={{
                prediction: liveData.currentRound?.ensemble_prediction || 0,
                confidence: liveData.currentRound?.ensemble_confidence || 0,
              }}
              trend={liveData.currentRound?.trend || "NEUTRAL"}
              signal={liveData.currentRound?.signal || "WAIT"}
              stats={{
                winRate: liveData.liveStats?.win_rate || 0,
                profitLoss: liveData.liveStats?.profit_loss || 0,
                totalRounds: liveData.liveStats?.total_rounds || 0,
              }}
              recentRounds={liveData.recentRounds}
            />
          )}
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="fixed bottom-4 right-4 bg-red-600 text-white px-4 py-3 rounded-lg shadow-lg">
          {error}
        </div>
      )}
    </div>
  );
}
