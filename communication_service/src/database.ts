import { Pool } from 'pg';
import dotenv from 'dotenv';
import path from 'path';

dotenv.config({ path: path.resolve(__dirname, '../../.env') });

const connectionString = process.env.DATABASE_URL || 'postgresql://postgres:rentora_secure_password@localhost:5432/rentora';

// Setup connection pool with schema support (substitute Python specific asyncpg prefix)
const cleanConnectionString = connectionString.replace('postgresql+asyncpg://', 'postgresql://');

const pool = new Pool({
  connectionString: cleanConnectionString,
  max: 10,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// Initialize schema on startup
const initDb = async () => {
  const client = await pool.connect();
  try {
    await client.query('CREATE SCHEMA IF NOT EXISTS communication;');
    await client.query(`
      CREATE TABLE IF NOT EXISTS communication.messages (
        id SERIAL PRIMARY KEY,
        sender_id TEXT NOT NULL,
        receiver_id TEXT NOT NULL,
        conversation_id TEXT NOT NULL,
        content TEXT NOT NULL,
        status TEXT DEFAULT 'sent',
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    `);
    await client.query('CREATE INDEX IF NOT EXISTS idx_conversation ON communication.messages(conversation_id);');
  } catch (err) {
    console.error('Error initializing communication database:', err);
  } finally {
    client.release();
  }
};

initDb();

export interface Message {
  id?: number;
  sender_id: string;
  receiver_id: string;
  conversation_id: string;
  content: string;
  status?: string;
  timestamp?: string;
}

export const saveMessage = async (msg: Message): Promise<any> => {
  const query = `
    INSERT INTO communication.messages (sender_id, receiver_id, conversation_id, content, status)
    VALUES ($1, $2, $3, $4, $5)
    RETURNING *;
  `;
  const values = [msg.sender_id, msg.receiver_id, msg.conversation_id, msg.content, msg.status || 'sent'];
  const res = await pool.query(query, values);
  return res.rows[0];
};

export const getMessages = async (conversationId: string, limit = 50, offset = 0): Promise<Message[]> => {
  const query = `
    SELECT id, sender_id, receiver_id, conversation_id, content, status, timestamp::text as timestamp
    FROM communication.messages 
    WHERE conversation_id = $1 
    ORDER BY timestamp DESC 
    LIMIT $2 OFFSET $3;
  `;
  const res = await pool.query(query, [conversationId, limit, offset]);
  return res.rows.reverse();
};

export default pool;
