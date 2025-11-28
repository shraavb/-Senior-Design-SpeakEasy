import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { SharedTooltip } from "./shared-tooltip";

interface GrammarFeedbackProps {
  timeFilter: "today" | "weekly" | "monthly";
}

const grammarMetrics = [
  {
    label: "Conjugation Accuracy",
    todayScore: 92,
    color: "bg-indigo-500",
    chartColor: "#6366f1",
    weeklyData: [
      { day: "Mon", score: 88 },
      { day: "Tue", score: 89 },
      { day: "Wed", score: 90 },
      { day: "Thu", score: 91 },
      { day: "Fri", score: 92 },
      { day: "Sat", score: 91 },
      { day: "Sun", score: 92 },
    ],
    monthlyData: [
      { week: "Week 1", score: 85 },
      { week: "Week 2", score: 88 },
      { week: "Week 3", score: 90 },
      { week: "Week 4", score: 92 },
    ],
  },
  {
    label: "Sentence Structure",
    todayScore: 85,
    color: "bg-blue-500",
    chartColor: "#3b82f6",
    weeklyData: [
      { day: "Mon", score: 82 },
      { day: "Tue", score: 83 },
      { day: "Wed", score: 84 },
      { day: "Thu", score: 85 },
      { day: "Fri", score: 86 },
      { day: "Sat", score: 85 },
      { day: "Sun", score: 85 },
    ],
    monthlyData: [
      { week: "Week 1", score: 78 },
      { week: "Week 2", score: 82 },
      { week: "Week 3", score: 84 },
      { week: "Week 4", score: 85 },
    ],
  },
  {
    label: "Filler Word Usage",
    todayScore: 78,
    color: "bg-purple-500",
    chartColor: "#a855f7",
    inverse: true,
    weeklyData: [
      { day: "Mon", score: 82 },
      { day: "Tue", score: 81 },
      { day: "Wed", score: 80 },
      { day: "Thu", score: 79 },
      { day: "Fri", score: 78 },
      { day: "Sat", score: 78 },
      { day: "Sun", score: 78 },
    ],
    monthlyData: [
      { week: "Week 1", score: 85 },
      { week: "Week 2", score: 82 },
      { week: "Week 3", score: 80 },
      { week: "Week 4", score: 78 },
    ],
  },
  {
    label: "Tense Consistency",
    todayScore: 88,
    color: "bg-cyan-500",
    chartColor: "#06b6d4",
    weeklyData: [
      { day: "Mon", score: 85 },
      { day: "Tue", score: 86 },
      { day: "Wed", score: 87 },
      { day: "Thu", score: 88 },
      { day: "Fri", score: 89 },
      { day: "Sat", score: 88 },
      { day: "Sun", score: 88 },
    ],
    monthlyData: [
      { week: "Week 1", score: 82 },
      { week: "Week 2", score: 85 },
      { week: "Week 3", score: 87 },
      { week: "Week 4", score: 88 },
    ],
  },
];

export function GrammarFeedback({ timeFilter }: GrammarFeedbackProps) {
  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {grammarMetrics.map((metric) => {
          const chartData = timeFilter === "weekly" ? metric.weeklyData : metric.monthlyData;
          const xAxisKey = timeFilter === "weekly" ? "day" : "week";
          
          return (
            <div key={metric.label}>
              <div className="flex items-center justify-between mb-3">
                <span className="text-gray-700">{metric.label}</span>
                {timeFilter === "today" && (
                  <span className="text-gray-900">
                    {metric.todayScore}%
                    {metric.inverse && <span className="text-gray-500 text-sm ml-1">(lower is better)</span>}
                  </span>
                )}
              </div>

              {timeFilter === "today" ? (
                <>
                  <div className="relative h-3 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={`absolute top-0 left-0 h-full ${metric.color} rounded-full transition-all duration-500`}
                      style={{ width: `${metric.todayScore}%` }}
                    ></div>
                  </div>

                  {/* Threshold indicators */}
                  <div className="flex justify-between mt-1 text-xs text-gray-400">
                    <span>0%</span>
                    <span>50%</span>
                    <span>100%</span>
                  </div>
                </>
              ) : (
                <ResponsiveContainer width="100%" height={120}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis 
                      dataKey={xAxisKey} 
                      stroke="#9ca3af" 
                      tick={{ fontSize: 11 }}
                    />
                    <YAxis 
                      stroke="#9ca3af" 
                      tick={{ fontSize: 11 }} 
                      domain={[0, 100]}
                      width={35}
                    />
                    <Tooltip 
                      content={<SharedTooltip 
                        getColor={() => metric.chartColor} 
                        formatter={(value) => [`${value}%`, ""]}
                        showOnlyValue={true}
                      />}
                    />
                    <Line
                      type="monotone"
                      dataKey="score"
                      stroke={metric.chartColor}
                      strokeWidth={2.5}
                      dot={{ fill: metric.chartColor, r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>
          );
        })}
      </div>

      {/* Additional insight */}
      <div className="mt-6 p-4 bg-blue-50 rounded-xl border border-blue-100">
        <p className="text-blue-900 text-sm">
          💡 <span>Tip:</span> Practice conjugating verbs in the subjunctive mood to improve your accuracy.
        </p>
      </div>
    </div>
  );
}

