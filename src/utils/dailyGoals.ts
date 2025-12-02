/**
 * Utility functions for tracking daily conversation goals
 * Uses localStorage temporarily until we have a database table
 */

export type ModuleType = "tourism" | "social" | "professional";

/**
 * Get today's date as a string key (YYYY-MM-DD)
 */
export const getTodayKey = (): string => {
  return new Date().toISOString().split('T')[0];
};

/**
 * Get the storage key for a user's daily goals
 */
export const getDailyGoalsKey = (userId: string): string => {
  const todayKey = getTodayKey();
  return `dailyGoals_${userId}_${todayKey}`;
};

/**
 * Get completed module types for today
 */
export const getTodayCompletedModules = (userId: string): ModuleType[] => {
  const storageKey = getDailyGoalsKey(userId);
  const stored = localStorage.getItem(storageKey);
  
  if (stored) {
    try {
      return JSON.parse(stored);
    } catch {
      return [];
    }
  }
  return [];
};

/**
 * Mark a module as completed for today
 */
export const markModuleCompleted = (userId: string, module: ModuleType): void => {
  const completed = getTodayCompletedModules(userId);
  
  // Only add if not already completed
  if (!completed.includes(module)) {
    completed.push(module);
    const storageKey = getDailyGoalsKey(userId);
    localStorage.setItem(storageKey, JSON.stringify(completed));
  }
};

/**
 * Determine module type from scenario name
 */
export const getModuleFromScenario = (scenario: string): ModuleType => {
  const scenarioLower = scenario.toLowerCase();
  
  // Tourism scenarios
  if (
    scenarioLower.includes("restaurant") ||
    scenarioLower.includes("directions") ||
    scenarioLower.includes("hotel") ||
    scenarioLower.includes("transportation") ||
    scenarioLower.includes("local friends") ||
    scenarioLower.includes("tourism") ||
    scenarioLower.includes("travel")
  ) {
    return "tourism";
  }
  
  // Professional scenarios
  if (
    scenarioLower.includes("professional") ||
    scenarioLower.includes("introduction") ||
    scenarioLower.includes("email") ||
    scenarioLower.includes("meeting") ||
    scenarioLower.includes("presentation") ||
    scenarioLower.includes("career") ||
    scenarioLower.includes("business")
  ) {
    return "professional";
  }
  
  // Social scenarios (default)
  return "social";
};

/**
 * Check if a module is completed today
 */
export const isModuleCompletedToday = (userId: string, module: ModuleType): boolean => {
  const completed = getTodayCompletedModules(userId);
  return completed.includes(module);
};

