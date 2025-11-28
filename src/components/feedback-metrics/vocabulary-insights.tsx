import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, Cell } from "recharts";
import { SharedTooltip } from "./shared-tooltip";

// Custom tooltip for bar chart to show only the value
const BarChartTooltip = ({ active, payload }: any) => {
  if (!active || !payload || !payload.length) {
    return null;
  }

  const entry = payload[0];
  const value = entry.value || 0;
  const category = entry.payload?.category || "";
  const color = getColorForCategory(category);

  return (
    <div
      style={{
        backgroundColor: "#fff",
        border: "1px solid #e5e7eb",
        borderRadius: "8px",
        fontSize: "13px",
        padding: "12px",
        boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        {color && (
          <div
            style={{
              width: "12px",
              height: "12px",
              borderRadius: "50%",
              backgroundColor: color,
            }}
          />
        )}
        <span style={{ color: "#111827", fontWeight: 600 }}>{value}</span>
      </div>
    </div>
  );
};

interface VocabularyInsightsProps {
  timeFilter: "today" | "weekly" | "monthly";
}

const partsOfSpeechToday = [
  { category: "Verbs", count: 142 },
  { category: "Nouns", count: 98 },
  { category: "Adjectives", count: 67 },
  { category: "Adverbs", count: 45 },
  { category: "Prepositions", count: 38 },
  { category: "Conjunctions", count: 22 },
];

const partsOfSpeechWeekly = [
  { day: "Mon", Verbs: 135, Nouns: 92, Adjectives: 62, Adverbs: 42 },
  { day: "Tue", Verbs: 138, Nouns: 94, Adjectives: 64, Adverbs: 43 },
  { day: "Wed", Verbs: 136, Nouns: 95, Adjectives: 65, Adverbs: 44 },
  { day: "Thu", Verbs: 140, Nouns: 96, Adjectives: 66, Adverbs: 44 },
  { day: "Fri", Verbs: 141, Nouns: 97, Adjectives: 66, Adverbs: 45 },
  { day: "Sat", Verbs: 140, Nouns: 97, Adjectives: 67, Adverbs: 45 },
  { day: "Sun", Verbs: 142, Nouns: 98, Adjectives: 67, Adverbs: 45 },
];

const partsOfSpeechMonthly = [
  { week: "Week 1", Verbs: 128, Nouns: 85, Adjectives: 58, Adverbs: 38 },
  { week: "Week 2", Verbs: 134, Nouns: 90, Adjectives: 62, Adverbs: 41 },
  { week: "Week 3", Verbs: 138, Nouns: 94, Adjectives: 65, Adverbs: 43 },
  { week: "Week 4", Verbs: 142, Nouns: 98, Adjectives: 67, Adverbs: 45 },
];

const VOCAB_COLORS = {
  Verbs: "#6366f1",
  Nouns: "#3b82f6",
  Adjectives: "#8b5cf6",
  Adverbs: "#06b6d4",
  Prepositions: "#10b981",
  Conjunctions: "#f59e0b",
};

// Helper function to get color for a category
const getColorForCategory = (category: string): string => {
  return VOCAB_COLORS[category as keyof typeof VOCAB_COLORS] || "#6366f1";
};

export function VocabularyInsights({ timeFilter }: VocabularyInsightsProps) {
  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
      <div className="mb-6">
        <h3 className="text-gray-900 font-semibold">Parts of Speech Distribution</h3>
        <p className="text-gray-600 text-sm mt-1">Breakdown of vocabulary by grammatical category</p>
      </div>

      {timeFilter === "today" ? (
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={partsOfSpeechToday}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="category" stroke="#9ca3af" angle={-15} textAnchor="end" height={80} tick={{ fontSize: 12 }} />
            <YAxis stroke="#9ca3af" tick={{ fontSize: 12 }} />
            <Tooltip content={<BarChartTooltip />} />
            <Bar dataKey="count" radius={[8, 8, 0, 0]}>
              {partsOfSpeechToday.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getColorForCategory(entry.category)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      ) : (
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={timeFilter === "weekly" ? partsOfSpeechWeekly : partsOfSpeechMonthly}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis 
              dataKey={timeFilter === "weekly" ? "day" : "week"} 
              stroke="#9ca3af"
              tick={{ fontSize: 12 }}
            />
            <YAxis stroke="#9ca3af" tick={{ fontSize: 12 }} />
            <Tooltip content={<SharedTooltip getColor={getColorForCategory} />} />
            <Line type="monotone" dataKey="Verbs" stroke={VOCAB_COLORS.Verbs} strokeWidth={2.5} dot={{ r: 3 }} />
            <Line type="monotone" dataKey="Nouns" stroke={VOCAB_COLORS.Nouns} strokeWidth={2.5} dot={{ r: 3 }} />
            <Line type="monotone" dataKey="Adjectives" stroke={VOCAB_COLORS.Adjectives} strokeWidth={2.5} dot={{ r: 3 }} />
            <Line type="monotone" dataKey="Adverbs" stroke={VOCAB_COLORS.Adverbs} strokeWidth={2.5} dot={{ r: 3 }} />
          </LineChart>
        </ResponsiveContainer>
      )}

      {/* Legend - Show for all time filters */}
      <div className="flex flex-wrap gap-4 justify-center mt-6">
        {timeFilter === "today" 
          ? partsOfSpeechToday.map((entry) => (
              <div key={entry.category} className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: getColorForCategory(entry.category) }}
                ></div>
                <span className="text-gray-700 text-sm">{entry.category}</span>
              </div>
            ))
          : Object.entries(VOCAB_COLORS).map(([category, color]) => (
              <div key={category} className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: color }}
                ></div>
                <span className="text-gray-700 text-sm">{category}</span>
              </div>
            ))
        }
      </div>
    </div>
  );
}

