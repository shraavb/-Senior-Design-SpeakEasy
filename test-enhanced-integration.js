#!/usr/bin/env node

/**
 * Quick Test for Enhanced Grammar Correction Integration
 * 
 * This tests the updated language-conversation function with grammar correction
 */

const SUPABASE_URL = 'https://goyhiczyiwsosgyzkboq.supabase.co';
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY || 'your-anon-key';

async function testGrammarCorrection() {
  console.log('🧪 Testing Enhanced Grammar Correction Integration...\n');
  
  const testCases = [
    {
      input: "I am go to school",
      language: "Spanish",
      scenario: "General Conversation",
      level: "Intermediate"
    },
    {
      input: "She don't like pizza",
      language: "French", 
      scenario: "Ordering at a Restaurant",
      level: "Beginner"
    },
    {
      input: "We was happy yesterday",
      language: "German",
      scenario: "Discussing Feelings", 
      level: "Intermediate"
    }
  ];

  for (const testCase of testCases) {
    console.log(`Testing: "${testCase.input}"`);
    console.log(`Language: ${testCase.language}, Level: ${testCase.level}`);
    
    try {
      const response = await fetch(`${SUPABASE_URL}/functions/v1/language-conversation`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: [{ role: "user", content: testCase.input }],
          language: testCase.language,
          scenario: testCase.scenario,
          level: testCase.level,
          enableGrammarCorrection: true
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      console.log(`✅ AI Response: "${data.message}"`);
      console.log(`✅ Has Correction: ${data.hasCorrection}`);
      
      if (data.hasCorrection) {
        console.log(`✅ Original: "${data.originalText}"`);
        console.log(`✅ Corrected: "${data.correctedText}"`);
        console.log(`✅ Grammar Feedback: "${data.grammarFeedback}"`);
      } else {
        console.log(`✅ No grammar correction needed`);
      }
      
      console.log('---\n');
      
    } catch (error) {
      console.error(`❌ Error testing "${testCase.input}":`, error.message);
      console.log('---\n');
    }
  }
}

async function main() {
  console.log('🚀 Testing Enhanced Grammar Correction Integration\n');
  
  if (SUPABASE_ANON_KEY.includes('your-anon-key')) {
    console.log('❌ Please set SUPABASE_ANON_KEY environment variable');
    console.log('Example: SUPABASE_ANON_KEY=your-key node test-enhanced-integration.js');
    process.exit(1);
  }
  
  try {
    await testGrammarCorrection();
    console.log('🎉 Test completed!');
    console.log('\n📋 Next Steps:');
    console.log('1. Deploy the updated language-conversation function');
    console.log('2. Set HUGGINGFACE_API_KEY environment variable');
    console.log('3. Test in your web app!');
    
  } catch (error) {
    console.error('❌ Test failed:', error);
    process.exit(1);
  }
}

main();
