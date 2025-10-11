import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ChevronLeft, Trophy, Medal, Award, Flame, ChevronDown } from "lucide-react";

const topThree = [
  { name: "Sarah Chen", points: 2847, streak: 28, rank: 1, initials: "SC" },
  { name: "Miguel Rodriguez", points: 2634, streak: 21, rank: 2, initials: "MR" },
  { name: "Emma Williams", points: 2521, streak: 19, rank: 3, initials: "EW" },
];

const otherUsers = [
  { name: "You", points: 1893, streak: 7, rank: 4, initials: "YO", isCurrentUser: true },
  { name: "James Park", points: 1756, streak: 14, rank: 5, initials: "JP" },
  { name: "Lisa Anderson", points: 1642, streak: 12, rank: 6, initials: "LA" },
  { name: "David Kim", points: 1534, streak: 9, rank: 7, initials: "DK" },
  { name: "Sophie Martin", points: 1421, streak: 11, rank: 8, initials: "SM" },
  { name: "Alex Johnson", points: 1298, streak: 8, rank: 9, initials: "AJ" },
  { name: "Maria Garcia", points: 1187, streak: 6, rank: 10, initials: "MG" },
];

const Leaderboard = () => {
  const navigate = useNavigate();
  const [showAll, setShowAll] = useState(false);
  
  // Show only first 2 entries by default (to make top 5 total with podium)
  const displayedUsers = showAll ? otherUsers : otherUsers.slice(0, 2);

  const getRankIcon = (rank: number) => {
    switch (rank) {
      case 1:
        return <Trophy className="w-6 h-6 text-warning" />;
      case 2:
        return <Medal className="w-6 h-6 text-muted-foreground" />;
      case 3:
        return <Award className="w-6 h-6 text-professional" />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <Button variant="ghost" onClick={() => navigate("/dashboard")}>
            <ChevronLeft className="w-5 h-5 mr-2" />
            Back to Dashboard
          </Button>
          <h1 className="text-2xl font-bold mt-4">Weekly Leaderboard</h1>
          <p className="text-muted-foreground">Top learners this week</p>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        {/* Top 3 Podium */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          {/* 2nd Place */}
          <div className="flex flex-col items-center pt-12">
            <Medal className="w-8 h-8 text-muted-foreground mb-2" />
            <div className="w-16 h-16 rounded-full bg-secondary flex items-center justify-center text-lg font-bold mb-2">
              {topThree[1].initials}
            </div>
            <p className="font-semibold text-center">{topThree[1].name.split(" ")[0]}</p>
            <p className="text-2xl font-bold">{topThree[1].points}</p>
          </div>

          {/* 1st Place */}
          <div className="flex flex-col items-center">
            <Trophy className="w-10 h-10 text-warning mb-2" />
            <div className="w-20 h-20 rounded-full bg-warning/10 border-4 border-warning flex items-center justify-center text-xl font-bold mb-2">
              {topThree[0].initials}
            </div>
            <p className="font-semibold text-center">{topThree[0].name.split(" ")[0]}</p>
            <p className="text-3xl font-bold">{topThree[0].points}</p>
          </div>

          {/* 3rd Place */}
          <div className="flex flex-col items-center pt-12">
            <Award className="w-8 h-8 text-professional mb-2" />
            <div className="w-16 h-16 rounded-full bg-secondary flex items-center justify-center text-lg font-bold mb-2">
              {topThree[2].initials}
            </div>
            <p className="font-semibold text-center">{topThree[2].name.split(" ")[0]}</p>
            <p className="text-2xl font-bold">{topThree[2].points}</p>
          </div>
        </div>

        {/* Rest of Rankings */}
        <div className="space-y-2">
          {displayedUsers.map((user) => (
            <Card
              key={user.rank}
              className={`p-4 ${user.isCurrentUser ? "border-2 border-primary bg-primary/5" : ""}`}
            >
              <div className="flex items-center gap-4">
                <div className="w-12 text-center">
                  {getRankIcon(user.rank) || (
                    <span className="text-xl font-bold text-muted-foreground">{user.rank}</span>
                  )}
                </div>
                <div className="w-12 h-12 rounded-full bg-secondary flex items-center justify-center font-bold">
                  {user.initials}
                </div>
                <div className="flex-1">
                  <p className="font-semibold">
                    {user.name} {user.isCurrentUser && <Badge variant="secondary">You</Badge>}
                  </p>
                  <p className="text-sm text-muted-foreground flex items-center">
                    {user.streak} day streak <Flame className="w-4 h-4 ml-1 text-streak" />
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xl font-bold">{user.points}</p>
                  <p className="text-xs text-muted-foreground">points</p>
                </div>
              </div>
            </Card>
          ))}
          
          {/* Show More Button */}
          {otherUsers.length > 2 && (
            <Button
              variant="outline"
              className="w-full"
              onClick={() => setShowAll(!showAll)}
            >
              {showAll ? "Show Less" : `Show ${otherUsers.length - 2} More`}
              <ChevronDown className={`w-4 h-4 ml-2 transition-transform ${showAll ? "rotate-180" : ""}`} />
            </Button>
          )}
        </div>

        {/* How Points Work */}
        <Card className="p-6 bg-muted/30">
          <h3 className="font-semibold mb-3">How Points Work</h3>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li>• Complete a conversation: +100 points</li>
            <li>• Daily streak bonus: +50 points per day</li>
            <li>• High fluency score (85+): +50 bonus points</li>
            <li>• Complete a module: +200 points</li>
          </ul>
        </Card>
      </main>
    </div>
  );
};

export default Leaderboard;
