import { useState, useEffect, useRef } from "react";
import { ChevronLeft, Mic, MicOff, Volume2, Loader2 } from "lucide-react";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Card } from "./ui/card";
import { FeedbackCard } from "./FeedbackCard";
import { useToast } from "@/hooks/use-toast";
import avatarWaiter from "@/assets/avatar-waiter.jpg";
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

interface ConversationViewProps {
  feedbackMode: "on" | "off";
  scenario?: string;
  language?: string;
  languageFlag?: string;
  onBack?: () => void;
}

export function ConversationView({
  feedbackMode,
  scenario = "Ordering at a Restaurant",
  language = "Mandarin",
  languageFlag = "🇨🇳",
  onBack
}: ConversationViewProps) {
  const { toast } = useToast();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: "欢迎光临！你想点什么？",
    },
    // Demo example showing feedback when feedbackMode is ON
    ...(feedbackMode === "on" ? [{
      id: "2",
      role: "user" as const,
      content: "我要一个汉堡包",
      userSaid: "我要一个汉堡包",
      shouldSay: "我想点一个汉堡包",
      corrections: [
        {
          wrong: "我要",
          correct: "我想点",
          explanation: "In restaurant context, 点 (diǎn - to order) is more natural than 要 (yào - to want)"
        }
      ]
    },
    {
      id: "3",
      role: "assistant" as const,
      content: "好的，汉堡包。还需要什么饮料吗？",
    }] : [])
  ]);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState("");

  const recognitionRef = useRef<any>(null);
  const synthRef = useRef<SpeechSynthesis | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Map language names to language codes
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

  const languageCode = getLanguageCode(language);

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

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      if (synthRef.current) {
        synthRef.current.cancel();
      }
    };
  }, [languageCode]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

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
    console.log('User said:', text);
    console.log('Feedback mode:', feedbackMode);

    // Analyze the user's input to provide contextually relevant corrections
    const getCorrectionForText = (userText: string) => {
      const lowerText = userText.toLowerCase();

      // Handle English input for demo/testing purposes
      if (lowerText.includes("want") || lowerText.includes("i want")) {
        return {
          userSaid: userText,
          shouldSay: "我想点一个汉堡包",
          corrections: [
            {
              wrong: "want",
              correct: "想点 (xiǎng diǎn)",
              explanation: "In Chinese restaurants, use 想点 (want to order) rather than just 想要 (want)"
            }
          ]
        };
      }

      if (lowerText.includes("give me")) {
        return {
          userSaid: userText,
          shouldSay: "请给我一杯水",
          corrections: [
            {
              wrong: "give me",
              correct: "请给我 (qǐng gěi wǒ)",
              explanation: "Start with 请 (please) to be polite when making requests"
            }
          ]
        };
      }

      // Chinese pattern matching
      if (lowerText.includes("想要") || lowerText.includes("我要")) {
        return {
          userSaid: userText,
          shouldSay: userText.replace("想要", "想点").replace("我要", "我想点"),
          corrections: [
            {
              wrong: lowerText.includes("想要") ? "想要" : "我要",
              correct: lowerText.includes("想要") ? "想点" : "我想点",
              explanation: "In restaurant context, 点 (diǎn - to order) is more natural than 要 (yào - to want)"
            }
          ]
        };
      }

      if (lowerText.includes("给我") && !lowerText.includes("请")) {
        return {
          userSaid: userText,
          shouldSay: userText.replace("给我", "请给我"),
          corrections: [
            {
              wrong: "给我",
              correct: "请给我",
              explanation: "Adding 请 (qǐng - please) makes the request more polite"
            }
          ]
        };
      }

      if (lowerText.includes("多少钱")) {
        return {
          userSaid: userText,
          shouldSay: userText.replace("多少钱", "这个多少钱"),
          corrections: [
            {
              wrong: "多少钱",
              correct: "这个多少钱",
              explanation: "Adding 这个 (this) makes it clear what you're asking the price for"
            }
          ]
        };
      }

      // No corrections needed
      return null;
    };

    const correction = feedbackMode === "on" ? getCorrectionForText(text) : null;
    console.log('Correction generated:', correction);

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: text,
      userSaid: correction?.userSaid,
      shouldSay: correction?.shouldSay,
      corrections: correction?.corrections,
    };
    console.log('User message object:', userMessage);
    setMessages(prev => [...prev, userMessage]);
    setIsProcessing(true);

    // Simulate AI response - naturally incorporate corrections when feedback is off
    setTimeout(() => {
      let aiResponse = "谢谢！还需要别的吗？"; // Default response

      // Generate contextual responses
      if (text.toLowerCase().includes("汉堡") || text.toLowerCase().includes("burger")) {
        aiResponse = feedbackMode === "off" && correction
          ? `好的，您想点汉堡包。还需要什么饮料吗？` // Naturally model correct usage
          : "好的，汉堡包。还需要什么饮料吗？";
      } else if (text.toLowerCase().includes("饮料") || text.toLowerCase().includes("drink")) {
        aiResponse = "我们有可乐、橙汁和茶。您想要哪一种？";
      }

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: aiResponse,
      };
      setMessages(prev => [...prev, aiMessage]);

      // Only play TTS if there's no unacknowledged feedback
      // If feedback exists and is not acknowledged, audio will play after acknowledgment
      const hasFeedback = feedbackMode === "on" && correction;
      if (!hasFeedback) {
        speakText(aiMessage.content);
      }

      setIsProcessing(false);
    }, 1500);
  };

  const speakText = (text: string) => {
    if (!synthRef.current) return;

    synthRef.current.cancel();

    const cleanedText = text
      .replace(/\bcomma\b/gi, '')
      .replace(/\bperiod\b/gi, '')
      .replace(/\bquestion mark\b/gi, '')
      .replace(/\bexclamation mark\b/gi, '')
      .trim();

    const utterance = new SpeechSynthesisUtterance(cleanedText);
    utterance.lang = languageCode;
    utterance.rate = 0.9;

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
        <div className="max-w-4xl mx-auto px-4 py-4">
          <Button variant="ghost" onClick={onBack} className="mb-2">
            <ChevronLeft className="w-5 h-5 mr-2" />
            Back
          </Button>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold">{scenario}</h1>
              <p className="text-sm text-muted-foreground flex items-center gap-2">
                <span className="text-base">{languageFlag}</span> Learning {language}
              </p>
            </div>
            <Badge variant="secondary">Intermediate</Badge>
          </div>
        </div>
      </header>

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
                <div className="flex gap-4 items-start">
                  <div className="flex-shrink-0">
                    <img
                      src={avatarWaiter}
                      alt="Waiter"
                      className="w-16 h-16 rounded-full object-cover border-2 border-primary shadow-lg"
                    />
                  </div>
                  <Card className="bg-card max-w-[70%] p-4">
                    <p className="text-xs font-medium mb-2 opacity-70">Waiter</p>
                    <p>{message.content}</p>
                  </Card>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="flex gap-4 items-start flex-row-reverse">
                    <div className="flex-shrink-0">
                      <img
                        src={avatarUser}
                        alt="You"
                        className="w-16 h-16 rounded-full object-cover border-2 border-primary shadow-lg"
                      />
                    </div>
                    <Card className="bg-primary text-primary-foreground max-w-[70%] p-4">
                      <p className="text-xs font-medium mb-2 opacity-70">You</p>
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
            <div className="flex gap-4 items-start">
              <div className="flex-shrink-0">
                <img
                  src={avatarWaiter}
                  alt="Waiter"
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
}
