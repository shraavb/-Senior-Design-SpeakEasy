import { useState, useEffect } from "react";
import { Target, Volume2, BookOpen, CheckCircle2 } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { usePillarDetails } from "@/hooks/useFluencyMetrics";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { SharedTooltip } from "./shared-tooltip";

interface AccuracyPillarProps {
  timeFilter: "today" | "weekly" | "monthly";
}

export function AccuracyPillar({ timeFilter }: AccuracyPillarProps) {
  const {
    pronunciationTips,
    vocabularyAccuracy,
    phrasesMatched,
    accuracyTrend,
    loading,
  } = usePillarDetails(timeFilter);

  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    setIsAnimating(true);
    const timer = setTimeout(() => setIsAnimating(false), 300);
    return () => clearTimeout(timer);
  }, [timeFilter]);

  // Prepare chart data
  const chartData = accuracyTrend.map((value, index) => ({
    day: index + 1,
    accuracy: value,
  }));

  const hasData = vocabularyAccuracy > 0 || pronunciationTips.length > 0;

  if (loading || isAnimating) {
    return (
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 rounded-lg bg-emerald-100">
            <Target className="w-5 h-5 text-emerald-600" />
          </div>
          <div>
            <Skeleton className="h-5 w-32 mb-1" />
            <Skeleton className="h-4 w-48" />
          </div>
        </div>
        <div className="space-y-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 rounded-lg bg-emerald-100">
          <Target className="w-5 h-5 text-emerald-600" />
        </div>
        <div>
          <h3 className="font-semibold text-gray-900">Accuracy Details</h3>
          <p className="text-sm text-gray-500">Pronunciation & vocabulary precision</p>
        </div>
      </div>

      {!hasData ? (
        <div className="text-center py-8 text-gray-500">
          <Target className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p className="text-sm">Complete a conversation to see your accuracy metrics</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Vocabulary Accuracy */}
          <div className="bg-emerald-50 rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-emerald-600" />
                <span className="text-sm font-medium text-gray-700">Vocabulary Accuracy</span>
              </div>
              <span className="text-lg font-bold text-emerald-600">{vocabularyAccuracy}%</span>
            </div>
            <div className="w-full bg-emerald-200 rounded-full h-2">
              <div
                className="bg-emerald-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${vocabularyAccuracy}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-2">
              {vocabularyAccuracy >= 90
                ? "Excellent word choice!"
                : vocabularyAccuracy >= 70
                ? "Good vocabulary usage"
                : "Keep practicing new words"}
            </p>
          </div>

          {/* Phrases Matched */}
          {phrasesMatched.total > 0 && (
            <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-xl">
              <CheckCircle2 className="w-5 h-5 text-emerald-500" />
              <div>
                <p className="text-sm font-medium text-gray-700">Phrases Matched</p>
                <p className="text-xs text-gray-500">
                  {phrasesMatched.hit} of {phrasesMatched.total} expected phrases
                </p>
              </div>
              <span className="ml-auto text-lg font-bold text-emerald-600">
                {Math.round((phrasesMatched.hit / phrasesMatched.total) * 100)}%
              </span>
            </div>
          )}

          {/* Pronunciation Tips */}
          {pronunciationTips.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Volume2 className="w-4 h-4 text-gray-500" />
                <span className="text-sm font-medium text-gray-700">Sounds to Practice</span>
              </div>
              <div className="space-y-2">
                {pronunciationTips.map((tip, index) => (
                  <div
                    key={index}
                    className="flex items-start gap-3 p-3 bg-amber-50 rounded-lg border border-amber-100"
                  >
                    <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center flex-shrink-0">
                      <span className="text-xs font-bold text-amber-700">{index + 1}</span>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-800">
                        {tip.sound}: <span className="text-amber-700">"{tip.word}"</span>
                      </p>
                      <p className="text-xs text-gray-500 mt-0.5">{tip.suggestion}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Trend Chart (weekly/monthly only) */}
          {timeFilter !== "today" && chartData.length > 1 && (
            <div>
              <p className="text-sm font-medium text-gray-700 mb-3">Accuracy Trend</p>
              <div className="h-32">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <XAxis dataKey="day" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                    <Tooltip content={<SharedTooltip />} />
                    <Line
                      type="monotone"
                      dataKey="accuracy"
                      stroke="#10b981"
                      strokeWidth={2}
                      dot={{ fill: "#10b981", r: 3 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
