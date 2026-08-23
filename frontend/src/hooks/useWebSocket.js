import { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "../store/authStore";
import { useToast } from "../components/common/Toast";

export function useWebSocket() {
  const user = useAuthStore((state) => state.user);
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();
  const toast = useToast();
  const socketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  useEffect(() => {
    if (!user?.id || !token) {
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
      return;
    }

    let isSubscribed = true;

    const connect = () => {
      try {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const host = import.meta.env.VITE_WS_URL || "localhost:8000";
        const wsUrl = `${protocol}//${host}/ws/${user.id}?token=${encodeURIComponent(token)}`;

        const socket = new WebSocket(wsUrl);
        socketRef.current = socket;

        socket.onopen = () => {
          // Connected
        };

        socket.onmessage = (event) => {
          if (!isSubscribed) return;
          try {
            const data = JSON.parse(event.data);
            const type = data.type || "";

            if (type === "BOOKING_CREATED" || type === "SESSION_BOOKED") {
              toast.success(
                data.message || "A new peer mentoring session has been booked!",
                "New Booking 📌"
              );
              queryClient.invalidateQueries({ queryKey: ["upcomingSessions"] });
              queryClient.invalidateQueries({ queryKey: ["notifications"] });
              queryClient.invalidateQueries({ queryKey: ["notifications", "unread"] });
              queryClient.invalidateQueries({ queryKey: ["wallet"] });
              queryClient.invalidateQueries({ queryKey: ["mentorBookableSlots"] });
            } else if (type === "SESSION_STARTED") {
              toast.info(
                data.message || "Your session is now LIVE! 🚀",
                "Session Started"
              );
              if (data.session_id) {
                queryClient.invalidateQueries({ queryKey: ["sessionDetail", data.session_id] });
                queryClient.invalidateQueries({ queryKey: ["sessionTimeline", data.session_id] });
                queryClient.invalidateQueries({ queryKey: ["sessionPresence", data.session_id] });
              }
              queryClient.invalidateQueries({ queryKey: ["upcomingSessions"] });
            } else if (type === "BOOKING_CANCELLED" || type === "SESSION_CANCELLED") {
              toast.warning(
                data.message || "A scheduled session was cancelled.",
                "Session Cancelled ⚠️"
              );
              if (data.session_id) {
                queryClient.invalidateQueries({ queryKey: ["sessionDetail", data.session_id] });
                queryClient.invalidateQueries({ queryKey: ["sessionTimeline", data.session_id] });
                queryClient.invalidateQueries({ queryKey: ["sessionPresence", data.session_id] });
              }
              queryClient.invalidateQueries({ queryKey: ["upcomingSessions"] });
              queryClient.invalidateQueries({ queryKey: ["cancelledSessions"] });
              queryClient.invalidateQueries({ queryKey: ["notifications"] });
              queryClient.invalidateQueries({ queryKey: ["notifications", "unread"] });
              queryClient.invalidateQueries({ queryKey: ["wallet"] });
              queryClient.invalidateQueries({ queryKey: ["mentorBookableSlots"] });
            } else if (type === "SESSION_COMPLETED") {
              toast.success(
                data.message || "Your session has been marked completed!",
                "Session Completed 🎉"
              );
              if (data.session_id) {
                queryClient.invalidateQueries({ queryKey: ["sessionDetail", data.session_id] });
                queryClient.invalidateQueries({ queryKey: ["sessionTimeline", data.session_id] });
                queryClient.invalidateQueries({ queryKey: ["sessionPresence", data.session_id] });
                queryClient.invalidateQueries({ queryKey: ["sessionIntelligence", data.session_id] });
              }
              queryClient.invalidateQueries({ queryKey: ["upcomingSessions"] });
              queryClient.invalidateQueries({ queryKey: ["completedSessions"] });
              queryClient.invalidateQueries({ queryKey: ["activities"] });
              queryClient.invalidateQueries({ queryKey: ["learning-activities"] });
              queryClient.invalidateQueries({ queryKey: ["streak"] });
              queryClient.invalidateQueries({ queryKey: ["heatmap"] });
              queryClient.invalidateQueries({ queryKey: ["analytics"] });
              queryClient.invalidateQueries({ queryKey: ["notifications"] });
              queryClient.invalidateQueries({ queryKey: ["notifications", "unread"] });
              queryClient.invalidateQueries({ queryKey: ["wallet"] });
            } else if (type === "PARTICIPANT_JOINED") {
              if (data.session_id) {
                queryClient.invalidateQueries({ queryKey: ["sessionPresence", data.session_id] });
                queryClient.invalidateQueries({ queryKey: ["sessionTimeline", data.session_id] });
              }
              toast.info(data.message || "A participant joined the session workspace.", "Participant Joined 🟢");
            } else if (type === "PARTICIPANT_LEFT") {
              if (data.session_id) {
                queryClient.invalidateQueries({ queryKey: ["sessionPresence", data.session_id] });
                queryClient.invalidateQueries({ queryKey: ["sessionTimeline", data.session_id] });
              }
            } else if (type === "SESSION_NOTE_UPDATED") {
              if (data.session_id) {
                queryClient.invalidateQueries({ queryKey: ["sessionNotes", data.session_id] });
                queryClient.invalidateQueries({ queryKey: ["sessionTimeline", data.session_id] });
              }
            } else if (type === "SESSION_TOPIC_ADDED") {
              if (data.session_id) {
                queryClient.invalidateQueries({ queryKey: ["sessionTopics", data.session_id] });
                queryClient.invalidateQueries({ queryKey: ["sessionTimeline", data.session_id] });
              }
              toast.info(data.message || "Discussion topic tagged.", "Topic Added 🏷️");
            } else if (type === "ACTION_ITEM_CREATED" || type === "ACTION_ITEM_UPDATED" || type === "ACTION_ITEM_DELETED") {
              if (data.session_id) {
                queryClient.invalidateQueries({ queryKey: ["sessionActionItems", data.session_id] });
                queryClient.invalidateQueries({ queryKey: ["sessionTimeline", data.session_id] });
              }
              if (type === "ACTION_ITEM_CREATED") {
                toast.info(data.message || "New action item created.", "Action Item 📌");
              }
            } else if (type === "REQUEST_RECEIVED") {
              toast.info(
                data.message || "You received a new session request.",
                "New Request 📌"
              );
              queryClient.invalidateQueries({ queryKey: ["notifications"] });
              queryClient.invalidateQueries({ queryKey: ["notifications", "unread"] });
            } else if (type === "REQUEST_ACCEPTED" || type === "REQUEST_REJECTED") {
              toast.info(
                data.message || "Your session request status updated.",
                "Request Update"
              );
              queryClient.invalidateQueries({ queryKey: ["notifications"] });
              queryClient.invalidateQueries({ queryKey: ["notifications", "unread"] });
            } else if (data.message) {
              toast.info(data.message, "Notification");
              queryClient.invalidateQueries({ queryKey: ["notifications"] });
              queryClient.invalidateQueries({ queryKey: ["notifications", "unread"] });
            }
          } catch (err) {
            // Non-json or debug messages
          }
        };

        socket.onclose = (e) => {
          if (isSubscribed && e.code !== 1008) {
            // Reconnect after 3s if not a policy violation
            reconnectTimeoutRef.current = setTimeout(() => {
              if (isSubscribed) connect();
            }, 3000);
          }
        };

        socket.onerror = () => {
          // Socket error
        };
      } catch (err) {
        // Connection error
      }
    };

    connect();

    return () => {
      isSubscribed = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
    };
  }, [user?.id, token, queryClient, toast]);

  return socketRef;
}
