// Socket.IO client for real-time updates

import { io, Socket } from "socket.io-client";

const SOCKET_URL = process.env.NEXT_PUBLIC_SOCKET_URL || "http://localhost:5001";

let socket: Socket | null = null;

export function initSocket(): Socket {
  if (socket) return socket;

  socket = io(SOCKET_URL, {
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    reconnectionAttempts: 5,
  });

  socket.on("connect", () => {
    console.log("Socket.IO connected:", socket?.id);
  });

  socket.on("disconnect", () => {
    console.log("Socket.IO disconnected");
  });

  socket.on("connect_error", (error: Error) => {
    console.error("Socket.IO connection error:", error);
  });

  return socket;
}

export function getSocket(): Socket | null {
  return socket;
}

export function closeSocket(): void {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
}

// Event listeners

export function onLiveUpdate(callback: (data: any) => void): void {
  if (!socket) initSocket();
  socket?.on("live_update", callback);
}

export function onRoundUpdate(callback: (data: any) => void): void {
  if (!socket) initSocket();
  socket?.on("round_update", callback);
}

export function onStatsUpdate(callback: (data: any) => void): void {
  if (!socket) initSocket();
  socket?.on("stats_update", callback);
}

// Event emitters

export function requestUpdate(): void {
  if (!socket) initSocket();
  socket?.emit("request_update");
}

export function placeBet(data: { stake: number; target: number }): void {
  if (!socket) initSocket();
  socket?.emit("place_bet", data);
}

export function cancelBet(): void {
  if (!socket) initSocket();
  socket?.emit("cancel_bet");
}

export function pauseBot(): void {
  if (!socket) initSocket();
  socket?.emit("pause_bot");
}

export function resumeBot(): void {
  if (!socket) initSocket();
  socket?.emit("resume_bot");
}
