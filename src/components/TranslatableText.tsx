import { useState } from "react";
import { supabase } from "@/integrations/supabase/client";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Loader2 } from "lucide-react";

interface TranslatableTextProps {
  text: string;
  sourceLanguage: string;
}

const TranslatableText = ({ text, sourceLanguage }: TranslatableTextProps) => {
  const [translations, setTranslations] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState<Record<string, boolean>>({});

  const handleWordHover = async (word: string) => {
    // Skip if already translated or currently loading
    if (translations[word] || loading[word]) return;
    
    // Skip punctuation-only
    if (!word.match(/[a-zA-ZáéíóúñÁÉÍÓÚÑ]/)) return;

    setLoading(prev => ({ ...prev, [word]: true }));

    try {
      const { data, error } = await supabase.functions.invoke('translate-word', {
        body: {
          word,
          sourceLanguage,
          targetLanguage: 'English',
        },
      });

      if (error) throw error;

      setTranslations(prev => ({ ...prev, [word]: data.translation }));
    } catch (error) {
      console.error('Translation error:', error);
    } finally {
      setLoading(prev => ({ ...prev, [word]: false }));
    }
  };

  // Split text into words and punctuation
  const parts = text.split(/(\s+|[.,;:!?¿¡])/);

  return (
    <TooltipProvider delayDuration={200}>
      <span>
        {parts.map((part, index) => {
          const cleanWord = part.trim();
          
          // If it's whitespace or empty, render as-is
          if (!cleanWord || /^\s+$/.test(part)) {
            return <span key={index}>{part}</span>;
          }

          // If it's only punctuation, render as-is
          if (!cleanWord.match(/[a-zA-ZáéíóúñÁÉÍÓÚÑ]/)) {
            return <span key={index}>{part}</span>;
          }

          const translation = translations[cleanWord];
          const isLoading = loading[cleanWord];

          return (
            <Tooltip key={index}>
              <TooltipTrigger asChild>
                <span
                  className="cursor-help hover:bg-primary/10 rounded px-0.5 transition-colors"
                  onMouseEnter={() => handleWordHover(cleanWord)}
                >
                  {part}
                </span>
              </TooltipTrigger>
              <TooltipContent>
                {isLoading ? (
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-3 h-3 animate-spin" />
                    <span className="text-xs">Translating...</span>
                  </div>
                ) : translation ? (
                  <p className="text-sm font-medium">{translation}</p>
                ) : (
                  <p className="text-xs text-muted-foreground">Hover to translate</p>
                )}
              </TooltipContent>
            </Tooltip>
          );
        })}
      </span>
    </TooltipProvider>
  );
};

export default TranslatableText;
