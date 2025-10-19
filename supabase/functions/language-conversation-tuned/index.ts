import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

// Simple hash function for A/B testing
function hashUserId(userId: string): number {
  let hash = 0;
  for (let i = 0; i < userId.length; i++) {
    const char = userId.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash);
}

// Free model configurations for testing
const FREE_MODELS = [
  {
    id: 'microsoft-dialo',
    name: 'Microsoft DialoGPT',
    endpoint: 'https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium',
    description: 'Microsoft DialoGPT Medium'
  },
  {
    id: 'gpt2',
    name: 'GPT-2',
    endpoint: 'https://api-inference.huggingface.co/models/gpt2',
    description: 'OpenAI GPT-2'
  },
  {
    id: 'distilgpt2',
    name: 'DistilGPT-2',
    endpoint: 'https://api-inference.huggingface.co/models/distilgpt2',
    description: 'Distilled GPT-2'
  }
];

// Test free model API
async function testFreeModel(model: any, token: string): Promise<boolean> {
  try {
    const response = await fetch(model.endpoint, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        inputs: 'Hello',
        parameters: {
          max_new_tokens: 10,
          temperature: 0.7,
          do_sample: true,
          return_full_text: false
        }
      })
    });
    
    return response.ok;
  } catch (error) {
    console.error(`Model ${model.name} test failed:`, error);
    return false;
  }
}

// Generate response using free model
async function generateWithFreeModel(model: any, token: string, prompt: string): Promise<string> {
  try {
    const response = await fetch(model.endpoint, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        inputs: prompt,
        parameters: {
          max_new_tokens: 100,
          temperature: 0.8,
          do_sample: true,
          return_full_text: false
        }
      })
    });

    if (!response.ok) {
      throw new Error(`Model ${model.name} failed: ${response.status}`);
    }

    const data = await response.json();
    return data?.[0]?.generated_text?.trim() || 'Sorry, I could not generate a response.';
  } catch (error) {
    console.error(`Error with model ${model.name}:`, error);
    throw error;
  }
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const body = await req.json();
    const { 
      messages, 
      language, 
      scenario, 
      level, 
      userId,
      userPreference = {}
    } = body;

    console.log('Request received:', { language, scenario, level, userId });

    // Check for API keys
    const HF_TOKEN = Deno.env.get('HUGGINGFACE_API_KEY');
    const LOVABLE_API_KEY = Deno.env.get('LOVABLE_API_KEY');
    
    if (!HF_TOKEN && !LOVABLE_API_KEY) {
      throw new Error('No API keys configured (HUGGINGFACE_API_KEY or LOVABLE_API_KEY)');
    }

    // A/B testing logic
    const testUserId = userId || 'anonymous';
    const hash = hashUserId(testUserId);
    const isInABTest = hash % 100 < 50; // 50% of users get new model
    const selectedModel = isInABTest ? 'Free Model (A/B Test)' : 'Lovable AI (Control)';
    
    console.log('A/B Test - User:', testUserId, 'Hash:', hash, 'Selected:', selectedModel);

    // Try free models first if HuggingFace token is available
    if (HF_TOKEN && isInABTest) {
      console.log('Testing free models...');
      
      // Test which free models are available
      const availableModels = [];
      for (const model of FREE_MODELS) {
        const isAvailable = await testFreeModel(model, HF_TOKEN);
        if (isAvailable) {
          availableModels.push(model);
          console.log(`✅ ${model.name} is available`);
        } else {
          console.log(`❌ ${model.name} is not available`);
        }
      }

      if (availableModels.length > 0) {
        // Use the first available model
        const selectedFreeModel = availableModels[0];
        console.log(`Using free model: ${selectedFreeModel.name}`);

        // Create conversation context
        const conversation = messages.map(m => `${m.role === 'user' ? 'User' : 'Assistant'}: ${m.content}`).join('\n');
        
        const prompt = `You are a native ${language} speaker helping someone practice ${language}.
- Respond ONLY in ${language}. Never use English.
- Keep it 2–3 sentences.
- Level: ${level}; Scenario: ${scenario}.
- Be encouraging and ask a brief follow-up question.
- Use natural, colloquial language when appropriate.

Conversation so far:
${conversation}

Assistant:`;

        try {
          const response = await generateWithFreeModel(selectedFreeModel, HF_TOKEN, prompt);
          
          return new Response(
            JSON.stringify({ 
              message: response,
              modelUsed: 'Free Model (A/B Test)',
              selectedModel: selectedFreeModel.name,
              modelVersion: '1.0',
              userId: testUserId,
              scenario: scenario,
              language: language,
              level: level,
              abTestInfo: {
                isInABTest: true,
                hash: hash,
                testGroup: 'A',
                availableModels: availableModels.map(m => m.name),
                selectedFreeModel: selectedFreeModel.name
              }
            }),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
          );
        } catch (error) {
          console.warn('Free model failed, falling back to Lovable AI:', error);
          // Fall through to Lovable AI
        }
      } else {
        console.warn('No free models available, falling back to Lovable AI');
        // Fall through to Lovable AI
      }
    }

    // Fallback to Lovable AI
    if (LOVABLE_API_KEY) {
      const systemPrompt = `You are a native ${language} speaker helping someone practice conversational ${language}. 

Context:
- Learner Level: ${level || 'Intermediate'}
- Scenario: ${scenario || 'General conversation'}

Instructions:
- Respond ONLY in ${language} (not English)
- Keep responses conversational and natural (2-3 sentences)
- Match the learner's level - use appropriate vocabulary and grammar
- Stay in character for the scenario
- Be encouraging and patient
- Ask follow-up questions to keep the conversation flowing
- Use natural, colloquial language when appropriate`;

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

      return new Response(
        JSON.stringify({ 
          message: assistantMessage,
          modelUsed: 'Lovable AI (Control)',
          selectedModel: selectedModel,
          modelVersion: '1.0',
          userId: testUserId,
          scenario: scenario,
          language: language,
          level: level,
          abTestInfo: {
            isInABTest: false,
            hash: hash,
            testGroup: 'B'
          }
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // If no Lovable API key, return a test response
    return new Response(
      JSON.stringify({ 
        message: `Hello! I'm here to help you practice ${language}. How can I assist you today?`,
        modelUsed: 'Test Mode',
        modelVersion: '1.0',
        userId: testUserId,
        scenario: scenario,
        language: language,
        level: level,
        abTestInfo: {
          isInABTest: isInABTest,
          hash: hash,
          testGroup: isInABTest ? 'A' : 'B'
        }
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('Error in language-conversation-tuned:', error);
    const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
    return new Response(
      JSON.stringify({ 
        error: errorMessage,
        details: error instanceof Error ? error.stack : 'No stack trace available'
      }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});