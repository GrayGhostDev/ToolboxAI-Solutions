import { configureStore } from "@reduxjs/toolkit";
import { TypedUseSelectorHook, useDispatch, useSelector } from "react-redux";
import uiReducer from "./slices/uiSlice";
import userReducer from "./slices/userSlice";
import gamificationReducer from "./slices/gamificationSlice";
import dashboardReducer from "./slices/dashboardSlice";
import classesReducer from "./slices/classesSlice";
import lessonsReducer from "./slices/lessonsSlice";
import assessmentsReducer from "./slices/assessmentsSlice";
import messagesReducer from "./slices/messagesSlice";
import progressReducer from "./slices/progressSlice";
import analyticsReducer from "./slices/analyticsSlice";
import complianceReducer from "./slices/complianceSlice";
import realtimeReducer from "./slices/realtimeSlice";
import robloxReducer from "./slices/robloxSlice";
import { createWebSocketMiddleware, setupWebSocketListeners } from "./middleware/websocketMiddleware";
import { PusherService } from "../services/pusher";

// Create Pusher service instance (using WebSocket name for backward compatibility)
const webSocketService = PusherService.getInstance();

export const store = configureStore({
  reducer: {
    ui: uiReducer,
    user: userReducer,
    gamification: gamificationReducer,
    dashboard: dashboardReducer,
    classes: classesReducer,
    lessons: lessonsReducer,
    assessments: assessmentsReducer,
    messages: messagesReducer,
    progress: progressReducer,
    analytics: analyticsReducer,
    compliance: complianceReducer,
    realtime: realtimeReducer,
    roblox: robloxReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignore these action types
        ignoredActions: [
          "ui/addNotification",
          "realtime/setWebSocketState",
          "realtime/setWebSocketError",
          "realtime/addRealtimeMessage",
          "realtime/addSystemNotification",
          "realtime/updateContentProgress",
          "realtime/setContentComplete",
        ],
        // Ignore these field paths in all actions
        ignoredActionPaths: ["payload.timestamp", "payload.lastSeen", "payload.startedAt"],
        // Ignore these paths in the state
        ignoredPaths: [
          "ui.notifications",
          "realtime.websocket.error.timestamp",
          "realtime.messages",
          "realtime.notifications",
          "realtime.userPresence",
          "realtime.classrooms",
          "realtime.leaderboard.lastUpdated",
        ],
      },
    }).concat(createWebSocketMiddleware(webSocketService)),
});

// Setup WebSocket listeners after store is created
setupWebSocketListeners(webSocketService, store.dispatch);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// Typed hooks for use throughout the app
export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;