"use client";
import { useEffect, useRef, useCallback } from "react";
import { useAuthStore } from "@/store/auth.store";

type WSMessage = {
  type: string;
  [key: string]: unknown;
};

type UseWebSocketOptions = {
  onMessage?: (msg: WSMessage) => void;
  onDocumentStatus?: (docId: string, status: string, title: string) => void;
  onNotification?: (type: string, title: string, body: string) => void;
};

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
const RECONNECT_DELAY = 3000;
const MAX_RECONNECTS = 5;

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const { accessToken } = useAuthStore();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCount = useRef(0);
  const reconnectTimer = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    if (!accessToken) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(`${WS_URL}/api/v1/ws?token=${accessToken}`);
      wsRef.current = ws;

      ws.onopen = () => {
        reconnectCount.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const msg: WSMessage = JSON.parse(event.data);

          options.onMessage?.(msg);

          if (msg.type === "document_status" && options.onDocumentStatus) {
            options.onDocumentStatus(
              msg.document_id as string,
              msg.status as string,
              msg.title as string
            );
          }

          if (msg.type === "notification" && options.onNotification) {
            options.onNotification(
              msg.notification_type as string,
              msg.title as string,
              msg.body as string
            );
          }
        } catch {
          // ignore parse errors
        }
      };

      ws.onclose = () => {
        if (reconnectCount.current < MAX_RECONNECTS) {
          reconnectCount.current++;
          reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY);
        }
      };

      ws.onerror = () => {
        ws.close();
      };

      // Heartbeat
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "ping" }));
        }
      }, 30000);

      return () => clearInterval(pingInterval);
    } catch {
      // WebSocket not available (SSR)
    }
  }, [accessToken, options]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const send = useCallback((msg: WSMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  return { send };
}
