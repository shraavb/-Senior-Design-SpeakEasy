import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { word, sourceLanguage, targetLanguage } = await req.json();
    
    const LOVABLE_API_KEY = Deno.env.get('LOVABLE_API_KEY');
    if (!LOVABLE_API_KEY) {
      throw new Error('LOVABLE_API_KEY is not configured');
    }

    // Create a better prompt for character/word translation
    const isSingleCharacter = word.length === 1;
    const prompt = isSingleCharacter && /[\u4e00-\u9fff]/.test(word)
      ? `You are a ${sourceLanguage} language teacher. Translate this single ${sourceLanguage} character to ${targetLanguage}.

Character: "${word}"

Provide ONLY the most common/basic meaning of this character as a single word or short phrase (2-3 words maximum). Do not provide example sentences, grammar notes, or multiple meanings. Just the translation.

Examples of good responses:
- I/me
- good
- want
- eat
- person

Your translation:`
      : `Translate this ${sourceLanguage} word or phrase to ${targetLanguage}. Provide only the most common translation as a short phrase (1-3 words). No explanations or examples.

${sourceLanguage}: "${word}"
${targetLanguage}:`;

    // Use Lovable AI for quick translation
    const response = await fetch('https://ai.gateway.lovable.dev/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${LOVABLE_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'google/gemini-2.5-flash',
        messages: [
          {
            role: 'user',
            content: prompt
          }
        ],
        temperature: 0.3, // Lower temperature for more consistent translations
      }),
    });

    if (!response.ok) {
      throw new Error('Translation failed');
    }

    const data = await response.json();
    let translation = data.choices[0].message.content.trim();

    // Clean up the translation - remove quotes, extra punctuation, prefixes
    translation = translation
      .replace(/^["'`]|["'`]$/g, '') // Remove surrounding quotes
      .replace(/^(Translation:|Answer:|Response:)\s*/i, '') // Remove common prefixes
      .replace(/\.$/, '') // Remove trailing period
      .trim();

    // If translation is still too long (likely an explanation), take only first part
    if (translation.length > 20) {
      const firstPart = translation.split(/[,;.]/)[0];
      if (firstPart.length < translation.length) {
        translation = firstPart.trim();
      }
    }

    return new Response(
      JSON.stringify({ translation }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('Error in translate-word:', error);
    const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
    return new Response(
      JSON.stringify({ error: errorMessage }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});
