import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ChevronLeft, ArrowUp, LogOut } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";
import { QuickSummary } from "@/components/feedback-metrics/quick-summary";
import { FluencyMetrics } from "@/components/feedback-metrics/fluency-metrics";
import { GrammarFeedback } from "@/components/feedback-metrics/grammar-feedback";
import { ErrorBreakdown } from "@/components/feedback-metrics/error-breakdown";
import { VocabularyInsights } from "@/components/feedback-metrics/vocabulary-insights";
import { SectionNav } from "@/components/feedback-metrics/section-nav";

const Progress = () => {
  const navigate = useNavigate();
  const { user, signOut } = useAuth();
  const { toast } = useToast();
  // Persist time filter to localStorage
  const [timeFilter, setTimeFilter] = useState<"today" | "weekly" | "monthly">(() => {
    const saved = localStorage.getItem("progressTimeFilter");
    return (saved as "today" | "weekly" | "monthly") || "weekly";
  });
  const [showScrollTop, setShowScrollTop] = useState(false);
  const [activeSection, setActiveSection] = useState("fluency");

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

  // Save time filter to localStorage when it changes
  useEffect(() => {
    localStorage.setItem("progressTimeFilter", timeFilter);
  }, [timeFilter]);

  // Handle scroll to top button visibility
  useEffect(() => {
    const handleScroll = () => {
      setShowScrollTop(window.scrollY > 400);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <header className="border-b bg-card/80 backdrop-blur-sm shadow-sm">
        <div className="max-w-[1600px] mx-auto px-8 py-4 flex items-center justify-between">
          <Button variant="ghost" onClick={() => navigate("/dashboard")}>
            <ChevronLeft className="w-5 h-5 mr-2" />
            Back to Dashboard
          </Button>
          {user && (
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
          )}
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto px-8 py-8 space-y-8">
        {/* Quick Summary */}
        <QuickSummary timeFilter={timeFilter} />

        {/* Section Navigation */}
        <SectionNav 
          activeSection={activeSection} 
          onSectionChange={setActiveSection}
          timeFilter={timeFilter}
          onTimeFilterChange={setTimeFilter}
        />

        {/* Main Metrics Sections */}
        <div className="space-y-16">
          {/* Section 1: Fluency & Pronunciation */}
          <section id="fluency" className="scroll-mt-32">
            <div className="mb-6 pb-4 border-b border-gray-200">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-1 h-8 bg-indigo-500 rounded-full"></div>
                <h2 className="text-2xl font-bold text-gray-900">Fluency & Pronunciation</h2>
              </div>
              <p className="text-gray-600 ml-4">Track your speaking clarity, speed, and natural flow</p>
            </div>
            <FluencyMetrics timeFilter={timeFilter} />
          </section>

          {/* Section 2: Grammar Feedback */}
          <section id="grammar" className="scroll-mt-32">
            <div className="mb-6 pb-4 border-b border-gray-200">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-1 h-8 bg-blue-500 rounded-full"></div>
                <h2 className="text-2xl font-bold text-gray-900">Grammar Feedback</h2>
              </div>
              <p className="text-gray-600 ml-4">Monitor your grammatical accuracy and sentence structure</p>
            </div>
            <GrammarFeedback timeFilter={timeFilter} />
          </section>

          {/* Section 3: Error Breakdown */}
          <section id="errors" className="scroll-mt-32">
            <div className="mb-6 pb-4 border-b border-gray-200">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-1 h-8 bg-red-500 rounded-full"></div>
                <h2 className="text-2xl font-bold text-gray-900">Error Breakdown</h2>
              </div>
              <p className="text-gray-600 ml-4">Understand the types of errors in your speech</p>
            </div>
            <ErrorBreakdown timeFilter={timeFilter} />
          </section>

          {/* Section 4: Vocabulary Insights */}
          <section id="vocabulary" className="scroll-mt-32">
            <div className="mb-6 pb-4 border-b border-gray-200">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-1 h-8 bg-emerald-500 rounded-full"></div>
                <h2 className="text-2xl font-bold text-gray-900">Vocabulary Insights</h2>
              </div>
              <p className="text-gray-600 ml-4">Explore your word usage and vocabulary growth</p>
            </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Most Common Words */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
              <div className="mb-4">
                <h3 className="text-gray-900 font-semibold">Most Common Words</h3>
                <p className="text-gray-600 text-sm mt-1">Your frequently used vocabulary</p>
              </div>

              {(() => {
                const commonWordsData = {
                  today: [
                    { word: "hablar", translation: "to speak", count: 8 },
                    { word: "tener", translation: "to have", count: 6 },
                    { word: "hacer", translation: "to do/make", count: 5 },
                    { word: "estar", translation: "to be", count: 4 },
                    { word: "poder", translation: "to be able", count: 3 },
                  ],
                  weekly: [
                    { word: "hablar", translation: "to speak", count: 24 },
                    { word: "tener", translation: "to have", count: 19 },
                    { word: "hacer", translation: "to do/make", count: 16 },
                    { word: "estar", translation: "to be", count: 15 },
                    { word: "poder", translation: "to be able", count: 12 },
                  ],
                  monthly: [
                    { word: "hablar", translation: "to speak", count: 98 },
                    { word: "tener", translation: "to have", count: 76 },
                    { word: "hacer", translation: "to do/make", count: 64 },
                    { word: "estar", translation: "to be", count: 58 },
                    { word: "poder", translation: "to be able", count: 45 },
                  ],
                };

                const commonWords = commonWordsData[timeFilter];

                if (commonWords.length === 0) {
                  return (
                    <div className="py-8 text-center">
                      <p className="text-gray-500 text-sm">No words tracked yet</p>
                      <p className="text-gray-400 text-xs mt-1">Start conversations to see your most used words</p>
                    </div>
                  );
                }

                return (
                  <div className="space-y-3">
                    {commonWords.map((item) => (
                      <div key={item.word} className="flex items-center justify-between">
                        <div className="flex-1">
                          <p className="text-gray-900">{item.word}</p>
                          <p className="text-gray-500 text-sm">{item.translation}</p>
                        </div>
                        <div className="w-12 h-8 bg-indigo-100 rounded-lg flex items-center justify-center text-indigo-700">
                          {item.count}
                        </div>
                      </div>
                    ))}
                  </div>
                );
              })()}
            </div>

            {/* Vocabulary Usage Chart */}
            <div className="lg:col-span-2">
              <VocabularyInsights timeFilter={timeFilter} />
            </div>
          </div>

          {/* New Words Used */}
          <div className="mt-6">
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
              <div className="mb-4">
                <h3 className="text-gray-900 font-semibold">New Words Used</h3>
                <p className="text-gray-600 text-sm mt-1">Recently learned vocabulary</p>
              </div>

              {(() => {
                const newWordsData = {
                  today: [
                    { word: "imprescindible", translation: "essential" },
                    { word: "desenvolver", translation: "to develop" },
                  ],
                  weekly: [
                    { word: "imprescindible", translation: "essential" },
                    { word: "desenvolver", translation: "to develop" },
                    { word: "cotidiano", translation: "daily" },
                    { word: "sustancial", translation: "substantial" },
                  ],
                  monthly: [
                    { word: "imprescindible", translation: "essential" },
                    { word: "desenvolver", translation: "to develop" },
                    { word: "cotidiano", translation: "daily" },
                    { word: "sustancial", translation: "substantial" },
                    { word: "persistente", translation: "persistent" },
                    { word: "efímero", translation: "ephemeral" },
                    { word: "próspero", translation: "prosperous" },
                    { word: "versátil", translation: "versatile" },
                  ],
                };

                const newWords = newWordsData[timeFilter];
                
                if (newWords.length === 0) {
                  return (
                    <div className="py-8 text-center">
                      <p className="text-gray-500 text-sm">No new words yet</p>
                      <p className="text-gray-400 text-xs mt-1">Start practicing to see your new vocabulary here</p>
                    </div>
                  );
                }

                return (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {newWords.map((item) => (
                      <div key={item.word} className="p-3 bg-emerald-50 rounded-lg border border-emerald-100">
                        <p className="text-emerald-900 font-medium">{item.word}</p>
                        <p className="text-emerald-700 text-sm mt-0.5">{item.translation}</p>
                      </div>
                    ))}
                  </div>
                );
              })()}
            </div>
          </div>
          </section>
        </div>
      </main>

      {/* Scroll to Top Button */}
      {showScrollTop && (
        <button
          onClick={scrollToTop}
          className="fixed bottom-8 right-8 p-3 bg-indigo-500 text-white rounded-full shadow-lg hover:bg-indigo-600 transition-all hover:scale-110 z-50"
          aria-label="Scroll to top"
        >
          <ArrowUp className="w-5 h-5" />
        </button>
      )}
    </div>
  );
};

export default Progress;
