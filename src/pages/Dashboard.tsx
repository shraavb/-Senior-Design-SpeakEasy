import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Flame, TrendingUp, Trophy, Plane, Users, Briefcase, ChevronRight, ChevronDown, CheckCircle2, Circle, Map } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

const languages = [
  { name: "Spanish", flag: "🇪🇸" },
  { name: "French", flag: "🇫🇷" },
  { name: "German", flag: "🇩🇪" },
  { name: "Italian", flag: "🇮🇹" },
  { name: "Japanese", flag: "🇯🇵" },
  { name: "Mandarin", flag: "🇨🇳" },
];

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
  const storedLanguage = localStorage.getItem('selectedLanguage');
  const initialLanguage = languages.find(lang => lang.name === storedLanguage) || languages[0];
  const [selectedLanguage, setSelectedLanguage] = useState(initialLanguage);
  const [goalsExpanded, setGoalsExpanded] = useState(false);

  const handleLanguageChange = (language: typeof languages[0]) => {
    setSelectedLanguage(language);
    localStorage.setItem('selectedLanguage', language.name);
  };

  const dailyGoals = [
    { id: 1, title: "Complete 1 Tourism conversation", completed: true },
    { id: 2, title: "Complete 1 Social conversation", completed: true },
    { id: 3, title: "Complete 1 Professional conversation", completed: false },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-tourism-light/50 to-background">
      <header className="border-b bg-card/80 backdrop-blur-sm shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-social bg-clip-text text-transparent">SpeakEasy</h1>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors">
                  <span className="text-lg">{selectedLanguage.flag}</span>
                  <span>Learning {selectedLanguage.name}</span>
                  <ChevronDown className="w-4 h-4" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="bg-card border shadow-lg z-50">
                {languages.map((language) => (
                  <DropdownMenuItem
                    key={language.name}
                    onClick={() => handleLanguageChange(language)}
                    className="flex items-center gap-3 cursor-pointer"
                  >
                    <span className="text-lg">{language.flag}</span>
                    <span>{language.name}</span>
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
          <div className="flex gap-2">
            <Button variant="ghost" onClick={() => navigate("/learning-map")} className="hover:bg-tourism-light">
              <Map className="w-5 h-5 mr-2 text-primary" />
              Map
            </Button>
            <Button variant="ghost" onClick={() => navigate("/leaderboard")} className="hover:bg-tourism-light">
              <Trophy className="w-5 h-5 mr-2 text-warning" />
              Leaderboard
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 space-y-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="p-6 bg-gradient-to-br from-professional-light to-card hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-muted-foreground">Daily Streak</h3>
              <Flame className="w-5 h-5 text-streak" />
            </div>
            <p className="text-3xl font-bold text-professional">7</p>
            <p className="text-sm text-muted-foreground">days</p>
          </Card>

          <Card className="p-6 bg-gradient-to-br from-tourism-light to-card hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-muted-foreground">Fluency Score</h3>
              <TrendingUp className="w-5 h-5 text-success" />
            </div>
            <p className="text-3xl font-bold text-tourism">82</p>
          </Card>

          <Card className="p-6 bg-gradient-to-br from-social-light to-card cursor-pointer hover:shadow-lg transition-shadow" onClick={() => navigate("/progress")}>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-muted-foreground">View Progress</h3>
              <Trophy className="w-5 h-5 text-warning" />
            </div>
            <p className="text-base font-medium text-primary">Detailed stats →</p>
          </Card>
        </div>

        {/* Today's Goal */}
        <Collapsible open={goalsExpanded} onOpenChange={setGoalsExpanded}>
          <Card className="p-6">
            <CollapsibleTrigger className="w-full">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <Trophy className="w-6 h-6 text-warning" />
                  <div className="text-left">
                    <h2 className="text-xl font-bold mb-1">Today's Goal</h2>
                    <p className="text-sm text-muted-foreground">
                      {dailyGoals.filter(g => g.completed).length} of {dailyGoals.length} conversations
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-2xl font-bold text-primary">
                    {Math.round((dailyGoals.filter(g => g.completed).length / dailyGoals.length) * 100)}%
                  </span>
                  <ChevronDown className={`w-5 h-5 transition-transform ${goalsExpanded ? "rotate-180" : ""}`} />
                </div>
              </div>
            </CollapsibleTrigger>
            <Progress 
              value={(dailyGoals.filter(g => g.completed).length / dailyGoals.length) * 100} 
              className="h-3 mb-4" 
            />
            
            <CollapsibleContent>
              <div className="space-y-2 pt-2 border-t">
                {dailyGoals.map((goal) => (
                  <div
                    key={goal.id}
                    className="flex items-center gap-3 p-3 rounded-lg bg-muted/30"
                  >
                    {goal.completed ? (
                      <CheckCircle2 className="w-5 h-5 text-success flex-shrink-0" />
                    ) : (
                      <Circle className="w-5 h-5 text-muted-foreground flex-shrink-0" />
                    )}
                    <span className={goal.completed ? "text-muted-foreground line-through" : ""}>
                      {goal.title}
                    </span>
                  </div>
                ))}
              </div>
            </CollapsibleContent>
          </Card>
        </Collapsible>

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
