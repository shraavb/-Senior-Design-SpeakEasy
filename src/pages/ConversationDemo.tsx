import { useState } from "react";
import { ConversationView } from "@/components/ConversationView";
import { FeedbackToggle } from "@/components/FeedbackToggle";
import { useNavigate } from "react-router-dom";
import { TooltipProvider } from "@/components/ui/tooltip";

export default function ConversationDemo() {
  const navigate = useNavigate();
  const [feedbackMode, setFeedbackMode] = useState<"on" | "off">("on");

  return (
    <TooltipProvider>
      <div className="h-screen flex flex-col">
        <FeedbackToggle
          feedbackMode={feedbackMode}
          onToggle={(mode) => setFeedbackMode(mode)}
        />
        <ConversationView
          feedbackMode={feedbackMode}
          scenario="Ordering at a Restaurant"
          language="Mandarin"
          languageFlag="🇨🇳"
          onBack={() => navigate(-1)}
        />
      </div>
    </TooltipProvider>
  );
}
