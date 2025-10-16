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
    const { messages, language, scenario, level, enableGrammarCorrection = true } = await req.json();
    
    const LOVABLE_API_KEY = Deno.env.get('LOVABLE_API_KEY');
    const HUGGINGFACE_API_KEY = Deno.env.get('HUGGINGFACE_API_KEY');
    
    if (!LOVABLE_API_KEY) {
      throw new Error('LOVABLE_API_KEY is not configured');
    }

    // Get the latest user message for grammar correction
    const latestUserMessage = messages[messages.length - 1];
    let correctedUserMessage = latestUserMessage;
    let grammarFeedback = null;

    // Apply grammar correction if enabled and HuggingFace API key is available
    if (enableGrammarCorrection && HUGGINGFACE_API_KEY && latestUserMessage?.role === 'user') {
      try {
        console.log('Applying grammar correction to:', latestUserMessage.content);
        
        const grammarResponse = await fetch('https://api-inference.huggingface.co/models/sylviali/eracond_llama_2_grammar', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${HUGGINGFACE_API_KEY}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            inputs: latestUserMessage.content,
            parameters: {
              max_length: 200,
              temperature: 0.3,
              do_sample: true,
              return_full_text: false
            }
          }),
        });

        if (grammarResponse.ok) {
          const grammarData = await grammarResponse.json();
          const correctedText = grammarData[0]?.generated_text || latestUserMessage.content;
          
          // Check if there was a correction
          if (correctedText.toLowerCase() !== latestUserMessage.content.toLowerCase()) {
            correctedUserMessage = { ...latestUserMessage, content: correctedText };
            
            // Generate empathetic feedback for the correction
            grammarFeedback = await generateEmpatheticFeedback(
              latestUserMessage.content, 
              correctedText, 
              language, 
              level
            );
            
            console.log('Grammar correction applied:', {
              original: latestUserMessage.content,
              corrected: correctedText,
              feedback: grammarFeedback
            });
          }
        } else {
          console.warn('Grammar correction failed:', grammarResponse.status);
        }
      } catch (error) {
        console.warn('Grammar correction error:', error);
      }
    }

    // Create a system prompt based on the learning context
    const systemPrompt = `You are a native ${language} speaker helping someone practice conversational ${language}. 

Context:
- Learner Level: ${level || 'Intermediate'}
- Scenario: ${scenario || 'General conversation'}

Instructions:
- Respond ONLY in ${language} (not English)
- Keep responses conversational and natural (2-3 sentences)
- Match the learner's level - use appropriate vocabulary and grammar
- Stay in character for the scenario
- Gently correct major mistakes by using the correct form naturally in your response
- Be encouraging and patient
- Ask follow-up questions to keep the conversation flowing
- Write naturally - do NOT say punctuation marks out loud (no "comma", "period", "question mark", etc.)
- Use punctuation normally in your written response - the speech system will handle the intonation`;

    // Use corrected message in conversation
    const messagesWithCorrection = messages.map((msg, index) => 
      index === messages.length - 1 && msg.role === 'user' ? correctedUserMessage : msg
    );

    const response = await fetch('https://ai.gateway.lovable.dev/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${LOVABLE_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'google/gemini-2.5-flash',
        messages: [
          { role: 'system', content: systemPrompt },
          ...messagesWithCorrection
        ],
      }),
    });

    if (!response.ok) {
      if (response.status === 429) {
        return new Response(
          JSON.stringify({ error: 'Rate limit exceeded. Please try again in a moment.' }),
          { status: 429, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        );
      }
      if (response.status === 402) {
        return new Response(
          JSON.stringify({ error: 'Usage limit reached. Please add credits to continue.' }),
          { status: 402, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        );
      }
      const errorText = await response.text();
      console.error('Lovable AI error:', response.status, errorText);
      throw new Error('Failed to get AI response');
    }

    const data = await response.json();
    const assistantMessage = data.choices[0].message.content;

    return new Response(
      JSON.stringify({ 
        message: assistantMessage,
        grammarFeedback: grammarFeedback,
        originalText: latestUserMessage?.content,
        correctedText: correctedUserMessage?.content,
        hasCorrection: grammarFeedback !== null
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('Error in language-conversation:', error);
    const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
    return new Response(
      JSON.stringify({ error: errorMessage }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});

// Generate empathetic feedback for grammar corrections
async function generateEmpatheticFeedback(originalText: string, correctedText: string, language: string, level: string) {
  const LOVABLE_API_KEY = Deno.env.get('LOVABLE_API_KEY');
  if (!LOVABLE_API_KEY) {
    return "Good effort! Keep practicing.";
  }

  // Generate adaptive empathetic feedback
  const empathyPrompt = `You are an empathetic language learning assistant. Generate encouraging feedback for a ${level} level ${language} learner.

Original: "${originalText}"
Corrected: "${correctedText}"

Generate a brief, encouraging response (1-2 sentences) that:
- Acknowledges their effort positively
- Provides gentle encouragement
- Uses appropriate language for their level
- Responds in ${language}

Examples of empathetic responses:
- "Great attempt! I can see you're trying to express yourself clearly."
- "You're making good progress! Here's a small adjustment to help you sound more natural."
- "Nice work! Let me help you with a small grammar improvement."

Respond ONLY in ${language}:`;

  try {
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
            content: empathyPrompt
          }
        ],
        max_tokens: 100,
        temperature: 0.7
      }),
    });

    if (!response.ok) {
      throw new Error('Empathy generation failed');
    }

    const data = await response.json();
    return data.choices[0].message.content.trim();
  } catch (error) {
    console.error('Error generating empathetic feedback:', error);
    return "Good effort! Keep practicing.";
  }
}
