import React, { useState, useEffect, useRef } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  TextField, 
  IconButton, 
  Avatar, 
  useTheme, 
  alpha,
  Divider
} from '@mui/material';
import { Send, Close, Check, DoneAll } from '@mui/icons-material';


interface Message {
  id: number;
  sender_id: string;
  receiver_id: string;
  property_id: number;
  body: string;
  is_read: boolean;
  created_at: string;
}

interface ChatBoxProps {
  propertyId: number;
  hostId: string;
  hostName: string;
  onClose: () => void;
}

const ChatBox: React.FC<ChatBoxProps> = ({ propertyId, hostId, hostName, onClose }) => {
  const theme = useTheme();
  const [messages, setMessages] = useState<Message[]>([]);
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);
  
  const currentUserId = localStorage.getItem('userId') || 'mockUser'; 

  useEffect(() => {
    // Poll or fetch messages initially
    const fetchMessages = async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await fetch(`${import.meta.env.VITE_API_URL}/profile/messages/${hostId}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setMessages(data);
        }
      } catch (err) {
        console.error("Failed to load messages", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchMessages();
    const interval = setInterval(fetchMessages, 5000); // Poll every 5s logic
    return () => clearInterval(interval);
  }, [hostId]);

  useEffect(() => {
    // Auto-scroll to bottom
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!text.trim()) return;
    
    // Optimistic UI updates
    const tempMsg: Message = {
      id: Date.now(),
      sender_id: currentUserId,
      receiver_id: hostId,
      property_id: propertyId,
      body: text,
      is_read: false,
      created_at: new Date().toISOString()
    };
    setMessages(prev => [...prev, tempMsg]);
    setText('');
    
    try {
      const token = localStorage.getItem('token');
      await fetch(`${import.meta.env.VITE_API_URL}/profile/messages`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          receiver_id: hostId,
          property_id: propertyId,
          body: tempMsg.body
        })
      });
    } catch (err) {
      console.error("Failed to send message", err);
    }
  };

  return (
    <Paper 
      elevation={6}
      sx={{ 
        position: 'fixed',
        bottom: 24,
        right: 24,
        width: 360,
        height: 500,
        borderRadius: 4,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        zIndex: 1300
      }}
    >
      <Box 
        sx={{ 
          p: 2, 
          bgcolor: 'primary.main', 
          color: '#fff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}
      >
        <Box display="flex" alignItems="center" gap={1.5}>
          <Avatar sx={{ width: 32, height: 32 }}>{hostName[0]}</Avatar>
          <Box>
            <Typography variant="subtitle2" fontWeight={700}>{hostName}</Typography>
            <Typography variant="caption" sx={{ opacity: 0.8 }}>Online</Typography>
          </Box>
        </Box>
        <IconButton size="small" onClick={onClose} sx={{ color: '#fff' }}>
          <Close fontSize="small" />
        </IconButton>
      </Box>

      <Box sx={{ flex: 1, p: 2, overflowY: 'auto', bgcolor: alpha(theme.palette.background.default, 0.5) }}>
        {loading ? (
          <Typography variant="caption" color="text.secondary" align="center" display="block">Loading history...</Typography>
        ) : messages.length === 0 ? (
          <Typography variant="caption" color="text.secondary" align="center" display="block" sx={{ mt: 10 }}>
            Start a conversation with {hostName}.
          </Typography>
        ) : (
          messages.map((m, i) => {
            const isMe = m.sender_id === currentUserId;
            return (
              <Box 
                key={m.id || i} 
                display="flex" 
                justifyContent={isMe ? 'flex-end' : 'flex-start'}
                mb={2}
              >
                <Box 
                  sx={{ 
                    maxWidth: '80%',
                    bgcolor: isMe ? 'primary.main' : 'background.paper',
                    color: isMe ? '#fff' : 'text.primary',
                    p: 1.5,
                    borderRadius: 3,
                    borderTopRightRadius: isMe ? 0 : undefined,
                    borderTopLeftRadius: !isMe ? 0 : undefined,
                    boxShadow: theme.shadows[1]
                  }}
                >
                  <Typography variant="body2">{m.body}</Typography>
                  <Box display="flex" justifyContent="flex-end" alignItems="center" gap={0.5} mt={0.5}>
                    <Typography variant="caption" sx={{ opacity: 0.7, fontSize: '0.65rem' }}>
                      {new Date(m.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    </Typography>
                    {isMe && (
                      m.is_read ? <DoneAll sx={{ fontSize: 14, color: '#4CAF50' }} /> : <Check sx={{ fontSize: 14, opacity: 0.7 }} />
                    )}
                  </Box>
                </Box>
              </Box>
            )
          })
        )}
        <div ref={bottomRef} />
      </Box>

      <Divider />
      
      <Box sx={{ p: 1.5, bgcolor: 'background.paper', display: 'flex', gap: 1 }}>
        <TextField 
          fullWidth
          size="small"
          placeholder="Type a message..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          sx={{ '& .MuiOutlinedInput-root': { borderRadius: 6 } }}
        />
        <IconButton color="primary" onClick={handleSend} disabled={!text.trim()}>
          <Send />
        </IconButton>
      </Box>
    </Paper>
  );
};

export default ChatBox;
