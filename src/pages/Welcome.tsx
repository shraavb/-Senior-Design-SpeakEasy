import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Languages } from "lucide-react";

const languages = [
  "Spanish",
  "French",
  "German",
  "Italian",
  "Japanese",
  "Mandarin",
];

const Welcome = () => {
  const [selectedLanguage, setSelectedLanguage] = useState<string>("");
  const navigate = useNavigate();

  const handleContinue = () => {
    if (selectedLanguage) {
      navigate("/level");
    }
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
            <p className="text-lg text-muted-foreground">From Textbook to Real Conversation</p>
          </div>
        </div>

        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Which language are you learning?</h2>
          <div className="space-y-2">
            {languages.map((language) => (
              <button
                key={language}
                onClick={() => setSelectedLanguage(language)}
                className={`w-full p-4 text-left rounded-xl border-2 transition-all ${
                  selectedLanguage === language
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-primary/50 bg-card"
                }`}
              >
                <span className="text-lg">{language}</span>
              </button>
            ))}
          </div>
        </div>

        <Button
          onClick={handleContinue}
          disabled={!selectedLanguage}
          className="w-full py-6 text-lg"
          size="lg"
        >
          Continue
        </Button>
      </Card>
    </div>
  );
};

export default Welcome;
