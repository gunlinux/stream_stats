-- Create messages table
-- Migration: 001_messages_table.sql
-- __transactional__ = False

CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    body TEXT,
    source int, -- 0 twitch, 1 youtube,
    message_id VARCHAR(255),
    author_id VARCHAR(255),
    stream_id VARCHAR(255),
    channel_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

