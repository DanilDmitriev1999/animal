-- AICODE-NOTE: Core relational schema for AI Learning platform
-- Entities mirror the proposed frontend stores and future backend services.

BEGIN;

-- Namespacing
CREATE SCHEMA IF NOT EXISTS public;
SET search_path TO public;

-- Users (guest via deviceId until auth is implemented)
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  device_id TEXT UNIQUE NOT NULL,
  name TEXT,
  settings_json JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Tracks catalog (program definition)
CREATE TABLE IF NOT EXISTS tracks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  goal TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Roadmap items per track
CREATE TABLE IF NOT EXISTS track_roadmap_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  track_id UUID NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
  position INT NOT NULL,
  text TEXT NOT NULL,
  done BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_track_roadmap_items_track_pos ON track_roadmap_items(track_id, position);

-- LLM chat templates (global, per-track, and flow-specific like createTrack)
CREATE TYPE template_scope AS ENUM ('global', 'track', 'createTrack');

CREATE TABLE IF NOT EXISTS chat_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scope template_scope NOT NULL,
  track_id UUID REFERENCES tracks(id) ON DELETE CASCADE,
  version TEXT NOT NULL DEFAULT 'v1',
  variables_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chat_templates_track_scope CHECK ((scope <> 'track') OR (track_id IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS idx_chat_templates_scope_track ON chat_templates(scope, track_id);

-- Track session for a user (UI-state + links to threads/synopses)
CREATE TABLE IF NOT EXISTS track_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  track_id UUID NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
  active_tab TEXT NOT NULL DEFAULT 'chat', -- chat | practice | simulation
  sidebar_visible BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, track_id)
);
CREATE INDEX IF NOT EXISTS idx_track_sessions_user ON track_sessions(user_id);

-- Chat threads: one per tab per session
CREATE TYPE chat_tab AS ENUM ('chat', 'practice', 'simulation');

CREATE TABLE IF NOT EXISTS chat_threads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES track_sessions(id) ON DELETE CASCADE,
  tab chat_tab NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (session_id, tab)
);
CREATE INDEX IF NOT EXISTS idx_chat_threads_session ON chat_threads(session_id);

-- Messages within a thread
CREATE TYPE message_role AS ENUM ('user', 'assistant', 'tool');

CREATE TABLE IF NOT EXISTS chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  thread_id UUID NOT NULL REFERENCES chat_threads(id) ON DELETE CASCADE,
  role message_role NOT NULL,
  content TEXT NOT NULL,
  meta_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_chat_messages_thread_created ON chat_messages(thread_id, created_at);

-- Synopses: one live + many snapshots per session
CREATE TYPE synopsis_origin AS ENUM ('live', 'snapshot', 'imported');

CREATE TABLE IF NOT EXISTS synopses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES track_sessions(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  items_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  origin synopsis_origin NOT NULL DEFAULT 'live',
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_synopses_session_origin ON synopses(session_id, origin);

COMMIT;


