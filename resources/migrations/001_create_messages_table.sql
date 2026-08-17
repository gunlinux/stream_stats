-- Create messages table
-- Migration: 001_create_messages_table.sql
-- __transactional__ = False

CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    body TEXT NOT NULL,
    source int NOT NULL CHECK (source IN (0, 1)), -- 0 twitch, 1 youtube
    message_id VARCHAR(255) NOT NULL,
    author_id VARCHAR(255) NOT NULL,
    stream_id VARCHAR(255) NOT NULL,
    channel_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Make stream-ingestion retries idempotent: a (source, message_id) pair maps
-- to at most one stored message.
CREATE UNIQUE INDEX uq_messages_source_message_id
    ON messages (source, message_id);
