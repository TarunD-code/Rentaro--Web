import Database from 'better-sqlite3';
import path from 'path';

const dbPath = path.resolve(__dirname, '../../rentora_communication.db');
const db = new Database(dbPath);

// Initialize schema
db.exec(`
  CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id TEXT NOT NULL,
    receiver_id TEXT NOT NULL,
    conversation_id TEXT NOT NULL,
    content TEXT NOT NULL,
    status TEXT DEFAULT 'sent',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
  );
  CREATE INDEX IF NOT EXISTS idx_conversation ON messages(conversation_id);
`);

export interface Message {
  id?: number;
  sender_id: string;
  receiver_id: string;
  conversation_id: string;
  content: string;
  status?: string;
  timestamp?: string;
}

export const saveMessage = (msg: Message) => {
  const stmt = db.prepare(`
    INSERT INTO messages (sender_id, receiver_id, conversation_id, content, status)
    VALUES (?, ?, ?, ?, ?)
  `);
  return stmt.run(msg.sender_id, msg.receiver_id, msg.conversation_id, msg.content, msg.status || 'sent');
};

export const getMessages = (conversationId: string, limit = 50, offset = 0) => {
  const stmt = db.prepare(`
    SELECT * FROM messages 
    WHERE conversation_id = ? 
    ORDER BY timestamp DESC 
    LIMIT ? OFFSET ?
  `);
  return stmt.all(conversationId, limit, offset).reverse();
};

export default db;
