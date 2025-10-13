import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { ChevronLeft, CheckCircle2, Lock, Clock } from "lucide-react";
import introductionsImg from "@/assets/scenario-introductions.jpg";
import emailsImg from "@/assets/scenario-emails.jpg";
import meetingImg from "@/assets/scenario-meeting.jpg";
import presentationImg from "@/assets/scenario-presentation.jpg";

const scenarios = [
  {
    title: "Professional Introductions",
    description: "Introduce yourself in business settings and networking events",
    difficulty: "easy",
    duration: "2 min",
    completed: false,
    image: introductionsImg,
  },
  {
    title: "Discussing Emails",
    description: "Talk about work emails, schedules, and project updates",
    difficulty: "medium",
    duration: "3 min",
    completed: false,
    image: emailsImg,
  },
  {
    title: "Team Meetings",
    description: "Participate in meetings, share ideas, and ask questions",
    difficulty: "medium",
    duration: "3 min",
    completed: false,
    image: meetingImg,
  },
  {
    title: "Giving Presentations",
    description: "Present ideas clearly and answer questions from colleagues",
    difficulty: "hard",
    duration: "4 min",
    locked: true,
    image: presentationImg,
  },
];

const ModuleProfessional = () => {
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleStartScenario = (scenarioTitle: string, isLocked: boolean) => {
    if (isLocked) {
      toast({
        title: "Scenario Locked",
        description: "Complete easier scenarios to unlock this one.",
        variant: "destructive",
      });
      return;
    }

    const language = localStorage.getItem('selectedLanguage') || 'Spanish';
    navigate(`/conversation?scenario=${encodeURIComponent(scenarioTitle)}&language=${language}`);
  };

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
          <h1 className="text-2xl font-bold">Professional & Career</h1>
          <p className="text-muted-foreground">Choose a scenario to practice</p>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8 space-y-4">
        {scenarios.map((scenario, index) => (
          <Card key={index} className={`overflow-hidden ${scenario.locked ? "opacity-60" : "hover:shadow-md transition-shadow"}`}>
            <div className="flex flex-col md:flex-row gap-4">
              <div className="w-full md:w-48 h-32 md:h-auto flex-shrink-0">
                <img 
                  src={scenario.image} 
                  alt={scenario.title}
                  className="w-full h-full object-cover"
                />
              </div>
              <div className="flex-1 p-4 md:p-6 flex items-start justify-between gap-4">
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
                <Button 
                  onClick={() => handleStartScenario(scenario.title, scenario.locked || false)}
                  disabled={scenario.locked} 
                  className="flex-shrink-0"
                >
                  Start
                </Button>
              </div>
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

export default ModuleProfessional;
