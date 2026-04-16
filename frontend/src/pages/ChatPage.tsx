import React, { useState } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { 
  Typography, Container, Grid, Card, CardContent, Divider, 
  Avatar, List, ListItem, ListItemAvatar, ListItemText, ListItemButton 
} from '@mui/material';
import ChatComponent from '../components/ChatComponent';
import { motion } from 'framer-motion';

const ChatPage: React.FC = () => {
  const { receiverId } = useParams<{ receiverId: string }>();
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const initialReceiver = receiverId || searchParams.get('to') || 'support@rentora.com';
  
  // In a real app, this comes from an Auth Context
  const [currentUser] = useState({
    email_or_phone: localStorage.getItem('userEmail') || 'tenant@rentora.com',
    role: localStorage.getItem('userRole') || 'tenant'
  });

  const [activeChat, setActiveChat] = useState(initialReceiver);

  const CONTACTS = [
    { email: 'support@rentora.com', name: 'Rentora Support', role: 'system' },
    { email: 'owner@rentora.com', name: 'Property Owner', role: 'owner' },
    { email: 'maintenance@rentora.com', name: 'Maintenance Desk', role: 'vendor' },
  ];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Grid container spacing={3}>
        {/* Sidebar */}
        <Grid size={{ xs: 12, md: 4 }}>
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}>
            <Card sx={{ borderRadius: 4, height: '600px', display: 'flex', flexDirection: 'column' }}>
              <CardContent>
                <Typography variant="h5" fontWeight={800} gutterBottom>Messages</Typography>
                <Divider sx={{ mb: 2 }} />
                <List>
                  {CONTACTS.filter(c => c.email !== currentUser.email_or_phone).map((contact) => (
                    <ListItem key={contact.email} disablePadding sx={{ mb: 1 }}>
                      <ListItemButton 
                        onClick={() => setActiveChat(contact.email)}
                        selected={activeChat === contact.email}
                        sx={{ borderRadius: 2 }}
                      >
                        <ListItemAvatar>
                          <Avatar sx={{ bgcolor: contact.role === 'system' ? 'secondary.main' : 'primary.main' }}>
                            {contact.name[0]}
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText 
                          primary={contact.name} 
                          secondary={contact.email}
                          primaryTypographyProps={{ fontWeight: activeChat === contact.email ? 700 : 500 }}
                        />
                      </ListItemButton>
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>

        {/* Chat Area */}
        <Grid size={{ xs: 12, md: 8 }}>
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}>
            <ChatComponent currentUser={currentUser} receiverId={activeChat} />
          </motion.div>
        </Grid>
      </Grid>
    </Container>
  );
};

export default ChatPage;
