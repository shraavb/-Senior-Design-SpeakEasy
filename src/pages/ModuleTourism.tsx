import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ChevronLeft, CheckCircle2, Lock, Clock } from "lucide-react";

const scenarios = [
  {
    title: "Ordering at a Restaurant",
    description: "Practice ordering food, asking about ingredients, and making special requests",
    difficulty: "easy",
    duration: "2 min",
    completed: true,
  },
  {
    title: "Asking for Directions",
    description: "Navigate a city by asking locals for help finding places",
    difficulty: "easy",
    duration: "2 min",
    completed: true,
  },
  {
    title: "Hotel Check-in",
    description: "Check into a hotel, ask about amenities, and resolve issues",
    difficulty: "medium",
    duration: "3 min",
    completed: false,
  },
  {
    title: "Using Public Transportation",
    description: "Buy tickets, ask about routes, and understand announcements",
    difficulty: "medium",
    duration: "2 min",
    completed: false,
  },
  {
    title: "Making Local Friends",
    description: "Strike up conversations with locals at cafes or events",
    difficulty: "hard",
    duration: "3 min",
    locked: true,
  },
];

const ModuleTourism = () => {
  const navigate = useNavigate();

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case "easy":
        return "bg-success/10 text-success";
      case "medium":
        return "bg-warning/10 text-warning";
      case "hard":
        return "bg-destructive/10 text-destructive";
      default:
        return "bg-muted text-muted-foreground";
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <Button variant="ghost" onClick={() => navigate("/dashboard")} className="mb-4">
            <ChevronLeft className="w-5 h-5 mr-2" />
            Back to Dashboard
          </Button>
          <h1 className="text-2xl font-bold">Tourism & Travel</h1>
          <p className="text-muted-foreground">Choose a scenario to practice</p>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8 space-y-4">
        {scenarios.map((scenario, index) => (
          <Card key={index} className={`p-6 ${scenario.locked ? "opacity-60" : "hover:shadow-md transition-shadow"}`}>
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-xl font-semibold">{scenario.title}</h3>
                  {scenario.completed && <CheckCircle2 className="w-5 h-5 text-success flex-shrink-0" />}
                  {scenario.locked && <Lock className="w-5 h-5 text-muted-foreground flex-shrink-0" />}
                </div>
                <p className="text-sm text-muted-foreground mb-3">{scenario.description}</p>
                <div className="flex items-center gap-3">
                  <Badge className={getDifficultyColor(scenario.difficulty)}>{scenario.difficulty}</Badge>
                  <span className="text-sm text-muted-foreground flex items-center">
                    <Clock className="w-4 h-4 mr-1" />
                    {scenario.duration}
                  </span>
                </div>
              </div>
              <Button disabled={scenario.locked} className="flex-shrink-0">
                Start
              </Button>
            </div>
          </Card>
        ))}

        <Card className="p-6 bg-muted/30 text-center">
          <p className="text-sm text-muted-foreground">
            Complete easier scenarios to unlock harder ones 🔒
          </p>
        </Card>
      </main>
    </div>
  );
};

export default ModuleTourism;
