import express from "express";
import bodyParser from "body-parser";
import cors from "cors";
import { WebSocketServer } from "ws";

const app = express();
const PORT = process.env.PORT || 4000;
const WS_PORT = process.env.WS_PORT || 8080;

app.use(cors());
app.use(bodyParser.json({ limit: "1mb" }));

// Simple health
app.get("/", (req, res) => res.send({ status: "realtime server ok" }));

// Keep an in-memory list of connected ws clients from the WSS
let wss;
const clients = new Set();

// Create WebSocket server
wss = new WebSocketServer({ port: WS_PORT });

wss.on("connection", (socket) => {
  console.log("WS client connected");
  clients.add(socket);

  socket.on("close", () => {
    clients.delete(socket);
    console.log("WS client disconnected");
  });

  socket.on("message", (msg) => {
    // Optionally accept direct socket messages from clients (not used here)
    console.log("Received from client:", msg.toString());
  });
});

function broadcastToClients(obj) {
  const payload = JSON.stringify(obj);
  for (const c of clients) {
    if (c.readyState === c.OPEN) {
      try {
        c.send(payload);
      } catch (err) {
        console.error("Send error", err);
      }
    }
  }
}

// Endpoint for FastAPI to POST updates which we broadcast to WebSocket clients
app.post("/broadcast", (req, res) => {
  const body = req.body || {};
  // Basic validation
  if (!body || !body.type) {
    // we still broadcast raw body
  }
  broadcastToClients(body);
  res.json({ status: "broadcasted", received: body });
});

// Optional example: return last known buses if node server tracked them
app.post("/echo", (req, res) => {
  res.json({ echo: req.body });
});

app.listen(PORT, () => {
  console.log(`Realtime HTTP API listening on http://localhost:${PORT}`);
});
console.log(`WebSocket server running on ws://localhost:${WS_PORT}`);
