import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./ui/dialog";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { TrendingUp, BookOpen, AlertCircle } from "lucide-react";

interface ErrorBreakdown {
  [key: string]: number;
}

interface VocabularyWord {
  word: string;
  translation?: string;
  count: number;
}

interface SessionSummaryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onEndSession: () => void;
  errorBreakdown: ErrorBreakdown;
  mostCommonWords: VocabularyWord[];
  newWordsUsed: VocabularyWord[];
  totalCorrections: number;
  sessionDuration?: string;
}

export function SessionSummaryModal({
  isOpen,
  onClose,
  onEndSession,
  errorBreakdown,
  mostCommonWords,
  newWordsUsed,
  totalCorrections,
  sessionDuration = "0m"
}: SessionSummaryModalProps) {
  const errorTypes = Object.entries(errorBreakdown).sort((a, b) => b[1] - a[1]);
  const hasErrors = errorTypes.length > 0;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold">Session Summary</DialogTitle>
          <p className="text-sm text-muted-foreground">Great practice! Here's your progress</p>
        </DialogHeader>

        <div className="space-y-6 mt-4">
          {/* Session Stats */}
          <div className="grid grid-cols-2 gap-4">
            <Card className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <AlertCircle className="h-5 w-5 text-amber-600" />
                <h3 className="font-semibold">Corrections</h3>
              </div>
              <p className="text-3xl font-bold text-amber-600">{totalCorrections}</p>
              <p className="text-xs text-muted-foreground mt-1">opportunities to improve</p>
            </Card>

            <Card className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="h-5 w-5 text-green-600" />
                <h3 className="font-semibold">Session Time</h3>
              </div>
              <p className="text-3xl font-bold text-green-600">{sessionDuration}</p>
              <p className="text-xs text-muted-foreground mt-1">practicing conversation</p>
            </Card>
          </div>

          {/* Error Breakdown */}
          {hasErrors && (
            <Card className="p-4">
              <div className="flex items-center gap-2 mb-4">
                <AlertCircle className="h-5 w-5 text-red-600" />
                <h3 className="font-semibold">Error Breakdown</h3>
              </div>
              <p className="text-sm text-muted-foreground mb-4">
                Understand the types of errors in your speech
              </p>
              <div className="space-y-3">
                {errorTypes.map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between">
                    <div className="flex items-center gap-3 flex-1">
                      <span className="text-sm font-medium">{type}</span>
                      <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-red-500"
                          style={{
                            width: `${(count / totalCorrections) * 100}%`
                          }}
                        />
                      </div>
                    </div>
                    <span className="text-sm font-bold text-red-600 ml-3">{count}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Most Common Words */}
          {mostCommonWords.length > 0 && (
            <Card className="p-4">
              <div className="flex items-center gap-2 mb-4">
                <BookOpen className="h-5 w-5 text-blue-600" />
                <h3 className="font-semibold">Most Common Words</h3>
              </div>
              <p className="text-sm text-muted-foreground mb-4">
                Your frequently used vocabulary
              </p>
              <div className="space-y-2">
                {mostCommonWords.slice(0, 5).map((word, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-2 rounded bg-muted/50"
                  >
                    <div>
                      <p className="font-medium">{word.word}</p>
                      {word.translation && (
                        <p className="text-xs text-muted-foreground">{word.translation}</p>
                      )}
                    </div>
                    <span className="text-lg font-bold text-blue-600">{word.count}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* New Words Used */}
          {newWordsUsed.length > 0 && (
            <Card className="p-4 bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="h-5 w-5 text-green-600" />
                <h3 className="font-semibold text-green-900 dark:text-green-100">
                  New Words Used
                </h3>
              </div>
              <p className="text-sm text-green-700 dark:text-green-300 mb-4">
                Recently learned vocabulary
              </p>
              <div className="grid grid-cols-2 gap-2">
                {newWordsUsed.map((word, index) => (
                  <div
                    key={index}
                    className="p-2 rounded bg-white dark:bg-gray-900 border border-green-200 dark:border-green-800"
                  >
                    <p className="font-medium text-sm">{word.word}</p>
                    {word.translation && (
                      <p className="text-xs text-muted-foreground">{word.translation}</p>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* No errors message */}
          {!hasErrors && totalCorrections === 0 && (
            <Card className="p-6 text-center bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800">
              <TrendingUp className="h-12 w-12 text-green-600 mx-auto mb-3" />
              <h3 className="font-semibold text-green-900 dark:text-green-100 mb-2">
                Perfect Session!
              </h3>
              <p className="text-sm text-green-700 dark:text-green-300">
                No corrections needed. Keep up the great work!
              </p>
            </Card>
          )}
        </div>

        <div className="flex justify-end gap-3 mt-6">
          <Button variant="outline" onClick={onEndSession}>
            End Session
          </Button>
          <Button onClick={onClose}>Continue Practicing</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
