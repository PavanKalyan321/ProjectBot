// API client for Flask backend communication

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5001";

// Types
export interface ModelPrediction {
  model_id: string;
  name: string;
  prediction: number;
  confidence: number;
  accuracy: number;
}

export interface CurrentRound {
  round_id: string;
  timestamp: string;
  actual_multiplier: number;
  ensemble_prediction: number;
  ensemble_confidence: number;
  models: ModelPrediction[];
  trend: "UP" | "DOWN" | "NEUTRAL";
  signal: "BET" | "SKIP" | "CAUTIOUS" | "OPPORTUNITY" | "WAIT";
  target_multiplier: number;
}

export interface LiveStats {
  total_rounds: number;
  win_rate: number;
  profit_loss: number;
  current_streak: string;
  average_confidence: number;
  last_updated: string;
}

export interface TopModel {
  rank: number;
  model_id: string;
  name: string;
  accuracy: number;
  predictions_count: number;
}

export interface RoundHistory {
  round_id: string;
  timestamp: string;
  actual_multiplier: number;
  prediction: number;
  confidence: number;
  result: "WIN" | "LOSS";
}

// API Functions

export async function getCurrentRound(): Promise<CurrentRound | null> {
  try {
    const response = await fetch(`${API_BASE}/api/current_round`);
    if (!response.ok) throw new Error("Failed to fetch current round");
    return await response.json();
  } catch (error) {
    console.error("Error fetching current round:", error);
    return null;
  }
}

export async function getLiveStats(): Promise<LiveStats | null> {
  try {
    const response = await fetch(`${API_BASE}/api/live_stats`);
    if (!response.ok) throw new Error("Failed to fetch live stats");
    return await response.json();
  } catch (error) {
    console.error("Error fetching live stats:", error);
    return null;
  }
}

export async function getModelComparison(): Promise<ModelPrediction[] | null> {
  try {
    const response = await fetch(`${API_BASE}/api/model_comparison`);
    if (!response.ok) throw new Error("Failed to fetch model comparison");
    return await response.json();
  } catch (error) {
    console.error("Error fetching model comparison:", error);
    return null;
  }
}

export async function getTopModels(): Promise<TopModel[] | null> {
  try {
    const response = await fetch(`${API_BASE}/api/top_models`);
    if (!response.ok) throw new Error("Failed to fetch top models");
    return await response.json();
  } catch (error) {
    console.error("Error fetching top models:", error);
    return null;
  }
}

export async function getRecentRounds(limit: number = 20): Promise<RoundHistory[] | null> {
  try {
    const response = await fetch(`${API_BASE}/api/recent_rounds?limit=${limit}`);
    if (!response.ok) throw new Error("Failed to fetch recent rounds");
    return await response.json();
  } catch (error) {
    console.error("Error fetching recent rounds:", error);
    return null;
  }
}

export async function getTrendSignal(): Promise<{
  trend: string;
  signal: string;
  confidence: number;
} | null> {
  try {
    const response = await fetch(`${API_BASE}/api/trend_signal`);
    if (!response.ok) throw new Error("Failed to fetch trend signal");
    return await response.json();
  } catch (error) {
    console.error("Error fetching trend signal:", error);
    return null;
  }
}

export async function getRulesStatus(): Promise<{
  low_green_series: boolean;
  post_high_echo: boolean;
  mean_reversion: boolean;
} | null> {
  try {
    const response = await fetch(`${API_BASE}/api/rules_status`);
    if (!response.ok) throw new Error("Failed to fetch rules status");
    return await response.json();
  } catch (error) {
    console.error("Error fetching rules status:", error);
    return null;
  }
}

export async function cleanupData(): Promise<{ status: string } | null> {
  try {
    const response = await fetch(`${API_BASE}/api/cleanup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    if (!response.ok) throw new Error("Failed to cleanup data");
    return await response.json();
  } catch (error) {
    console.error("Error cleaning up data:", error);
    return null;
  }
}

// Multiplier logging API functions

export interface MultiplierLogRequest {
  bot_id: string;
  multiplier: number;
  round_id?: number;
  is_crash?: boolean;
  is_cashout?: boolean;
  ocr_confidence?: number;
  game_name?: string;
  platform_code?: string;
  timestamp?: string;
}

export interface RoundCreateRequest {
  bot_id: string;
  round_number: number;
  stake_value?: number;
  strategy_name?: string;
  game_name?: string;
  platform_code?: string;
  session_id?: string;
}

export async function logMultiplier(data: MultiplierLogRequest): Promise<{
  status: string;
  message: string;
  record_id?: number;
  timestamp?: string;
} | null> {
  try {
    const response = await fetch(`${API_BASE}/api/multiplier/log`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const error = await response.json();
      console.error("Error logging multiplier:", error);
      return error;
    }
    return await response.json();
  } catch (error) {
    console.error("Error logging multiplier:", error);
    return null;
  }
}

export async function createRound(data: RoundCreateRequest): Promise<{
  status: string;
  message: string;
  round_id?: number;
} | null> {
  try {
    const response = await fetch(`${API_BASE}/api/multiplier/create_round`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const error = await response.json();
      console.error("Error creating round:", error);
      return error;
    }
    return await response.json();
  } catch (error) {
    console.error("Error creating round:", error);
    return null;
  }
}

export async function getLatestRound(botId: string): Promise<{
  status: string;
  round?: { id: number; number: number };
} | null> {
  try {
    const response = await fetch(`${API_BASE}/api/multiplier/latest_round/${botId}`);
    if (!response.ok) throw new Error("Failed to get latest round");
    return await response.json();
  } catch (error) {
    console.error("Error getting latest round:", error);
    return null;
  }
}
