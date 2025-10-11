import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Progress as ProgressBar } from "@/components/ui/progress";
import { ChevronLeft, Trophy, Flame, TrendingUp, Target, Zap, Award } from "lucide-react";

const Progress = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card">
        <div className="max-w-5xl mx-auto px-4 py-4">
          <Button variant="ghost" onClick={() => navigate("/dashboard")}>
            <ChevronLeft className="w-5 h-5 mr-2" />
            Back to Dashboard
          </Button>
          <h1 className="text-2xl font-bold mt-4">Your Progress</h1>
          <p className="text-muted-foreground">Track your journey to fluency</p>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8 space-y-6">
        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="p-6 text-center">
            <Trophy className="w-8 h-8 text-warning mx-auto mb-2" />
            <p className="text-3xl font-bold">12</p>
            <p className="text-sm text-muted-foreground">Conversations</p>
          </Card>
          <Card className="p-6 text-center">
            <Target className="w-8 h-8 text-tourism mx-auto mb-2" />
            <p className="text-3xl font-bold">36</p>
            <p className="text-sm text-muted-foreground">Minutes</p>
          </Card>
          <Card className="p-6 text-center">
            <TrendingUp className="w-8 h-8 text-success mx-auto mb-2" />
            <p className="text-3xl font-bold">78</p>
            <p className="text-sm text-muted-foreground">Avg Score</p>
          </Card>
          <Card className="p-6 text-center">
            <Flame className="w-8 h-8 text-streak mx-auto mb-2" />
            <p className="text-3xl font-bold">7</p>
            <p className="text-sm text-muted-foreground">Day Streak</p>
          </Card>
        </div>

        {/* Module Progress */}
        <Card className="p-6">
          <h2 className="text-xl font-bold mb-4">Module Progress</h2>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="font-medium">Tourism & Travel</span>
                <span className="text-sm text-muted-foreground">3/5 scenarios</span>
              </div>
              <ProgressBar value={60} className="h-2" />
            </div>
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="font-medium">Personal & Social</span>
                <span className="text-sm text-muted-foreground">1/4 scenarios</span>
              </div>
              <ProgressBar value={25} className="h-2" />
            </div>
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="font-medium">Professional</span>
                <span className="text-sm text-muted-foreground">0/4 scenarios</span>
              </div>
              <ProgressBar value={0} className="h-2" />
            </div>
          </div>
        </Card>

        {/* Achievements */}
        <Card className="p-6">
          <h2 className="text-xl font-bold mb-4">Achievements</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-lg bg-muted/30">
              <Award className="w-8 h-8 mb-2" />
              <h3 className="font-semibold mb-1">First Conversation</h3>
              <p className="text-sm text-muted-foreground">Complete your first practice</p>
            </div>
            <div className="p-4 rounded-lg bg-muted/30">
              <Flame className="w-8 h-8 mb-2 text-streak" />
              <h3 className="font-semibold mb-1">7-Day Streak</h3>
              <p className="text-sm text-muted-foreground">Practice for 7 days in a row</p>
            </div>
            <div className="p-4 rounded-lg border-2 border-dashed border-border">
              <Zap className="w-8 h-8 mb-2 text-muted-foreground" />
              <h3 className="font-semibold mb-1 text-muted-foreground">Speed Speaker</h3>
              <p className="text-sm text-muted-foreground">Reach 90 WPM</p>
            </div>
          </div>
        </Card>

        {/* Current Goals */}
        <Card className="p-6">
          <h2 className="text-xl font-bold mb-4">Current Goals</h2>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between items-center mb-2">
                <div>
                  <p className="font-medium">Reach 30-day streak</p>
                  <p className="text-sm text-muted-foreground">7 / 30 days</p>
                </div>
              </div>
              <ProgressBar value={23} className="h-2" />
            </div>
            <div>
              <div className="flex justify-between items-center mb-2">
                <div>
                  <p className="font-medium">Complete Tourism module</p>
                  <p className="text-sm text-muted-foreground">3 / 5 scenarios</p>
                </div>
              </div>
              <ProgressBar value={60} className="h-2" />
            </div>
            <div>
              <div className="flex justify-between items-center mb-2">
                <div>
                  <p className="font-medium">Achieve 90+ average score</p>
                  <p className="text-sm text-muted-foreground">Current: 78</p>
                </div>
              </div>
              <ProgressBar value={87} className="h-2" />
            </div>
          </div>
        </Card>
      </main>
    </div>
  );
};

export default Progress;
