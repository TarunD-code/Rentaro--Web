import { Kafka } from 'kafkajs';

const kafka = new Kafka({
  clientId: 'communication-service',
  brokers: ['localhost:9092']
});

const producer = kafka.producer();

export const emitMessageEvent = async (message: any) => {
  try {
    // In production, keep the producer connected. For local/demo, we connect/disconnect.
    await producer.connect();
    await producer.send({
      topic: 'message.received',
      messages: [
        { 
          key: message.receiver_id, 
          value: JSON.stringify({
            event_id: `msg-${Date.now()}`,
            event_type: 'message.received',
            payload: message,
            occurred_at: new Date().toISOString()
          }) 
        },
      ],
    });
    console.log(`Event message.received emitted for msg TO ${message.receiver_id}`);
    await producer.disconnect();
  } catch (err) {
    console.error("Failed to emit Kafka event from communication-service", err);
    // Silent fail for local dev if Kafka is missing
  }
};
