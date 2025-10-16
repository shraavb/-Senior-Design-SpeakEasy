#!/usr/bin/env node

/**
 * Test script for Grammar Correction Integration
 * 
 * This script tests the grammar correction and empathy generation functions
 * to ensure they're working correctly with the HuggingFace Llama-2-7B model.
 */

const SUPABASE_URL = process.env.SUPABASE_URL || 'https://goyhiczyiwsosgyzkboq.supabase.co';
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY || 'your-anon-key';

// Test cases for grammar correction
const testCases = [
  {
    input: "I am go to school",
    language: "Spanish",
    scenario: "General Conversation",
    level: "Intermediate",
    expectedCorrection: "I go to school" // Expected correction
  },
  {
    input: "She don't like pizza",
    language: "French", 
    scenario: "Ordering at a Restaurant",
    level: "Beginner",
    expectedCorrection: "She doesn't like pizza"
  },
  {
    input: "We was happy yesterday",
    language: "German",
    scenario: "Discussing Feelings", 
    level: "Intermediate",
    expectedCorrection: "We were happy yesterday"
  }
];

async function testGrammarCorrection() {
  console.log('🧪 Testing Grammar Correction Integration...\n');
  
  for (const testCase of testCases) {
    console.log(`Testing: "${testCase.input}"`);
    console.log(`Language: ${testCase.language}, Level: ${testCase.level}`);
    
    try {
      const response = await fetch(`${SUPABASE_URL}/functions/v1/grammar-correction`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userInput: testCase.input,
          language: testCase.language,
          scenario: testCase.scenario,
          level: testCase.level
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      console.log(`✅ Original: "${data.originalText}"`);
      console.log(`✅ Corrected: "${data.correctedText}"`);
      console.log(`✅ Has Correction: ${data.hasCorrection}`);
      console.log(`✅ Empathy Feedback: "${data.empathyFeedback}"`);
      console.log('---\n');
      
    } catch (error) {
      console.error(`❌ Error testing "${testCase.input}":`, error.message);
      console.log('---\n');
    }
  }
}

async function testEmpathyGeneration() {
  console.log('🧪 Testing Empathy Generation...\n');
  
  const empathyTestCases = [
    {
      input: "I am go to school",
      language: "Spanish",
      scenario: "General Conversation",
      level: "Beginner"
    },
    {
      input: "I feel frustrated with this exercise",
      language: "French",
      scenario: "Discussing Feelings",
      level: "Intermediate"
    },
    {
      input: "This is really easy for me",
      language: "German", 
      scenario: "Sharing Opinions",
      level: "Advanced"
    }
  ];

  for (const testCase of empathyTestCases) {
    console.log(`Testing empathy for: "${testCase.input}"`);
    console.log(`Language: ${testCase.language}, Level: ${testCase.level}`);
    
    try {
      const response = await fetch(`${SUPABASE_URL}/functions/v1/empathy-generation`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userInput: testCase.input,
          language: testCase.language,
          scenario: testCase.scenario,
          level: testCase.level,
          conversationHistory: []
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      console.log(`✅ Empathetic Feedback: "${data.empatheticFeedback}"`);
      console.log(`✅ Feedback Type: ${data.feedbackType}`);
      console.log('---\n');
      
    } catch (error) {
      console.error(`❌ Error testing empathy for "${testCase.input}":`, error.message);
      console.log('---\n');
    }
  }
}

async function testEndToEndFlow() {
  console.log('🧪 Testing End-to-End Conversation Flow...\n');
  
  // Simulate a conversation with grammar correction
  const conversationSteps = [
    {
      userInput: "I am go to school",
      language: "Spanish",
      scenario: "General Conversation", 
      level: "Intermediate"
    }
  ];

  for (const step of conversationSteps) {
    console.log(`User says: "${step.userInput}"`);
    
    try {
      // Step 1: Grammar correction
      const grammarResponse = await fetch(`${SUPABASE_URL}/functions/v1/grammar-correction`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userInput: step.userInput,
          language: step.language,
          scenario: step.scenario,
          level: step.level
        }),
      });

      if (!grammarResponse.ok) {
        throw new Error(`Grammar correction failed: ${grammarResponse.status}`);
      }

      const grammarData = await grammarResponse.json();
      
      if (grammarData.hasCorrection) {
        console.log(`📝 Grammar Helper: "${grammarData.empathyFeedback}"`);
        console.log(`📝 Original: "${grammarData.originalText}"`);
        console.log(`📝 Corrected: "${grammarData.correctedText}"`);
        
        // Step 2: Continue conversation with corrected text
        const conversationResponse = await fetch(`${SUPABASE_URL}/functions/v1/language-conversation`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            messages: [
              { role: "user", content: grammarData.correctedText }
            ],
            language: step.language,
            scenario: step.scenario,
            level: step.level
          }),
        });

        if (conversationResponse.ok) {
          const conversationData = await conversationResponse.json();
          console.log(`🤖 AI Response: "${conversationData.message}"`);
        }
      } else {
        console.log(`✅ No grammar correction needed`);
      }
      
      console.log('---\n');
      
    } catch (error) {
      console.error(`❌ Error in end-to-end test:`, error.message);
      console.log('---\n');
    }
  }
}

async function main() {
  console.log('🚀 Starting Grammar Correction Integration Tests\n');
  console.log(`Using Supabase URL: ${SUPABASE_URL}\n`);
  
  // Check if environment variables are set
  if (SUPABASE_URL.includes('your-project') || SUPABASE_ANON_KEY.includes('your-anon-key')) {
    console.log('❌ Please set SUPABASE_URL and SUPABASE_ANON_KEY environment variables');
    console.log('Example: SUPABASE_URL=https://your-project.supabase.co SUPABASE_ANON_KEY=your-key node test-grammar-integration.js');
    process.exit(1);
  }
  
  try {
    await testGrammarCorrection();
    await testEmpathyGeneration();
    await testEndToEndFlow();
    
    console.log('🎉 All tests completed!');
    console.log('\n📋 Next Steps:');
    console.log('1. Deploy the Edge Functions: supabase functions deploy grammar-correction empathy-generation');
    console.log('2. Set up HuggingFace API key in Supabase environment variables');
    console.log('3. Test the integration in your web app');
    
  } catch (error) {
    console.error('❌ Test suite failed:', error);
    process.exit(1);
  }
}

// Run the tests
main();
