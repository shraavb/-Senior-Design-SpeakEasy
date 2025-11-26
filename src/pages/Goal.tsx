import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Target, ChevronLeft, Plane, Users, Briefcase } from "lucide-react";

const goals = [
  {
    title: "Tourism & Travel",
    description: "Navigate cities, order food, make friends abroad",
    icon: Plane,
    color: "tourism",
  },
  {
    title: "Personal & Social",
    description: "Build friendships, discuss culture, express yourself",
    icon: Users,
    color: "social",
  },
  {
    title: "Professional & Career",
    description: "Workplace communication, meetings, presentations",
    icon: Briefcase,
    color: "professional",
  },
];

const Goal = () => {
  const [selectedGoal, setSelectedGoal] = useState<string>("");
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const language = searchParams.get("language") || "Spanish";

  const handleStartLearning = () => {
    if (selectedGoal) {
      // Map goals to their respective module routes
      const goalToModuleMap: Record<string, string> = {
        "Tourism & Travel": "/module/tourism",
        "Personal & Social": "/module/social",
        "Professional & Career": "/module/professional",
      };

      const moduleRoute = goalToModuleMap[selectedGoal] || "/dashboard";
      navigate(moduleRoute);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-social-light via-accent to-professional-light p-4">
      <Card className="w-full max-w-2xl p-8 md:p-12 space-y-8 shadow-xl">
        <div className="flex flex-col items-center text-center space-y-4">
          <div className="w-20 h-20 rounded-full border-4 border-primary flex items-center justify-center bg-gradient-to-br from-primary/10 to-tourism-light shadow-lg">
            <Target className="w-10 h-10 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl md:text-4xl font-bold mb-2">What's your main goal?</h1>
            <p className="text-lg text-muted-foreground">We'll personalize your experience</p>
          </div>
        </div>

        <div className="space-y-3">
          {goals.map((goal) => {
            const Icon = goal.icon;
            return (
              <button
                key={goal.title}
                onClick={() => setSelectedGoal(goal.title)}
                className={`w-full p-6 text-left rounded-2xl border-2 transition-all ${
                  selectedGoal === goal.title
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-primary/50 bg-card"
                }`}
              >
                <div className="flex items-start gap-4">
                  <div className={`w-12 h-12 rounded-xl bg-${goal.color}-light flex items-center justify-center flex-shrink-0`}>
                    <Icon className={`w-6 h-6 text-${goal.color}`} />
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold mb-1">{goal.title}</h3>
                    <p className="text-muted-foreground">{goal.description}</p>
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        <div className="flex gap-4">
          <Button
            onClick={() => navigate(`/level?language=${language}`)}
            variant="outline"
            className="flex-1 py-6 text-lg"
            size="lg"
          >
            <ChevronLeft className="w-5 h-5 mr-2" />
            Back
          </Button>
          <Button
            onClick={handleStartLearning}
            disabled={!selectedGoal}
            className="flex-1 py-6 text-lg"
            size="lg"
          >
            Start Learning
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default Goal;
