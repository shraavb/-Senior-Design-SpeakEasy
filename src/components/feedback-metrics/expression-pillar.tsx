import { useState, useEffect } from "react";
import { Sparkles, Music, MessageSquare, UserCheck } from "lucide-react";
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

interface ExpressionPillarProps {
  timeFilter: "today" | "weekly" | "monthly";
}

export function ExpressionPillar({ timeFilter }: ExpressionPillarProps) {
  const {
    emotionalRange,
    discourseMarkersUsed,
    registerMatch,
    expressionTrend,
    loading,
  } = usePillarDetails(timeFilter);

  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    setIsAnimating(true);
    const timer = setTimeout(() => setIsAnimating(false), 300);
    return () => clearTimeout(timer);
  }, [timeFilter]);

  // Prepare chart data
  const chartData = expressionTrend.map((value, index) => ({
    day: index + 1,
    expression: value,
  }));

  const hasData = emotionalRange !== "moderate" || discourseMarkersUsed.length > 0;

  // Get emotional range info
  const getEmotionalInfo = () => {
    if (emotionalRange === "monotone") {
      return {
        color: "text-amber-600",
        bg: "bg-amber-100",
        icon: "bg-amber-200",
        message: "Try adding more vocal variety",
        level: 1,
      };
    }
    if (emotionalRange === "expressive") {
      return {
        color: "text-emerald-600",
        bg: "bg-emerald-100",
        icon: "bg-emerald-200",
        message: "Great emotional expression!",
        level: 3,
      };
    }
    return {
      color: "text-blue-600",
      bg: "bg-blue-100",
      icon: "bg-blue-200",
      message: "Good vocal variety",
      level: 2,
    };
  };

  const emotionalInfo = getEmotionalInfo();

  if (loading || isAnimating) {
    return (
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 rounded-lg bg-violet-100">
            <Sparkles className="w-5 h-5 text-violet-600" />
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
        <div className="p-2 rounded-lg bg-violet-100">
          <Sparkles className="w-5 h-5 text-violet-600" />
        </div>
        <div>
          <h3 className="font-semibold text-gray-900">Expression Details</h3>
          <p className="text-sm text-gray-500">Natural delivery & communication style</p>
        </div>
      </div>

      {!hasData ? (
        <div className="text-center py-8 text-gray-500">
          <Sparkles className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p className="text-sm">Complete a conversation to see your expression metrics</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Emotional Range */}
          <div className={`${emotionalInfo.bg} rounded-xl p-4`}>
            <div className="flex items-center gap-3 mb-3">
              <div className={`p-2 rounded-lg ${emotionalInfo.icon}`}>
                <Music className={`w-4 h-4 ${emotionalInfo.color}`} />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-700">Emotional Range</p>
                <p className={`text-xs ${emotionalInfo.color}`}>{emotionalInfo.message}</p>
              </div>
              <span className={`text-lg font-bold capitalize ${emotionalInfo.color}`}>
                {emotionalRange}
              </span>
            </div>
            {/* Visual indicator */}
            <div className="flex gap-2 mt-2">
              {[1, 2, 3].map((level) => (
                <div
                  key={level}
                  className={`h-2 flex-1 rounded-full transition-all ${
                    level <= emotionalInfo.level
                      ? emotionalRange === "monotone"
                        ? "bg-amber-400"
                        : emotionalRange === "expressive"
                        ? "bg-emerald-400"
                        : "bg-blue-400"
                      : "bg-white/50"
                  }`}
                />
              ))}
            </div>
            <div className="flex justify-between mt-1">
              <span className="text-xs text-gray-500">Monotone</span>
              <span className="text-xs text-gray-500">Expressive</span>
            </div>
          </div>

          {/* Discourse Markers Used */}
          <div className="p-4 bg-gray-50 rounded-xl">
            <div className="flex items-center gap-2 mb-3">
              <MessageSquare className="w-4 h-4 text-violet-600" />
              <span className="text-sm font-medium text-gray-700">Discourse Markers Used</span>
            </div>
            {discourseMarkersUsed.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {discourseMarkersUsed.map((marker, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-violet-100 text-violet-700 rounded-full text-sm"
                  >
                    {marker}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">
                Try using connectors like "bueno", "pues", "entonces" to sound more natural
              </p>
            )}
            <p className="text-xs text-gray-500 mt-2">
              {discourseMarkersUsed.length >= 3
                ? "Great use of natural connectors!"
                : discourseMarkersUsed.length > 0
                ? "Good start! Try using more connectors."
                : "Discourse markers make speech sound more natural."}
            </p>
          </div>

          {/* Register Appropriateness */}
          <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-xl">
            <div className={`p-2 rounded-lg ${
              registerMatch.appropriate ? "bg-emerald-100" : "bg-amber-100"
            }`}>
              <UserCheck className={`w-5 h-5 ${
                registerMatch.appropriate ? "text-emerald-600" : "text-amber-600"
              }`} />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-700">Register</p>
              <p className="text-xs text-gray-500">
                {registerMatch.appropriate
                  ? "Your formality level matches the context"
                  : "Consider adjusting your formality level"}
              </p>
            </div>
            <div className="text-right">
              <span className={`text-sm font-bold capitalize ${
                registerMatch.appropriate ? "text-emerald-600" : "text-amber-600"
              }`}>
                {registerMatch.detected}
              </span>
              <p className="text-xs text-gray-500">detected</p>
            </div>
          </div>

          {/* Trend Chart (weekly/monthly only) */}
          {timeFilter !== "today" && chartData.length > 1 && (
            <div>
              <p className="text-sm font-medium text-gray-700 mb-3">Expression Trend</p>
              <div className="h-32">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <XAxis dataKey="day" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                    <Tooltip content={<SharedTooltip />} />
                    <Line
                      type="monotone"
                      dataKey="expression"
                      stroke="#8b5cf6"
                      strokeWidth={2}
                      dot={{ fill: "#8b5cf6", r: 3 }}
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
