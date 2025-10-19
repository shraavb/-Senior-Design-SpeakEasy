# Model Tuning Configuration

## Model Configurations
This file contains the configuration for different model versions used in the conversation system.

```typescript
export interface ModelConfig {
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

export interface ConversationContext {
  userPreference: {
    userId: string;
    style: 'formal' | 'informal' | 'mixed';
    personality: 'friendly' | 'professional' | 'casual';
  };
  scenario: string;
  language: string;
  level: string;
  userId: string;
}

export const MODEL_CONFIGS: ModelConfig[] = [
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
