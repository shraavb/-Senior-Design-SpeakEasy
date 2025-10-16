// Fixed Debug Test - Paste this in your browser console
async function debugGrammarCorrection() {
  console.log('🔍 Debugging Grammar Correction...');
  
  try {
    // Use the full Supabase URL
    const response = await fetch('https://goyhiczyiwsosgyzkboq.supabase.co/functions/v1/language-conversation', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer sb_publishable_E6DduYBibrStKdFFPzj5ew_ZjRcoLcN'
      },
      body: JSON.stringify({
        messages: [{ role: "user", content: "I am go to school" }],
        language: "Spanish",
        scenario: "General Conversation",
        level: "Intermediate",
        enableGrammarCorrection: true
      }),
    });
    
    console.log('Response status:', response.status);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.log('Error response:', errorText);
      return;
    }
    
    const data = await response.json();
    console.log('Full response:', data);
    
    if (data.hasCorrection) {
      console.log('✅ Grammar correction is working!');
      console.log('Original:', data.originalText);
      console.log('Corrected:', data.correctedText);
      console.log('Feedback:', data.grammarFeedback);
    } else {
      console.log('❌ No grammar correction detected');
      console.log('Response message:', data.message);
    }
    
  } catch (error) {
    console.error('❌ Error:', error);
  }
}

debugGrammarCorrection();
