import { useState } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { isNativePlatform } from "@/services/speechService";
import { SplashScreen } from "@/components/SplashScreen";
import Welcome from "./pages/Welcome";
import Login from "./pages/Login";
import SignUp from "./pages/SignUp";
import Level from "./pages/Level";
import Goal from "./pages/Goal";
import Dashboard from "./pages/Dashboard";
import ModuleTourism from "./pages/ModuleTourism";
import ModuleSocial from "./pages/ModuleSocial";
import ModuleProfessional from "./pages/ModuleProfessional";
import Progress from "./pages/Progress";
import Leaderboard from "./pages/Leaderboard";
import LearningMap from "./pages/LearningMap";
import Conversation from "./pages/Conversation";
import ConversationDemo from "./pages/ConversationDemo";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

// Use root path for native mobile apps, Vite's base URL for web
const basename = isNativePlatform() ? '/' : import.meta.env.BASE_URL;

const App = () => {
  const [showSplash, setShowSplash] = useState(() => {
    // Only show splash on first visit per session
    const hasSeenSplash = sessionStorage.getItem("hasSeenSplash");
    return !hasSeenSplash;
  });

  const handleSplashComplete = () => {
    sessionStorage.setItem("hasSeenSplash", "true");
    setShowSplash(false);
  };

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <TooltipProvider>
          {showSplash && <SplashScreen onComplete={handleSplashComplete} />}
          <Toaster />
          <Sonner />
          <BrowserRouter basename={basename}>
            <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/welcome" element={<Welcome />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<SignUp />} />
            <Route path="/level" element={<Level />} />
            <Route path="/goal" element={<Goal />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route
              path="/module/tourism"
              element={
                <ProtectedRoute>
                  <ModuleTourism />
                </ProtectedRoute>
              }
            />
            <Route
              path="/module/social"
              element={
                <ProtectedRoute>
                  <ModuleSocial />
                </ProtectedRoute>
              }
            />
            <Route
              path="/module/professional"
              element={
                <ProtectedRoute>
                  <ModuleProfessional />
                </ProtectedRoute>
              }
            />
            <Route
              path="/conversation"
              element={
                <ProtectedRoute>
                  <Conversation />
                </ProtectedRoute>
              }
            />
            <Route path="/conversation-demo" element={<ConversationDemo />} />
            <Route
              path="/progress"
              element={
                <ProtectedRoute>
                  <Progress />
                </ProtectedRoute>
              }
            />
            <Route
              path="/leaderboard"
              element={
                <ProtectedRoute>
                  <Leaderboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/learning-map"
              element={
                <ProtectedRoute>
                  <LearningMap />
                </ProtectedRoute>
              }
            />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </TooltipProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
