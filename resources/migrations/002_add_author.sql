-- Add author display name to messages
-- Migration: 002_add_author.sql
-- __transactional__ = False

-- The chatter's display name alongside the existing numeric author_id.
-- Existing rows get an empty string so the column can stay NOT NULL and the
-- Message entity (author: str) never reads back NULL.
ALTER TABLE messages
    ADD COLUMN author VARCHAR(255) NOT NULL DEFAULT '';
