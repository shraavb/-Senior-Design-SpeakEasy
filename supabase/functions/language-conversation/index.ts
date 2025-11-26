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
    const { messages, language, scenario, level, feedbackMode, provideFeedback } = await req.json();
    
    const LOVABLE_API_KEY = Deno.env.get('LOVABLE_API_KEY');
    if (!LOVABLE_API_KEY) {
      throw new Error('LOVABLE_API_KEY is not configured');
    }

    // Create a system prompt based on the learning context and feedback mode
    const feedbackInstruction = feedbackMode === "off"
      ? "- Gently correct mistakes by naturally incorporating the correct form in your response (indirect correction)"
      : "- Respond naturally without explicitly correcting mistakes (corrections will be shown separately)";

    const systemPrompt = `You are a native ${language} speaker helping someone practice conversational ${language}.

Context:
- Learner Level: ${level || 'Intermediate'}
- Scenario: ${scenario || 'General conversation'}
- Feedback Mode: ${feedbackMode || 'on'}

Instructions:
- Respond ONLY in ${language} (not English)
- Keep responses conversational and natural (2-3 sentences)
- Match the learner's level - use appropriate vocabulary and grammar
- Stay in character for the scenario
${feedbackInstruction}
- Be encouraging and patient
- Ask follow-up questions to keep the conversation flowing
- Write naturally - do NOT say punctuation marks out loud (no "comma", "period", "question mark", etc.)
- Use punctuation normally in your written response - the speech system will handle the intonation`;

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
          ...messages
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

    // If feedback is requested, analyze the user's last message for corrections
    let corrections = null;
    console.log('Checking if should provide feedback:', { provideFeedback, messageCount: messages.length });

    if (provideFeedback && messages.length > 0) {
      const lastUserMessage = messages[messages.length - 1];
      console.log('Last user message:', lastUserMessage);

      if (lastUserMessage.role === 'user') {
        console.log('Generating feedback for user message:', lastUserMessage.content);
        const feedbackPrompt = `You are a ${language} language teacher. Analyze this learner's message for grammatical errors, unnatural phrasing, or vocabulary issues in the context of: ${scenario}.

Learner's message: "${lastUserMessage.content}"

Provide corrections in this JSON format ONLY (no additional text):
{
  "userSaid": "the exact text the user said",
  "shouldSay": "the corrected version",
  "corrections": [
    {
      "wrong": "incorrect word/phrase",
      "correct": "correct word/phrase",
      "explanation": "brief explanation of why this is better"
    }
  ]
}

If the message is already correct or has only very minor issues, return:
{
  "userSaid": "the exact text",
  "shouldSay": null,
  "corrections": []
}`;

        try {
          const feedbackResponse = await fetch('https://ai.gateway.lovable.dev/v1/chat/completions', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${LOVABLE_API_KEY}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              model: 'google/gemini-2.5-flash',
              messages: [
                { role: 'user', content: feedbackPrompt }
              ],
            }),
          });

          if (feedbackResponse.ok) {
            const feedbackData = await feedbackResponse.json();
            const feedbackText = feedbackData.choices[0].message.content;
            console.log('Feedback AI response:', feedbackText);

            // Try to parse JSON from the response
            try {
              // Extract JSON from the response (in case it's wrapped in markdown or text)
              const jsonMatch = feedbackText.match(/\{[\s\S]*\}/);
              if (jsonMatch) {
                const parsedCorrections = JSON.parse(jsonMatch[0]);
                console.log('Parsed corrections:', parsedCorrections);

                // Include corrections if there's a shouldSay field (even if corrections array is empty)
                // This way we can show "good job" messages too
                if (parsedCorrections.shouldSay || (parsedCorrections.corrections && parsedCorrections.corrections.length > 0)) {
                  corrections = parsedCorrections;
                  console.log('Setting corrections to:', corrections);
                } else {
                  console.log('No corrections needed - user message was correct');
                }
              } else {
                console.log('No JSON match found in feedback response');
              }
            } catch (parseError) {
              console.error('Error parsing feedback JSON:', parseError, 'Text was:', feedbackText);
            }
          } else {
            console.error('Feedback response not ok:', feedbackResponse.status);
          }
        } catch (feedbackError) {
          console.error('Error getting feedback:', feedbackError);
          // Continue without feedback rather than failing the whole request
        }
      }
    }

    const responseData = {
      message: assistantMessage,
      corrections: corrections
    };
    console.log('Returning response with corrections:', corrections ? 'YES' : 'NO');
    console.log('Final response data:', JSON.stringify(responseData));

    return new Response(
      JSON.stringify(responseData),
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
