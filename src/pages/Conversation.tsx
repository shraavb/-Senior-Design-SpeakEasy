import { useState, useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { invokeFunction } from "@/lib/api";
import { ChevronLeft, Mic, MicOff, Volume2, Loader2, LogOut } from "lucide-react";
import TranslatableText from "@/components/TranslatableText";
import { FeedbackToggle } from "@/components/FeedbackToggle";
import { FeedbackCard } from "@/components/FeedbackCard";
import { SessionSummaryModal } from "@/components/SessionSummaryModal";
import { useAuth } from "@/contexts/AuthContext";
import { useUserProfile } from "@/hooks/useUserProfile";
import { markModuleCompleted, getModuleFromScenario } from "@/utils/dailyGoals";
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
  id: string;
  role: "user" | "assistant";
  content: string;
  userSaid?: string;
  shouldSay?: string;
  corrections?: Array<{ wrong: string; correct: string; explanation: string }>;
  feedbackAcknowledged?: boolean;
}

const Conversation = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [searchParams] = useSearchParams();
  const { user } = useAuth();
  const { profile } = useUserProfile();
  const scenario = searchParams.get("scenario") || "General Conversation";
  
  // Track module type for this conversation
  const moduleType = getModuleFromScenario(scenario);
  // Use language from URL param, then profile, then localStorage, then default
  const language = searchParams.get("language") || 
                   (user && profile?.selected_language) || 
                   localStorage.getItem('selectedLanguage') || 
                   "Spanish";
  
  // Map language names to language codes for speech recognition and TTS
  const getLanguageCode = (lang: string) => {
    const languageMap: Record<string, string> = {
      "Spanish": "es-ES",
      "French": "fr-FR",
      "German": "de-DE",
      "Italian": "it-IT",
      "Japanese": "ja-JP",
      "Mandarin": "zh-CN",
    };
    return languageMap[lang] || "es-ES";
  };
  
  // Map language names to flag emojis
  const getLanguageFlag = (lang: string) => {
    const flagMap: Record<string, string> = {
      "Spanish": "🇪🇸",
      "French": "🇫🇷",
      "German": "🇩🇪",
      "Italian": "🇮🇹",
      "Japanese": "🇯🇵",
      "Mandarin": "🇨🇳",
    };
    return flagMap[lang] || "🇪🇸";
  };
  
  const languageCode = getLanguageCode(language);
  const languageFlag = getLanguageFlag(language);
  
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
  const [audioEnabled, setAudioEnabled] = useState(false);
  const [pendingGreeting, setPendingGreeting] = useState<string | null>(null);
  const [feedbackMode, setFeedbackMode] = useState<"on" | "off">("on");

  // Session tracking state
  const [showSummary, setShowSummary] = useState(false);
  const [sessionStartTime] = useState(Date.now());
  const [errorBreakdown, setErrorBreakdown] = useState<Record<string, number>>({});
  const [vocabularyUsed, setVocabularyUsed] = useState<Map<string, number>>(new Map());
  const [newWordsLearned, setNewWordsLearned] = useState<Map<string, string>>(new Map()); // word -> translation

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
      recognitionRef.current.lang = languageCode;

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

    // Ensure voices are loaded
    const loadVoices = () => {
      if (synthRef.current) {
        const voices = synthRef.current.getVoices();
        console.log(`Loaded ${voices.length} voices`);
        if (voices.length > 0) {
          console.log('Sample voices:', voices.slice(0, 5).map(v => `${v.name} (${v.lang})`));
        }
      }
    };

    // Load voices immediately
    loadVoices();

    // Also listen for voiceschanged event (some browsers load voices asynchronously)
    if (synthRef.current) {
      synthRef.current.onvoiceschanged = loadVoices;
    }

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

  // Enable audio on user interaction
  const enableAudio = async () => {
    setAudioEnabled(true);
    if (pendingGreeting) {
      await speakText(pendingGreeting);
      setPendingGreeting(null);
    }
  };

  // Start conversation with AI greeting
  useEffect(() => {
    const startConversation = async () => {
      setIsProcessing(true);
      try {
        const data = await invokeFunction('language-conversation', {
          messages: [{ role: "user", content: "Hello! Let's start practicing." }],
          language,
          scenario,
          level: "Intermediate",
          feedbackMode,
        });

        const aiMessage: Message = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: data.message,
        };
        setMessages([aiMessage]);
        setPendingGreeting(data.message);
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

  // TEMPORARY: Client-side correction generator (fallback until backend is deployed)
  const generateClientSideCorrections = (text: string, lang: string) => {
    const lowerText = text.toLowerCase();

    // Spanish patterns
    if (lang === "Spanish") {
      if (lowerText.includes("yo quiero") || lowerText.includes("quiero")) {
        return {
          userSaid: text,
          shouldSay: text.replace(/yo quiero|quiero/gi, "Me gustaría"),
          corrections: [{
            wrong: "Quiero",
            correct: "Me gustaría",
            explanation: "In polite contexts, 'Me gustaría' (I would like) is more polite than 'Quiero' (I want)"
          }]
        };
      }
      if (lowerText.includes("está bien")) {
        return {
          userSaid: text,
          shouldSay: text.replace(/está bien/gi, "perfecto"),
          corrections: [{
            wrong: "Está bien",
            correct: "Perfecto",
            explanation: "Using 'Perfecto' (perfect) sounds more natural and enthusiastic"
          }]
        };
      }
    }

    // Mandarin patterns
    if (lang === "Mandarin") {
      if (lowerText.includes("我要") || lowerText.includes("想要")) {
        const wrongPhrase = lowerText.includes("我要") ? "我要" : "想要";
        return {
          userSaid: text,
          shouldSay: text.replace("我要", "我想点").replace("想要", "想点"),
          corrections: [{
            wrong: wrongPhrase,
            correct: "想点",
            explanation: "In restaurant context, 点 (diǎn - to order) is more natural than 要 (yào - to want)"
          }]
        };
      }
      if (lowerText.includes("给我") && !lowerText.includes("请")) {
        return {
          userSaid: text,
          shouldSay: "请" + text,
          corrections: [{
            wrong: "给我",
            correct: "请给我",
            explanation: "Adding 请 (qǐng - please) makes the request more polite"
          }]
        };
      }
    }

    // French patterns
    if (lang === "French") {
      if (lowerText.includes("je veux")) {
        return {
          userSaid: text,
          shouldSay: text.replace(/je veux/gi, "je voudrais"),
          corrections: [{
            wrong: "Je veux",
            correct: "Je voudrais",
            explanation: "Use 'je voudrais' (I would like) for politeness instead of 'je veux' (I want)"
          }]
        };
      }
    }

    // If no specific patterns match, return null (no corrections needed)
    return null;
  };

  // Session tracking functions
  const categorizeError = (explanation: string): string => {
    const lowerExp = explanation.toLowerCase();
    if (lowerExp.includes("tense") || lowerExp.includes("conjugat")) return "Verb Tense";
    if (lowerExp.includes("agreement") || lowerExp.includes("gender") || lowerExp.includes("plural")) return "Agreement";
    if (lowerExp.includes("word order") || lowerExp.includes("position")) return "Word Order";
    if (lowerExp.includes("article") || lowerExp.includes("el") || lowerExp.includes("la") || lowerExp.includes("un")) return "Articles";
    if (lowerExp.includes("polite") || lowerExp.includes("formal")) return "Politeness";
    if (lowerExp.includes("preposition")) return "Prepositions";
    return "Other";
  };

  const trackError = async (corrections: Array<{ wrong: string; correct: string; explanation: string }>) => {
    corrections.forEach(correction => {
      const category = categorizeError(correction.explanation);
      setErrorBreakdown(prev => ({
        ...prev,
        [category]: (prev[category] || 0) + 1
      }));
    });

    // Track new words/phrases learned from corrections with translations
    for (const correction of corrections) {
      const correctPhrase = correction.correct.trim();

      // Try to translate the correct phrase to English
      try {
        const translation = await invokeFunction('translate-word', {
          word: correctPhrase,
          sourceLanguage: language,
          targetLanguage: 'English'
        });

        setNewWordsLearned(prev => {
          const newMap = new Map(prev);
          newMap.set(correctPhrase, translation.translation || '');
          return newMap;
        });
      } catch (error) {
        console.error('Translation error for new word:', error);
        // Store without translation if translation fails
        setNewWordsLearned(prev => {
          const newMap = new Map(prev);
          newMap.set(correctPhrase, '');
          return newMap;
        });
      }
    }
  };

  const trackVocabulary = (text: string) => {
    // Simple word extraction (split by spaces and common punctuation)
    const words = text
      .toLowerCase()
      .replace(/[.,!?¿¡;:""'']/g, '')
      .split(/\s+/)
      .filter(word => word.length > 2); // Filter out very short words

    setVocabularyUsed(prev => {
      const newMap = new Map(prev);
      words.forEach(word => {
        newMap.set(word, (newMap.get(word) || 0) + 1);
      });
      return newMap;
    });
  };

  const getSessionDuration = (): string => {
    const durationMs = Date.now() - sessionStartTime;
    const minutes = Math.floor(durationMs / 60000);
    const seconds = Math.floor((durationMs % 60000) / 1000);
    if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    }
    return `${seconds}s`;
  };

  const endSession = () => {
    // Stop speech recognition if it's running
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    }

    // Cancel any ongoing speech synthesis
    if (synthRef.current) {
      synthRef.current.cancel();
    }
    setIsSpeaking(false);

    // Stop processing state to prevent new API calls
    setIsProcessing(false);

    // Mark this module as completed for today if user is logged in
    if (user && messages.length > 1) { // Only mark if there was actual conversation
      markModuleCompleted(user.id, moduleType);
    }

    // Show the summary modal
    setShowSummary(true);
  };

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
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: text
    };
    setMessages(prev => [...prev, userMessage]);
    setIsProcessing(true);

    console.log('=== FEEDBACK DEBUG ===');
    console.log('Feedback mode:', feedbackMode);
    console.log('User said:', text);

    const requestBody = {
      messages: [...messages, userMessage],
      language,
      scenario,
      level: "Intermediate",
      feedbackMode,
      provideFeedback: feedbackMode === "on",
    };
    console.log('Request body being sent to backend:', requestBody);

    try {
      const data = await invokeFunction('language-conversation', requestBody);

      console.log('Full backend response:', JSON.stringify(data, null, 2));
      console.log('data.message:', data.message);
      console.log('data.corrections:', data.corrections);
      console.log('Type of data.corrections:', typeof data.corrections);
      console.log('data.corrections === null:', data.corrections === null);
      console.log('data.corrections === undefined:', data.corrections === undefined);
      console.log('Has corrections property:', 'corrections' in data);
      console.log('All data keys:', Object.keys(data));

      // TEMPORARY FALLBACK: Generate corrections client-side if backend doesn't provide them
      let corrections = data.corrections;

      if (feedbackMode === "on" && !corrections) {
        console.log('⚠️ Backend did not provide corrections, generating client-side fallback...');
        console.log('Corrections value that triggered fallback:', corrections);
        console.log('Calling generateClientSideCorrections with:', { text, language });
        corrections = generateClientSideCorrections(text, language);
        console.log('✅ Client-side corrections generated:', corrections);

        if (!corrections) {
          console.log('ℹ️ No client-side pattern matched. User message appears correct or unrecognized pattern.');
        }
      }

      // If feedback mode is ON and corrections are available, update the user message
      if (feedbackMode === "on" && corrections) {
        console.log('Applying corrections to message');

        // Track errors for session summary
        if (corrections.corrections && corrections.corrections.length > 0) {
          trackError(corrections.corrections);
        }

        setMessages(prev => {
          const updatedMessages = [...prev];
          const lastUserMessageIndex = updatedMessages.length - 1;
          updatedMessages[lastUserMessageIndex] = {
            ...updatedMessages[lastUserMessageIndex],
            userSaid: corrections.userSaid || text,
            shouldSay: corrections.shouldSay,
            corrections: corrections.corrections,
          };
          console.log('Updated message:', updatedMessages[lastUserMessageIndex]);
          return updatedMessages;
        });
      } else {
        console.log('No corrections to apply');
      }

      // Track vocabulary usage
      trackVocabulary(text);

      const aiMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: data.message,
      };
      setMessages(prev => [...prev, aiMessage]);

      // Enable audio and play response (user interaction via mic enables autoplay)
      if (!audioEnabled) {
        setAudioEnabled(true);
      }

      // Only play TTS if there's no unacknowledged feedback
      // If feedback exists and is not acknowledged, audio will play after acknowledgment
      const hasFeedback = feedbackMode === "on" && corrections;
      if (!hasFeedback) {
        speakText(data.message);
      }
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

  const speakText = async (text: string) => {
    try {
      console.log('Speaking text:', text);
      console.log('Language:', language);

      setIsSpeaking(true);

      // Call backend text-to-speech endpoint
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3001';
      const response = await fetch(`${API_BASE_URL}/text-to-speech`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text,
          language,
          dialect: null,
        }),
      });

      if (!response.ok) {
        throw new Error('Text-to-speech failed');
      }

      // Check content type to determine if it's JSON (browser TTS) or audio (ElevenLabs)
      const contentType = response.headers.get('content-type');

      if (contentType?.includes('application/json')) {
        // Browser TTS mode
        const data = await response.json();
        console.log('Using browser TTS');

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = getLanguageCode(language);
        utterance.rate = 0.9;
        utterance.pitch = 1;

        utterance.onend = () => {
          console.log('Browser TTS ended');
          setIsSpeaking(false);
        };

        utterance.onerror = (event) => {
          console.error('Browser TTS error:', event);
          setIsSpeaking(false);
        };

        window.speechSynthesis.speak(utterance);
        return;
      }

      // ElevenLabs audio response
      console.log('Using ElevenLabs TTS');
      const audioBlob = await response.blob();
      console.log('ElevenLabs audio blob received:', audioBlob.size, 'bytes');

      const typedBlob = new Blob([audioBlob], { type: 'audio/mpeg' });
      const audioUrl = URL.createObjectURL(typedBlob);

      const audio = new Audio(audioUrl);
      audio.preload = 'auto';

      const cleanup = () => {
        setIsSpeaking(false);
        URL.revokeObjectURL(audioUrl);
      };

      audio.onplay = () => console.log('ElevenLabs audio playing');
      audio.onended = () => {
        console.log('ElevenLabs audio ended');
        cleanup();
      };

      audio.onerror = (event) => {
        console.error('Audio error:', event);
        cleanup();
        toast({
          title: "Speech Error",
          description: 'Could not play audio',
          variant: "destructive",
        });
      };

      await audio.play();
    } catch (error) {
      console.error('Error in text-to-speech:', error);
      setIsSpeaking(false);
      toast({
        title: "Speech Error",
        description: error instanceof Error ? error.message : 'Could not generate speech',
        variant: "destructive",
      });
    }
  };

  const repeatLastMessage = () => {
    const lastAssistantMessage = [...messages].reverse().find(m => m.role === "assistant");
    if (lastAssistantMessage) {
      speakText(lastAssistantMessage.content);
    }
  };

  const handleFeedbackAcknowledgment = (messageId: string) => {
    setMessages(prev => prev.map(msg =>
      msg.id === messageId ? { ...msg, feedbackAcknowledged: true } : msg
    ));

    // Find the AI message that comes after this user message and play its audio
    const messageIndex = messages.findIndex(msg => msg.id === messageId);
    if (messageIndex !== -1 && messageIndex + 1 < messages.length) {
      const nextMessage = messages[messageIndex + 1];
      if (nextMessage.role === "assistant") {
        // Play the AI's response audio now that feedback has been acknowledged
        speakText(nextMessage.content);
      }
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="border-b bg-card sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <Button variant="ghost" onClick={() => navigate("/module/tourism")} className="" size="sm">
              <ChevronLeft className="w-4 h-4 mr-1" />
              Back
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={endSession}
              className="text-muted-foreground hover:text-foreground"
            >
              <LogOut className="w-4 h-4 mr-1" />
              End
            </Button>
          </div>
          <div className="ml-3 mt-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-lg font-bold">{scenario}</h1>
              <Badge variant="secondary" className="text-xs">Intermediate</Badge>
            </div>
            <p className="text-xs text-muted-foreground flex items-center gap-1">
              <span>{languageFlag}</span> {language}
            </p>
          </div>
        </div>
      </header>

      {/* Feedback Toggle */}
      <FeedbackToggle
        feedbackMode={feedbackMode}
        onToggle={(mode) => setFeedbackMode(mode)}
      />

      {/* Enable Audio Banner */}
      {pendingGreeting && !audioEnabled && (
        <div className="border-b bg-primary/10">
          <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <Volume2 className="w-5 h-5 text-primary" />
              <div>
                <p className="text-sm font-medium">Enable Audio to hear the conversation</p>
                <p className="text-xs text-muted-foreground">Click to play the greeting and enable automatic audio responses</p>
              </div>
            </div>
            <Button onClick={enableAudio} size="sm" className="shrink-0">
              <Volume2 className="w-4 h-4 mr-2" />
              Enable Audio
            </Button>
          </div>
        </div>
      )}

      {/* Messages */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
          {messages.map((message, index) => {
            // Check if this is an AI message that should be hidden due to unacknowledged feedback
            const previousMessage = index > 0 ? messages[index - 1] : null;
            const shouldHideAIMessage =
              message.role === "assistant" &&
              previousMessage?.role === "user" &&
              feedbackMode === "on" &&
              previousMessage.userSaid &&
              previousMessage.shouldSay &&
              !previousMessage.feedbackAcknowledged;

            // Skip rendering this message if it should be hidden
            if (shouldHideAIMessage) {
              return null;
            }

            return (
            <div key={message.id}>
              {message.role === "assistant" ? (
                <div className="flex gap-2 md:gap-4 items-start">
                  {/* Avatar */}
                  <div className="flex-shrink-0">
                    <img
                      src={getAvatar(message.role)}
                      alt={conversationPartner}
                      className="w-10 h-10 md:w-14 md:h-14 rounded-full object-cover border-2 border-primary shadow-lg"
                    />
                  </div>

                  {/* Message Card */}
                  <Card className="p-3 md:p-4 max-w-[80%] md:max-w-[70%] bg-card">
                    <p className="text-xs font-medium mb-1 md:mb-2 opacity-70">
                      {conversationPartner}
                    </p>
                    <TranslatableText text={message.content} sourceLanguage={language} />
                  </Card>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="flex gap-2 md:gap-4 items-start flex-row-reverse">
                    {/* Avatar */}
                    <div className="flex-shrink-0">
                      <img
                        src={getAvatar(message.role)}
                        alt="You"
                        className="w-10 h-10 md:w-14 md:h-14 rounded-full object-cover border-2 border-primary shadow-lg"
                      />
                    </div>

                    {/* Message Card */}
                    <Card className="p-3 md:p-4 max-w-[80%] md:max-w-[70%] bg-primary text-primary-foreground">
                      <p className="text-xs font-medium mb-1 md:mb-2 opacity-70">You</p>
                      <p>{message.content}</p>
                    </Card>
                  </div>

                  {/* Feedback Card - Only show when feedback mode is ON and not acknowledged */}
                  {feedbackMode === "on" && message.userSaid && message.shouldSay && !message.feedbackAcknowledged && (
                    <FeedbackCard
                      userSaid={message.userSaid}
                      shouldSay={message.shouldSay}
                      corrections={message.corrections || []}
                      onPlayAudio={speakText}
                      onAcknowledge={() => handleFeedbackAcknowledgment(message.id)}
                    />
                  )}
                </div>
              )}
            </div>
            );
          })}
          {isProcessing && (
            <div className="flex gap-2 md:gap-4 items-start">
              <div className="flex-shrink-0">
                <img
                  src={getAvatar("assistant")}
                  alt={conversationPartner}
                  className="w-10 h-10 md:w-14 md:h-14 rounded-full object-cover border-2 border-primary shadow-lg"
                />
              </div>
              <Card className="bg-card max-w-[80%] md:max-w-[70%] p-3 md:p-4">
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
          
          <div className="flex flex-col items-center gap-4">
            {/* Mic button centered */}
            <Button
              size="lg"
              onClick={toggleListening}
              disabled={isProcessing || isSpeaking}
              className={`w-20 h-20 md:w-24 md:h-24 rounded-full ${
                isListening ? "bg-destructive hover:bg-destructive/90" : ""
              }`}
            >
              {isListening ? (
                <MicOff className="w-7 h-7 md:w-8 md:h-8" />
              ) : (
                <Mic className="w-7 h-7 md:w-8 md:h-8" />
              )}
            </Button>

            {/* Status text */}
            <div className="h-5 text-center">
              {isListening && (
                <p className="text-sm text-muted-foreground animate-pulse">Listening...</p>
              )}
              {isSpeaking && (
                <p className="text-sm text-muted-foreground animate-pulse">Speaking...</p>
              )}
              {isProcessing && (
                <p className="text-sm text-muted-foreground">Processing...</p>
              )}
              {!isListening && !isSpeaking && !isProcessing && (
                <p className="text-sm text-muted-foreground">Tap to speak in {language}</p>
              )}
            </div>

            {/* Repeat button below */}
            <Button
              variant="outline"
              size="sm"
              onClick={repeatLastMessage}
              disabled={messages.length === 0 || isSpeaking}
            >
              <Volume2 className="w-4 h-4 mr-2" />
              Repeat last message
            </Button>
          </div>
        </div>
      </div>

      {/* Session Summary Modal */}
      <SessionSummaryModal
        isOpen={showSummary}
        onClose={() => setShowSummary(false)}
        onEndSession={() => navigate("/dashboard")}
        errorBreakdown={errorBreakdown}
        mostCommonWords={Array.from(vocabularyUsed.entries())
          .map(([word, count]) => ({ word, count }))
          .sort((a, b) => b.count - a.count)}
        newWordsUsed={Array.from(newWordsLearned.entries()).map(([word, translation]) => ({
          word,
          translation,
          count: 1
        }))}
        totalCorrections={Object.values(errorBreakdown).reduce((sum, count) => sum + count, 0)}
        sessionDuration={getSessionDuration()}
      />
    </div>
  );
};

export default Conversation;
