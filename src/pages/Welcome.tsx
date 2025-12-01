import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Languages } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

const languages = [
  { name: "Spanish", flag: "🇪🇸" },
  { name: "French", flag: "🇫🇷" },
  { name: "German", flag: "🇩🇪" },
  { name: "Italian", flag: "🇮🇹" },
  { name: "Japanese", flag: "🇯🇵" },
  { name: "Mandarin", flag: "🇨🇳" },
];

const Welcome = () => {
  const [selectedLanguage, setSelectedLanguage] = useState<string>("");
  const navigate = useNavigate();
  const { user } = useAuth();

  // Allow logged-in users to select language (don't auto-redirect)
  // This allows new signups to complete onboarding

  const handleContinue = () => {
    if (selectedLanguage) {
      localStorage.setItem('selectedLanguage', selectedLanguage);
      // If user is logged in, go to dashboard to see modules
      // If not logged in, go to level selection for onboarding
      if (user) {
        navigate("/dashboard");
      } else {
        navigate(`/level?language=${selectedLanguage}`);
      }
    }
  };

  const handleGetStarted = () => {
    navigate("/signup");
  };

  const handleSignIn = () => {
    navigate("/login");
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-tourism-light via-accent to-professional-light p-4">
      <Card className="w-full max-w-2xl p-8 md:p-12 space-y-8 shadow-xl">
        <div className="flex flex-col items-center text-center space-y-4">
          <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-primary to-social flex items-center justify-center shadow-lg">
            <Languages className="w-10 h-10 text-white" />
          </div>
          <div>
            <h1 className="text-3xl md:text-4xl font-bold mb-2">Welcome to SpeakEasy</h1>
            <p className="text-lg text-muted-foreground">Stop Memorizing. Start Conversing.</p>
          </div>
        </div>

        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Which language are you learning?</h2>
          <div className="space-y-2">
            {languages.map((language) => (
              <button
                key={language.name}
                onClick={() => setSelectedLanguage(language.name)}
                className={`w-full p-4 text-left rounded-xl border-2 transition-all ${
                  selectedLanguage === language.name
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-primary/50 bg-card"
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-3xl">{language.flag}</span>
                  <span className="text-lg">{language.name}</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-3">
          <Button
            onClick={handleContinue}
            disabled={!selectedLanguage}
            className="w-full py-6 text-lg"
            size="lg"
          >
            Continue
          </Button>
          {!user && (
            <>
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-card px-2 text-muted-foreground">Or</span>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <Button
                  onClick={handleGetStarted}
                  variant="outline"
                  className="w-full"
                >
                  Get Started
                </Button>
                <Button
                  onClick={handleSignIn}
                  variant="outline"
                  className="w-full"
                >
                  Sign In
                </Button>
              </div>
            </>
          )}
        </div>
      </Card>
    </div>
  );
};

export default Welcome;
