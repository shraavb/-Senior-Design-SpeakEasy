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
    const { userInput, language, scenario, level } = await req.json();
    
    const HUGGINGFACE_API_KEY = Deno.env.get('HUGGINGFACE_API_KEY');
    if (!HUGGINGFACE_API_KEY) {
      throw new Error('HUGGINGFACE_API_KEY is not configured');
    }

    // Use the fine-tuned Llama-2-7B model for grammar correction
    const grammarResponse = await fetch('https://api-inference.huggingface.co/models/sylviali/eracond_llama_2_grammar', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${HUGGINGFACE_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        inputs: userInput,
        parameters: {
          max_length: 200,
          temperature: 0.3,
          do_sample: true,
          return_full_text: false
        }
      }),
    });

    if (!grammarResponse.ok) {
      const errorText = await grammarResponse.text();
      console.error('HuggingFace API error:', grammarResponse.status, errorText);
      throw new Error('Grammar correction failed');
    }

    const grammarData = await grammarResponse.json();
    const correctedText = grammarData[0]?.generated_text || userInput;

    // Generate empathetic feedback using the dedicated empathy generation service
    const empathyResponse = await generateEmpatheticFeedback(userInput, correctedText, language, level);
    
    return new Response(
      JSON.stringify({ 
        originalText: userInput,
        correctedText: correctedText,
        empathyFeedback: empathyResponse,
        hasCorrection: userInput.toLowerCase() !== correctedText.toLowerCase()
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('Error in grammar-correction:', error);
    const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
    return new Response(
      JSON.stringify({ error: errorMessage }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});

// Generate empathetic feedback using the dedicated empathy generation service
async function generateEmpatheticFeedback(originalText: string, correctedText: string, language: string, level: string) {
  try {
    // Call the empathy generation service
    const response = await fetch(`${Deno.env.get('SUPABASE_URL')}/functions/v1/empathy-generation`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${Deno.env.get('SUPABASE_ANON_KEY')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        userInput: originalText,
        language,
        scenario: 'Grammar Correction',
        level,
        conversationHistory: []
      }),
    });

    if (!response.ok) {
      throw new Error('Empathy generation service failed');
    }

    const data = await response.json();
    return data.empatheticFeedback || "Good effort! Keep practicing.";
  } catch (error) {
    console.error('Error calling empathy generation service:', error);
    return "Good effort! Keep practicing.";
  }
}
