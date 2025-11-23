"use client";

import React, { useMemo } from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface ModelPrediction {
  model_id: string;
  name: string;
  prediction: number;
  confidence: number;
}

interface RightIframeProps {
  models?: ModelPrediction[];
  actualMultiplier?: number;
  ensemble?: {
    prediction: number;
    confidence: number;
  };
  trend?: "UP" | "DOWN" | "NEUTRAL";
  signal?: "BET" | "SKIP" | "CAUTIOUS" | "OPPORTUNITY" | "WAIT";
  stats?: {
    winRate: number;
    profitLoss: number;
    totalRounds: number;
  };
  recentRounds?: Array<{
    timestamp: string;
    prediction: number;
    actual: number;
    result: "WIN" | "LOSS";
  }>;
}

export default function RightIframe({
  models = [],
  actualMultiplier = 0,
  ensemble = { prediction: 0, confidence: 0 },
  trend = "NEUTRAL",
  signal = "WAIT",
  stats = { winRate: 0, profitLoss: 0, totalRounds: 0 },
  recentRounds = [],
}: RightIframeProps) {
  const getTrendIcon = () => {
    switch (trend) {
      case "UP":
        return <TrendingUp className="w-5 h-5 text-green-500" />;
      case "DOWN":
        return <TrendingDown className="w-5 h-5 text-red-500" />;
      default:
        return <Minus className="w-5 h-5 text-yellow-500" />;
    }
  };

  const getTrendColor = () => {
    switch (trend) {
      case "UP":
        return "text-green-500";
      case "DOWN":
        return "text-red-500";
      default:
        return "text-yellow-500";
    }
  };

  const getSignalColor = () => {
    switch (signal) {
      case "BET":
        return "bg-green-600";
      case "SKIP":
        return "bg-red-600";
      case "CAUTIOUS":
        return "bg-yellow-600";
      case "OPPORTUNITY":
        return "bg-blue-600";
      default:
        return "bg-slate-600";
    }
  };

  const chartData = useMemo(() => {
    return recentRounds.map((round, idx) => ({
      round: idx + 1,
      prediction: round.prediction,
      actual: round.actual,
    }));
  }, [recentRounds]);

  // Top 3 models
  const topModels = useMemo(() => {
    return [...models]
      .sort((a, b) => b.confidence - a.confidence)
      .slice(0, 3);
  }, [models]);

  return (
    <div className="h-full w-full bg-gradient-to-br from-slate-900 to-slate-800 p-6 flex flex-col overflow-y-auto">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">Analytics & Predictions</h2>
        <p className="text-slate-400">ML model ensemble analysis</p>
      </div>

      {/* Current Round Info */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        {/* Actual Multiplier */}
        <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
          <p className="text-xs text-slate-400 mb-1">Actual Multiplier</p>
          <p className="text-2xl font-bold text-white">{actualMultiplier.toFixed(2)}x</p>
        </div>

        {/* Ensemble Prediction */}
        <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
          <p className="text-xs text-slate-400 mb-1">Ensemble Prediction</p>
          <p className="text-2xl font-bold text-blue-400">{ensemble.prediction.toFixed(2)}x</p>
          <p className="text-xs text-slate-500 mt-1">{ensemble.confidence}% confidence</p>
        </div>
      </div>

      {/* Trend & Signal */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        {/* Trend */}
        <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4 flex items-center gap-3">
          {getTrendIcon()}
          <div>
            <p className="text-xs text-slate-400">Trend</p>
            <p className={`text-lg font-semibold ${getTrendColor()}`}>{trend}</p>
          </div>
        </div>

        {/* Signal */}
        <div className={`rounded-lg border ${getSignalColor()}/30 bg-${getSignalColor().split('-')[1]}-600/10 p-4`}>
          <p className="text-xs text-slate-400 mb-1">Trading Signal</p>
          <p className={`text-lg font-semibold ${getSignalColor()}`}>{signal}</p>
        </div>
      </div>

      {/* Live Stats */}
      <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4 mb-6">
        <h3 className="text-sm font-semibold text-white mb-3">Live Statistics</h3>
        <div className="grid grid-cols-3 gap-3">
          <div>
            <p className="text-xs text-slate-400">Win Rate</p>
            <p className="text-xl font-bold text-green-400">{stats.winRate.toFixed(1)}%</p>
          </div>
          <div>
            <p className="text-xs text-slate-400">P/L</p>
            <p className={`text-xl font-bold ${stats.profitLoss >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              ${stats.profitLoss.toFixed(2)}
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-400">Rounds</p>
            <p className="text-xl font-bold text-blue-400">{stats.totalRounds}</p>
          </div>
        </div>
      </div>

      {/* Top 3 Models */}
      <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4 mb-6">
        <h3 className="text-sm font-semibold text-white mb-3">Top 3 Models</h3>
        <div className="space-y-2">
          {topModels.map((model, idx) => (
            <div key={model.model_id} className="flex items-center justify-between py-2 px-3 rounded bg-slate-700/50">
              <div className="flex items-center gap-3">
                <span className="text-xs font-bold text-yellow-500">#{idx + 1}</span>
                <div>
                  <p className="text-sm font-medium text-white">{model.name}</p>
                </div>
              </div>
              <p className="text-sm font-bold text-blue-400">{model.confidence}%</p>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Rounds Chart */}
      {chartData.length > 0 && (
        <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
          <h3 className="text-sm font-semibold text-white mb-3">Last 10 Rounds</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
              <XAxis dataKey="round" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1e293b",
                  border: "1px solid #475569",
                  borderRadius: "8px",
                }}
                labelStyle={{ color: "#e2e8f0" }}
              />
              <Line
                type="monotone"
                dataKey="prediction"
                stroke="#3b82f6"
                name="Prediction"
                dot={false}
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="actual"
                stroke="#10b981"
                name="Actual"
                dot={false}
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
