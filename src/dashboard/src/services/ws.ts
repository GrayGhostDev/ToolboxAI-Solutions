import { io, Socket } from "socket.io-client";
import { WS_URL, WS_CONFIG, AUTH_TOKEN_KEY } from "../config";
import { store } from "../store";
import { addNotification } from "../store/slices/uiSlice";
import { addXP, addBadge, setLeaderboard } from "../store/slices/gamificationSlice";
import { addActivity, addEvent } from "../store/slices/dashboardSlice";

class WebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private reconnectTimer: number | null = null;

  connect(): void {
    if (this.socket?.connected) {
      return;
    }

    const token = localStorage.getItem(AUTH_TOKEN_KEY);

    // Don't attempt connection without a valid token
    if (!token) {
      console.log("WebSocket: Skipping connection - no auth token available");
      return;
    }

    this.socket = io(WS_URL, {
      path: '/socket.io/',
      auth: {
        token,
      },
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionAttempts: WS_CONFIG.maxReconnectAttempts,
      reconnectionDelay: WS_CONFIG.reconnectInterval,
    });

    this.setupEventListeners();
  }

  private setupEventListeners(): void {
    if (!this.socket) return;

    // Connection events
    this.socket.on("connect", () => {
      console.log("WebSocket connected");
      this.reconnectAttempts = 0;
      store.dispatch(
        addNotification({
          type: "success",
          message: "Real-time connection established",
          autoHide: true,
        })
      );
    });

    this.socket.on("disconnect", (reason) => {
      console.log("WebSocket disconnected:", reason);
      if (reason === "io server disconnect") {
        // Server initiated disconnect, try to reconnect
        this.reconnect();
      }
    });

    this.socket.on("connect_error", (error) => {
      console.error("WebSocket connection error:", error);
      this.reconnectAttempts++;
      if (this.reconnectAttempts >= WS_CONFIG.maxReconnectAttempts) {
        store.dispatch(
          addNotification({
            type: "error",
            message: "Unable to establish real-time connection",
          })
        );
      }
    });

    // Application events
    this.socket.on("notification", (data) => {
      store.dispatch(
        addNotification({
          type: data.type || "info",
          message: data.message,
          autoHide: data.autoHide !== false,
        })
      );
    });

    this.socket.on("xp_gained", (data) => {
      store.dispatch(
        addXP({
          amount: data.amount,
          reason: data.reason,
          source: data.source,
        })
      );
      store.dispatch(
        addNotification({
          type: "success",
          message: `+${data.amount} XP: ${data.reason}`,
          autoHide: true,
        })
      );
    });

    this.socket.on("badge_earned", (data) => {
      store.dispatch(addBadge(data.badge));
      store.dispatch(
        addNotification({
          type: "success",
          message: `🏆 New badge earned: ${data.badge.name}`,
          autoHide: false,
        })
      );
    });

    this.socket.on("leaderboard_update", (data) => {
      store.dispatch(setLeaderboard(data.leaderboard));
    });

    this.socket.on("class_online", (data) => {
      store.dispatch(
        addNotification({
          type: "info",
          message: `Class "${data.className}" is now online!`,
          autoHide: true,
        })
      );
    });

    this.socket.on("assignment_due", (data) => {
      store.dispatch(
        addNotification({
          type: "warning",
          message: `Assignment "${data.title}" is due in ${data.timeRemaining}`,
          autoHide: false,
        })
      );
    });

    this.socket.on("new_message", (data) => {
      store.dispatch(
        addNotification({
          type: "info",
          message: `New message from ${data.senderName}`,
          autoHide: true,
        })
      );
    });

    this.socket.on("activity", (data) => {
      store.dispatch(addActivity(data));
    });

    this.socket.on("event", (data) => {
      store.dispatch(addEvent(data));
    });

    // Heartbeat for connection monitoring
    this.socket.on("ping", () => {
      this.socket?.emit("pong");
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private reconnect(): void {
    if (this.reconnectTimer) {
      return;
    }

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, WS_CONFIG.reconnectInterval);
  }

  // Emit events
  emit(event: string, data?: any): void {
    if (this.socket?.connected) {
      this.socket.emit(event, data);
    }
  }

  // Subscribe to specific events
  on(event: string, callback: (data: any) => void): void {
    this.socket?.on(event, callback);
  }

  // Unsubscribe from events
  off(event: string, callback?: (data: any) => void): void {
    if (callback) {
      this.socket?.off(event, callback);
    } else {
      this.socket?.off(event);
    }
  }

  // Join a room (for class-specific updates)
  joinRoom(roomId: string): void {
    this.emit("join_room", { roomId });
  }

  // Leave a room
  leaveRoom(roomId: string): void {
    this.emit("leave_room", { roomId });
  }

  // Request leaderboard update
  requestLeaderboard(classId?: string): void {
    this.emit("request_leaderboard", { classId });
  }

  // Mark user as active
  sendHeartbeat(): void {
    this.emit("heartbeat");
  }

  // Get connection status
  isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

// Export singleton instance
export const wsService = new WebSocketService();

// Connect WebSocket when imported if enabled and authenticated
if (import.meta.env.VITE_ENABLE_WEBSOCKET === "true") {
  // Attempt connection only if token is available
  const token = localStorage.getItem(AUTH_TOKEN_KEY);
  if (token) {
    wsService.connect();
  }
}

export function connectWS(url: string, onMessage: (ev: MessageEvent) => void) {
  const ws = new WebSocket(url);
  ws.onmessage = onMessage;
  return ws;
}
