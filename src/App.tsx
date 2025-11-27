import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Welcome from "./pages/Welcome";
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

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter basename={import.meta.env.BASE_URL}>
        <Routes>
          <Route path="/" element={<Welcome />} />
          <Route path="/level" element={<Level />} />
          <Route path="/goal" element={<Goal />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/module/tourism" element={<ModuleTourism />} />
          <Route path="/module/social" element={<ModuleSocial />} />
          <Route path="/module/professional" element={<ModuleProfessional />} />
          <Route path="/conversation" element={<Conversation />} />
          <Route path="/conversation-demo" element={<ConversationDemo />} />
          <Route path="/progress" element={<Progress />} />
          <Route path="/leaderboard" element={<Leaderboard />} />
          <Route path="/learning-map" element={<LearningMap />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
