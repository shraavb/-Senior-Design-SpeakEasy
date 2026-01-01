import { useState, useEffect } from "react";
import appIcon from "@/assets/icon.png";

interface SplashScreenProps {
  onComplete: () => void;
  duration?: number;
}

export function SplashScreen({ onComplete, duration = 2500 }: SplashScreenProps) {
  const [isVisible, setIsVisible] = useState(true);
  const [isFadingOut, setIsFadingOut] = useState(false);

  useEffect(() => {
    // Start fade out before completing
    const fadeTimer = setTimeout(() => {
      setIsFadingOut(true);
    }, duration - 500);

    // Complete after full duration
    const completeTimer = setTimeout(() => {
      setIsVisible(false);
      onComplete();
    }, duration);

    return () => {
      clearTimeout(fadeTimer);
      clearTimeout(completeTimer);
    };
  }, [duration, onComplete]);

  if (!isVisible) return null;

  return (
    <div
      className={`fixed inset-0 z-50 flex flex-col items-center justify-center bg-gradient-to-br from-primary/10 via-background to-social/10 transition-opacity duration-500 ${
        isFadingOut ? "opacity-0" : "opacity-100"
      }`}
    >
      {/* Animated logo container */}
      <div className="flex flex-col items-center gap-6">
        {/* App Icon with pulse animation */}
        <div className="relative">
          <div className="absolute inset-0 bg-primary/20 rounded-3xl blur-xl animate-pulse" />
          <img
            src={appIcon}
            alt="SpeakEasy"
            className="relative w-28 h-28 md:w-36 md:h-36 rounded-3xl opacity-0 animate-scale-in"
          />
        </div>

        {/* App name */}
        <div className="text-center opacity-0 animate-slide-up">
          <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-primary to-social bg-clip-text text-transparent">
            SpeakEasy
          </h1>
          <p className="text-muted-foreground mt-2 text-lg">
            Stop Memorizing. Start Conversing.
          </p>
        </div>

        {/* Loading indicator */}
        <div className="flex gap-1.5 mt-4 opacity-0 animate-fade-in-delayed">
          <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: "0ms" }} />
          <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: "150ms" }} />
          <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: "300ms" }} />
        </div>
      </div>
    </div>
  );
}
