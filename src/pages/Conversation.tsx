import { useState, useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { supabase } from "@/integrations/supabase/client";
import { ChevronLeft, Mic, MicOff, Volume2, Loader2 } from "lucide-react";
import TranslatableText from "@/components/TranslatableText";
import avatarWaiter from "@/assets/avatar-waiter.jpg";
import avatarLocal from "@/assets/avatar-local.jpg";
import avatarReceptionist from "@/assets/avatar-receptionist.jpg";
import avatarAttendant from "@/assets/avatar-attendant.jpg";
import avatarFriend from "@/assets/avatar-friend.jpg";
import avatarGuide from "@/assets/avatar-guide.jpg";
import avatarColleague from "@/assets/avatar-colleague.jpg";
import avatarManager from "@/assets/avatar-manager.jpg";
import avatarUser from "@/assets/avatar-user.jpg";

interface Message {
  role: "user" | "assistant";
  content: string;
}

const Conversation = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [searchParams] = useSearchParams();
  const scenario = searchParams.get("scenario") || "General Conversation";
  const language = "Spanish"; // This would come from user settings
  
  // Get contextually appropriate conversation partner based on scenario
  const getConversationPartner = () => {
    const scenarioMap: Record<string, string> = {
      "Ordering at a Restaurant": "Waiter",
      "Asking for Directions": "Friendly Local",
      "Hotel Check-in": "Hotel Receptionist",
      "Using Public Transportation": "Station Attendant",
      "Making Local Friends": "New Friend",
      "Casual Small Talk": "Conversation Partner",
      "Sharing Opinions": "Friend",
      "Discussing Feelings": "Close Friend",
      "Cultural Discussions": "Cultural Guide",
      "Professional Introductions": "Colleague",
      "Discussing Emails": "Coworker",
      "Team Meetings": "Team Member",
      "Giving Presentations": "Manager",
    };
    return scenarioMap[scenario] || "Conversation Partner";
  };
  
  const conversationPartner = getConversationPartner();
  
  // Get avatar image for conversation partner
  const getAvatar = (role: "user" | "assistant") => {
    if (role === "user") return avatarUser;
    
    const avatarMap: Record<string, string> = {
      "Waiter": avatarWaiter,
      "Friendly Local": avatarLocal,
      "Hotel Receptionist": avatarReceptionist,
      "Station Attendant": avatarAttendant,
      "New Friend": avatarFriend,
      "Conversation Partner": avatarFriend,
      "Friend": avatarFriend,
      "Close Friend": avatarFriend,
      "Cultural Guide": avatarGuide,
      "Colleague": avatarColleague,
      "Coworker": avatarColleague,
      "Team Member": avatarColleague,
      "Manager": avatarManager,
    };
    return avatarMap[conversationPartner] || avatarFriend;
  };
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState("");
  
  const recognitionRef = useRef<any>(null);
  const synthRef = useRef<SpeechSynthesis | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize speech recognition
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'es-ES'; // Spanish

      recognitionRef.current.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setTranscript(transcript);
        handleUserMessage(transcript);
      };

      recognitionRef.current.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
        toast({
          title: "Speech Recognition Error",
          description: "Could not recognize speech. Please try again.",
          variant: "destructive",
        });
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    } else {
      toast({
        title: "Speech Recognition Not Supported",
        description: "Your browser doesn't support speech recognition. Try Chrome.",
        variant: "destructive",
      });
    }

    synthRef.current = window.speechSynthesis;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      if (synthRef.current) {
        synthRef.current.cancel();
      }
    };
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Start conversation with AI greeting
  useEffect(() => {
    const startConversation = async () => {
      setIsProcessing(true);
      try {
        const { data, error } = await supabase.functions.invoke('language-conversation', {
          body: {
            messages: [{ role: "user", content: "Hello! Let's start practicing." }],
            language,
            scenario,
            level: "Intermediate",
          },
        });

        if (error) throw error;

        const aiMessage: Message = {
          role: "assistant",
          content: data.message,
        };
        setMessages([aiMessage]);
        speakText(data.message);
      } catch (error) {
        console.error('Error starting conversation:', error);
        toast({
          title: "Error",
          description: "Could not start conversation. Please try again.",
          variant: "destructive",
        });
      } finally {
        setIsProcessing(false);
      }
    };

    startConversation();
  }, []);

  const toggleListening = () => {
    if (!recognitionRef.current) return;

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      if (isSpeaking && synthRef.current) {
        synthRef.current.cancel();
        setIsSpeaking(false);
      }
      setTranscript("");
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  const handleUserMessage = async (text: string) => {
    const userMessage: Message = { role: "user", content: text };
    setMessages(prev => [...prev, userMessage]);
    setIsProcessing(true);

    try {
      const { data, error } = await supabase.functions.invoke('language-conversation', {
        body: {
          messages: [...messages, userMessage],
          language,
          scenario,
          level: "Intermediate",
        },
      });

      if (error) throw error;

      const aiMessage: Message = {
        role: "assistant",
        content: data.message,
      };
      setMessages(prev => [...prev, aiMessage]);
      speakText(data.message);
    } catch (error: any) {
      console.error('Error getting AI response:', error);
      toast({
        title: "Error",
        description: error.message || "Could not get response. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const speakText = (text: string) => {
    if (!synthRef.current) return;

    synthRef.current.cancel();
    
    // Clean text to remove any verbalized punctuation
    const cleanedText = text
      .replace(/\bcomma\b/gi, '')
      .replace(/\bperiod\b/gi, '')
      .replace(/\bquestion mark\b/gi, '')
      .replace(/\bexclamation mark\b/gi, '')
      .replace(/\bcolon\b/gi, '')
      .replace(/\bsemicolon\b/gi, '')
      .replace(/\bdash\b/gi, '')
      .trim();
    
    const utterance = new SpeechSynthesisUtterance(cleanedText);
    utterance.lang = 'es-ES'; // Spanish
    utterance.rate = 0.9; // Slightly slower for learning
    
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    synthRef.current.speak(utterance);
  };

  const repeatLastMessage = () => {
    const lastAssistantMessage = [...messages].reverse().find(m => m.role === "assistant");
    if (lastAssistantMessage) {
      speakText(lastAssistantMessage.content);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="border-b bg-card sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <Button variant="ghost" onClick={() => navigate("/module/tourism")} className="mb-2">
            <ChevronLeft className="w-5 h-5 mr-2" />
            Back
          </Button>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold">{scenario}</h1>
              <p className="text-sm text-muted-foreground flex items-center gap-2">
                <span className="text-base">🇪🇸</span> Learning {language}
              </p>
            </div>
            <Badge variant="secondary">Intermediate</Badge>
          </div>
        </div>
      </header>

      {/* Messages */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex gap-4 items-start ${
                message.role === "user" ? "flex-row-reverse" : "flex-row"
              }`}
            >
              {/* Avatar */}
              <div className="flex-shrink-0">
                <img
                  src={getAvatar(message.role)}
                  alt={message.role === "user" ? "You" : conversationPartner}
                  className="w-16 h-16 rounded-full object-cover border-2 border-primary shadow-lg"
                />
              </div>
              
              {/* Message Card */}
              <Card
                className={`p-4 max-w-[70%] ${
                  message.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-card"
                }`}
              >
                <p className="text-xs font-medium mb-2 opacity-70">
                  {message.role === "user" ? "You" : conversationPartner}
                </p>
                {message.role === "assistant" ? (
                  <TranslatableText text={message.content} sourceLanguage={language} />
                ) : (
                  <p>{message.content}</p>
                )}
              </Card>
            </div>
          ))}
          {isProcessing && (
            <div className="flex gap-4 items-start">
              <div className="flex-shrink-0">
                <img
                  src={getAvatar("assistant")}
                  alt={conversationPartner}
                  className="w-16 h-16 rounded-full object-cover border-2 border-primary shadow-lg"
                />
              </div>
              <Card className="bg-card max-w-[70%] p-4">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm">Thinking...</span>
                </div>
              </Card>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Controls */}
      <div className="border-t bg-card sticky bottom-0">
        <div className="max-w-4xl mx-auto px-4 py-6">
          {transcript && (
            <Card className="mb-4 p-3 bg-muted/50">
              <p className="text-sm text-muted-foreground">Listening: {transcript}</p>
            </Card>
          )}
          
          <div className="flex items-center justify-center gap-4">
            <Button
              variant="outline"
              size="lg"
              onClick={repeatLastMessage}
              disabled={messages.length === 0 || isSpeaking}
            >
              <Volume2 className="w-5 h-5 mr-2" />
              Repeat
            </Button>
            
            <Button
              size="lg"
              onClick={toggleListening}
              disabled={isProcessing || isSpeaking}
              className={`w-24 h-24 rounded-full ${
                isListening ? "bg-destructive hover:bg-destructive/90" : ""
              }`}
            >
              {isListening ? (
                <MicOff className="w-8 h-8" />
              ) : (
                <Mic className="w-8 h-8" />
              )}
            </Button>

            <div className="w-32 text-center">
              {isListening && (
                <p className="text-sm text-muted-foreground animate-pulse">Listening...</p>
              )}
              {isSpeaking && (
                <p className="text-sm text-muted-foreground animate-pulse">Speaking...</p>
              )}
              {isProcessing && (
                <p className="text-sm text-muted-foreground">Processing...</p>
              )}
            </div>
          </div>

          <p className="text-center text-sm text-muted-foreground mt-4">
            Tap the microphone to speak in {language}
          </p>
        </div>
      </div>
    </div>
  );
};

export default Conversation;
