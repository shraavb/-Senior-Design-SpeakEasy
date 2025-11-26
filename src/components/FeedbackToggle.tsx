import { Switch } from "./ui/switch";
import { Label } from "./ui/label";
import { Info } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "./ui/tooltip";

interface FeedbackToggleProps {
  feedbackMode: "on" | "off";
  onToggle: (mode: "on" | "off") => void;
}

export function FeedbackToggle({ feedbackMode, onToggle }: FeedbackToggleProps) {
  return (
    <div className="border-b bg-card px-4 py-3">
      {feedbackMode === "on" && (
        <div className="max-w-4xl mx-auto mb-3 p-2 bg-blue-50 dark:bg-blue-950 rounded text-xs">
          <p className="font-semibold text-blue-900 dark:text-blue-100 mb-1">💡 Test feedback with these phrases:</p>
          <p className="text-blue-800 dark:text-blue-200">
            Spanish: "Quiero un café" | Mandarin: "我要咖啡" | French: "Je veux un café"
          </p>
        </div>
      )}
      <div className="max-w-4xl mx-auto flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Label htmlFor="feedback-mode" className="text-sm font-medium">
            Direct Feedback
          </Label>
          <Tooltip delayDuration={0}>
            <TooltipTrigger asChild>
              <button
                type="button"
                className="text-muted-foreground hover:text-foreground transition-colors cursor-help"
                aria-label="Information about feedback modes"
              >
                <Info className="h-4 w-4" />
              </button>
            </TooltipTrigger>
            <TooltipContent side="bottom" className="max-w-sm p-4 bg-popover text-popover-foreground">
              <div className="space-y-3 text-xs">
                <div>
                  <p className="font-semibold mb-1 text-foreground">Feedback ON:</p>
                  <ul className="space-y-1 list-disc list-inside">
                    <li>See corrections immediately after you speak</li>
                    <li>Hear correct pronunciation with audio</li>
                    <li>Get grammar explanations for mistakes</li>
                  </ul>
                </div>
                <div>
                  <p className="font-semibold mb-1 text-foreground">Feedback OFF:</p>
                  <ul className="space-y-1 list-disc list-inside">
                    <li>Natural conversation flow without interruptions</li>
                    <li>Soft corrections embedded in AI's replies</li>
                    <li>Learn through context and example</li>
                  </ul>
                </div>
              </div>
            </TooltipContent>
          </Tooltip>
        </div>
        <div className="flex items-center gap-3">
          <span className={`text-xs font-medium ${feedbackMode === "off" ? "text-foreground" : "text-muted-foreground"}`}>
            OFF
          </span>
          <Switch
            id="feedback-mode"
            checked={feedbackMode === "on"}
            onCheckedChange={(checked) => onToggle(checked ? "on" : "off")}
          />
          <span className={`text-xs font-medium ${feedbackMode === "on" ? "text-foreground" : "text-muted-foreground"}`}>
            ON
          </span>
        </div>
      </div>
    </div>
  );
}
