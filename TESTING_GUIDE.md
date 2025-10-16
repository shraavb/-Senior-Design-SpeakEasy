# 🧪 Grammar Correction Testing Guide

## Method 1: Browser Console Test (Easiest)

1. **Open your web app** in the browser
2. **Open Developer Tools** (F12)
3. **Go to Console tab**
4. **Paste this test code**:

```javascript
// Test grammar correction
async function testGrammarCorrection() {
  const testCases = [
    "I am go to school",
    "She don't like pizza", 
    "We was happy yesterday"
  ];
  
  for (const testCase of testCases) {
    console.log(`\n🧪 Testing: "${testCase}"`);
    
    try {
      const response = await fetch('/functions/v1/language-conversation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: [{ role: "user", content: testCase }],
          language: "Spanish",
          scenario: "General Conversation",
          level: "Intermediate",
          enableGrammarCorrection: true
        }),
      });
      
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
      
    } catch (error) {
      console.error(`❌ Error:`, error);
    }
  }
}

// Run the test
testGrammarCorrection();
```

## Method 2: Test in Your App

1. **Start your app**: `npm run dev`
2. **Go to a conversation**
3. **Try these test phrases**:
   - "I am go to school"
   - "She don't like pizza"
   - "We was happy yesterday"

4. **Look for**:
   - Blue-tinted "Grammar Helper" message
   - Original vs corrected text comparison
   - Empathetic feedback in target language

## Method 3: Check Function Logs

1. **Go to Supabase Dashboard**
2. **Navigate to Edge Functions**
3. **Click on your `language-conversation` function**
4. **Check the logs** for grammar correction activity

## Expected Results:

### ✅ **Successful Grammar Correction:**
- Grammar Helper message appears
- Shows: "Original: I am go to school"
- Shows: "Corrected: I go to school"  
- Shows empathetic feedback in Spanish/French/German
- AI responds to corrected text

### ❌ **If Not Working:**
- Check environment variable `HUGGINGFACE_API_KEY` is set
- Check function logs for errors
- Verify function is deployed correctly

## Quick Debug Steps:

1. **Check Environment Variables**:
   - Go to Supabase Dashboard → Edge Functions → Environment Variables
   - Verify `HUGGINGFACE_API_KEY` = `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`

2. **Check Function Logs**:
   - Look for "Applying grammar correction to:" messages
   - Look for any error messages

3. **Test Simple Case**:
   - Try saying "I am go to school" in your app
   - Should see grammar correction if working

The easiest way is **Method 2** - just try it in your app! 🚀
