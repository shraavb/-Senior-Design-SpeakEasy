import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const { word, sourceLanguage, targetLanguage } = await req.json();

    const GOOGLE_AI_API_KEY = Deno.env.get("GOOGLE_AI_API_KEY");
    if (!GOOGLE_AI_API_KEY) {
      throw new Error("GOOGLE_AI_API_KEY is not configured");
    }

    // Detect single Chinese characters
    const isSingleCharacter = word.length === 1 && /[\u4e00-\u9fff]/.test(word);

    const prompt = isSingleCharacter
      ? `
You are a ${sourceLanguage} language teacher.
Translate this single ${sourceLanguage} character into ${targetLanguage}.

Character: "${word}"

Rules:
- Give ONLY the most common/basic meaning.
- Answer must be 1–3 words.
- No explanations, examples, or multiple meanings.
- Just the translation.

Your translation:
`
      : `
Translate the following ${sourceLanguage} word/phrase into ${targetLanguage}.
Rules:
- Provide the most common translation only.
- Keep answer to 1–3 words.
- No explanation, no examples.

${sourceLanguage}: "${word}"
${targetLanguage}:
`;

    // --- Call Gemini ---
    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=${GOOGLE_AI_API_KEY}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contents: [
            {
              role: "user",
              parts: [{ text: prompt }],
            },
          ],
          generationConfig: {
            temperature: 0.3,
            maxOutputTokens: 64,
          },
        }),
      }
    );

    if (!response.ok) {
      const err = await response.text();
      console.error("Gemini error:", err);
      throw new Error("Translation failed");
    }

    const data = await response.json();
    let translation =
      data.candidates?.[0]?.content?.parts?.[0]?.text?.trim() || "";

    // --- Clean translation ---
    translation = translation
      .replace(/^["'`]|["'`]$/g, "") // strip surrounding quotes
      .replace(/^(Translation:|Answer:|Response:)\s*/i, "")
      .replace(/\.$/, "")
      .trim();

    // Trim overly long explanations
    if (translation.length > 20) {
      const firstPart = translation.split(/[,;.]/)[0]?.trim();
      if (firstPart) translation = firstPart;
    }

    return new Response(JSON.stringify({ translation }), {
      headers: {
        ...corsHeaders,
        "Content-Type": "application/json",
      },
    });
  } catch (error) {
    console.error("Error in translate-word:", error);
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: {
        ...corsHeaders,
        "Content-Type": "application/json",
      },
    });
  }
});
