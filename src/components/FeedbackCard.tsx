import { Volume2, AlertCircle } from "lucide-react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";

interface Correction {
  wrong: string;
  correct: string;
  explanation: string;
}

interface FeedbackCardProps {
  userSaid: string;
  shouldSay: string;
  corrections: Correction[];
  onPlayAudio: (text: string) => void;
  onAcknowledge?: () => void;
}

export function FeedbackCard({ userSaid, shouldSay, corrections, onPlayAudio, onAcknowledge }: FeedbackCardProps) {
  return (
    <Card className="max-w-md ml-auto bg-amber-50 dark:bg-amber-950 border-amber-200 dark:border-amber-800 p-4">
      <div className="flex items-start gap-2 mb-3">
        <AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <h4 className="font-semibold text-amber-900 dark:text-amber-100 text-sm">
            Correction Available
          </h4>
        </div>
      </div>

      {/* What you said vs What you should say */}
      <div className="space-y-3 mb-4">
        <div>
          <p className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">You said:</p>
          <p className="text-sm text-gray-800 dark:text-gray-200 bg-white dark:bg-gray-900 p-2 rounded border border-gray-200 dark:border-gray-700">
            {userSaid}
          </p>
        </div>

        <div>
          <p className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Better way to say it:</p>
          <div className="flex items-center gap-2 bg-green-50 dark:bg-green-950 p-2 rounded border border-green-200 dark:border-green-800">
            <p className="text-sm text-green-900 dark:text-green-100 flex-1">
              {shouldSay}
            </p>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => onPlayAudio(shouldSay)}
              className="h-8 w-8 p-0 hover:bg-green-100 dark:hover:bg-green-900"
            >
              <Volume2 className="h-4 w-4 text-green-700 dark:text-green-300" />
            </Button>
          </div>
        </div>
      </div>

      {/* Detailed corrections */}
      {corrections && corrections.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-medium text-gray-600 dark:text-gray-400">What to improve:</p>
          {corrections.map((correction, index) => (
            <div key={index} className="bg-white dark:bg-gray-900 p-2.5 rounded border border-gray-200 dark:border-gray-700">
              <div className="flex items-baseline gap-2 mb-1">
                <span className="text-sm line-through text-red-600 dark:text-red-400 font-medium">
                  {correction.wrong}
                </span>
                <span className="text-gray-400">→</span>
                <span className="text-sm text-green-600 dark:text-green-400 font-medium">
                  {correction.correct}
                </span>
              </div>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                {correction.explanation}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Acknowledge button */}
      {onAcknowledge && (
        <div className="mt-4 pt-3 border-t border-amber-200 dark:border-amber-800">
          <Button
            onClick={onAcknowledge}
            className="w-full bg-amber-600 hover:bg-amber-700 text-white"
            size="sm"
          >
            I've reviewed this feedback
          </Button>
        </div>
      )}
    </Card>
  );
}
