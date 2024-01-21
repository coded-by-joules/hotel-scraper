import { reactive } from "vue";
import { io } from "socket.io-client";

export const state = reactive({
  connected: false,
  messageEvents: [],
});

// "undefined" means the URL will be computed from the `window.location` object
const URL = process.env.NODE_ENV === "production" ? undefined : "http://localhost:5000";

export const socket = io(URL);

socket.on("connect", () => {
  state.connected = true;
  socket.emit("client_connected");
});

socket.on("disconnect", () => {
  state.connected = false;
});

socket.on("message", (...args) => {
  state.messageEvents.push(args);
});