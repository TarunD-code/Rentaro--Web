import express from 'express';
import { createServer } from 'http';
import { Server } from 'socket.io';
import cors from 'cors';
import jwt from 'jsonwebtoken';
import dotenv from 'dotenv';
import { saveMessage, getMessages } from './database';
import { initiateMaskedCall } from './services/TwilioService';

dotenv.config();

const app = express();
const httpServer = createServer(app);
const io = new Server(httpServer, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

const PORT = process.env.PORT || 8007;
const SECRET_KEY = process.env.JWT_SECRET || "RENTORA_SUPER_SECRET_KEY";

app.use(cors());
app.use(express.json());

// Auth Middleware
io.use((socket, next) => {
  const token = socket.handshake.auth.token;
  if (!token) return next(new Error("Authentication error"));
  
  jwt.verify(token, SECRET_KEY, (err: any, decoded: any) => {
    if (err) return next(new Error("Authentication error"));
    (socket as any).user = decoded;
    next();
  });
});

// REST Endpoints
app.get('/messages/:conversationId', (req, res) => {
  const { conversationId } = req.params;
  const { limit, offset } = req.query;
  const history = getMessages(conversationId, Number(limit) || 50, Number(offset) || 0);
  res.json(history);
});

app.post('/calls/initiate', async (req, res) => {
  const { from, to } = req.body;
  const result = await initiateMaskedCall(from, to);
  res.json(result);
});

// WebSocket Events
io.on('connection', (socket) => {
  const user = (socket as any).user;
  console.log(`User connected: ${user.sub} (${socket.id})`);

  socket.on('join_room', (room) => {
    socket.join(room);
    console.log(`User ${user.sub} joined room: ${room}`);
  });

  socket.on('send_message', (data) => {
    const { receiver_id, conversation_id, content } = data;
    const message = {
      sender_id: user.sub,
      receiver_id,
      conversation_id,
      content,
      status: 'sent',
      timestamp: new Date().toISOString()
    };

    // Persist to DB
    saveMessage(message);

    // Broadcast to the room (both sender and receiver should be in it)
    io.to(conversation_id).emit('receive_message', message);
  });

  socket.on('typing', (data) => {
    const { conversation_id } = data;
    socket.to(conversation_id).emit('user_typing', { user: user.sub });
  });

  socket.on('disconnect', () => {
    console.log(`User disconnected: ${user.sub}`);
  });
});

httpServer.listen(PORT, () => {
  console.log(`Communication service running on port ${PORT}`);
});
