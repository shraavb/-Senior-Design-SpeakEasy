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
    const { userInput, language, scenario, level, conversationHistory } = await req.json();
    
    const LOVABLE_API_KEY = Deno.env.get('LOVABLE_API_KEY');
    if (!LOVABLE_API_KEY) {
      throw new Error('LOVABLE_API_KEY is not configured');
    }

    // Generate adaptive empathetic feedback based on the research paper's methodology
    const empathyResponse = await generateAdaptiveEmpatheticFeedback(
      userInput, 
      language, 
      scenario, 
      level, 
      conversationHistory || []
    );
    
    return new Response(
      JSON.stringify({ 
        empatheticFeedback: empathyResponse,
        feedbackType: determineFeedbackType(userInput, language, level)
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('Error in empathy-generation:', error);
    const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
    return new Response(
      JSON.stringify({ error: errorMessage }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});

// Generate adaptive empathetic feedback following the research paper's approach
async function generateAdaptiveEmpatheticFeedback(
  userInput: string, 
  language: string, 
  scenario: string, 
  level: string, 
  conversationHistory: any[]
) {
  const LOVABLE_API_KEY = Deno.env.get('LOVABLE_API_KEY');
  
  // Analyze the user's input for emotional context and difficulty level
  const emotionalContext = analyzeEmotionalContext(userInput);
  const difficultyLevel = assessDifficultyLevel(userInput, level);
  const conversationContext = analyzeConversationContext(conversationHistory);
  
  // Create adaptive prompt based on the research paper's empathetic response framework
  const empathyPrompt = `You are an adaptive empathetic language learning assistant following evidence-based pedagogical principles.

Context Analysis:
- Learner Level: ${level}
- Scenario: ${scenario}
- Emotional Context: ${emotionalContext}
- Difficulty Level: ${difficultyLevel}
- Conversation Context: ${conversationContext}

User Input: "${userInput}"

Generate an empathetic response that:
1. Acknowledges the learner's effort and emotional state
2. Provides encouragement appropriate to their level
3. Adapts tone based on the scenario context
4. Uses appropriate complexity for their level
5. Maintains motivation and confidence

Empathetic Response Guidelines:
- Use warm, encouraging language
- Acknowledge progress and effort
- Provide gentle guidance when needed
- Match the emotional tone of the scenario
- Keep responses concise (1-2 sentences)
- Respond ONLY in ${language}

Examples of adaptive empathetic responses:
- For beginners: "I can see you're really trying hard! That's wonderful progress."
- For intermediate: "Great effort! You're expressing yourself clearly and naturally."
- For advanced: "Excellent! Your language skills are really developing well."

Respond in ${language}:`;

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
        max_tokens: 150,
        temperature: 0.8
      }),
    });

    if (!response.ok) {
      throw new Error('Empathy generation failed');
    }

    const data = await response.json();
    return data.choices[0].message.content.trim();
  } catch (error) {
    console.error('Error generating empathetic feedback:', error);
    return getFallbackEmpatheticResponse(language, level);
  }
}

// Analyze emotional context from user input
function analyzeEmotionalContext(input: string): string {
  const positiveWords = ['happy', 'good', 'great', 'wonderful', 'excited', 'love', 'like'];
  const negativeWords = ['sad', 'bad', 'difficult', 'hard', 'confused', 'frustrated', 'hate'];
  const uncertainWords = ['maybe', 'think', 'not sure', 'perhaps', 'might'];
  
  const lowerInput = input.toLowerCase();
  
  if (positiveWords.some(word => lowerInput.includes(word))) {
    return 'positive';
  } else if (negativeWords.some(word => lowerInput.includes(word))) {
    return 'negative';
  } else if (uncertainWords.some(word => lowerInput.includes(word))) {
    return 'uncertain';
  }
  
  return 'neutral';
}

// Assess difficulty level of the input
function assessDifficultyLevel(input: string, learnerLevel: string): string {
  const wordCount = input.split(' ').length;
  const hasComplexGrammar = /(if|when|because|although|however|therefore)/i.test(input);
  
  if (learnerLevel === 'Beginner') {
    return wordCount > 10 ? 'challenging' : 'appropriate';
  } else if (learnerLevel === 'Intermediate') {
    return wordCount > 20 || hasComplexGrammar ? 'challenging' : 'appropriate';
  } else {
    return 'appropriate';
  }
}

// Analyze conversation context
function analyzeConversationContext(history: any[]): string {
  if (history.length === 0) return 'new conversation';
  if (history.length < 3) return 'early conversation';
  if (history.length < 6) return 'developing conversation';
  return 'established conversation';
}

// Determine feedback type for UI display
function determineFeedbackType(input: string, language: string, level: string): string {
  const hasErrors = /(is|are|was|were|have|has|had)/i.test(input) && 
                   !/(I am|you are|he is|she is|we are|they are)/i.test(input);
  
  if (hasErrors) return 'grammar_correction';
  if (input.length < 5) return 'encouragement';
  return 'general_feedback';
}

// Fallback empathetic responses
function getFallbackEmpatheticResponse(language: string, level: string): string {
  const responses = {
    'Beginner': {
      'Spanish': '¡Muy bien! Sigue practicando.',
      'French': 'Très bien ! Continue à pratiquer.',
      'German': 'Sehr gut! Übe weiter.',
      'Italian': 'Molto bene! Continua a praticare.',
      'Japanese': 'とても良いです！練習を続けてください。',
      'Mandarin': '很好！继续练习。'
    },
    'Intermediate': {
      'Spanish': '¡Excelente esfuerzo! Tu progreso es notable.',
      'French': 'Excellent effort ! Votre progrès est remarquable.',
      'German': 'Ausgezeichnete Anstrengung! Ihr Fortschritt ist bemerkenswert.',
      'Italian': 'Sforzo eccellente! Il tuo progresso è notevole.',
      'Japanese': '素晴らしい努力です！あなたの進歩は顕著です。',
      'Mandarin': '出色的努力！你的进步很明显。'
    },
    'Advanced': {
      'Spanish': '¡Fantástico! Tu dominio del idioma es impresionante.',
      'French': 'Fantastique ! Votre maîtrise de la langue est impressionnante.',
      'German': 'Fantastisch! Ihre Sprachbeherrschung ist beeindruckend.',
      'Italian': 'Fantastico! La tua padronanza della lingua è impressionante.',
      'Japanese': '素晴らしい！あなたの言語習得は印象的です。',
      'Mandarin': '太棒了！你的语言掌握令人印象深刻。'
    }
  };
  
  return responses[level]?.[language] || 'Great effort! Keep practicing.';
}
