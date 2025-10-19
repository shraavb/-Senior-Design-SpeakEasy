import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type'
};

interface ConversationData {
  userId: string;
  timestamp: Date;
  scenario: string;
  language: string;
  userMessage: string;
  aiResponse: string;
  userRating?: number;
  context: {
    level: string;
    topic: string;
    culturalBackground?: string;
  };
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const body = await req.json();
    const { 
      userId, 
      scenario, 
      language, 
      userMessage, 
      aiResponse, 
      userRating, 
      context 
    } = body;

    // Validate required fields
    if (!userId || !scenario || !language || !userMessage || !aiResponse) {
      return new Response(JSON.stringify({
        error: 'Missing required fields: userId, scenario, language, userMessage, aiResponse'
      }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // Create conversation data object
    const conversationData: ConversationData = {
      userId: userId, // Should be anonymized on frontend
      timestamp: new Date(),
      scenario,
      language,
      userMessage,
      aiResponse,
      userRating,
      context: {
        level: context?.level || 'Intermediate',
        topic: context?.topic || 'General',
        culturalBackground: context?.culturalBackground
      }
    };

    // Store in Supabase (you'll need to create a conversations table)
    const supabaseUrl = Deno.env.get('SUPABASE_URL');
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
    
    if (supabaseUrl && supabaseKey) {
      const response = await fetch(`${supabaseUrl}/rest/v1/conversations`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${supabaseKey}`,
          'Content-Type': 'application/json',
          'Prefer': 'return=minimal'
        },
        body: JSON.stringify(conversationData)
      });

      if (!response.ok) {
        console.error('Failed to store conversation data:', await response.text());
      }
    }

    // Return success response
    return new Response(JSON.stringify({
      success: true,
      message: 'Conversation data collected successfully'
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });

  } catch (error) {
    console.error('Error in data collection:', error);
    return new Response(JSON.stringify({
      error: 'Internal server error'
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
});
