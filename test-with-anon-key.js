// Grammar Correction Test with Correct Anon Key
async function testGrammarCorrection() {
  console.log('🧪 Testing Grammar Correction with correct anon key...');
  
  const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFoYWp5bHd2cnd2eHltZWV4aXhjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA1NDgwMjQsImV4cCI6MjA3NjEyNDAyNH0.xvQEriF1FYpDnOhkail1ksiA7nT0uqnIiTArZEOwg0o';
  
  try {
    const response = await fetch('https://goyhiczyiwsosgyzkboq.supabase.co/functions/v1/language-conversation', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${ANON_KEY}`
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
      console.log('❌ Error response:', errorText);
      return;
    }
    
    const data = await response.json();
    console.log('✅ Full response:', data);
    
    if (data.hasCorrection) {
      console.log('🎉 Grammar correction is working!');
      console.log('📝 Original:', data.originalText);
      console.log('✅ Corrected:', data.correctedText);
      console.log('💬 Grammar Feedback:', data.grammarFeedback);
      console.log('🤖 AI Response:', data.message);
    } else {
      console.log('❌ No grammar correction detected');
      console.log('🤖 AI Response:', data.message);
      console.log('🔍 Possible issues:');
      console.log('- HUGGINGFACE_API_KEY not set in Supabase');
      console.log('- Function not deployed correctly');
      console.log('- HuggingFace API error');
    }
    
  } catch (error) {
    console.error('❌ Error:', error);
  }
}

// Run the test
testGrammarCorrection();
