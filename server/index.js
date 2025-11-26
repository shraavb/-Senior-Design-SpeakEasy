import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

const GOOGLE_AI_API_KEY = process.env.GOOGLE_AI_API_KEY;
const GROQ_API_KEY = process.env.GROQ_API_KEY;
const ELEVENLABS_API_KEY = process.env.ELEVENLABS_API_KEY;
const USE_GROQ = process.env.USE_GROQ === 'true';
const USE_ELEVENLABS = process.env.USE_ELEVENLABS === 'true'; // Set to false to use browser TTS

console.log(`Using ${USE_GROQ ? 'Groq (Llama)' : 'Google Gemini'} for AI responses`);

// Helper function to call AI (Groq or Gemini)
async function callAI(messages, temperature = 0.9, maxTokens = 1024) {
  if (USE_GROQ) {
    // Groq API (OpenAI-compatible)
    const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${GROQ_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'llama-3.3-70b-versatile', // Fast and good quality
        messages,
        temperature,
        max_tokens: maxTokens,
      }),
    });

    if (!response.ok) {
      const err = await response.text();
      console.error('Groq error:', response.status, err);
      throw new Error(err);
    }

    const data = await response.json();
    return data.choices[0].message.content;
  } else {
    // Google Gemini API
    const firstUserMessage = messages[0]?.content || "";
    const geminiMessages = [
      {
        role: "user",
        parts: [{ text: messages[0].role === 'system' ? `${messages[0].content}\n\nUser: ${firstUserMessage}` : firstUserMessage }],
      },
      ...messages.slice(1).map((m) => ({
        role: m.role === "assistant" ? "model" : "user",
        parts: [{ text: m.content }],
      })),
    ];

    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=${GOOGLE_AI_API_KEY}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: geminiMessages,
          generationConfig: { temperature, maxOutputTokens: maxTokens },
        }),
      }
    );

    if (!response.ok) {
      const err = await response.text();
      console.error('Gemini error:', response.status, err);
      throw new Error(err);
    }

    const data = await response.json();
    return data.candidates?.[0]?.content?.parts?.[0]?.text || "";
  }
}

// Language conversation endpoint
app.post('/language-conversation', async (req, res) => {
  try {
    const { messages = [], language, scenario, level, feedbackMode, provideFeedback } = req.body;

    if (USE_GROQ && !GROQ_API_KEY) {
      return res.status(500).json({ error: 'Missing GROQ_API_KEY' });
    }
    if (!USE_GROQ && !GOOGLE_AI_API_KEY) {
      return res.status(500).json({ error: 'Missing GOOGLE_AI_API_KEY' });
    }

    // Build system prompt
    const feedbackInstruction = feedbackMode === "off"
      ? "- Gently correct mistakes by naturally incorporating the correct form (indirect correction)"
      : "- Respond naturally without explicit corrections";

    const systemPrompt = `You are a native ${language} speaker helping someone practice conversational ${language}.

Context:
- Level: ${level || "Intermediate"}
- Scenario: ${scenario || "General conversation"}
- Feedback Mode: ${feedbackMode || "on"}

Instructions:
- Respond ONLY in ${language}
- Keep responses 2–3 sentences
- Match learner's level
- Stay in scenario
${feedbackInstruction}
- Ask follow-up questions
- Use normal punctuation`;

    // Format messages for AI
    const aiMessages = [
      { role: 'system', content: systemPrompt },
      ...messages.map(m => ({ role: m.role, content: m.content }))
    ];

    // Get AI response
    const assistantMessage = await callAI(aiMessages, 0.9, 1024);

    // Generate feedback corrections if requested
    let corrections = null;

    if (provideFeedback && messages.length > 0) {
      const lastUser = messages[messages.length - 1];

      if (lastUser.role === "user") {
        const feedbackPrompt = `You are a ${language} language teacher.
Analyze this learner message: "${lastUser.content}"

Return ONLY this JSON (no other text):

{
  "userSaid": "...",
  "shouldSay": "... or null",
  "corrections": [
    { "wrong": "...", "correct": "...", "explanation": "..." }
  ]
}`;

        try {
          const feedbackMessages = [{ role: 'user', content: feedbackPrompt }];
          const raw = await callAI(feedbackMessages, 0.2, 512);

          console.log("Feedback AI response:", raw);

          // Extract JSON
          const match = raw.match(/\{[\s\S]*\}/);
          if (match) {
            try {
              corrections = JSON.parse(match[0]);
              console.log("Parsed corrections:", corrections);
            } catch (e) {
              console.error("Feedback parse failed:", e);
            }
          }
        } catch (e) {
          console.error("Error getting feedback:", e);
        }
      }
    }

    console.log("Returning response with corrections:", corrections);
    res.json({
      message: assistantMessage,
      corrections,
    });
  } catch (error) {
    console.error('Error in language-conversation:', error);
    res.status(500).json({ error: error.message });
  }
});

// Translate word endpoint
app.post('/translate-word', async (req, res) => {
  try {
    const { word, sourceLanguage, targetLanguage } = req.body;

    if (USE_GROQ && !GROQ_API_KEY) {
      return res.status(500).json({ error: 'Missing GROQ_API_KEY' });
    }
    if (!USE_GROQ && !GOOGLE_AI_API_KEY) {
      return res.status(500).json({ error: 'Missing GOOGLE_AI_API_KEY' });
    }

    // Detect single Chinese characters
    const isSingleCharacter = word.length === 1 && /[\u4e00-\u9fff]/.test(word);

    const prompt = isSingleCharacter
      ? `You are a ${sourceLanguage} language teacher.
Translate this single ${sourceLanguage} character into ${targetLanguage}.

Character: "${word}"

Rules:
- Give ONLY the most common/basic meaning.
- Answer must be 1–3 words.
- No explanations, examples, or multiple meanings.
- Just the translation.

Your translation:`
      : `Translate the following ${sourceLanguage} word/phrase into ${targetLanguage}.
Rules:
- Provide the most common translation only.
- Keep answer to 1–3 words.
- No explanation, no examples.

${sourceLanguage}: "${word}"
${targetLanguage}:`;

    const aiMessages = [{ role: 'user', content: prompt }];
    let translation = await callAI(aiMessages, 0.3, 64);

    // Clean translation
    translation = translation
      .replace(/^["'`]|["'`]$/g, "")
      .replace(/^(Translation:|Answer:|Response:)\s*/i, "")
      .replace(/\.$/, "")
      .trim();

    // Trim overly long explanations
    if (translation.length > 20) {
      const firstPart = translation.split(/[,;.]/)[0]?.trim();
      if (firstPart) translation = firstPart;
    }

    res.json({ translation });
  } catch (error) {
    console.error('Error in translate-word:', error);
    res.status(500).json({ error: error.message });
  }
});

// Text-to-speech endpoint using ElevenLabs (optional)
app.post('/text-to-speech', async (req, res) => {
  try {
    const { text, language, dialect } = req.body;

    // If ElevenLabs is disabled, return a flag to use browser TTS
    if (!USE_ELEVENLABS) {
      return res.json({ useBrowserTTS: true, text });
    }

    if (!ELEVENLABS_API_KEY) {
      console.warn('ElevenLabs API key missing, falling back to browser TTS');
      return res.json({ useBrowserTTS: true, text });
    }

    // Map language/dialect to ElevenLabs voice IDs
    const voiceMap = {
      'Spanish': 'gD1IexrzCvsXPHUuT0s3', // Latin American Spanish (male)
      'Spanish-Spain': 'LBI5rXF0AWwMYPvTCq7W', // European Spanish (female)
      'French': 'zrHiDhphv9ZnVXBqCLjz', // French (male)
      'German': 'N2lVS1w4EtoT3dr4eOWO', // German (male)
      'Italian': 'AZnzlk1XvdvUeBnXmlld', // Italian (female)
      'Japanese': 'cYMPBHPKVq9TbGVjJIqX', // Japanese (female)
      'Mandarin': 'FGY2WhTYpPnrIDTdsKH5', // Mandarin (female)
      'English': 'pNInz6obpgDQGcFmaJgB', // Default (Adam)
    };

    // Select voice based on language and dialect
    const voiceKey = dialect ? `${language}-${dialect}` : language;
    const voiceId = voiceMap[voiceKey] || voiceMap[language] || voiceMap['English'];

    console.log(`Generating speech for "${text}" in ${language} (${dialect || 'default'}) using voice ${voiceId}`);

    const response = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`, {
      method: 'POST',
      headers: {
        'Accept': 'audio/mpeg',
        'Content-Type': 'application/json',
        'xi-api-key': ELEVENLABS_API_KEY,
      },
      body: JSON.stringify({
        text,
        model_id: 'eleven_multilingual_v2',
        voice_settings: {
          stability: 0.5,
          similarity_boost: 0.75,
        }
      }),
    });

    if (!response.ok) {
      const err = await response.text();
      console.error('ElevenLabs error:', response.status, err);
      return res.status(500).json({ error: 'Text-to-speech failed' });
    }

    // Get audio data as buffer and send it back
    const audioBuffer = await response.arrayBuffer();
    res.setHeader('Content-Type', 'audio/mpeg');
    res.send(Buffer.from(audioBuffer));
  } catch (error) {
    console.error('Error in text-to-speech:', error);
    res.status(500).json({ error: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`Backend server running on http://localhost:${PORT}`);
  console.log(`Using: ${USE_GROQ ? 'Groq (Llama 3.3 70B)' : 'Google Gemini'}`);
  console.log('Endpoints:');
  console.log(`  POST http://localhost:${PORT}/language-conversation`);
  console.log(`  POST http://localhost:${PORT}/translate-word`);
  console.log(`  POST http://localhost:${PORT}/text-to-speech`);
});
