/**
 * Hook for fetching and managing fluency metrics data
 */

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { fluencyService } from "@/services/fluencyService";
import type {
  ThreePillarScores,
  ActionableHighlights,
  DailyMetrics,
  SessionEvaluation,
  VocabularyWord,
} from "@/types/fluency";

export interface FluencyMetricsData {
  // Pillar scores
  pillarScores: ThreePillarScores | null;
  overallScore: number | null;
  levelAssessment: string | null;

  // Actionable highlights
  highlights: ActionableHighlights | null;

  // Historical data for trends
  historicalData: DailyMetrics[];

  // Latest evaluation
  latestEvaluation: SessionEvaluation | null;

  // State
  loading: boolean;
  error: Error | null;

  // Actions
  refetch: () => Promise<void>;
}

export function useFluencyMetrics(
  timeFilter: "today" | "weekly" | "monthly"
): FluencyMetricsData {
  const { user } = useAuth();

  const [pillarScores, setPillarScores] = useState<ThreePillarScores | null>(null);
  const [overallScore, setOverallScore] = useState<number | null>(null);
  const [levelAssessment, setLevelAssessment] = useState<string | null>(null);
  const [highlights, setHighlights] = useState<ActionableHighlights | null>(null);
  const [historicalData, setHistoricalData] = useState<DailyMetrics[]>([]);
  const [latestEvaluation, setLatestEvaluation] = useState<SessionEvaluation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    if (!user) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Fetch latest evaluation for current scores
      const latest = await fluencyService.getLatestEvaluation(user.id);
      setLatestEvaluation(latest);

      if (latest) {
        // Set pillar scores from latest evaluation
        setPillarScores({
          accuracy: latest.accuracy_score,
          flow: latest.flow_score,
          expression: latest.expression_score,
        });
        setOverallScore(latest.fluency_score);
        setLevelAssessment(latest.level_assessment);

        // Extract actionable highlights from metrics
        const actionableHighlights = fluencyService.extractActionableHighlights({
          pronunciation_accuracy: latest.pronunciation_metrics,
          temporal_metrics: latest.temporal_metrics,
          lexical_accuracy: latest.lexical_metrics,
          disfluency_detection: latest.disfluency_metrics,
          prosodic_quality: latest.prosodic_metrics,
          communicative_competence: latest.communicative_metrics,
        });
        setHighlights(actionableHighlights);
      }

      // Fetch historical data for trends
      const historical = await fluencyService.getHistoricalMetrics(user.id, timeFilter);
      setHistoricalData(historical);

    } catch (err) {
      console.error("Error fetching fluency metrics:", err);
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [user, timeFilter]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    pillarScores,
    overallScore,
    levelAssessment,
    highlights,
    historicalData,
    latestEvaluation,
    loading,
    error,
    refetch: fetchData,
  };
}

/**
 * Hook for fetching vocabulary data
 */
export interface VocabularyData {
  // Vocabulary lists
  mostUsedWords: VocabularyWord[];
  newWords: VocabularyWord[];
  recentWords: VocabularyWord[];

  // Stats
  totalWords: number;
  newThisWeek: number;

  // State
  loading: boolean;
  error: Error | null;

  // Actions
  refetch: () => Promise<void>;
}

export function useVocabulary(): VocabularyData {
  const { user } = useAuth();

  const [mostUsedWords, setMostUsedWords] = useState<VocabularyWord[]>([]);
  const [newWords, setNewWords] = useState<VocabularyWord[]>([]);
  const [recentWords, setRecentWords] = useState<VocabularyWord[]>([]);
  const [totalWords, setTotalWords] = useState(0);
  const [newThisWeek, setNewThisWeek] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    if (!user) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Fetch vocabulary stats
      const stats = await fluencyService.getVocabularyStats(user.id);
      setTotalWords(stats.totalWords);
      setNewThisWeek(stats.newThisWeek);
      setMostUsedWords(stats.mostUsedWords);

      // Fetch new words from last 7 days
      const newWordsData = await fluencyService.getNewWords(user.id);
      setNewWords(newWordsData);

      // Fetch recent words
      const recentWordsData = await fluencyService.getUserVocabulary(user.id, {
        limit: 10,
        sortBy: 'recent',
      });
      setRecentWords(recentWordsData);

    } catch (err) {
      console.error("Error fetching vocabulary:", err);
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    mostUsedWords,
    newWords,
    recentWords,
    totalWords,
    newThisWeek,
    loading,
    error,
    refetch: fetchData,
  };
}

/**
 * Hook for fetching pillar-specific detailed data
 */
export interface PillarDetailData {
  // Accuracy pillar
  pronunciationTips: ActionableHighlights['pronunciationTips'];
  vocabularyAccuracy: number;
  phrasesMatched: { hit: number; total: number };

  // Flow pillar
  speakingPace: ActionableHighlights['speakingPace'];
  fillerWordCount: number;
  pauseQuality: ActionableHighlights['pauseQuality'];

  // Expression pillar
  emotionalRange: ActionableHighlights['emotionalRange'];
  discourseMarkersUsed: string[];
  registerMatch: ActionableHighlights['registerMatch'];

  // Trends (for charts)
  accuracyTrend: number[];
  flowTrend: number[];
  expressionTrend: number[];

  // State
  loading: boolean;
}

export function usePillarDetails(timeFilter: "today" | "weekly" | "monthly"): PillarDetailData {
  const { highlights, historicalData, loading } = useFluencyMetrics(timeFilter);

  // Extract trends from historical data
  const accuracyTrend = historicalData.map(d => d.accuracy);
  const flowTrend = historicalData.map(d => d.flow);
  const expressionTrend = historicalData.map(d => d.expression);

  return {
    // Accuracy pillar
    pronunciationTips: highlights?.pronunciationTips || [],
    vocabularyAccuracy: highlights?.vocabularyAccuracy || 0,
    phrasesMatched: highlights?.phrasesMatched || { hit: 0, total: 0 },

    // Flow pillar
    speakingPace: highlights?.speakingPace || { current_wpm: 0, target_wpm: 150, assessment: 'good' },
    fillerWordCount: highlights?.fillerWordCount || 0,
    pauseQuality: highlights?.pauseQuality || { avg_duration_ms: 0, assessment: 'good' },

    // Expression pillar
    emotionalRange: highlights?.emotionalRange || 'moderate',
    discourseMarkersUsed: highlights?.discourseMarkersUsed || [],
    registerMatch: highlights?.registerMatch || { detected: 'neutral', appropriate: true },

    // Trends
    accuracyTrend,
    flowTrend,
    expressionTrend,

    loading,
  };
}
