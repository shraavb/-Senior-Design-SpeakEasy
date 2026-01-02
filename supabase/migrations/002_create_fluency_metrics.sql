-- Migration: Create fluency metrics tables for storing evaluation results
-- This supports the 3-pillar metrics system (Accuracy, Flow, Expression)

-- Add new columns to user_profiles for latest pillar scores
ALTER TABLE public.user_profiles
ADD COLUMN IF NOT EXISTS latest_accuracy_score NUMERIC(5,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS latest_flow_score NUMERIC(5,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS latest_expression_score NUMERIC(5,2) DEFAULT 0;

-- Table: session_evaluations
-- Stores individual session evaluation results with all metrics
CREATE TABLE IF NOT EXISTS public.session_evaluations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  session_id UUID NOT NULL,
  scenario VARCHAR(100),
  language VARCHAR(50) DEFAULT 'es-ES',

  -- Overall scores
  fluency_score NUMERIC(5,2) NOT NULL CHECK (fluency_score >= 0 AND fluency_score <= 100),
  level_assessment VARCHAR(50),
  cefr_level VARCHAR(5),

  -- 3 Pillar Scores (calculated from metrics)
  accuracy_score NUMERIC(5,2) CHECK (accuracy_score >= 0 AND accuracy_score <= 100),
  flow_score NUMERIC(5,2) CHECK (flow_score >= 0 AND flow_score <= 100),
  expression_score NUMERIC(5,2) CHECK (expression_score >= 0 AND expression_score <= 100),

  -- Raw metrics from analyzers (JSONB for flexibility)
  pronunciation_metrics JSONB,
  temporal_metrics JSONB,
  lexical_metrics JSONB,
  disfluency_metrics JSONB,
  prosodic_metrics JSONB,
  communicative_metrics JSONB,

  -- Feedback from evaluation
  feedback_summary TEXT,
  strengths TEXT[],
  improvements TEXT[],
  practice_suggestions TEXT[],

  -- Transcript data
  transcript TEXT,
  transcript_duration_seconds NUMERIC(10,2),

  -- Vocabulary tracking
  words_used TEXT[],
  new_words TEXT[],

  -- Metadata
  processing_time_ms INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Indexes for session_evaluations
CREATE INDEX IF NOT EXISTS idx_session_evaluations_user_id
  ON public.session_evaluations(user_id);
CREATE INDEX IF NOT EXISTS idx_session_evaluations_created_at
  ON public.session_evaluations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_session_evaluations_user_created
  ON public.session_evaluations(user_id, created_at DESC);

-- Table: user_metrics_daily
-- Aggregated daily metrics for trend charts
CREATE TABLE IF NOT EXISTS public.user_metrics_daily (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  date DATE NOT NULL,

  -- 3 Pillar averages
  avg_accuracy_score NUMERIC(5,2),
  avg_flow_score NUMERIC(5,2),
  avg_expression_score NUMERIC(5,2),
  avg_fluency_score NUMERIC(5,2),

  -- Session stats
  session_count INTEGER DEFAULT 0,
  total_practice_minutes NUMERIC(10,2) DEFAULT 0,

  -- Actionable metrics averages
  avg_speaking_rate_wpm NUMERIC(6,2),
  avg_pause_duration_ms NUMERIC(10,2),
  avg_filler_word_count NUMERIC(5,2),

  -- Vocabulary stats
  new_words_count INTEGER DEFAULT 0,
  total_words_used INTEGER DEFAULT 0,

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

  UNIQUE(user_id, date)
);

-- Index for user_metrics_daily
CREATE INDEX IF NOT EXISTS idx_user_metrics_daily_user_date
  ON public.user_metrics_daily(user_id, date DESC);

-- Table: user_vocabulary
-- Track all unique words a user has ever used
CREATE TABLE IF NOT EXISTS public.user_vocabulary (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  word VARCHAR(100) NOT NULL,
  translation VARCHAR(200),

  -- Usage tracking
  usage_count INTEGER DEFAULT 1,
  first_seen_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  last_used_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

  -- Word metadata
  part_of_speech VARCHAR(50),
  is_from_lesson BOOLEAN DEFAULT false,

  UNIQUE(user_id, word)
);

-- Indexes for user_vocabulary
CREATE INDEX IF NOT EXISTS idx_user_vocabulary_user_id
  ON public.user_vocabulary(user_id);
CREATE INDEX IF NOT EXISTS idx_user_vocabulary_first_seen
  ON public.user_vocabulary(user_id, first_seen_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_vocabulary_usage
  ON public.user_vocabulary(user_id, usage_count DESC);

-- Enable Row Level Security on all tables
ALTER TABLE public.session_evaluations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_metrics_daily ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_vocabulary ENABLE ROW LEVEL SECURITY;

-- RLS Policies for session_evaluations
CREATE POLICY "Users can view own session evaluations"
  ON public.session_evaluations FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own session evaluations"
  ON public.session_evaluations FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- RLS Policies for user_metrics_daily
CREATE POLICY "Users can view own daily metrics"
  ON public.user_metrics_daily FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own daily metrics"
  ON public.user_metrics_daily FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own daily metrics"
  ON public.user_metrics_daily FOR UPDATE
  USING (auth.uid() = user_id);

-- RLS Policies for user_vocabulary
CREATE POLICY "Users can view own vocabulary"
  ON public.user_vocabulary FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own vocabulary"
  ON public.user_vocabulary FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own vocabulary"
  ON public.user_vocabulary FOR UPDATE
  USING (auth.uid() = user_id);

-- Trigger to update updated_at on user_metrics_daily
CREATE OR REPLACE TRIGGER on_user_metrics_daily_updated
  BEFORE UPDATE ON public.user_metrics_daily
  FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();
