import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

// --- CORS ---
const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

serve(async (req) => {
  // Handle preflight
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  // Parse JSON safely
  let body;
  try {
    body = await req.json();
  } catch (_) {
    return new Response(JSON.stringify({ error: "Invalid JSON body" }), {
      status: 400,
      headers: corsHeaders,
    });
  }

  const { messages = [], language, scenario, level, feedbackMode, provideFeedback } = body;

  const GOOGLE_AI_API_KEY = Deno.env.get("GOOGLE_AI_API_KEY");
  if (!GOOGLE_AI_API_KEY) {
    return new Response(JSON.stringify({ error: "Missing GOOGLE_AI_API_KEY" }), {
      status: 500,
      headers: corsHeaders,
    });
  }

  // ---- Build system prompt ----
  const feedbackInstruction =
    feedbackMode === "off"
      ? "- Gently correct mistakes by naturally incorporating the correct form (indirect correction)"
      : "- Respond naturally without explicit corrections";

  const systemPrompt = `
You are a native ${language} speaker helping someone practice conversational ${language}.

Context:
- Level: ${level || "Intermediate"}
- Scenario: ${scenario || "General conversation"}
- Feedback Mode: ${feedbackMode || "on"}

Instructions:
- Respond ONLY in ${language}
- Keep responses 2–3 sentences
- Match learner’s level
- Stay in scenario
${feedbackInstruction}
- Ask follow-up questions
- Use normal punctuation
`;

  // --- Format content for Gemini ---
  const firstUserMessage = messages[0]?.content || "";

  const geminiMessages = [
    {
      role: "user",
      parts: [
        {
          text: `${systemPrompt}\n\nUser: ${firstUserMessage}`,
        },
      ],
    },
    ...messages.slice(1).map((m) => ({
      role: m.role === "assistant" ? "model" : "user",
      parts: [{ text: m.content }],
    })),
  ];

  // --- Call Gemini for chat response ---
  const aiResponse = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=${GOOGLE_AI_API_KEY}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contents: geminiMessages,
        generationConfig: { temperature: 0.9, maxOutputTokens: 1024 },
      }),
    },
  );

  if (!aiResponse.ok) {
    const err = await aiResponse.text();
    console.error("Gemini error:", aiResponse.status, err);
    return new Response(JSON.stringify({ error: err }), {
      status: 500,
      headers: corsHeaders,
    });
  }

  const aiData = await aiResponse.json();
  const assistantMessage =
    aiData.candidates?.[0]?.content?.parts?.[0]?.text || "";

  // --- Optional feedback correction ---
  let corrections = null;

  if (provideFeedback && messages.length > 0) {
    const lastUser = messages[messages.length - 1];

    if (lastUser.role === "user") {
      const feedbackPrompt = `
You are a ${language} language teacher.
Analyze this learner message: "${lastUser.content}"

Return ONLY this JSON (no other text):

{
  "userSaid": "...",
  "shouldSay": "... or null",
  "corrections": [
    { "wrong": "...", "correct": "...", "explanation": "..." }
  ]
}
`;

      const fb = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=${GOOGLE_AI_API_KEY}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            contents: [{ role: "user", parts: [{ text: feedbackPrompt }] }],
            generationConfig: { temperature: 0.2, maxOutputTokens: 256 },
          }),
        },
      );

      if (fb.ok) {
        const fbData = await fb.json();
        const raw = fbData.candidates?.[0]?.content?.parts?.[0]?.text || "";

        // Extract JSON cleanly
        const match = raw.match(/\{[\s\S]*\}/);
        if (match) {
          try {
            corrections = JSON.parse(match[0]);
          } catch {
            console.log("Feedback parse failed");
          }
        }
      }
    }
  }

  // --- Final output ---
  console.log("DEPLOYMENT VERSION: 2.0"); // <-- DEPLOYMENT MARKER
  console.log("Returning corrections:", corrections);
  console.log("Corrections is null:", corrections === null);

  return new Response(
    JSON.stringify({
      message: assistantMessage,
      corrections,
    }),
    {
      headers: {
        ...corsHeaders,
        "Content-Type": "application/json",
      },
    },
  );
});
