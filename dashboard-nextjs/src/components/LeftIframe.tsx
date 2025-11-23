"use client";

import React, { useState } from "react";
import { Play, Pause, Send, X } from "lucide-react";

interface LeftIframeProps {
  multiplier?: number;
  status?: "AWAITING" | "RUNNING" | "CRASHED";
  onBet?: (stake: number, target: number) => void;
  onCancelBet?: () => void;
  onPause?: () => void;
  onResume?: () => void;
}

export default function LeftIframe({
  multiplier = 1.0,
  status = "AWAITING",
  onBet,
  onCancelBet,
  onPause,
  onResume,
}: LeftIframeProps) {
  const [stake, setStake] = useState("25");
  const [targetMultiplier, setTargetMultiplier] = useState("2.0");
  const [isPaused, setIsPaused] = useState(false);

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

  return (
    <div className="h-full w-full bg-gradient-to-br from-slate-900 to-slate-800 p-6 flex flex-col">
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-white mb-2">Aviator Bot Controller</h2>
        <p className="text-slate-400">Live game monitoring and manual controls</p>
      </div>

      {/* Game Display Area */}
      <div className="flex-1 flex flex-col items-center justify-center mb-8 rounded-lg border border-slate-700 bg-slate-800/50 p-6">
        {/* Multiplier Display */}
        <div className="text-center mb-8">
          <p className="text-slate-400 text-sm mb-2">Current Multiplier</p>
          <div className="text-6xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-blue-500 font-mono">
            {multiplier.toFixed(2)}x
          </div>
        </div>

        {/* Status Badge */}
        <div
          className={`flex items-center gap-2 px-4 py-2 rounded-lg border ${getStatusBg()} mb-6`}
        >
          <div className={`w-3 h-3 rounded-full ${getStatusColor().replace("text-", "bg-")}`} />
          <span className={`font-semibold ${getStatusColor()}`}>{status}</span>
        </div>

        {/* Placeholder for Aviator game embed */}
        <div className="w-full h-32 rounded border-2 border-dashed border-slate-600 flex items-center justify-center text-slate-500">
          <p>Aviator Game / Bot Screen</p>
        </div>
      </div>

      {/* Controls */}
      <div className="space-y-4">
        {/* Stake Input */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">Stake Amount ($)</label>
          <input
            type="number"
            value={stake}
            onChange={(e) => setStake(e.target.value)}
            className="w-full px-4 py-2 rounded border border-slate-600 bg-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            placeholder="25"
            disabled={status === "RUNNING"}
          />
        </div>

        {/* Target Multiplier Input */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">Target Multiplier</label>
          <input
            type="number"
            step="0.01"
            value={targetMultiplier}
            onChange={(e) => setTargetMultiplier(e.target.value)}
            className="w-full px-4 py-2 rounded border border-slate-600 bg-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            placeholder="2.0"
            disabled={status === "RUNNING"}
          />
        </div>

        {/* Action Buttons */}
        <div className="grid grid-cols-2 gap-3">
          {status !== "RUNNING" ? (
            <button
              onClick={handleBet}
              className="col-span-2 py-2 px-4 bg-green-600 hover:bg-green-700 text-white font-semibold rounded transition-colors flex items-center justify-center gap-2"
            >
              <Send size={18} />
              Place Bet
            </button>
          ) : (
            <button
              onClick={handleCancel}
              className="col-span-2 py-2 px-4 bg-red-600 hover:bg-red-700 text-white font-semibold rounded transition-colors flex items-center justify-center gap-2"
            >
              <X size={18} />
              Cancel Bet
            </button>
          )}
        </div>

        {/* Pause/Resume Button */}
        <button
          onClick={handlePause}
          className={`w-full py-2 px-4 font-semibold rounded transition-colors flex items-center justify-center gap-2 ${
            isPaused
              ? "bg-blue-600 hover:bg-blue-700 text-white"
              : "bg-slate-700 hover:bg-slate-600 text-white"
          }`}
        >
          {isPaused ? <Play size={18} /> : <Pause size={18} />}
          {isPaused ? "Resume" : "Pause"}
        </button>
      </div>

      {/* Status Info */}
      <div className="mt-6 p-4 rounded bg-slate-700/50 border border-slate-600">
        <p className="text-xs text-slate-400">
          <strong>Status:</strong> Bot is {isPaused ? "paused" : "active"} and ready for betting
        </p>
      </div>
    </div>
  );
}
