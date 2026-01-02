/**
 * Fluency Evaluation Types
 * Mirrors the backend fluency service API models
 */

// Individual analyzer metrics

export interface PronunciationMetrics {
  score: number;
  phoneme_errors: PhonemeError[];
  catalan_markers: string[];
  catalan_marker_score: number;
  intonation_score: number;
  stress_score: number;
  confidence_based_score: number;
}

export interface PhonemeError {
  word: string;
  type: string; // rolled_r, jota, ene, ll_sound, theta
  confidence: number;
  suggestion: string;
}

export interface TemporalMetrics {
  score: number;
  speaking_rate_wpm: number;
  target_rate_wpm: number;
  pause_analysis: PauseAnalysis;
  response_latency_ms: number | null;
  total_speech_duration_ms: number;
  total_pause_duration_ms: number;
}

export interface PauseAnalysis {
  count: number;
  avg_duration_ms: number;
  short_pauses: number;
  medium_pauses: number;
  long_pauses: number;
  very_long_pauses: number;
  placement_score: number;
}

export interface LexicalMetrics {
  score: number;
  wer: number; // Word Error Rate (0-1)
  catalan_expressions_used: string[];
  catalan_expressions_expected: string[];
  spanish_slang_used: string[];
  expected_phrases_hit: number;
  expected_phrases_total: number;
  vocabulary_level: 'beginner' | 'intermediate' | 'advanced';
}

export interface DisfluencyMetrics {
  score: number; // Lower is better (fewer disfluencies)
  filled_pauses: string[];
  filled_pause_count: number;
  repetitions: number;
  self_corrections: number;
  false_starts: number;
  disfluency_rate: number; // per minute
}

export interface ProsodicMetrics {
  score: number;
  pitch_range_hz: [number, number];
  pitch_mean_hz: number;
  pitch_std_hz: number;
  emotional_congruence: number;
  volume_consistency: number;
  rhythm_score: number;
  pvi: number; // Pairwise Variability Index
}

export interface CommunicativeMetrics {
  score: number;
  register_match: 'formal' | 'informal' | 'mixed' | 'neutral';
  register_appropriateness: number;
  discourse_markers_used: string[];
  discourse_markers_expected: string[];
  turn_taking_score: number;
}

// Aggregated metrics breakdown
export interface MetricsBreakdown {
  pronunciation_accuracy: PronunciationMetrics;
  temporal_metrics: TemporalMetrics;
  lexical_accuracy: LexicalMetrics;
  disfluency_detection: DisfluencyMetrics;
  prosodic_quality: ProsodicMetrics;
  communicative_competence: CommunicativeMetrics;
}

// Feedback structure
export interface FeedbackResult {
  summary: string;
  strengths: string[];
  improvements: string[];
  practice_suggestions: string[];
}

// Transcript with word-level timing
export interface WordTimestamp {
  word: string;
  start: number;
  end: number;
  confidence: number;
}

export interface TranscriptResult {
  text: string;
  words: WordTimestamp[];
  language: string;
  duration_seconds: number;
}

// Full API response
export interface FluencyResponse {
  fluency_score: number;
  level_assessment: 'Native-like' | 'Proficient' | 'Developing' | 'Needs work';
  cefr_level: 'A1' | 'A2' | 'B1' | 'B2' | 'C1' | 'C2';
  metrics: MetricsBreakdown;
  transcript: TranscriptResult;
  feedback: FeedbackResult;
  processing_time_ms: number;
  model_version: string;
}

// 3 Pillar Scores (aggregated for user display)
export interface ThreePillarScores {
  accuracy: number;  // Pronunciation (25%) + Lexical (15%)
  flow: number;      // Temporal (20%) + Disfluency inverted (20%)
  expression: number; // Prosodic (10%) + Communicative (10%)
}

// Curated actionable highlights for user display
export interface ActionableHighlights {
  // Accuracy pillar
  pronunciationTips: PronunciationTip[];
  vocabularyAccuracy: number; // WER inverted to percentage (0-100)
  phrasesMatched: { hit: number; total: number };

  // Flow pillar
  speakingPace: {
    current_wpm: number;
    target_wpm: number;
    assessment: 'too_slow' | 'good' | 'too_fast';
  };
  fillerWordCount: number;
  fillerWordsUsed: string[];
  pauseQuality: {
    avg_duration_ms: number;
    assessment: 'too_many_long' | 'good' | 'natural';
  };

  // Expression pillar
  emotionalRange: 'monotone' | 'moderate' | 'expressive';
  discourseMarkersUsed: string[];
  registerMatch: {
    detected: string;
    appropriate: boolean;
  };
}

export interface PronunciationTip {
  sound: string; // e.g., "rolled R", "ñ"
  word: string;  // example word
  suggestion: string;
}

// Historical data for trend charts
export interface DailyMetrics {
  date: string;
  accuracy: number;
  flow: number;
  expression: number;
  fluency: number;
  session_count: number;
  practice_minutes: number;
}

// User vocabulary tracking
export interface VocabularyWord {
  word: string;
  translation?: string;
  usage_count: number;
  first_seen_at: string;
  last_used_at: string;
  is_new: boolean; // true if first seen in recent session
}

// Session evaluation stored in database
export interface SessionEvaluation {
  id: string;
  user_id: string;
  session_id: string;
  scenario?: string;
  language?: string;

  // Scores
  fluency_score: number;
  level_assessment: string;
  cefr_level?: string;
  accuracy_score: number;
  flow_score: number;
  expression_score: number;

  // Raw metrics (JSONB)
  pronunciation_metrics: PronunciationMetrics;
  temporal_metrics: TemporalMetrics;
  lexical_metrics: LexicalMetrics;
  disfluency_metrics: DisfluencyMetrics;
  prosodic_metrics: ProsodicMetrics;
  communicative_metrics: CommunicativeMetrics;

  // Feedback
  feedback_summary: string;
  strengths: string[];
  improvements: string[];
  practice_suggestions: string[];

  // Transcript
  transcript: string;
  transcript_duration_seconds: number;

  // Vocabulary
  words_used: string[];
  new_words: string[];

  // Metadata
  processing_time_ms: number;
  created_at: string;
}

// API request options
export interface EvaluationOptions {
  expectedResponse?: string;
  scenario?: string;
  userLevel?: string;
  language?: string;
  contextBefore?: string[];
  detailedFeedback?: boolean;
}
