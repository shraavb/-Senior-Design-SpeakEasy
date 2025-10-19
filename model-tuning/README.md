# Model Tuning Integration for SpeakEasy

## Overview
This branch implements model tuning capabilities for the SpeakEasy conversation app, focusing on making conversations more natural and colloquial through fine-tuned language models.

## 🎯 **Quick Start Guide**

### **No-Cost MVP (Current)**
- ✅ A/B testing framework with free models
- ✅ Data collection pipeline
- ✅ Graceful fallbacks
- **Cost: $0/month**

### **Full-Featured Version (Future)**
- 🚀 Custom fine-tuned models
- 🚀 HuggingFace Inference Endpoints ($20-100/month)
- 🚀 ElevenLabs Voice Integration ($20-50/month)
- 🚀 Advanced analytics and personalization
- **Cost: $50-200/month**

📋 **See [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md) for detailed upgrade path and cost breakdown**

🧪 **See [AB_TESTING_BREAKDOWN.md](./AB_TESTING_BREAKDOWN.md) for complete A/B testing framework details**

🚀 **See [NEXT_STEPS.md](./NEXT_STEPS.md) for immediate next steps**

## Features

### 🎯 Model Selection & A/B Testing
- **Dynamic Model Selection**: Automatically chooses the best model based on context
- **A/B Testing**: Gradual rollout of new models to measure performance
- **Fallback System**: Graceful degradation to base models if tuned models fail

### 📊 Data Collection Pipeline
- **Real-time Collection**: Gathers conversation data for future training
- **Privacy-First**: Anonymized data collection with user consent
- **Quality Metrics**: Tracks response quality, engagement, and naturalness

### 🔧 Model Configuration
- **Multiple Model Support**: Base models, tuned models, and personalized models
- **Performance Tracking**: Monitors naturalness, engagement, and accuracy scores
- **Parameter Optimization**: Fine-tuned temperature, token limits, and sampling

## File Structure

```
model-tuning/
├── data-collection.md          # Data collection strategy
├── fine-tuning-pipeline.md     # Model training pipeline
├── model-integration.md        # Integration guide
├── config.ts                   # Model configurations
└── model-selector.ts           # Model selection logic

supabase/functions/
├── language-conversation-tuned/ # Enhanced conversation function
└── collect-conversation-data/   # Data collection function
```

## Quick Start

### 1. Set Up Data Collection
```bash
# Deploy the data collection function
supabase functions deploy collect-conversation-data --project-ref qhajylwvrwvxymeexixc
```

### 2. Deploy Enhanced Conversation Function
```bash
# Deploy the model-tuned conversation function
supabase functions deploy language-conversation-tuned --project-ref qhajylwvrwvxymeexixc
```

### 3. Test Model Selection
```bash
curl -X POST 'https://qhajylwvrwvxymeexixc.supabase.co/functions/v1/language-conversation-tuned' \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -H "Content-Type: application/json" \
  --data '{
    "messages": [{"role": "user", "content": "Hey, how are you doing?"}],
    "language": "English",
    "scenario": "casual",
    "level": "Intermediate",
    "userId": "test-user-123",
    "userPreference": {
      "style": "informal",
      "personality": "friendly"
    }
  }'
```

## Model Tuning Pipeline

### 1. Data Collection
- Collect conversation data from real users
- Filter for high-quality interactions
- Anonymize and prepare for training

### 2. Model Training
- Use HuggingFace Transformers with LoRA
- Fine-tune on colloquial conversation data
- Evaluate naturalness and engagement

### 3. Model Deployment
- Upload to HuggingFace Hub
- Integrate into conversation flow
- Monitor performance metrics

### 4. Continuous Improvement
- Collect feedback and ratings
- Retrain models with new data
- A/B test new model versions

## Configuration

### Model Configurations
Edit `model-tuning/config.ts` to add new models:

```typescript
{
  id: 'my-new-model',
  name: 'My Custom Model',
  version: '1.0',
  type: 'tuned',
  endpoint: 'https://api-inference.huggingface.co/models/username/model-name',
  parameters: {
    temperature: 0.8,
    maxTokens: 120,
    topP: 0.95
  },
  metadata: {
    trainingData: 'Custom conversation data',
    lastUpdated: new Date(),
    performance: {
      naturalnessScore: 0.9,
      engagementScore: 0.8,
      accuracyScore: 0.7
    }
  }
}
```

### A/B Testing
Modify the A/B testing logic in `model-selector.ts`:

```typescript
private isInABTest(userId: string): boolean {
  const hash = this.hashUserId(userId);
  return hash % 100 < 25; // 25% of users get new model
}
```

## Environment Variables

Required environment variables in Supabase:

```bash
# HuggingFace API Key
HUGGINGFACE_API_KEY=hf_xxxxx

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Optional: Lovable AI fallback
LOVABLE_API_KEY=your-lovable-key
```

## Database Schema

Create a `conversations` table in Supabase:

```sql
CREATE TABLE conversations (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id TEXT NOT NULL,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  scenario TEXT NOT NULL,
  language TEXT NOT NULL,
  user_message TEXT NOT NULL,
  ai_response TEXT NOT NULL,
  user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 5),
  context JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- Create policy for service role
CREATE POLICY "Service role can insert conversations" ON conversations
  FOR INSERT TO service_role WITH CHECK (true);
```

## Monitoring & Analytics

### Key Metrics
- **Model Selection Rate**: Which models are being used
- **Response Quality**: User ratings and engagement
- **Naturalness Score**: Linguistic analysis of responses
- **A/B Test Performance**: Comparison between model versions

### Logging
The system logs:
- Model selection decisions
- API call performance
- Error rates and fallbacks
- User engagement metrics

## Next Steps

1. **Deploy Functions**: Deploy the enhanced conversation function
2. **Set Up Database**: Create the conversations table
3. **Collect Data**: Start gathering conversation data
4. **Train Models**: Run the fine-tuning pipeline
5. **Monitor Performance**: Track metrics and iterate

## Contributing

When adding new features:
1. Update model configurations in `config.ts`
2. Modify selection logic in `model-selector.ts`
3. Test with different scenarios and user preferences
4. Monitor performance metrics
5. Document changes in this README

## Troubleshooting

### Common Issues
- **Model Not Found**: Check HuggingFace model availability
- **API Rate Limits**: Implement retry logic and fallbacks
- **Data Collection Errors**: Verify Supabase permissions
- **A/B Test Issues**: Check user ID hashing logic

### Debug Mode
Enable debug logging by setting:
```bash
DEBUG=true
```

This will log model selection decisions and API responses.
