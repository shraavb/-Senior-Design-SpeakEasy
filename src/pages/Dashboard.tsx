import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Flame, TrendingUp, Trophy, Plane, Users, Briefcase, ChevronRight, ChevronDown, CheckCircle2, Circle, Map, LogOut, User, Languages } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";
import { useUserProfile } from "@/hooks/useUserProfile";
import { getTodayCompletedModules, type ModuleType } from "@/utils/dailyGoals";
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
  const { user, signOut } = useAuth();
  const { toast } = useToast();
  const { profile, loading: profileLoading, updateProfile } = useUserProfile();
  
  // Get language from profile or fallback to localStorage or default
  const getInitialLanguage = () => {
    if (profile?.selected_language) {
      return languages.find(lang => lang.name === profile.selected_language) || languages[0];
    }
    const storedLanguage = localStorage.getItem('selectedLanguage');
    return languages.find(lang => lang.name === storedLanguage) || languages[0];
  };
  
  const [selectedLanguage, setSelectedLanguage] = useState(getInitialLanguage());
  const [goalsExpanded, setGoalsExpanded] = useState(false);

  // Update selected language when profile loads
  useEffect(() => {
    if (profile?.selected_language) {
      const lang = languages.find(l => l.name === profile.selected_language);
      if (lang) {
        setSelectedLanguage(lang);
      }
    }
  }, [profile?.selected_language]);

  const handleLanguageChange = async (language: typeof languages[0]) => {
    setSelectedLanguage(language);
    localStorage.setItem('selectedLanguage', language.name);
    
    // Update user profile if logged in
    if (user && updateProfile) {
      const { error } = await updateProfile({ selected_language: language.name });
      if (error) {
        console.error('Error updating language:', error);
        toast({
          title: "Error",
          description: "Failed to save language preference",
          variant: "destructive",
        });
      }
    }
  };

  const handleSignOut = async () => {
    await signOut();
    toast({
      title: "Signed out",
      description: "You have been signed out successfully",
    });
    navigate("/");
  };

  const getUserInitials = () => {
    if (!user?.email) return "U";
    return user.email.charAt(0).toUpperCase();
  };

  // Define daily goals
  const dailyGoalsConfig = [
    { id: 1, title: "Complete 1 Tourism conversation", module: "tourism" as ModuleType },
    { id: 2, title: "Complete 1 Social conversation", module: "social" as ModuleType },
    { id: 3, title: "Complete 1 Professional conversation", module: "professional" as ModuleType },
  ];

  // Get completed modules for today
  const completedToday = user ? getTodayCompletedModules(user.id) : [];
  
  // Map goals with completion status
  const dailyGoals = dailyGoalsConfig.map(goal => ({
    ...goal,
    completed: completedToday.includes(goal.module)
  }));

  return (
    <div className="min-h-screen bg-gradient-to-br from-tourism-light/50 to-background">
      <header className="border-b bg-card/80 backdrop-blur-sm shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-social bg-clip-text text-transparent">SpeakEasy</h1>
            {user && (
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
            )}
          </div>
          <div className="flex items-center gap-2">
            {user ? (
              <>
                <Button variant="ghost" onClick={() => navigate("/learning-map")} className="hover:bg-tourism-light">
                  <Map className="w-5 h-5 mr-2 text-primary" />
                  Map
                </Button>
                <Button variant="ghost" onClick={() => navigate("/leaderboard")} className="hover:bg-tourism-light">
                  <Trophy className="w-5 h-5 mr-2 text-warning" />
                  Leaderboard
                </Button>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button className="flex items-center gap-2 p-2 rounded-full hover:bg-muted transition-colors">
                      <Avatar className="w-8 h-8">
                        <AvatarFallback className="bg-primary text-primary-foreground">
                          {getUserInitials()}
                        </AvatarFallback>
                      </Avatar>
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-56">
                    <div className="px-2 py-1.5">
                      <p className="text-sm font-medium">{user?.email}</p>
                    </div>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={handleSignOut} className="cursor-pointer text-destructive">
                      <LogOut className="w-4 h-4 mr-2" />
                      Sign Out
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </>
            ) : (
              <Button onClick={() => navigate("/signup")} className="ml-auto">
                Sign Up
              </Button>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 space-y-6">
        {/* Stats Cards - Only show when logged in */}
        {user ? (
          <>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card className="p-6 bg-gradient-to-br from-professional-light to-card hover:shadow-lg transition-shadow">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-muted-foreground">Daily Streak</h3>
                  <Flame className="w-5 h-5 text-streak" />
                </div>
                <p className="text-3xl font-bold text-professional">
                  {profileLoading ? "..." : (profile?.daily_streak || 0)}
                </p>
                <p className="text-sm text-muted-foreground">days</p>
              </Card>

              <Card className="p-6 bg-gradient-to-br from-tourism-light to-card hover:shadow-lg transition-shadow">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-muted-foreground">Fluency Score</h3>
                  <TrendingUp className="w-5 h-5 text-success" />
                </div>
                <p className="text-3xl font-bold text-tourism">
                  {profileLoading ? "..." : (profile?.fluency_score || 0)}
                </p>
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
          </>
        ) : (
          /* Call-to-Action Card for Non-Signed-In Users */
          <Card className="p-8 md:p-12 bg-gradient-to-br from-primary/10 via-social/10 to-tourism/10 border-2 border-primary/20">
            <div className="flex flex-col md:flex-row items-center gap-6 md:gap-8">
              <div className="flex-1 text-center md:text-left">
                <h2 className="text-3xl md:text-4xl font-bold mb-3 bg-gradient-to-r from-primary to-social bg-clip-text text-transparent">
                  Start Your Language Learning Journey
                </h2>
                <p className="text-lg text-muted-foreground mb-6">
                  Master conversational fluency through real-world practice. Sign up to track your progress, build your streak, and achieve your language goals.
                </p>
                <div className="flex flex-col sm:flex-row gap-3 justify-center md:justify-start">
                  <Button 
                    onClick={() => navigate("/signup")} 
                    size="lg"
                    className="text-lg px-8 py-6"
                  >
                    Get Started
                  </Button>
                  <Button 
                    onClick={() => navigate("/login")} 
                    variant="outline"
                    size="lg"
                    className="text-lg px-8 py-6"
                  >
                    Sign In
                  </Button>
                </div>
              </div>
              <div className="flex-shrink-0">
                <div className="w-32 h-32 md:w-40 md:h-40 rounded-full bg-gradient-to-br from-primary to-social flex items-center justify-center shadow-lg">
                  <Languages className="w-16 h-16 md:w-20 md:h-20 text-white" />
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* Practice Modules */}
        <div>
          <h2 className="text-2xl font-bold mb-4">Choose Your Practice Module</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {modules.map((module) => {
              const Icon = module.icon;
              const handleModuleClick = () => {
                if (!user) {
                  toast({
                    title: "Sign up required",
                    description: "Please sign up to access practice modules",
                    variant: "default",
                  });
                  navigate("/signup");
                } else {
                  navigate(module.path);
                }
              };
              return (
                <Card
                  key={module.title}
                  className="p-6 cursor-pointer hover:shadow-lg transition-all hover:-translate-y-1"
                  onClick={handleModuleClick}
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

        {/* Recommended - Only show when logged in */}
        {user && profile?.goal && (
          <Card className="p-6 bg-muted/30">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold mb-1">Recommended for You</h3>
                <p className="text-sm text-muted-foreground">Continue with {profile.goal}</p>
              </div>
              <Button onClick={() => {
                const modulePath = modules.find(m => m.title === profile.goal)?.path || "/module/tourism";
                navigate(modulePath);
              }}>Start Practicing</Button>
            </div>
          </Card>
        )}
      </main>
    </div>
  );
};

export default Dashboard;
