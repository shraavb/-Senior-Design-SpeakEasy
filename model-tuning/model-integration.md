# Model Tuning Integration

## Overview
This module integrates the fine-tuned colloquial model into the SpeakEasy conversation flow.

## Features

### 1. Model Version Management
- A/B testing between different model versions
- Gradual rollout of new models
- Fallback to base model if tuned model fails

### 2. Dynamic Model Selection
- Select model based on user preferences
- Context-aware model selection (formal vs casual)
- Performance-based model routing

### 3. Real-time Adaptation
- Learn from user feedback
- Continuous model improvement
- Personalized responses

## Implementation

### Model Configuration
```typescript
interface ModelConfig {
  id: string;
  name: string;
  version: string;
  type: 'base' | 'tuned' | 'personalized';
  endpoint: string;
  parameters: {
    temperature: number;
    maxTokens: number;
    topP: number;
  };
  metadata: {
    trainingData: string;
    lastUpdated: Date;
    performance: {
      naturalnessScore: number;
      engagementScore: number;
      accuracyScore: number;
    };
  };
}

const MODEL_CONFIGS: ModelConfig[] = [
  {
    id: 'base-model',
    name: 'Base DialoGPT',
    version: '1.0',
    type: 'base',
    endpoint: 'https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium',
    parameters: {
      temperature: 0.7,
      maxTokens: 100,
      topP: 0.9
    },
    metadata: {
      trainingData: 'General conversation data',
      lastUpdated: new Date('2024-01-01'),
      performance: {
        naturalnessScore: 0.6,
        engagementScore: 0.5,
        accuracyScore: 0.8
      }
    }
  },
  {
    id: 'colloquial-model',
    name: 'Colloquial Tuned Model',
    version: '2.0',
    type: 'tuned',
    endpoint: 'https://api-inference.huggingface.co/models/your-username/speak-easy-colloquial',
    parameters: {
      temperature: 0.8,
      maxTokens: 120,
      topP: 0.95
    },
    metadata: {
      trainingData: 'Colloquial conversation data',
      lastUpdated: new Date(),
      performance: {
        naturalnessScore: 0.9,
        engagementScore: 0.8,
        accuracyScore: 0.7
      }
    }
  }
];
```

### Model Selection Logic
```typescript
class ModelSelector {
  private configs: ModelConfig[];
  
  constructor(configs: ModelConfig[]) {
    this.configs = configs;
  }
  
  selectModel(context: ConversationContext): ModelConfig {
    const { userPreference, scenario, language, level } = context;
    
    // A/B testing logic
    if (this.isInABTest(userPreference.userId)) {
      return this.getABTestModel(userPreference.userId);
    }
    
    // Context-based selection
    if (scenario === 'casual' || userPreference.style === 'informal') {
      return this.getBestModel('tuned');
    }
    
    // Performance-based selection
    return this.getBestPerformingModel();
  }
  
  private isInABTest(userId: string): boolean {
    // Simple hash-based A/B testing
    const hash = this.hashUserId(userId);
    return hash % 100 < 50; // 50% of users get new model
  }
  
  private getABTestModel(userId: string): ModelConfig {
    const hash = this.hashUserId(userId);
    return hash % 2 === 0 
      ? this.configs.find(c => c.id === 'base-model')!
      : this.configs.find(c => c.id === 'colloquial-model')!;
  }
  
  private getBestModel(type: 'base' | 'tuned' | 'personalized'): ModelConfig {
    return this.configs
      .filter(c => c.type === type)
      .sort((a, b) => b.metadata.performance.naturalnessScore - a.metadata.performance.naturalnessScore)[0];
  }
  
  private getBestPerformingModel(): ModelConfig {
    return this.configs
      .sort((a, b) => {
        const scoreA = this.calculateOverallScore(a);
        const scoreB = this.calculateOverallScore(b);
        return scoreB - scoreA;
      })[0];
  }
  
  private calculateOverallScore(config: ModelConfig): number {
    const { naturalnessScore, engagementScore, accuracyScore } = config.metadata.performance;
    return (naturalnessScore * 0.4) + (engagementScore * 0.4) + (accuracyScore * 0.2);
  }
  
  private hashUserId(userId: string): number {
    let hash = 0;
    for (let i = 0; i < userId.length; i++) {
      const char = userId.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash);
  }
}
```

### Enhanced Conversation Function
```typescript
// Updated language-conversation function with model tuning
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type'
};

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const body = await req.json();
    const { 
      messages, 
      language, 
      scenario, 
      level, 
      enableGrammarCorrection = true,
      userPreference = {},
      userId 
    } = body;

    const HF_TOKEN = Deno.env.get('HUGGINGFACE_API_KEY');
    if (!HF_TOKEN) {
      throw new Error('HUGGINGFACE_API_KEY is not configured');
    }

    // Select appropriate model
    const modelSelector = new ModelSelector(MODEL_CONFIGS);
    const selectedModel = modelSelector.selectModel({
      userPreference,
      scenario,
      language,
      level,
      userId
    });

    console.log('Selected model:', selectedModel.name, 'version:', selectedModel.version);

    // Generate response using selected model
    const response = await generateResponseWithModel(
      messages,
      selectedModel,
      HF_TOKEN,
      language,
      scenario,
      level
    );

    // Collect conversation data for future training
    if (userId) {
      await collectConversationData({
        userId,
        scenario,
        language,
        userMessage: messages[messages.length - 1]?.content || '',
        aiResponse: response.message,
        context: { level, topic: scenario }
      });
    }

    return new Response(JSON.stringify({
      message: response.message,
      modelUsed: selectedModel.name,
      modelVersion: selectedModel.version,
      grammarFeedback: response.grammarFeedback,
      originalText: response.originalText,
      correctedText: response.correctedText,
      hasCorrection: response.hasCorrection
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });

  } catch (error) {
    console.error('Error in language-conversation:', error);
    return new Response(JSON.stringify({
      error: error.message
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
});

async function generateResponseWithModel(
  messages: any[],
  modelConfig: ModelConfig,
  token: string,
  language: string,
  scenario: string,
  level: string
) {
  // Implementation similar to existing function but using selected model
  // ... (rest of the implementation)
}
```

## Usage

1. **Deploy the updated function**:
   ```bash
   supabase functions deploy language-conversation --project-ref qhajylwvrwvxymeexixc
   ```

2. **Test with different models**:
   ```bash
   curl -X POST 'https://qhajylwvrwvxymeexixc.supabase.co/functions/v1/language-conversation' \
     -H "Authorization: Bearer YOUR_ANON_KEY" \
     -H "Content-Type: application/json" \
     --data '{
       "messages": [{"role": "user", "content": "Hey, how are you doing?"}],
       "language": "English",
       "scenario": "casual",
       "level": "Intermediate",
       "userId": "test-user-123"
     }'
   ```

3. **Monitor model performance**:
   - Check logs for model selection
   - Track user engagement metrics
   - Collect feedback for model improvement

## Next Steps
1. Implement data collection in the conversation flow
2. Set up A/B testing infrastructure
3. Deploy fine-tuned models
4. Monitor and iterate based on performance
