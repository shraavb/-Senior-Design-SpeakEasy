import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type'
};
// Public HF models (free API). You can swap the chat model if preferred.
const HF_CHAT_MODEL = 'HuggingFaceH4/zephyr-7b-beta';
// Use the Llama‑2 fine‑tuned grammar model (requires Inference Endpoint - not available on free API)
// const HF_GRAMMAR_MODEL = 'sylviali/eracond_llama_2_grammar';
// Temporary: Use public grammar model until Inference Endpoint is created
const HF_GRAMMAR_MODEL = 'pszemraj/flan-t5-large-grammar-synthesis';
// Small retry helper for HF cold starts/rate limits on free tier
async function fetchWithRetry(url, init, attempts = 3, delayMs = 1500) {
  for(let i = 0; i < attempts; i++){
    const res = await fetch(url, init);
    if (res.ok) return res;
    if (res.status === 503 || res.status === 429) {
      await new Promise((r)=>setTimeout(r, delayMs * (i + 1)));
      continue;
    }
    return res;
  }
  return fetch(url, init);
}
serve(async (req)=>{
  if (req.method === 'OPTIONS') {
    return new Response(null, {
      headers: corsHeaders
    });
  }
  try {
    const body = await req.json();
    const { messages, language, scenario, level, enableGrammarCorrection = true } = body;
    const HF_TOKEN = Deno.env.get('HUGGINGFACE_API_KEY');
    if (!HF_TOKEN) {
      throw new Error('HUGGINGFACE_API_KEY is not configured');
    }
    // Optional private HF Endpoints (no query params). You can set one global or separate ones.
    const HF_ENDPOINT_URL = Deno.env.get('HF_ENDPOINT_URL') || '';
    const HF_GRAMMAR_ENDPOINT_URL = Deno.env.get('HF_GRAMMAR_ENDPOINT_URL') || '';
    const HF_CHAT_ENDPOINT_URL = Deno.env.get('HF_CHAT_ENDPOINT_URL') || '';
    function buildUrl(endpointUrl, modelId) {
      // If an endpoint URL is provided, use it directly (no /models/... or query params)
      if (endpointUrl && typeof endpointUrl === 'string' && endpointUrl.startsWith('http')) return endpointUrl;
      // Use the new Inference Providers API format
      return `https://api-inference.huggingface.co/models/${modelId}`;
    }
    const grammarUrl = buildUrl(HF_GRAMMAR_ENDPOINT_URL || HF_ENDPOINT_URL, HF_GRAMMAR_MODEL);
    const chatUrl = buildUrl(HF_CHAT_ENDPOINT_URL || HF_ENDPOINT_URL, HF_CHAT_MODEL);
    console.log('Resolved HF URLs:', { grammarUrl, chatUrl });
    // Latest user message
    const latestUserMessage = messages?.[messages.length - 1];
    let correctedUserMessage = latestUserMessage;
    let grammarFeedback = null;
    // 1) Grammar correction (HF)
    if (enableGrammarCorrection && latestUserMessage?.role === 'user') {
      try {
        const grammarRes = await fetchWithRetry(grammarUrl, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${HF_TOKEN}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            inputs: latestUserMessage.content,
            parameters: {
              max_new_tokens: 64,
              temperature: 0.3,
              do_sample: true,
              return_full_text: false
            }
          })
        });
        let correctedText = latestUserMessage.content;
        if (!grammarRes.ok) {
          console.warn('Grammar correction failed:', grammarRes.status, await grammarRes.text());
          // If 404, the model is not available through Inference Providers
          if (grammarRes.status === 404) {
            console.warn('Model not available through Inference Providers. Consider creating an Inference Endpoint.');
          }
        } else {
          const raw = await grammarRes.text();
          console.log('grammar raw:', raw);
          let grammarData;
          try {
            grammarData = JSON.parse(raw);
          } catch  {
            grammarData = raw;
          }
          // Robust parsing across different HF models
          if (Array.isArray(grammarData) && grammarData[0]?.generated_text) {
            correctedText = String(grammarData[0].generated_text).trim();
          } else if (typeof grammarData === 'string') {
            correctedText = grammarData.trim();
          } else if (grammarData?.generated_text) {
            correctedText = String(grammarData.generated_text).trim();
          }
        }
        // 2) Fallback: if no change, ask chat model to strictly rewrite
        if (!correctedText || correctedText.toLowerCase() === latestUserMessage.content.toLowerCase()) {
          const rewritePrompt = `Rewrite the following sentence in correct English. Only output the corrected sentence (no quotes, no extra words):
"${latestUserMessage.content}"`;
          const rewriteRes = await fetchWithRetry(chatUrl, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${HF_TOKEN}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              inputs: rewritePrompt,
              parameters: {
                max_new_tokens: 64,
                temperature: 0.2,
                top_p: 0.9,
                do_sample: true,
                return_full_text: false
              }
            })
          });
          if (rewriteRes.ok) {
            const rawRewrite = await rewriteRes.text();
            console.log('rewrite raw:', rawRewrite);
            let rewriteData;
            try {
              rewriteData = JSON.parse(rawRewrite);
            } catch  {
              rewriteData = rawRewrite;
            }
            let rewriteText = '';
            if (Array.isArray(rewriteData) && rewriteData[0]?.generated_text) {
              rewriteText = String(rewriteData[0].generated_text).trim();
            } else if (typeof rewriteData === 'string') {
              rewriteText = rewriteData.trim();
            } else if (rewriteData?.generated_text) {
              rewriteText = String(rewriteData.generated_text).trim();
            }
            if (rewriteText && rewriteText.toLowerCase() !== latestUserMessage.content.toLowerCase()) {
              correctedText = rewriteText;
            }
          } else {
            console.warn('Rewrite fallback failed:', rewriteRes.status, await rewriteRes.text());
          }
        }
        if (correctedText && correctedText.toLowerCase() !== latestUserMessage.content.toLowerCase()) {
          correctedUserMessage = {
            ...latestUserMessage,
            content: correctedText
          };
          grammarFeedback = await generateEmpatheticFeedbackViaHF(latestUserMessage.content, correctedText, language, level || 'Intermediate', HF_TOKEN, chatUrl);
        }
      } catch (err) {
        console.warn('Grammar correction exception:', err);
      }
    }
    // Replace last user message with corrected one (if any)
    const messagesWithCorrection = messages.map((m, idx)=>idx === messages.length - 1 && m.role === 'user' ? correctedUserMessage : m);
    // 3) Assistant reply (HF instruct model)
    const assistantMessage = await generateAIResponseViaHF(messagesWithCorrection, language, scenario || 'General conversation', level || 'Intermediate', HF_TOKEN, chatUrl);
    return new Response(JSON.stringify({
      message: assistantMessage,
      grammarFeedback,
      originalText: latestUserMessage?.content,
      correctedText: correctedUserMessage?.content,
      hasCorrection: grammarFeedback !== null
    }), {
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  } catch (error) {
    console.error('Error in language-conversation:', error);
    const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
    return new Response(JSON.stringify({
      error: errorMessage
    }), {
      status: 500,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  }
});
function fallbackInLanguage(language) {
  return language === 'Spanish' ? '¡Vamos a practicar! ¿De qué te gustaría hablar?' : language === 'French' ? 'Pratiquons ! De quoi aimerais-tu parler ?' : language === 'German' ? 'Lass uns üben! Worüber möchtest du sprechen?' : 'Let’s practice!';
}
async function generateAIResponseViaHF(messages, language, scenario, level, hfToken, endpointUrl) {
  const conversation = messages.map((m)=>`${m.role === 'user' ? 'User' : 'Assistant'}: ${m.content}`).join('\n');
  const prompt = `You are a native ${language} speaker helping someone practice ${language}.
- Respond ONLY in ${language}. Never use English.
- Keep it 2–3 sentences.
- Level: ${level}; Scenario: ${scenario}.
- Be encouraging and ask a brief follow-up question.

Conversation so far:
${conversation}

Assistant:`;
  try {
    const res = await fetchWithRetry(endpointUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${hfToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        inputs: prompt,
        parameters: {
          max_new_tokens: 200,
          temperature: 0.7,
          top_p: 0.9,
          do_sample: true,
          return_full_text: false
        }
      })
    });
    if (!res.ok) {
      console.error('HF chat error:', res.status, await res.text());
      return fallbackInLanguage(language);
    }
    const data = await res.json();
    return data?.[0]?.generated_text?.trim() || fallbackInLanguage(language);
  } catch (err) {
    console.error('HF chat exception:', err);
    return fallbackInLanguage(language);
  }
}
async function generateEmpatheticFeedbackViaHF(originalText, correctedText, language, level, hfToken, endpointUrl) {
  const prompt = `You are an empathetic tutor. Respond ONLY in ${language}.
Generate 1–2 sentences of encouraging feedback for a ${level} learner.

Original: "${originalText}"
Corrected: "${correctedText}"`;
  try {
    const res = await fetchWithRetry(endpointUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${hfToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        inputs: prompt,
        parameters: {
          max_new_tokens: 80,
          temperature: 0.7,
          top_p: 0.9,
          do_sample: true,
          return_full_text: false
        }
      })
    });
    if (!res.ok) {
      console.error('HF empathy error:', res.status, await res.text());
      return fallbackInLanguage(language);
    }
    const data = await res.json();
    return data?.[0]?.generated_text?.trim() || fallbackInLanguage(language);
  } catch (err) {
    console.error('HF empathy exception:', err);
    return fallbackInLanguage(language);
  }
}
