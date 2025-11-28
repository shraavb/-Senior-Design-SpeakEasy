import { useState, useEffect } from "react";
import { TrendingUp, Award, Zap } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

interface QuickSummaryProps {
  timeFilter: "today" | "weekly" | "monthly";
}

export function QuickSummary({ timeFilter }: QuickSummaryProps) {
  const [isLoading, setIsLoading] = useState(true);

  // Simulate loading state when filter changes
  useEffect(() => {
    setIsLoading(true);
    const timer = setTimeout(() => setIsLoading(false), 500);
    return () => clearTimeout(timer);
  }, [timeFilter]);
  const highlights = {
    today: {
      score: "92%",
      improvement: "Pronunciation",
      achievement: "Perfect grammar score",
    },
    weekly: {
      score: "88%",
      improvement: "Fluency +12%",
      achievement: "7 practice sessions",
    },
    monthly: {
      score: "85%",
      improvement: "Vocabulary +230 words",
      achievement: "30-day streak",
    },
  };

  const current = highlights[timeFilter];

  if (isLoading) {
    return (
      <div className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl p-8 shadow-lg text-white">
        <div className="flex items-start justify-between mb-6">
          <div>
            <Skeleton className="h-4 w-32 bg-white/20 mb-2" />
            <Skeleton className="h-4 w-48 bg-white/20" />
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white/10 backdrop-blur-sm rounded-xl p-5 border border-white/20">
              <Skeleton className="h-4 w-24 bg-white/20 mb-3" />
              <Skeleton className="h-8 w-16 bg-white/20" />
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
          <p className="text-indigo-100 mt-1">Keep up the great work! 🎉</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white/10 backdrop-blur-sm rounded-xl p-5 border border-white/20">
          <div className="flex items-center gap-2 mb-3">
            <div className="p-2 rounded-lg bg-white/20">
              <Award className="w-5 h-5" />
            </div>
            <span className="text-indigo-100">Overall Score</span>
          </div>
          <p className="text-white">{current.score}</p>
        </div>

        <div className="bg-white/10 backdrop-blur-sm rounded-xl p-5 border border-white/20">
          <div className="flex items-center gap-2 mb-3">
            <div className="p-2 rounded-lg bg-white/20">
              <TrendingUp className="w-5 h-5" />
            </div>
            <span className="text-indigo-100">Best Improvement</span>
          </div>
          <p className="text-white">{current.improvement}</p>
        </div>

        <div className="bg-white/10 backdrop-blur-sm rounded-xl p-5 border border-white/20">
          <div className="flex items-center gap-2 mb-3">
            <div className="p-2 rounded-lg bg-white/20">
              <Zap className="w-5 h-5" />
            </div>
            <span className="text-indigo-100">Achievement</span>
          </div>
          <p className="text-white">{current.achievement}</p>
        </div>
      </div>
    </div>
  );
}

