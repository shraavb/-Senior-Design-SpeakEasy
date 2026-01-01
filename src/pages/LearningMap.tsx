import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ChevronLeft, CheckCircle2, Lock, MapPin } from "lucide-react";
import restaurantImg from "@/assets/scenario-restaurant.jpg";
import directionsImg from "@/assets/scenario-directions.jpg";
import hotelImg from "@/assets/scenario-hotel.jpg";
import transitImg from "@/assets/scenario-transit.jpg";
import cafeFriendsImg from "@/assets/scenario-cafe-friends.jpg";
import smalltalkImg from "@/assets/scenario-smalltalk.jpg";
import opinionsImg from "@/assets/scenario-opinions.jpg";
import feelingsImg from "@/assets/scenario-feelings.jpg";
import culturalImg from "@/assets/scenario-cultural.jpg";
import introductionsImg from "@/assets/scenario-introductions.jpg";
import emailsImg from "@/assets/scenario-emails.jpg";
import meetingImg from "@/assets/scenario-meeting.jpg";
import presentationImg from "@/assets/scenario-presentation.jpg";

const learningPath = [
  // Tourism Module
  {
    module: "Tourism & Travel",
    moduleColor: "tourism",
    scenarios: [
      {
        title: "Ordering at a Restaurant",
        difficulty: "easy",
        completed: true,
        image: restaurantImg,
        path: "/module/tourism",
      },
      {
        title: "Asking for Directions",
        difficulty: "easy",
        completed: true,
        image: directionsImg,
        path: "/module/tourism",
      },
      {
        title: "Hotel Check-in",
        difficulty: "medium",
        completed: false,
        image: hotelImg,
        path: "/module/tourism",
      },
      {
        title: "Using Public Transportation",
        difficulty: "medium",
        completed: false,
        image: transitImg,
        path: "/module/tourism",
      },
      {
        title: "Making Local Friends",
        difficulty: "hard",
        locked: true,
        image: cafeFriendsImg,
        path: "/module/tourism",
      },
    ],
  },
  // Social Module
  {
    module: "Personal & Social",
    moduleColor: "social",
    scenarios: [
      {
        title: "Casual Small Talk",
        difficulty: "easy",
        completed: false,
        image: smalltalkImg,
        path: "/module/social",
      },
      {
        title: "Sharing Opinions",
        difficulty: "medium",
        completed: false,
        image: opinionsImg,
        path: "/module/social",
      },
      {
        title: "Discussing Feelings",
        difficulty: "medium",
        completed: false,
        image: feelingsImg,
        path: "/module/social",
      },
      {
        title: "Cultural Discussions",
        difficulty: "hard",
        locked: true,
        image: culturalImg,
        path: "/module/social",
      },
    ],
  },
  // Professional Module
  {
    module: "Professional & Career",
    moduleColor: "professional",
    scenarios: [
      {
        title: "Professional Introductions",
        difficulty: "easy",
        completed: false,
        image: introductionsImg,
        path: "/module/professional",
      },
      {
        title: "Discussing Emails",
        difficulty: "medium",
        completed: false,
        image: emailsImg,
        path: "/module/professional",
      },
      {
        title: "Team Meetings",
        difficulty: "medium",
        completed: false,
        image: meetingImg,
        path: "/module/professional",
      },
      {
        title: "Giving Presentations",
        difficulty: "hard",
        locked: true,
        image: presentationImg,
        path: "/module/professional",
      },
    ],
  },
];

const LearningMap = () => {
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
    <div className="min-h-screen bg-gradient-to-br from-tourism-light/30 via-background to-social-light/30">
      <header className="border-b bg-card/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <Button variant="ghost" onClick={() => navigate("/dashboard")} className="mb-2">
            <ChevronLeft className="w-5 h-5 mr-2" />
            Back to Dashboard
          </Button>
          <div className="flex items-center gap-3 ml-3">
            <MapPin className="w-6 h-6 text-primary" />
            <div>
              <h1 className="text-xl font-bold">Learning Journey Map</h1>
              <p className="text-sm text-muted-foreground">Follow your path to fluency</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Legend - centered on mobile */}
        <Card className="mb-6 p-3 bg-muted/30">
          <div className="flex justify-center">
            <div className="flex flex-wrap justify-center items-center gap-x-6 gap-y-2 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 rounded-full bg-success flex items-center justify-center">
                  <CheckCircle2 className="w-3 h-3 text-white" />
                </div>
                <span>Completed</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 rounded-full bg-primary flex items-center justify-center">
                  <div className="w-2 h-2 rounded-full bg-white" />
                </div>
                <span>Available</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 rounded-full bg-muted flex items-center justify-center">
                  <Lock className="w-3 h-3 text-muted-foreground" />
                </div>
                <span>Locked</span>
              </div>
            </div>
          </div>
        </Card>

        <div className="space-y-12">
          {learningPath.map((module, moduleIndex) => (
            <div key={moduleIndex} className="relative">
              {/* Module Header */}
              <div className="flex items-center gap-4 mb-6">
                <div className={`w-2 h-16 bg-gradient-to-b from-${module.moduleColor} to-${module.moduleColor}/50 rounded-full`} />
                <div>
                  <h2 className="text-2xl font-bold">{module.module}</h2>
                  <p className="text-sm text-muted-foreground">
                    {module.scenarios.filter(s => s.completed).length} of {module.scenarios.length} completed
                  </p>
                </div>
              </div>

              {/* Scenarios Path */}
              <div className="ml-8 space-y-6 relative">
                {/* Connecting Line */}
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-muted via-muted to-transparent" />

                {module.scenarios.map((scenario, scenarioIndex) => (
                  <div 
                    key={scenarioIndex}
                    className="relative pl-12 animate-fade-in"
                    style={{ animationDelay: `${moduleIndex * 100 + scenarioIndex * 50}ms` }}
                  >
                    {/* Node Indicator */}
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-1/2">
                      {scenario.completed ? (
                        <div className="w-8 h-8 rounded-full bg-success flex items-center justify-center shadow-lg">
                          <CheckCircle2 className="w-5 h-5 text-white" />
                        </div>
                      ) : scenario.locked ? (
                        <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center shadow-lg">
                          <Lock className="w-4 h-4 text-muted-foreground" />
                        </div>
                      ) : (
                        <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center shadow-lg animate-pulse">
                          <div className="w-3 h-3 rounded-full bg-white" />
                        </div>
                      )}
                    </div>

                    {/* Scenario Card */}
                    <Card 
                      className={`overflow-hidden hover:shadow-xl transition-all hover:-translate-y-1 cursor-pointer ${
                        scenario.locked ? "opacity-60" : ""
                      }`}
                      onClick={() => !scenario.locked && navigate(scenario.path)}
                    >
                      <div className="flex flex-col sm:flex-row gap-4">
                        <div className="w-full sm:w-48 h-32 flex-shrink-0 overflow-hidden">
                          <img 
                            src={scenario.image} 
                            alt={scenario.title}
                            className="w-full h-full object-cover hover:scale-110 transition-transform duration-300"
                          />
                        </div>
                        <div className="flex-1 p-4 flex items-center justify-between gap-4">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <h3 className="text-lg font-semibold">{scenario.title}</h3>
                              {scenario.completed && (
                                <Badge className="bg-success/10 text-success">Completed</Badge>
                              )}
                              {scenario.locked && (
                                <Badge variant="secondary">Locked</Badge>
                              )}
                            </div>
                            <Badge className={getDifficultyColor(scenario.difficulty)}>
                              {scenario.difficulty}
                            </Badge>
                          </div>
                        </div>
                      </div>
                    </Card>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

      </main>
    </div>
  );
};

export default LearningMap;
