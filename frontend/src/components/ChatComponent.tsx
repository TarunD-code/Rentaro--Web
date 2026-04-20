import React, { useState, useEffect, useRef } from 'react';
import { io, Socket } from 'socket.io-client';
import { 
  Box, TextField, Typography, Paper, List, ListItem, 
  Avatar, IconButton, CircularProgress, alpha, useTheme 
} from '@mui/material';
import { Send, Phone, FiberManualRecord } from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';

interface Message {
  sender_id: string;
  receiver_id: string;
  conversation_id: string;
  content: string;
  timestamp: string;
  status: string;
}

interface ChatComponentProps {
  currentUser: any;
  receiverId: string;
}

const ChatComponent: React.FC<ChatComponentProps> = ({ currentUser, receiverId }) => {
  const theme = useTheme();
  const [socket, setSocket] = useState<Socket | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [otherUserTyping, setOtherUserTyping] = useState(false);
  const [loading, setLoading] = useState(true);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const conversation_id = [currentUser.email_or_phone, receiverId].sort().join('_');
  const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  useEffect(() => {
    // 1. Fetch History
    const fetchHistory = async () => {
      try {
        const resp = await fetch(`${API}/communication/messages/${conversation_id}`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        if (resp.ok) {
          setMessages(await resp.json());
        }
      } catch (err) {
        console.error("Failed to fetch chat history", err);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();

    // 2. Setup Socket
    let newSocket: Socket | null = null;
    try {
      if (!currentUser?.email_or_phone) {
          console.warn("Chat session skipped: User context missing");
          return;
      }

      newSocket = io('http://localhost:8007', {
        auth: { token: localStorage.getItem('token') },
        transports: ['websocket', 'polling'],
        reconnection: true
      });

      newSocket.on('connect_error', (err) => {
        console.error("Socket Connection Error:", err.message);
      });

      newSocket.emit('join_room', conversation_id);

      newSocket.on('user_typing', (data) => {
        if (data.user !== currentUser.email_or_phone) {
          setOtherUserTyping(true);
          setTimeout(() => setOtherUserTyping(false), 3000);
        }
      });

      setSocket(newSocket);
    } catch (err) {
      console.error("Socket Initialization Failed:", err);
    }

    return () => {
      newSocket?.disconnect();
    };
  }, [conversation_id, currentUser?.email_or_phone]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, otherUserTyping]);

  const handleSendMessage = () => {
    if (!inputText.trim() || !socket) return;

    socket.emit('send_message', {
      receiver_id: receiverId,
      conversation_id,
      content: inputText
    });

    setInputText('');
  };

  const handleTyping = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputText(e.target.value);
    if (!isTyping && socket) {
      socket.emit('typing', { conversation_id });
      setIsTyping(true);
      setTimeout(() => setIsTyping(false), 2000);
    }
  };

  const handleCall = async () => {
    try {
      const resp = await fetch(`${API}/communication/calls/initiate`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}` 
        },
        body: JSON.stringify({ from: currentUser.email_or_phone, to: receiverId })
      });
      if (resp.ok) {
        alert("Masked call initiated! You will receive a call on your registered number shortly.");
      }
    } catch (err) {
      alert("Failed to initiate call masking.");
    }
  };

  if (loading) return <Box display="flex" justifyContent="center" p={4}><CircularProgress /></Box>;

  return (
    <Paper elevation={0} sx={{ 
      height: '600px', display: 'flex', flexDirection: 'column', 
      borderRadius: 4, overflow: 'hidden', border: `1px solid ${theme.palette.divider}`,
      background: alpha(theme.palette.background.paper, 0.8), backdropFilter: 'blur(10px)'
    }}>
      {/* Header */}
      <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', bgcolor: alpha(theme.palette.primary.main, 0.05), borderBottom: `1px solid ${theme.palette.divider}` }}>
        <Box display="flex" alignItems="center" gap={1.5}>
          <Avatar sx={{ bgcolor: theme.palette.primary.main }}>{receiverId[0].toUpperCase()}</Avatar>
          <Box>
            <Typography variant="subtitle1" fontWeight={700}>{receiverId}</Typography>
            <Box display="flex" alignItems="center" gap={0.5}>
              <FiberManualRecord sx={{ fontSize: 10, color: 'success.main' }} />
              <Typography variant="caption" color="text.secondary">Online</Typography>
            </Box>
          </Box>
        </Box>
        <IconButton onClick={handleCall} color="primary" sx={{ bgcolor: alpha(theme.palette.primary.main, 0.1) }}>
          <Phone />
        </IconButton>
      </Box>

      {/* Message List */}
      <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 2 }}>
        <List sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          <AnimatePresence initial={false}>
            {messages.map((msg, idx) => {
              const isMine = msg.sender_id === currentUser.email_or_phone;
              return (
                <ListItem key={idx} sx={{ 
                  display: 'flex', justifyContent: isMine ? 'flex-end' : 'flex-start',
                  p: 0
                }}>
                  <motion.div initial={{ opacity: 0, scale: 0.9, y: 10 }} animate={{ opacity: 1, scale: 1, y: 0 }}>
                    <Box sx={{ 
                      maxWidth: '80%', p: 1.5, borderRadius: isMine ? '20px 20px 4px 20px' : '20px 20px 20px 4px',
                      bgcolor: isMine ? theme.palette.primary.main : alpha(theme.palette.background.default, 0.8),
                      color: isMine ? 'white' : 'text.primary',
                      boxShadow: isMine ? `0 4px 12px ${alpha(theme.palette.primary.main, 0.3)}` : '0 2px 8px rgba(0,0,0,0.05)',
                      border: isMine ? 'none' : `1px solid ${theme.palette.divider}`
                    }}>
                      <Typography variant="body2">{msg.content}</Typography>
                      <Typography variant="caption" sx={{ display: 'block', mt: 0.5, opacity: 0.7, textAlign: 'right', fontSize: '10px' }}>
                        {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </Typography>
                    </Box>
                  </motion.div>
                </ListItem>
              );
            })}
          </AnimatePresence>
          {otherUserTyping && (
            <ListItem sx={{ p: 0 }}>
              <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic' }}>Typing...</Typography>
            </ListItem>
          )}
          <div ref={messagesEndRef} />
        </List>
      </Box>

      {/* Input */}
      <Box sx={{ p: 2, borderTop: `1px solid ${theme.palette.divider}` }}>
        <Box display="flex" gap={1}>
          <TextField
            fullWidth size="small" placeholder="Type a message..." value={inputText}
            onChange={handleTyping} onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            sx={{ '& .MuiOutlinedInput-root': { borderRadius: 10 } }}
          />
          <IconButton color="primary" onClick={handleSendMessage} disabled={!inputText.trim()}
            sx={{ bgcolor: theme.palette.primary.main, color: 'white', '&:hover': { bgcolor: theme.palette.primary.dark } }}>
            <Send />
          </IconButton>
        </Box>
      </Box>
    </Paper>
  );
};

export default ChatComponent;
