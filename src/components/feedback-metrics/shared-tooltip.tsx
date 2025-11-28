import React from "react";

interface TooltipEntry {
  dataKey: string;
  value: number | string;
  color?: string;
  name?: string;
}

interface SharedTooltipProps {
  active?: boolean;
  payload?: Array<{
    dataKey: string;
    value: number | string;
    color?: string;
    name?: string;
    payload?: any;
  }>;
  sortByValue?: boolean;
  getColor?: (dataKey: string) => string;
  formatter?: (value: number | string, name: string) => [string, string];
  showOnlyValue?: boolean; // For single-line graphs, show only the value
}

export const SharedTooltip = ({ 
  active, 
  payload, 
  sortByValue = false,
  getColor,
  formatter,
  showOnlyValue = false
}: SharedTooltipProps) => {
  if (!active || !payload || !payload.length) {
    return null;
  }

  // Process payload entries
  let entries: TooltipEntry[] = payload.map((entry) => {
    const value = entry.value || 0;
    const name = entry.name || entry.dataKey || "";
    let displayValue = String(value);
    let displayName = name;
    
    // Apply formatter if provided
    if (formatter) {
      const formatted = formatter(value, name);
      displayValue = formatted[0];
      displayName = formatted[1] || name;
    }
    
    return {
      dataKey: entry.dataKey || name,
      value: displayValue,
      name: displayName,
      color: getColor ? getColor(entry.dataKey || "") : entry.color,
    };
  });

  // Sort by value if requested (highest to lowest)
  if (sortByValue) {
    entries = entries.sort((a, b) => {
      // Extract numeric value from string (handles "85%", "85", etc.)
      const aStr = String(a.value).replace(/[^0-9.-]/g, '');
      const bStr = String(b.value).replace(/[^0-9.-]/g, '');
      const aValue = parseFloat(aStr) || 0;
      const bValue = parseFloat(bStr) || 0;
      return bValue - aValue;
    });
  }

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
      {entries.map((entry, index) => (
        <div 
          key={entry.dataKey} 
          style={{ 
            display: "flex", 
            alignItems: "center", 
            gap: "8px", 
            marginBottom: index < entries.length - 1 ? "6px" : "0" 
          }}
        >
          {entry.color && !showOnlyValue && (
            <div
              style={{
                width: "12px",
                height: "12px",
                borderRadius: "50%",
                backgroundColor: entry.color,
              }}
            />
          )}
          {!showOnlyValue && (
            <span style={{ color: "#374151", fontWeight: 500 }}>
              {entry.name || entry.dataKey}:
            </span>
          )}
          <span style={{ color: "#111827", fontWeight: 600 }}>{entry.value}</span>
        </div>
      ))}
    </div>
  );
};

