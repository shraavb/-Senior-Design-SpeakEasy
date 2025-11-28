import { Mic, Clock, Volume2 } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { SharedTooltip } from "./shared-tooltip";

interface FluencyMetricsProps {
  timeFilter: "today" | "weekly" | "monthly";
}

const metrics = [
  {
    label: "Coherency Score",
    todayValue: "82%",
    change: "+5%",
    icon: Volume2,
    color: "text-emerald-600",
    bgColor: "bg-emerald-50",
    chartColor: "#10b981",
    description: "Pronunciation clarity",
    weeklyData: [
      { day: "Mon", value: 82 },
      { day: "Tue", value: 85 },
      { day: "Wed", value: 83 },
      { day: "Thu", value: 86 },
      { day: "Fri", value: 88 },
      { day: "Sat", value: 85 },
      { day: "Sun", value: 87 },
    ],
    monthlyData: [
      { week: "Week 1", value: 78 },
      { week: "Week 2", value: 82 },
      { week: "Week 3", value: 85 },
      { week: "Week 4", value: 87 },
    ],
  },
  {
    label: "Words Per Minute",
    todayValue: "142",
    change: "+8 WPM",
    icon: Mic,
    color: "text-blue-600",
    bgColor: "bg-blue-50",
    chartColor: "#3b82f6",
    description: "Speaking speed",
    weeklyData: [
      { day: "Mon", value: 135 },
      { day: "Tue", value: 138 },
      { day: "Wed", value: 136 },
      { day: "Thu", value: 140 },
      { day: "Fri", value: 143 },
      { day: "Sat", value: 141 },
      { day: "Sun", value: 142 },
    ],
    monthlyData: [
      { week: "Week 1", value: 128 },
      { week: "Week 2", value: 134 },
      { week: "Week 3", value: 138 },
      { week: "Week 4", value: 142 },
    ],
  },
  {
    label: "Avg Pause Length",
    todayValue: "0.8s",
    change: "-0.2s",
    icon: Clock,
    color: "text-purple-600",
    bgColor: "bg-purple-50",
    chartColor: "#a855f7",
    description: "Natural flow",
    weeklyData: [
      { day: "Mon", value: 1.2 },
      { day: "Tue", value: 1.1 },
      { day: "Wed", value: 1.0 },
      { day: "Thu", value: 0.9 },
      { day: "Fri", value: 0.85 },
      { day: "Sat", value: 0.82 },
      { day: "Sun", value: 0.8 },
    ],
    monthlyData: [
      { week: "Week 1", value: 1.4 },
      { week: "Week 2", value: 1.1 },
      { week: "Week 3", value: 0.95 },
      { week: "Week 4", value: 0.8 },
    ],
  },
];

export function FluencyMetrics({ timeFilter }: FluencyMetricsProps) {
  return (
    <div className="space-y-5">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {metrics.map((metric) => {
          const Icon = metric.icon;
          const chartData = timeFilter === "weekly" ? metric.weeklyData : metric.monthlyData;
          const xAxisKey = timeFilter === "weekly" ? "day" : "week";
          
          return (
            <div
              key={metric.label}
              className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <div className={`p-2.5 rounded-lg ${metric.bgColor}`}>
                  <Icon className={`w-5 h-5 ${metric.color}`} />
                </div>
                <div className="flex items-center gap-1 px-2 py-1 rounded-full bg-emerald-50 text-emerald-700 text-sm">
                  <span>↑</span>
                  <span>{metric.change}</span>
                </div>
              </div>

              <div>
                <p className="text-gray-600 text-sm">{metric.label}</p>
                {timeFilter === "today" ? (
                  <>
                    <p className="text-gray-900 mt-1">{metric.todayValue}</p>
                    <p className="text-gray-500 text-sm mt-1">{metric.description}</p>
                  </>
                ) : (
                  <p className="text-gray-500 text-sm mt-1">{metric.description}</p>
                )}
              </div>

              {/* Chart or Progress bar */}
              <div className="mt-4">
                {timeFilter === "today" ? (
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${metric.bgColor} rounded-full`}
                      style={{ width: metric.todayValue }}
                    ></div>
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height={140}>
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis 
                        dataKey={xAxisKey} 
                        stroke="#9ca3af" 
                        tick={{ fontSize: 11 }}
                        angle={-45}
                        textAnchor="end"
                        height={45}
                      />
                      <YAxis stroke="#9ca3af" tick={{ fontSize: 11 }} width={35} />
                      <Tooltip content={<SharedTooltip getColor={() => metric.chartColor} showOnlyValue={true} />} />
                      <Line
                        type="monotone"
                        dataKey="value"
                        stroke={metric.chartColor}
                        strokeWidth={2.5}
                        dot={{ fill: metric.chartColor, r: 4 }}
                        activeDot={{ r: 6 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

