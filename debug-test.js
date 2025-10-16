// Quick Debug Test - Paste this in your browser console
async function debugGrammarCorrection() {
  console.log('🔍 Debugging Grammar Correction...');
  
  try {
    const response = await fetch('/functions/v1/language-conversation', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
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
    const data = await response.json();
    console.log('Full response:', data);
    
    if (data.hasCorrection) {
      console.log('✅ Grammar correction is working!');
      console.log('Original:', data.originalText);
      console.log('Corrected:', data.correctedText);
      console.log('Feedback:', data.grammarFeedback);
    } else {
      console.log('❌ No grammar correction detected');
      console.log('Possible issues:');
      console.log('- HUGGINGFACE_API_KEY not set');
      console.log('- Function not deployed correctly');
      console.log('- HuggingFace API error');
    }
    
  } catch (error) {
    console.error('❌ Error:', error);
  }
}

debugGrammarCorrection();
