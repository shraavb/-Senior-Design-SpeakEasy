import { useState } from "react";
import { invokeFunction } from "@/lib/api";
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

    // Skip punctuation-only and whitespace
    // Support multiple character sets: Latin, accented characters, Chinese, Japanese, Korean, etc.
    if (!word.match(/[\p{L}\p{N}]/u)) return;

    setLoading(prev => ({ ...prev, [word]: true }));

    try {
      const data = await invokeFunction('translate-word', {
        word,
        sourceLanguage,
        targetLanguage: 'English',
      });

      setTranslations(prev => ({ ...prev, [word]: data.translation }));
    } catch (error) {
      console.error('Translation error:', error);
    } finally {
      setLoading(prev => ({ ...prev, [word]: false }));
    }
  };

  // Split text into words and punctuation
  // For Chinese/Japanese/Korean: split by character
  // For space-based languages: split by spaces and punctuation
  const isCJK = /[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]/.test(text);

  const parts = isCJK
    ? text.split(/([.,;:!?¿¡\s]+)/).flatMap(p => {
        // If it's punctuation or whitespace, keep as-is
        if (/^[.,;:!?¿¡\s]+$/.test(p)) return [p];
        // Otherwise split into individual characters for CJK
        return p.split('');
      })
    : text.split(/(\s+|[.,;:!?¿¡])/);

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
          if (!cleanWord.match(/[\p{L}\p{N}]/u)) {
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
