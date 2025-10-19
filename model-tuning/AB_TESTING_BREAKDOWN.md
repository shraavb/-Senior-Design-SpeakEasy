# A/B Testing Framework Breakdown

## Overview
The SpeakEasy model tuning integration includes a sophisticated A/B testing framework designed to compare different model approaches while minimizing risk and maximizing learning.

## 🎯 A/B Testing Strategy

### **Test Design**
- **Control Group (50%)**: Uses Lovable AI (existing, proven system)
- **Test Group (50%)**: Uses free HuggingFace models (new approach)
- **Random Assignment**: Based on user ID hash for consistent assignment
- **Gradual Rollout**: Can be adjusted from 0% to 100% test group

### **Primary Hypothesis**
> "Free HuggingFace models can provide comparable or better conversation quality than Lovable AI, enabling cost savings and custom model development."

## 🔧 Technical Implementation

### **Hash-Based Assignment**
```typescript
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

// A/B testing logic
const testUserId = userId || 'anonymous';
const hash = hashUserId(testUserId);
const isInABTest = hash % 100 < 50; // 50% of users get new model
const selectedModel = isInABTest ? 'Free Model (A/B Test)' : 'Lovable AI (Control)';
```

### **Assignment Logic**
- **Hash % 100 < 50**: User gets Test Group (free models)
- **Hash % 100 >= 50**: User gets Control Group (Lovable AI)
- **Consistent Assignment**: Same user always gets same group
- **Even Distribution**: Approximately 50/50 split

## 📊 Test Groups Breakdown

### **Group A: Test Group (Free Models)**
```typescript
{
  isInABTest: true,
  testGroup: 'A',
  modelUsed: 'Free Model (A/B Test)',
  models: [
    'Microsoft DialoGPT',
    'GPT-2', 
    'DistilGPT-2'
  ],
  fallback: 'Lovable AI (if free models fail)'
}
```

**What Group A Users Experience:**
1. **Primary**: Free HuggingFace models (Microsoft DialoGPT, GPT-2, DistilGPT-2)
2. **Testing**: Automatic model availability testing
3. **Fallback**: Graceful degradation to Lovable AI if free models fail
4. **Logging**: Detailed logs of which models work/fail

### **Group B: Control Group (Lovable AI)**
```typescript
{
  isInABTest: false,
  testGroup: 'B', 
  modelUsed: 'Lovable AI (Control)',
  models: ['google/gemini-2.5-flash'],
  fallback: 'Test Mode (if no API key)'
}
```

**What Group B Users Experience:**
1. **Primary**: Lovable AI with Gemini 2.5 Flash
2. **Consistent**: Same experience as before A/B testing
3. **Baseline**: Provides performance baseline for comparison
4. **Reliable**: Proven, stable system

## 🧪 Testing Methodology

### **Model Testing Sequence (Group A)**
```typescript
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

// Use first available model
if (availableModels.length > 0) {
  const selectedFreeModel = availableModels[0];
  const response = await generateWithFreeModel(selectedFreeModel, HF_TOKEN, prompt);
}
```

### **Free Models Tested**
1. **Microsoft DialoGPT Medium**
   - Endpoint: `https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium`
   - Type: Conversational AI
   - Strengths: Designed for dialogue

2. **GPT-2**
   - Endpoint: `https://api-inference.huggingface.co/models/gpt2`
   - Type: General language model
   - Strengths: Widely tested, reliable

3. **DistilGPT-2**
   - Endpoint: `https://api-inference.huggingface.co/models/distilgpt2`
   - Type: Lightweight GPT-2
   - Strengths: Faster, smaller

## 📈 Metrics and Data Collection

### **Response Data Collected**
```typescript
interface ABTestResponse {
  message: string;                    // AI response
  modelUsed: string;                 // Which model was used
  selectedModel: string;             // Specific model name
  modelVersion: string;              // Model version
  userId: string;                    // User identifier
  scenario: string;                  // Conversation scenario
  language: string;                  // Target language
  level: string;                     // User level
  abTestInfo: {
    isInABTest: boolean;             // Whether user is in test group
    hash: number;                    // User hash for assignment
    testGroup: 'A' | 'B';           // Test group assignment
    availableModels?: string[];      // Which free models worked
    selectedFreeModel?: string;      // Which free model was used
  };
}
```

### **Performance Metrics Tracked**
- **Response Time**: API call latency
- **Model Availability**: Which models work/fail
- **Response Quality**: User ratings (future)
- **User Engagement**: Conversation length, follow-up questions
- **Error Rates**: Fallback frequency

## 🔍 Example Test Results

### **User Assignment Examples**
```bash
# User: "test-user-123"
# Hash: 1333033973
# Hash % 100 = 73
# 73 >= 50 → Group B (Control)

# User: "abtest-user-001" 
# Hash: 865464713
# Hash % 100 = 13
# 13 < 50 → Group A (Test)
```

### **Sample Responses**

**Group A Response (Free Models):**
```json
{
  "message": "Hey there! I'm doing great, thanks for asking! How about you? What brings you here today?",
  "modelUsed": "Free Model (A/B Test)",
  "selectedModel": "Microsoft DialoGPT",
  "abTestInfo": {
    "isInABTest": true,
    "testGroup": "A",
    "availableModels": ["Microsoft DialoGPT", "GPT-2"],
    "selectedFreeModel": "Microsoft DialoGPT"
  }
}
```

**Group B Response (Control):**
```json
{
  "message": "Hello! I'm doing well, thank you for asking. How are you feeling today?",
  "modelUsed": "Lovable AI (Control)",
  "selectedModel": "Lovable AI (Control)",
  "abTestInfo": {
    "isInABTest": false,
    "testGroup": "B"
  }
}
```

## 🎛️ Configuration Options

### **Adjustable Parameters**
```typescript
// A/B test percentage (currently 50%)
const isInABTest = hash % 100 < 50; // Change 50 to adjust percentage

// Free models to test (easily expandable)
const FREE_MODELS = [
  { id: 'microsoft-dialo', name: 'Microsoft DialoGPT', endpoint: '...' },
  { id: 'gpt2', name: 'GPT-2', endpoint: '...' },
  { id: 'distilgpt2', name: 'DistilGPT-2', endpoint: '...' }
  // Add more models here
];

// Model selection criteria
const selectedFreeModel = availableModels[0]; // Use first available
// Could be changed to: best performing, random, user preference, etc.
```

### **Gradual Rollout Strategy**
- **Phase 1**: 10% test group (hash % 100 < 10)
- **Phase 2**: 25% test group (hash % 100 < 25)  
- **Phase 3**: 50% test group (hash % 100 < 50)
- **Phase 4**: 100% test group (if successful)

## 📊 Analysis Framework

### **Success Criteria**
1. **Model Availability**: >80% of free models work
2. **Response Quality**: Comparable to Lovable AI
3. **Response Time**: <2 seconds average
4. **User Engagement**: Similar conversation length
5. **Error Rate**: <5% fallback to Lovable AI

### **Statistical Significance**
- **Sample Size**: Track minimum 100 users per group
- **Duration**: Run test for minimum 1 week
- **Metrics**: Response time, quality, engagement
- **Confidence Level**: 95% confidence interval

### **Decision Framework**
```
IF (free models work well AND response quality is comparable):
  → Proceed to custom model training
ELSE IF (free models fail frequently OR quality is poor):
  → Stick with Lovable AI or try different free models
ELSE:
  → Extend test period for more data
```

## 🔄 Future Enhancements

### **Advanced A/B Testing**
- **Multi-armed Bandit**: Dynamically adjust traffic based on performance
- **User Segmentation**: Different tests for different user types
- **Contextual Testing**: Different models for different scenarios
- **Real-time Optimization**: Automatic model selection based on performance

### **Additional Test Groups**
- **Group C**: Custom fine-tuned models
- **Group D**: ElevenLabs voice integration
- **Group E**: Personalized models per user

## 🚨 Important Notes

### **Current Status**
- ✅ A/B testing framework is deployed and working
- 🔶 Free models need HuggingFace API key to test
- 📊 Data collection is ready for analysis
- 🔄 Can be easily adjusted or extended

### **Risk Mitigation**
- **Graceful Fallbacks**: Always falls back to working system
- **Consistent Assignment**: Users don't experience switching
- **Detailed Logging**: Full visibility into what's happening
- **Easy Rollback**: Can disable A/B testing instantly

This A/B testing framework provides a robust, data-driven approach to validating model improvements while minimizing risk and ensuring user experience quality.
