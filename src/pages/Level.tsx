import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { CheckCircle2, ChevronLeft } from "lucide-react";

const levels = [
  {
    title: "Beginner",
    description: "I know basic phrases and vocabulary",
  },
  {
    title: "Intermediate",
    description: "I can read and write, but struggle with conversations",
  },
  {
    title: "Advanced",
    description: "I'm fluent but want to refine specific skills",
  },
];

const Level = () => {
  const [selectedLevel, setSelectedLevel] = useState<string>("");
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-muted/30 to-background p-4">
      <Card className="w-full max-w-2xl p-8 md:p-12 space-y-8">
        <div className="flex flex-col items-center text-center space-y-4">
          <div className="w-20 h-20 rounded-full border-4 border-primary flex items-center justify-center">
            <CheckCircle2 className="w-10 h-10 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl md:text-4xl font-bold mb-2">What's your current level?</h1>
            <p className="text-lg text-muted-foreground">Be honest - we'll adapt to you!</p>
          </div>
        </div>

        <div className="space-y-3">
          {levels.map((level) => (
            <button
              key={level.title}
              onClick={() => setSelectedLevel(level.title)}
              className={`w-full p-6 text-left rounded-2xl border-2 transition-all ${
                selectedLevel === level.title
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary/50 bg-card"
              }`}
            >
              <h3 className="text-xl font-semibold mb-1">{level.title}</h3>
              <p className="text-muted-foreground">{level.description}</p>
            </button>
          ))}
        </div>

        <div className="flex gap-4">
          <Button
            onClick={() => navigate("/")}
            variant="outline"
            className="flex-1 py-6 text-lg"
            size="lg"
          >
            <ChevronLeft className="w-5 h-5 mr-2" />
            Back
          </Button>
          <Button
            onClick={() => navigate("/goal")}
            disabled={!selectedLevel}
            className="flex-1 py-6 text-lg"
            size="lg"
          >
            Continue
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default Level;
