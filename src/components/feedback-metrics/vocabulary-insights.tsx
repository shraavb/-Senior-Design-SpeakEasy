import { useState, useEffect } from "react";
import { BookMarked, TrendingUp, Sparkles, BookOpen } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { useVocabulary } from "@/hooks/useFluencyMetrics";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Tooltip,
  Cell,
} from "recharts";

interface VocabularyInsightsProps {
  timeFilter: "today" | "weekly" | "monthly";
}

export function VocabularyInsights({ timeFilter }: VocabularyInsightsProps) {
  const { mostUsedWords, newWords, totalWords, newThisWeek, loading } = useVocabulary();
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    setIsAnimating(true);
    const timer = setTimeout(() => setIsAnimating(false), 300);
    return () => clearTimeout(timer);
  }, [timeFilter]);

  // Prepare chart data for most used words
  const chartData = mostUsedWords.slice(0, 5).map((word, index) => ({
    word: word.word,
    count: word.usage_count,
    index,
  }));

  const barColors = ["#6366f1", "#8b5cf6", "#a78bfa", "#c4b5fd", "#ddd6fe"];

  const hasData = totalWords > 0 || mostUsedWords.length > 0;

  if (loading || isAnimating) {
    return (
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 rounded-lg bg-indigo-100">
            <BookMarked className="w-5 h-5 text-indigo-600" />
          </div>
          <div>
            <Skeleton className="h-5 w-32 mb-1" />
            <Skeleton className="h-4 w-48" />
          </div>
        </div>
        <div className="space-y-4">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 rounded-lg bg-indigo-100">
          <BookMarked className="w-5 h-5 text-indigo-600" />
        </div>
        <div>
          <h3 className="font-semibold text-gray-900">Vocabulary Growth</h3>
          <p className="text-sm text-gray-500">Words you've used in conversations</p>
        </div>
      </div>

      {!hasData ? (
        <div className="text-center py-8 text-gray-500">
          <BookMarked className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p className="text-sm">Complete a conversation to see your vocabulary</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Stats Summary */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-indigo-50 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-1">
                <BookOpen className="w-4 h-4 text-indigo-600" />
                <span className="text-sm text-gray-600">Total Words</span>
              </div>
              <p className="text-2xl font-bold text-indigo-600">{totalWords}</p>
            </div>
            <div className="bg-emerald-50 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-1">
                <Sparkles className="w-4 h-4 text-emerald-600" />
                <span className="text-sm text-gray-600">New This Week</span>
              </div>
              <p className="text-2xl font-bold text-emerald-600">{newThisWeek}</p>
            </div>
          </div>

          {/* Most Used Words Chart */}
          {chartData.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp className="w-4 h-4 text-gray-500" />
                <span className="text-sm font-medium text-gray-700">Most Used Words</span>
              </div>
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} layout="vertical" margin={{ left: 60, right: 20 }}>
                    <XAxis type="number" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                    <YAxis
                      type="category"
                      dataKey="word"
                      tick={{ fontSize: 12, fill: "#374151" }}
                      tickLine={false}
                      axisLine={false}
                      width={55}
                    />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (!active || !payload?.length) return null;
                        return (
                          <div className="bg-white border rounded-lg shadow-lg px-3 py-2">
                            <p className="font-medium text-gray-900">{payload[0].payload.word}</p>
                            <p className="text-sm text-gray-500">{payload[0].value} uses</p>
                          </div>
                        );
                      }}
                    />
                    <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={barColors[index]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* New Words Section */}
          {newWords.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="w-4 h-4 text-emerald-500" />
                <span className="text-sm font-medium text-gray-700">Recently Learned</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {newWords.slice(0, 8).map((word, index) => (
                  <span
                    key={index}
                    className="px-3 py-1.5 bg-emerald-50 text-emerald-700 rounded-full text-sm border border-emerald-100"
                  >
                    {word.word}
                    {word.translation && (
                      <span className="text-emerald-500 ml-1">({word.translation})</span>
                    )}
                  </span>
                ))}
              </div>
              {newWords.length > 8 && (
                <p className="text-xs text-gray-500 mt-2">
                  +{newWords.length - 8} more new words this week
                </p>
              )}
            </div>
          )}

          {/* Encouragement Message */}
          <div className="bg-gradient-to-r from-indigo-50 to-violet-50 rounded-xl p-4 border border-indigo-100">
            <p className="text-sm text-indigo-700">
              {newThisWeek >= 10
                ? "Amazing vocabulary growth! You're expanding your language skills rapidly."
                : newThisWeek >= 5
                ? "Great progress! Keep introducing new words in your conversations."
                : totalWords >= 50
                ? "Nice vocabulary base! Try using more diverse words."
                : "Start conversations to build your vocabulary!"}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
