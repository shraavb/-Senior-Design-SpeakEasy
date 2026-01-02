import { useState, useEffect } from "react";
import { Zap, Gauge, MessageCircle, Clock } from "lucide-react";
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

interface FlowPillarProps {
  timeFilter: "today" | "weekly" | "monthly";
}

export function FlowPillar({ timeFilter }: FlowPillarProps) {
  const {
    speakingPace,
    fillerWordCount,
    pauseQuality,
    flowTrend,
    loading,
  } = usePillarDetails(timeFilter);

  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    setIsAnimating(true);
    const timer = setTimeout(() => setIsAnimating(false), 300);
    return () => clearTimeout(timer);
  }, [timeFilter]);

  // Prepare chart data
  const chartData = flowTrend.map((value, index) => ({
    day: index + 1,
    flow: value,
  }));

  const hasData = speakingPace.current_wpm > 0;

  // Get pace color and message
  const getPaceInfo = () => {
    if (speakingPace.assessment === "too_slow") {
      return { color: "text-amber-600", bg: "bg-amber-100", message: "Try speaking a bit faster" };
    }
    if (speakingPace.assessment === "too_fast") {
      return { color: "text-orange-600", bg: "bg-orange-100", message: "Slow down a little" };
    }
    return { color: "text-blue-600", bg: "bg-blue-100", message: "Great speaking pace!" };
  };

  const paceInfo = getPaceInfo();

  // Calculate pace percentage (relative to target)
  const pacePercentage = Math.min(100, Math.round((speakingPace.current_wpm / speakingPace.target_wpm) * 100));

  // Get filler words assessment
  const getFillerAssessment = () => {
    if (fillerWordCount === 0) return { color: "text-emerald-600", message: "No filler words - excellent!" };
    if (fillerWordCount <= 2) return { color: "text-blue-600", message: "Minimal filler words" };
    if (fillerWordCount <= 5) return { color: "text-amber-600", message: "Some filler words detected" };
    return { color: "text-orange-600", message: "Try reducing filler words" };
  };

  const fillerAssessment = getFillerAssessment();

  if (loading || isAnimating) {
    return (
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 rounded-lg bg-blue-100">
            <Zap className="w-5 h-5 text-blue-600" />
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
        <div className="p-2 rounded-lg bg-blue-100">
          <Zap className="w-5 h-5 text-blue-600" />
        </div>
        <div>
          <h3 className="font-semibold text-gray-900">Flow Details</h3>
          <p className="text-sm text-gray-500">Speaking pace & smoothness</p>
        </div>
      </div>

      {!hasData ? (
        <div className="text-center py-8 text-gray-500">
          <Zap className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p className="text-sm">Complete a conversation to see your flow metrics</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Speaking Pace */}
          <div className={`${paceInfo.bg} rounded-xl p-4`}>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Gauge className="w-4 h-4 text-gray-600" />
                <span className="text-sm font-medium text-gray-700">Speaking Pace</span>
              </div>
              <div className="text-right">
                <span className={`text-lg font-bold ${paceInfo.color}`}>
                  {speakingPace.current_wpm} WPM
                </span>
                <p className="text-xs text-gray-500">Target: {speakingPace.target_wpm} WPM</p>
              </div>
            </div>
            <div className="w-full bg-white/50 rounded-full h-3 relative">
              {/* Target marker */}
              <div
                className="absolute top-0 w-0.5 h-3 bg-gray-400"
                style={{ left: "66%" }}
              />
              <div
                className={`h-3 rounded-full transition-all duration-500 ${
                  speakingPace.assessment === "good" ? "bg-blue-500" :
                  speakingPace.assessment === "too_slow" ? "bg-amber-500" : "bg-orange-500"
                }`}
                style={{ width: `${Math.min(100, pacePercentage * 1.5)}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-2">{paceInfo.message}</p>
          </div>

          {/* Filler Words */}
          <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-xl">
            <div className={`p-2 rounded-lg ${fillerWordCount === 0 ? "bg-emerald-100" : "bg-amber-100"}`}>
              <MessageCircle className={`w-5 h-5 ${fillerWordCount === 0 ? "text-emerald-600" : "text-amber-600"}`} />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-700">Filler Words</p>
              <p className={`text-xs ${fillerAssessment.color}`}>{fillerAssessment.message}</p>
            </div>
            <div className="text-right">
              <span className={`text-2xl font-bold ${fillerAssessment.color}`}>
                {fillerWordCount}
              </span>
              <p className="text-xs text-gray-500">detected</p>
            </div>
          </div>

          {/* Pause Quality */}
          <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-xl">
            <div className={`p-2 rounded-lg ${
              pauseQuality.assessment === "natural" ? "bg-emerald-100" :
              pauseQuality.assessment === "good" ? "bg-blue-100" : "bg-amber-100"
            }`}>
              <Clock className={`w-5 h-5 ${
                pauseQuality.assessment === "natural" ? "text-emerald-600" :
                pauseQuality.assessment === "good" ? "text-blue-600" : "text-amber-600"
              }`} />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-700">Pause Quality</p>
              <p className="text-xs text-gray-500">
                {pauseQuality.assessment === "natural"
                  ? "Natural pausing rhythm"
                  : pauseQuality.assessment === "good"
                  ? "Good pause timing"
                  : "Work on reducing long pauses"}
              </p>
            </div>
            <div className="text-right">
              <span className="text-lg font-bold text-gray-700">
                {pauseQuality.avg_duration_ms}ms
              </span>
              <p className="text-xs text-gray-500">avg pause</p>
            </div>
          </div>

          {/* Trend Chart (weekly/monthly only) */}
          {timeFilter !== "today" && chartData.length > 1 && (
            <div>
              <p className="text-sm font-medium text-gray-700 mb-3">Flow Trend</p>
              <div className="h-32">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <XAxis dataKey="day" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                    <Tooltip content={<SharedTooltip />} />
                    <Line
                      type="monotone"
                      dataKey="flow"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      dot={{ fill: "#3b82f6", r: 3 }}
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
