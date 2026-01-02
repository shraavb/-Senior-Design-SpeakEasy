/**
 * Fluency Evaluation Service
 * Handles API calls to fluency service, pillar score calculation, and data persistence
 */

import { supabase } from "@/integrations/supabase/client";
import type {
  FluencyResponse,
  MetricsBreakdown,
  ThreePillarScores,
  ActionableHighlights,
  PronunciationTip,
  DailyMetrics,
  SessionEvaluation,
  VocabularyWord,
  EvaluationOptions,
} from "@/types/fluency";

const FLUENCY_API_URL = import.meta.env.VITE_FLUENCY_API_URL || 'http://localhost:8001';

class FluencyService {
  /**
   * Call fluency evaluation API with audio data
   */
  async evaluateAudio(
    audioData: string, // Base64 encoded
    audioFormat: string,
    options: EvaluationOptions = {}
  ): Promise<FluencyResponse> {
    const response = await fetch(`${FLUENCY_API_URL}/api/v1/fluency/evaluate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        audio_data: audioData,
        audio_format: audioFormat,
        expected_response: options.expectedResponse,
        scenario: options.scenario,
        user_level: options.userLevel || 'B1',
        language: options.language || 'es-ES',
        context_before: options.contextBefore,
        detailed_feedback: options.detailedFeedback ?? true,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: response.statusText }));
      throw new Error(error.error || `Fluency evaluation failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Check if fluency service is available
   */
  async checkHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${FLUENCY_API_URL}/api/v1/fluency/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(3000),
      });
      return response.ok;
    } catch {
      return false;
    }
  }

  /**
   * Calculate 3 pillar scores from metrics breakdown
   * Accuracy = Pronunciation (25%) + Lexical (15%) => normalized to 0-100
   * Flow = Temporal (20%) + Disfluency inverted (20%) => normalized to 0-100
   * Expression = Prosodic (10%) + Communicative (10%) => normalized to 0-100
   */
  calculatePillarScores(metrics: MetricsBreakdown): ThreePillarScores {
    // Accuracy: (Pronunciation * 0.25 + Lexical * 0.15) / 0.40
    const accuracy = (
      (metrics.pronunciation_accuracy.score * 0.25 +
        metrics.lexical_accuracy.score * 0.15) / 0.40
    );

    // Flow: (Temporal * 0.20 + (100 - Disfluency) * 0.20) / 0.40
    const disfluencyInverted = 100 - metrics.disfluency_detection.score;
    const flow = (
      (metrics.temporal_metrics.score * 0.20 +
        disfluencyInverted * 0.20) / 0.40
    );

    // Expression: (Prosodic * 0.10 + Communicative * 0.10) / 0.20
    const expression = (
      (metrics.prosodic_quality.score * 0.10 +
        metrics.communicative_competence.score * 0.10) / 0.20
    );

    return {
      accuracy: Math.round(Math.min(100, Math.max(0, accuracy))),
      flow: Math.round(Math.min(100, Math.max(0, flow))),
      expression: Math.round(Math.min(100, Math.max(0, expression))),
    };
  }

  /**
   * Extract curated actionable highlights from metrics
   * Only includes metrics users can actively work on improving
   */
  extractActionableHighlights(metrics: MetricsBreakdown): ActionableHighlights {
    const temporal = metrics.temporal_metrics;
    const disfluency = metrics.disfluency_detection;
    const prosodic = metrics.prosodic_quality;
    const pronunciation = metrics.pronunciation_accuracy;
    const lexical = metrics.lexical_accuracy;
    const communicative = metrics.communicative_competence;

    // Speaking pace assessment
    let paceAssessment: 'too_slow' | 'good' | 'too_fast' = 'good';
    if (temporal.speaking_rate_wpm < 100) paceAssessment = 'too_slow';
    else if (temporal.speaking_rate_wpm > 200) paceAssessment = 'too_fast';

    // Pause quality assessment
    let pauseAssessment: 'too_many_long' | 'good' | 'natural' = 'good';
    if (temporal.pause_analysis?.very_long_pauses > 2) pauseAssessment = 'too_many_long';
    else if (temporal.pause_analysis?.avg_duration_ms < 500) pauseAssessment = 'natural';

    // Emotional range assessment
    let emotionalRange: 'monotone' | 'moderate' | 'expressive' = 'moderate';
    if (prosodic.pitch_std_hz < 20) emotionalRange = 'monotone';
    else if (prosodic.pitch_std_hz > 50) emotionalRange = 'expressive';

    // Pronunciation tips (top 3 actionable sounds to practice)
    const pronunciationTips: PronunciationTip[] = (pronunciation.phoneme_errors || [])
      .slice(0, 3)
      .map(e => ({
        sound: this.formatSoundType(e.type),
        word: e.word,
        suggestion: e.suggestion || `Practice the ${this.formatSoundType(e.type)} sound`,
      }));

    // Register appropriateness
    const registerAppropriate = communicative.register_appropriateness >= 0.7;

    return {
      // Accuracy pillar
      pronunciationTips,
      vocabularyAccuracy: Math.round((1 - lexical.wer) * 100),
      phrasesMatched: {
        hit: lexical.expected_phrases_hit,
        total: lexical.expected_phrases_total,
      },

      // Flow pillar
      speakingPace: {
        current_wpm: Math.round(temporal.speaking_rate_wpm),
        target_wpm: temporal.target_rate_wpm,
        assessment: paceAssessment,
      },
      fillerWordCount: disfluency.filled_pause_count,
      fillerWordsUsed: disfluency.filled_pauses.slice(0, 5),
      pauseQuality: {
        avg_duration_ms: Math.round(temporal.pause_analysis?.avg_duration_ms || 0),
        assessment: pauseAssessment,
      },

      // Expression pillar
      emotionalRange,
      discourseMarkersUsed: communicative.discourse_markers_used.slice(0, 5),
      registerMatch: {
        detected: communicative.register_match,
        appropriate: registerAppropriate,
      },
    };
  }

  /**
   * Format sound type to user-friendly name
   */
  private formatSoundType(type: string): string {
    const soundNames: Record<string, string> = {
      'rolled_r': 'Rolled R (rr)',
      'jota': 'J sound',
      'ene': '\u00d1 sound',
      'll_sound': 'LL/Y sound',
      'theta': 'Z/C sound',
      'tx': 'TX sound (Catalan)',
      'ny': 'NY sound (Catalan)',
    };
    return soundNames[type] || type;
  }

  /**
   * Store evaluation results to Supabase
   */
  async storeEvaluation(
    userId: string,
    sessionId: string,
    response: FluencyResponse,
    pillarScores: ThreePillarScores,
    scenario?: string,
    language?: string
  ): Promise<void> {
    // Extract words from transcript
    const wordsUsed = this.extractUniqueWords(response.transcript.text);

    // Get new words (words not in user's vocabulary yet)
    const newWords = await this.findNewWords(userId, wordsUsed);

    // Insert session evaluation
    const { error: evalError } = await supabase.from('session_evaluations').insert({
      user_id: userId,
      session_id: sessionId,
      scenario,
      language,
      fluency_score: response.fluency_score,
      level_assessment: response.level_assessment,
      cefr_level: response.cefr_level,
      accuracy_score: pillarScores.accuracy,
      flow_score: pillarScores.flow,
      expression_score: pillarScores.expression,
      pronunciation_metrics: response.metrics.pronunciation_accuracy,
      temporal_metrics: response.metrics.temporal_metrics,
      lexical_metrics: response.metrics.lexical_accuracy,
      disfluency_metrics: response.metrics.disfluency_detection,
      prosodic_metrics: response.metrics.prosodic_quality,
      communicative_metrics: response.metrics.communicative_competence,
      feedback_summary: response.feedback.summary,
      strengths: response.feedback.strengths,
      improvements: response.feedback.improvements,
      practice_suggestions: response.feedback.practice_suggestions,
      transcript: response.transcript.text,
      transcript_duration_seconds: response.transcript.duration_seconds,
      words_used: wordsUsed,
      new_words: newWords,
      processing_time_ms: response.processing_time_ms,
    });

    if (evalError) throw evalError;

    // Update user vocabulary
    await this.updateUserVocabulary(userId, wordsUsed);

    // Update daily metrics aggregate
    await this.updateDailyMetrics(userId, response, pillarScores, newWords.length, wordsUsed.length);

    // Update user profile with latest scores
    const { error: profileError } = await supabase.from('user_profiles').update({
      fluency_score: Math.round(response.fluency_score),
      latest_accuracy_score: pillarScores.accuracy,
      latest_flow_score: pillarScores.flow,
      latest_expression_score: pillarScores.expression,
    }).eq('id', userId);

    if (profileError) throw profileError;
  }

  /**
   * Extract unique words from transcript text
   */
  private extractUniqueWords(text: string): string[] {
    const words = text
      .toLowerCase()
      .replace(/[^\w\s\u00e0-\u00ff]/g, '') // Keep accented characters
      .split(/\s+/)
      .filter(word => word.length > 2); // Filter out very short words

    return [...new Set(words)];
  }

  /**
   * Find words that are new to the user's vocabulary
   */
  private async findNewWords(userId: string, words: string[]): Promise<string[]> {
    if (words.length === 0) return [];

    const { data: existingWords } = await supabase
      .from('user_vocabulary')
      .select('word')
      .eq('user_id', userId)
      .in('word', words);

    const existingSet = new Set((existingWords || []).map(w => w.word));
    return words.filter(word => !existingSet.has(word));
  }

  /**
   * Update user's vocabulary with words used in session
   */
  private async updateUserVocabulary(userId: string, words: string[]): Promise<void> {
    if (words.length === 0) return;

    const now = new Date().toISOString();

    // Upsert each word
    for (const word of words) {
      // Try to update existing word
      const { data: existing } = await supabase
        .from('user_vocabulary')
        .select('id, usage_count')
        .eq('user_id', userId)
        .eq('word', word)
        .single();

      if (existing) {
        // Update existing word
        await supabase
          .from('user_vocabulary')
          .update({
            usage_count: existing.usage_count + 1,
            last_used_at: now,
          })
          .eq('id', existing.id);
      } else {
        // Insert new word
        await supabase.from('user_vocabulary').insert({
          user_id: userId,
          word,
          usage_count: 1,
          first_seen_at: now,
          last_used_at: now,
        });
      }
    }
  }

  /**
   * Update daily metrics aggregation
   */
  private async updateDailyMetrics(
    userId: string,
    response: FluencyResponse,
    pillarScores: ThreePillarScores,
    newWordsCount: number,
    totalWordsUsed: number
  ): Promise<void> {
    const today = new Date().toISOString().split('T')[0];

    // Check if record exists for today
    const { data: existing } = await supabase
      .from('user_metrics_daily')
      .select('*')
      .eq('user_id', userId)
      .eq('date', today)
      .single();

    if (existing) {
      const count = existing.session_count + 1;
      await supabase.from('user_metrics_daily').update({
        session_count: count,
        avg_accuracy_score: ((existing.avg_accuracy_score * existing.session_count) + pillarScores.accuracy) / count,
        avg_flow_score: ((existing.avg_flow_score * existing.session_count) + pillarScores.flow) / count,
        avg_expression_score: ((existing.avg_expression_score * existing.session_count) + pillarScores.expression) / count,
        avg_fluency_score: ((existing.avg_fluency_score * existing.session_count) + response.fluency_score) / count,
        avg_speaking_rate_wpm: ((existing.avg_speaking_rate_wpm * existing.session_count) + response.metrics.temporal_metrics.speaking_rate_wpm) / count,
        avg_filler_word_count: ((existing.avg_filler_word_count * existing.session_count) + response.metrics.disfluency_detection.filled_pause_count) / count,
        total_practice_minutes: existing.total_practice_minutes + (response.transcript.duration_seconds / 60),
        new_words_count: existing.new_words_count + newWordsCount,
        total_words_used: existing.total_words_used + totalWordsUsed,
        updated_at: new Date().toISOString(),
      }).eq('id', existing.id);
    } else {
      await supabase.from('user_metrics_daily').insert({
        user_id: userId,
        date: today,
        session_count: 1,
        avg_accuracy_score: pillarScores.accuracy,
        avg_flow_score: pillarScores.flow,
        avg_expression_score: pillarScores.expression,
        avg_fluency_score: response.fluency_score,
        avg_speaking_rate_wpm: response.metrics.temporal_metrics.speaking_rate_wpm,
        avg_filler_word_count: response.metrics.disfluency_detection.filled_pause_count,
        total_practice_minutes: response.transcript.duration_seconds / 60,
        new_words_count: newWordsCount,
        total_words_used: totalWordsUsed,
      });
    }
  }

  /**
   * Fetch historical metrics for trends
   */
  async getHistoricalMetrics(
    userId: string,
    timeRange: 'today' | 'weekly' | 'monthly'
  ): Promise<DailyMetrics[]> {
    let daysAgo = 1;
    if (timeRange === 'weekly') daysAgo = 7;
    else if (timeRange === 'monthly') daysAgo = 30;

    const startDate = new Date();
    startDate.setDate(startDate.getDate() - daysAgo);

    const { data, error } = await supabase
      .from('user_metrics_daily')
      .select('date, avg_accuracy_score, avg_flow_score, avg_expression_score, avg_fluency_score, session_count, total_practice_minutes')
      .eq('user_id', userId)
      .gte('date', startDate.toISOString().split('T')[0])
      .order('date', { ascending: true });

    if (error) throw error;

    return (data || []).map(row => ({
      date: row.date,
      accuracy: row.avg_accuracy_score,
      flow: row.avg_flow_score,
      expression: row.avg_expression_score,
      fluency: row.avg_fluency_score,
      session_count: row.session_count,
      practice_minutes: row.total_practice_minutes,
    }));
  }

  /**
   * Fetch latest session evaluation
   */
  async getLatestEvaluation(userId: string): Promise<SessionEvaluation | null> {
    const { data, error } = await supabase
      .from('session_evaluations')
      .select('*')
      .eq('user_id', userId)
      .order('created_at', { ascending: false })
      .limit(1)
      .single();

    if (error && error.code !== 'PGRST116') throw error;
    return data;
  }

  /**
   * Fetch recent session evaluations
   */
  async getRecentEvaluations(userId: string, limit: number = 10): Promise<SessionEvaluation[]> {
    const { data, error } = await supabase
      .from('session_evaluations')
      .select('*')
      .eq('user_id', userId)
      .order('created_at', { ascending: false })
      .limit(limit);

    if (error) throw error;
    return data || [];
  }

  /**
   * Fetch user's vocabulary with usage stats
   */
  async getUserVocabulary(
    userId: string,
    options: { limit?: number; sortBy?: 'recent' | 'frequent' | 'alphabetical' } = {}
  ): Promise<VocabularyWord[]> {
    const { limit = 50, sortBy = 'recent' } = options;

    let query = supabase
      .from('user_vocabulary')
      .select('*')
      .eq('user_id', userId);

    // Apply sorting
    if (sortBy === 'recent') {
      query = query.order('last_used_at', { ascending: false });
    } else if (sortBy === 'frequent') {
      query = query.order('usage_count', { ascending: false });
    } else {
      query = query.order('word', { ascending: true });
    }

    const { data, error } = await query.limit(limit);

    if (error) throw error;

    return (data || []).map(row => ({
      word: row.word,
      translation: row.translation,
      usage_count: row.usage_count,
      first_seen_at: row.first_seen_at,
      last_used_at: row.last_used_at,
      is_new: this.isRecentlyAdded(row.first_seen_at),
    }));
  }

  /**
   * Get new words added in recent sessions
   */
  async getNewWords(userId: string, sinceDate?: Date): Promise<VocabularyWord[]> {
    const since = sinceDate || new Date(Date.now() - 7 * 24 * 60 * 60 * 1000); // Default: last 7 days

    const { data, error } = await supabase
      .from('user_vocabulary')
      .select('*')
      .eq('user_id', userId)
      .gte('first_seen_at', since.toISOString())
      .order('first_seen_at', { ascending: false });

    if (error) throw error;

    return (data || []).map(row => ({
      word: row.word,
      translation: row.translation,
      usage_count: row.usage_count,
      first_seen_at: row.first_seen_at,
      last_used_at: row.last_used_at,
      is_new: true,
    }));
  }

  /**
   * Check if a word was recently added (within last 24 hours)
   */
  private isRecentlyAdded(firstSeenAt: string): boolean {
    const dayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
    return new Date(firstSeenAt) > dayAgo;
  }

  /**
   * Get vocabulary statistics
   */
  async getVocabularyStats(userId: string): Promise<{
    totalWords: number;
    newThisWeek: number;
    mostUsedWords: VocabularyWord[];
  }> {
    const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);

    // Get total count
    const { count: totalWords } = await supabase
      .from('user_vocabulary')
      .select('*', { count: 'exact', head: true })
      .eq('user_id', userId);

    // Get new this week count
    const { count: newThisWeek } = await supabase
      .from('user_vocabulary')
      .select('*', { count: 'exact', head: true })
      .eq('user_id', userId)
      .gte('first_seen_at', weekAgo.toISOString());

    // Get most used words
    const mostUsedWords = await this.getUserVocabulary(userId, {
      limit: 5,
      sortBy: 'frequent',
    });

    return {
      totalWords: totalWords || 0,
      newThisWeek: newThisWeek || 0,
      mostUsedWords,
    };
  }
}

// Export singleton instance
export const fluencyService = new FluencyService();

// Export class for type inference
export type { FluencyService };
