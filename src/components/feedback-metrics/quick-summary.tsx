import { useState, useEffect } from "react";
import { Target, Zap, Sparkles } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { useFluencyMetrics } from "@/hooks/useFluencyMetrics";

interface QuickSummaryProps {
  timeFilter: "today" | "weekly" | "monthly";
}

export function QuickSummary({ timeFilter }: QuickSummaryProps) {
  const { pillarScores, overallScore, levelAssessment, historicalData, loading } = useFluencyMetrics(timeFilter);
  const [isAnimating, setIsAnimating] = useState(false);

  // Animate on filter change
  useEffect(() => {
    setIsAnimating(true);
    const timer = setTimeout(() => setIsAnimating(false), 500);
    return () => clearTimeout(timer);
  }, [timeFilter]);

  // Calculate averages for weekly/monthly views
  const getDisplayScores = () => {
    if (timeFilter === "today" || historicalData.length === 0) {
      return {
        accuracy: pillarScores?.accuracy ?? null,
        flow: pillarScores?.flow ?? null,
        expression: pillarScores?.expression ?? null,
      };
    }

    // Calculate averages from historical data
    const avgAccuracy = Math.round(
      historicalData.reduce((sum, d) => sum + (d.accuracy || 0), 0) / historicalData.length
    );
    const avgFlow = Math.round(
      historicalData.reduce((sum, d) => sum + (d.flow || 0), 0) / historicalData.length
    );
    const avgExpression = Math.round(
      historicalData.reduce((sum, d) => sum + (d.expression || 0), 0) / historicalData.length
    );

    return {
      accuracy: avgAccuracy,
      flow: avgFlow,
      expression: avgExpression,
    };
  };

  const displayScores = getDisplayScores();
  const hasData = displayScores.accuracy !== null;

  // Get score color based on value
  const getScoreColor = (score: number | null) => {
    if (score === null) return "text-white/60";
    if (score >= 80) return "text-emerald-300";
    if (score >= 60) return "text-yellow-300";
    return "text-orange-300";
  };

  // Get assessment message based on overall performance
  const getAssessmentMessage = () => {
    if (!hasData) {
      return "Start a conversation to see your progress!";
    }

    const avg = ((displayScores.accuracy || 0) + (displayScores.flow || 0) + (displayScores.expression || 0)) / 3;
    if (avg >= 80) return "Excellent work! Keep it up!";
    if (avg >= 60) return "Good progress! Room to grow.";
    return "Keep practicing! You're improving.";
  };

  if (loading || isAnimating) {
    return (
      <div className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl p-8 shadow-lg text-white">
        <div className="flex items-start justify-between mb-6">
          <div>
            <Skeleton className="h-8 w-48 bg-white/20 mb-2" />
            <Skeleton className="h-4 w-64 bg-white/20" />
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white/10 backdrop-blur-sm rounded-xl p-5 border border-white/20">
              <Skeleton className="h-4 w-24 bg-white/20 mb-3" />
              <Skeleton className="h-10 w-20 bg-white/20" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl p-8 shadow-lg text-white">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-white text-2xl font-bold">
            {timeFilter === "today" ? "Today" : timeFilter === "weekly" ? "This Week" : "This Month"} At a Glance
          </h1>
          <p className="text-indigo-100 mt-1">{getAssessmentMessage()}</p>
        </div>
        {levelAssessment && timeFilter === "today" && (
          <div className="bg-white/20 backdrop-blur-sm px-4 py-2 rounded-full">
            <span className="text-sm font-medium">{levelAssessment}</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Accuracy Pillar */}
        <div className="bg-white/10 backdrop-blur-sm rounded-xl p-5 border border-white/20 hover:bg-white/15 transition-colors">
          <div className="flex items-center gap-2 mb-3">
            <div className="p-2 rounded-lg bg-emerald-500/30">
              <Target className="w-5 h-5 text-emerald-200" />
            </div>
            <div>
              <span className="text-white font-medium">Accuracy</span>
              <p className="text-indigo-200 text-xs">Pronunciation & vocabulary</p>
            </div>
          </div>
          <div className="flex items-end gap-2">
            <p className={`text-3xl font-bold ${getScoreColor(displayScores.accuracy)}`}>
              {displayScores.accuracy !== null ? `${displayScores.accuracy}%` : "--"}
            </p>
            {displayScores.accuracy !== null && (
              <span className="text-indigo-200 text-sm mb-1">/ 100</span>
            )}
          </div>
        </div>

        {/* Flow Pillar */}
        <div className="bg-white/10 backdrop-blur-sm rounded-xl p-5 border border-white/20 hover:bg-white/15 transition-colors">
          <div className="flex items-center gap-2 mb-3">
            <div className="p-2 rounded-lg bg-blue-500/30">
              <Zap className="w-5 h-5 text-blue-200" />
            </div>
            <div>
              <span className="text-white font-medium">Flow</span>
              <p className="text-indigo-200 text-xs">Speaking pace & smoothness</p>
            </div>
          </div>
          <div className="flex items-end gap-2">
            <p className={`text-3xl font-bold ${getScoreColor(displayScores.flow)}`}>
              {displayScores.flow !== null ? `${displayScores.flow}%` : "--"}
            </p>
            {displayScores.flow !== null && (
              <span className="text-indigo-200 text-sm mb-1">/ 100</span>
            )}
          </div>
        </div>

        {/* Expression Pillar */}
        <div className="bg-white/10 backdrop-blur-sm rounded-xl p-5 border border-white/20 hover:bg-white/15 transition-colors">
          <div className="flex items-center gap-2 mb-3">
            <div className="p-2 rounded-lg bg-violet-500/30">
              <Sparkles className="w-5 h-5 text-violet-200" />
            </div>
            <div>
              <span className="text-white font-medium">Expression</span>
              <p className="text-indigo-200 text-xs">Natural delivery & style</p>
            </div>
          </div>
          <div className="flex items-end gap-2">
            <p className={`text-3xl font-bold ${getScoreColor(displayScores.expression)}`}>
              {displayScores.expression !== null ? `${displayScores.expression}%` : "--"}
            </p>
            {displayScores.expression !== null && (
              <span className="text-indigo-200 text-sm mb-1">/ 100</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
