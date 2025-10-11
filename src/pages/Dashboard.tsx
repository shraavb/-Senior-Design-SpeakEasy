import { useNavigate } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Flame, TrendingUp, Trophy, Plane, Users, Briefcase, ChevronRight } from "lucide-react";

const modules = [
  {
    title: "Tourism & Travel",
    description: "Navigate cities, order food, make friends",
    icon: Plane,
    color: "tourism",
    scenarios: 12,
    path: "/module/tourism",
  },
  {
    title: "Personal & Social",
    description: "Build friendships, discuss culture",
    icon: Users,
    color: "social",
    scenarios: 15,
    path: "/module/social",
  },
  {
    title: "Professional & Career",
    description: "Workplace communication, meetings",
    icon: Briefcase,
    color: "professional",
    scenarios: 10,
    path: "/module/professional",
  },
];

const Dashboard = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">SpeakEasy</h1>
            <p className="text-sm text-muted-foreground">Learning Spanish</p>
          </div>
          <Button variant="ghost" onClick={() => navigate("/leaderboard")}>
            <Trophy className="w-5 h-5 mr-2" />
            Leaderboard
          </Button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 space-y-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-muted-foreground">Daily Streak</h3>
              <Flame className="w-5 h-5 text-streak" />
            </div>
            <p className="text-3xl font-bold">7</p>
            <p className="text-sm text-muted-foreground">days</p>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-muted-foreground">Fluency Score</h3>
              <TrendingUp className="w-5 h-5 text-success" />
            </div>
            <p className="text-3xl font-bold">82</p>
          </Card>

          <Card className="p-6 cursor-pointer hover:shadow-md transition-shadow" onClick={() => navigate("/progress")}>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-muted-foreground">View Progress</h3>
              <Trophy className="w-5 h-5 text-warning" />
            </div>
            <p className="text-base font-medium text-primary">Detailed stats →</p>
          </Card>
        </div>

        {/* Today's Goal */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-bold mb-1">Today's Goal</h2>
              <p className="text-sm text-muted-foreground">2 of 3 conversations</p>
            </div>
            <span className="text-2xl font-bold text-primary">66%</span>
          </div>
          <Progress value={66} className="h-3" />
        </Card>

        {/* Practice Modules */}
        <div>
          <h2 className="text-2xl font-bold mb-4">Choose Your Practice Module</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {modules.map((module) => {
              const Icon = module.icon;
              return (
                <Card
                  key={module.title}
                  className="p-6 cursor-pointer hover:shadow-lg transition-all hover:-translate-y-1"
                  onClick={() => navigate(module.path)}
                >
                  <div className={`w-14 h-14 rounded-2xl bg-${module.color}-light flex items-center justify-center mb-4`}>
                    <Icon className={`w-7 h-7 text-${module.color}`} />
                  </div>
                  <h3 className="text-xl font-bold mb-2">{module.title}</h3>
                  <p className="text-sm text-muted-foreground mb-4">{module.description}</p>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">{module.scenarios} scenarios</span>
                    <ChevronRight className="w-5 h-5" />
                  </div>
                </Card>
              );
            })}
          </div>
        </div>

        {/* Recommended */}
        <Card className="p-6 bg-muted/30">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold mb-1">Recommended for You</h3>
              <p className="text-sm text-muted-foreground">Continue with Tourism & Travel</p>
            </div>
            <Button>Start Practicing</Button>
          </div>
        </Card>
      </main>
    </div>
  );
};

export default Dashboard;
