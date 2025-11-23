"use client";

import React, { useEffect, useState } from "react";
import LeftIframe from "./LeftIframe";
import RightIframe from "./RightIframe";
import { getCurrentRound, getLiveStats, getRecentRounds } from "@/lib/api";
import { initSocket, onLiveUpdate, onStatsUpdate, requestUpdate } from "@/lib/socket";

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

export default function Dashboard() {
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

  // Initialize data on mount
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        setIsLoading(true);
        const [roundData, statsData, roundsData] = await Promise.all([
          getCurrentRound(),
          getLiveStats(),
          getRecentRounds(20),
        ]);

        setLiveData((prev) => ({
          ...prev,
          currentRound: roundData,
          liveStats: statsData,
          recentRounds: roundsData || [],
          multiplier: roundData?.actual_multiplier || 1.0,
        }));

        setError(null);
      } catch (err) {
        console.error("Failed to load initial data:", err);
        setError("Failed to connect to backend");
      } finally {
        setIsLoading(false);
      }
    };

    loadInitialData();
  }, []);

  // Initialize Socket.IO
  useEffect(() => {
    const socket = initSocket();

    socket.on("connect", () => {
      console.log("Connected to WebSocket");
      setIsConnected(true);
      requestUpdate();
    });

    socket.on("disconnect", () => {
      console.log("Disconnected from WebSocket");
      setIsConnected(false);
    });

    onLiveUpdate((data) => {
      setLiveData((prev) => ({
        ...prev,
        currentRound: data,
        multiplier: data.actual_multiplier || prev.multiplier,
        status: data.status || prev.status,
      }));
    });

    onStatsUpdate((data) => {
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
  useEffect(() => {
    const interval = setInterval(async () => {
      const [roundData, statsData] = await Promise.all([getCurrentRound(), getLiveStats()]);

      if (roundData) {
        setLiveData((prev) => ({
          ...prev,
          currentRound: roundData,
          liveStats: statsData,
          multiplier: roundData.actual_multiplier || prev.multiplier,
        }));
      }
    }, 5000); // Refresh every 5 seconds

    return () => clearInterval(interval);
  }, []);

  const handleBet = (stake: number, target: number) => {
    console.log("Placing bet:", { stake, target });
    // This would typically emit to the backend via Socket.IO
  };

  const handleCancelBet = () => {
    console.log("Canceling bet");
    // Emit cancel event
  };

  const handlePause = () => {
    console.log("Pausing bot");
    // Emit pause event
  };

  const handleResume = () => {
    console.log("Resuming bot");
    // Emit resume event
  };

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
            {/* Connection Status */}
            <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 border border-slate-700">
              <div
                className={`w-2 h-2 rounded-full ${
                  isConnected ? "bg-green-500 animate-pulse" : "bg-red-500"
                }`}
              />
              <span className="text-sm text-slate-300">
                {isConnected ? "Connected" : "Disconnected"}
              </span>
            </div>

            {/* Last Updated */}
            <div className="text-right">
              <p className="text-xs text-slate-400">Last Updated</p>
              <p className="text-sm text-white font-mono">
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
            <LeftIframe
              multiplier={liveData.multiplier}
              status={liveData.status}
              onBet={handleBet}
              onCancelBet={handleCancelBet}
              onPause={handlePause}
              onResume={handleResume}
            />
          )}
        </div>

        {/* Right Iframe - Analytics */}
        <div className="flex-1 rounded-lg border border-slate-700 overflow-hidden shadow-lg">
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
