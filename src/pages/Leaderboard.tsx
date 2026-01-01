import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ChevronLeft, Trophy, Medal, Award, Flame, ChevronDown } from "lucide-react";

const leader = { name: "Sarah Chen", minutes: 847, streak: 28, rank: 1, initials: "SC" };

const allUsers = [
  { name: "Miguel Rodriguez", minutes: 634, streak: 21, rank: 2, initials: "MR" },
  { name: "Emma Williams", minutes: 521, streak: 19, rank: 3, initials: "EW" },
  { name: "You", minutes: 193, streak: 7, rank: 4, initials: "YO", isCurrentUser: true },
  { name: "James Park", minutes: 456, streak: 14, rank: 5, initials: "JP" },
  { name: "Lisa Anderson", minutes: 342, streak: 12, rank: 6, initials: "LA" },
  { name: "David Kim", minutes: 234, streak: 9, rank: 7, initials: "DK" },
  { name: "Sophie Martin", minutes: 421, streak: 11, rank: 8, initials: "SM" },
  { name: "Alex Johnson", minutes: 198, streak: 8, rank: 9, initials: "AJ" },
  { name: "Maria Garcia", minutes: 187, streak: 6, rank: 10, initials: "MG" },
];

const Leaderboard = () => {
  const navigate = useNavigate();
  const [showAll, setShowAll] = useState(false);

  // Show first 4 entries by default (ranks 2-5), rest on expand
  const displayedUsers = showAll ? allUsers : allUsers.slice(0, 4);

  const getRankIcon = (rank: number) => {
    switch (rank) {
      case 2:
        return <Medal className="w-5 h-5 text-muted-foreground" />;
      case 3:
        return <Award className="w-5 h-5 text-professional" />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <Button variant="ghost" onClick={() => navigate("/dashboard")} className="mb-2">
            <ChevronLeft className="w-5 h-5 mr-2" />
            Back to Dashboard
          </Button>
          <div className="ml-3">
            <h1 className="text-xl font-bold">Weekly Leaderboard</h1>
            <p className="text-sm text-muted-foreground">Top learners this week</p>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6 space-y-4">
        {/* Trophy Podium - Desktop Only */}
        <div className="hidden md:block">
          <Card className="p-8 bg-gradient-to-br from-warning/5 via-background to-primary/5">
            <div className="flex items-end justify-center gap-4">
              {/* 2nd Place - Silver */}
              <div className="flex flex-col items-center">
                <div className="w-16 h-16 rounded-full bg-gray-200 border-4 border-gray-400 flex items-center justify-center text-xl font-bold mb-2">
                  {allUsers[0].initials}
                </div>
                <Medal className="w-8 h-8 text-gray-400 mb-1" />
                <p className="font-semibold text-sm">{allUsers[0].name}</p>
                <p className="text-lg font-bold text-gray-600">{allUsers[0].minutes} min</p>
                <div className="w-24 h-20 bg-gray-300 rounded-t-lg mt-2 flex items-center justify-center">
                  <span className="text-3xl font-bold text-gray-600">2</span>
                </div>
              </div>

              {/* 1st Place - Gold */}
              <div className="flex flex-col items-center -mb-4">
                <div className="w-20 h-20 rounded-full bg-warning/20 border-4 border-warning flex items-center justify-center text-2xl font-bold mb-2">
                  {leader.initials}
                </div>
                <Trophy className="w-10 h-10 text-warning mb-1" />
                <p className="font-bold">{leader.name}</p>
                <p className="text-xl font-bold text-warning">{leader.minutes} min</p>
                <div className="w-28 h-28 bg-warning/30 rounded-t-lg mt-2 flex items-center justify-center">
                  <span className="text-4xl font-bold text-warning">1</span>
                </div>
              </div>

              {/* 3rd Place - Bronze */}
              <div className="flex flex-col items-center">
                <div className="w-16 h-16 rounded-full bg-orange-100 border-4 border-orange-400 flex items-center justify-center text-xl font-bold mb-2">
                  {allUsers[1].initials}
                </div>
                <Award className="w-8 h-8 text-orange-400 mb-1" />
                <p className="font-semibold text-sm">{allUsers[1].name}</p>
                <p className="text-lg font-bold text-orange-600">{allUsers[1].minutes} min</p>
                <div className="w-24 h-16 bg-orange-200 rounded-t-lg mt-2 flex items-center justify-center">
                  <span className="text-3xl font-bold text-orange-600">3</span>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Mobile: #1 Leader Highlight */}
        <Card className="p-6 bg-gradient-to-r from-warning/10 to-warning/5 border-warning/30 md:hidden">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3">
              <Trophy className="w-8 h-8 text-warning" />
              <div className="w-14 h-14 rounded-full bg-warning/20 border-2 border-warning flex items-center justify-center text-lg font-bold">
                {leader.initials}
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-bold text-lg">{leader.name}</p>
              <p className="text-sm text-muted-foreground flex items-center">
                <Flame className="w-4 h-4 mr-1 text-streak" /> {leader.streak} day streak
              </p>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold whitespace-nowrap">{leader.minutes} min</p>
            </div>
          </div>
        </Card>

        {/* Rankings List */}
        <div className="space-y-2">
          {displayedUsers.map((user) => (
            <Card
              key={user.rank}
              className={`p-4 ${user.isCurrentUser ? "border-2 border-primary bg-primary/5" : ""} ${
                (user.rank === 2 || user.rank === 3) ? "md:hidden" : ""
              }`}
            >
              <div className="flex items-center gap-3">
                <div className="w-8 text-center flex-shrink-0">
                  {getRankIcon(user.rank) || (
                    <span className="text-lg font-bold text-muted-foreground">{user.rank}</span>
                  )}
                </div>
                <div className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center font-bold text-sm flex-shrink-0">
                  {user.initials}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-sm">
                    {user.name} {user.isCurrentUser && <Badge variant="secondary" className="ml-1 text-xs">You</Badge>}
                  </p>
                  <p className="text-xs text-muted-foreground flex items-center">
                    <Flame className="w-3 h-3 mr-1 text-streak" /> {user.streak} day streak
                  </p>
                </div>
                <div className="text-right flex-shrink-0">
                  <p className="text-lg font-bold">{user.minutes}</p>
                  <p className="text-xs text-muted-foreground">minutes</p>
                </div>
              </div>
            </Card>
          ))}

          {/* Show More Button */}
          {allUsers.length > 4 && (
            <Button
              variant="outline"
              className="w-full"
              onClick={() => setShowAll(!showAll)}
            >
              {showAll ? "Show Less" : `Show ${allUsers.length - 4} More`}
              <ChevronDown className={`w-4 h-4 ml-2 transition-transform ${showAll ? "rotate-180" : ""}`} />
            </Button>
          )}
        </div>

        {/* How Ranking Works */}
        <Card className="p-6 bg-muted/30">
          <h3 className="font-semibold mb-3">How Ranking Works</h3>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li>• Rankings are based on total practice minutes this week</li>
            <li>• Keep your daily streak alive for consistent progress</li>
            <li>• The more you practice, the higher you climb!</li>
          </ul>
        </Card>
      </main>
    </div>
  );
};

export default Leaderboard;
