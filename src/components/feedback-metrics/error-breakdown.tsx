import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, LineChart, Line, LabelList } from "recharts";
import { SharedTooltip } from "./shared-tooltip";

interface ErrorBreakdownProps {
  timeFilter: "today" | "weekly" | "monthly";
}

const errorDataToday = [
  { type: "Agreement", count: 12, fullName: "Agreement errors (gender/number)" },
  { type: "Verb Tense", count: 8, fullName: "Verb tense/aspect errors" },
  { type: "Word Order", count: 5, fullName: "Word-order errors" },
  { type: "Articles", count: 15, fullName: "Article/determiner errors" },
  { type: "Case Marking", count: 3, fullName: "Case-marking errors" },
];

const errorDataWeekly = [
  { 
    day: "Mon", 
    Articles: 18,        // Highest
    Agreement: 15, 
    "Verb Tense": 10, 
    "Word Order": 7, 
    "Case Marking": 4 
  },
  { 
    day: "Tue", 
    Agreement: 16,       // Now highest - crosses Articles
    Articles: 14, 
    "Verb Tense": 11,   // Crosses Word Order
    "Word Order": 6, 
    "Case Marking": 3 
  },
  { 
    day: "Wed", 
    Articles: 17,       // Back to highest
    Agreement: 13, 
    "Verb Tense": 9, 
    "Word Order": 8,    // Crosses Verb Tense
    "Case Marking": 4 
  },
  { 
    day: "Thu", 
    Agreement: 14,      // Highest - crosses Articles
    Articles: 12, 
    "Verb Tense": 10,    // Crosses Word Order
    "Word Order": 5, 
    "Case Marking": 3 
  },
  { 
    day: "Fri", 
    Articles: 16,        // Highest again
    Agreement: 13, 
    "Verb Tense": 9, 
    "Word Order": 7,     // Crosses Verb Tense
    "Case Marking": 4 
  },
  { 
    day: "Sat", 
    Agreement: 12,       // Highest - crosses Articles
    Articles: 11, 
    "Verb Tense": 8, 
    "Word Order": 6, 
    "Case Marking": 3 
  },
  { 
    day: "Sun", 
    Articles: 15,        // Highest again
    Agreement: 13, 
    "Verb Tense": 9, 
    "Word Order": 5, 
    "Case Marking": 4 
  },
];

const errorDataMonthly = [
  { 
    week: "Week 1", 
    Articles: 22,        // Highest
    Agreement: 18, 
    "Verb Tense": 12, 
    "Word Order": 8, 
    "Case Marking": 6 
  },
  { 
    week: "Week 2", 
    Agreement: 19,       // Now highest - crosses Articles
    Articles: 18, 
    "Verb Tense": 13,     // Crosses Word Order
    "Word Order": 7, 
    "Case Marking": 4 
  },
  { 
    week: "Week 3", 
    Articles: 17,        // Back to highest
    Agreement: 15, 
    "Verb Tense": 11,     // Crosses Word Order
    "Word Order": 6, 
    "Case Marking": 3 
  },
  { 
    week: "Week 4", 
    Agreement: 16,       // Highest - crosses Articles
    Articles: 15, 
    "Verb Tense": 9, 
    "Word Order": 5, 
    "Case Marking": 3 
  },
];

const COLORS = ["#ef4444", "#f97316", "#f59e0b", "#eab308", "#84cc16"];

// Error type order for consistent color mapping
const ERROR_TYPES = ["Agreement", "Verb Tense", "Word Order", "Articles", "Case Marking"];

// Helper to get color for error type
const getErrorColor = (dataKey: string): string => {
  const errorTypeIndex = ERROR_TYPES.indexOf(dataKey);
  return errorTypeIndex >= 0 ? COLORS[errorTypeIndex] : "#6366f1";
};

export function ErrorBreakdown({ timeFilter }: ErrorBreakdownProps) {
  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
      {/* Chart */}
      <div className="mb-6">
        {timeFilter === "today" ? (
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={errorDataToday} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis type="number" stroke="#9ca3af" tick={{ fontSize: 12 }} />
              <YAxis dataKey="type" type="category" stroke="#9ca3af" width={100} tick={{ fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#fff",
                  border: "1px solid #e5e7eb",
                  borderRadius: "8px",
                  fontSize: "13px",
                }}
                formatter={(value, name, props) => [value, props.payload.fullName]}
              />
              <Bar dataKey="count" radius={[0, 8, 8, 0]}>
                {errorDataToday.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
                <LabelList 
                  dataKey="count" 
                  position="right" 
                  style={{ fill: "#374151", fontSize: "12px", fontWeight: 500 }}
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <ResponsiveContainer width="100%" height={320}>
            <LineChart 
              data={timeFilter === "weekly" ? errorDataWeekly : errorDataMonthly}
              margin={{ top: 5, right: 5, left: 5, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey={timeFilter === "weekly" ? "day" : "week"} 
                stroke="#9ca3af"
                tick={{ fontSize: 12 }}
              />
              <YAxis stroke="#9ca3af" tick={{ fontSize: 12 }} />
              <Tooltip content={<SharedTooltip sortByValue={true} getColor={getErrorColor} />} />
              {/* Lines ordered to allow proper overlapping - all rendered at same layer */}
              <Line 
                type="monotone" 
                dataKey="Articles" 
                stroke={COLORS[3]} 
                strokeWidth={2.5} 
                dot={{ r: 3 }} 
                activeDot={{ r: 5 }}
                connectNulls={false}
              />
              <Line 
                type="monotone" 
                dataKey="Agreement" 
                stroke={COLORS[0]} 
                strokeWidth={2.5} 
                dot={{ r: 3 }} 
                activeDot={{ r: 5 }}
                connectNulls={false}
              />
              <Line 
                type="monotone" 
                dataKey="Verb Tense" 
                stroke={COLORS[1]} 
                strokeWidth={2.5} 
                dot={{ r: 3 }} 
                activeDot={{ r: 5 }}
                connectNulls={false}
              />
              <Line 
                type="monotone" 
                dataKey="Word Order" 
                stroke={COLORS[2]} 
                strokeWidth={2.5} 
                dot={{ r: 3 }} 
                activeDot={{ r: 5 }}
                connectNulls={false}
              />
              <Line 
                type="monotone" 
                dataKey="Case Marking" 
                stroke={COLORS[4]} 
                strokeWidth={2.5} 
                dot={{ r: 3 }} 
                activeDot={{ r: 5 }}
                connectNulls={false}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Total Errors - Only show for today */}
      {timeFilter === "today" && (
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <span className="text-gray-700">Total Errors</span>
            <span className="text-gray-900">
              {errorDataToday.reduce((sum, item) => sum + item.count, 0)}
            </span>
          </div>
        </div>
      )}

      {/* Legend for weekly/monthly */}
      {timeFilter !== "today" && (
        <div className="flex flex-wrap gap-4 justify-center">
          {errorDataToday.map((error, index) => (
            <div key={error.type} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: COLORS[index % COLORS.length] }}
              ></div>
              <span className="text-gray-700 text-sm">{error.type}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

