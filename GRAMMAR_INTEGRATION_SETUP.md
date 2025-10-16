# Environment Variables Setup for Grammar Correction Integration

## Required Environment Variables

Add these environment variables to your Supabase project settings:

### 1. HuggingFace API Key
```
HUGGINGFACE_API_KEY=your_huggingface_api_key_here
```
- Get your API key from: https://huggingface.co/settings/tokens
- This is required to access the fine-tuned Llama-2-7B model

### 2. Existing Variables (should already be configured)
```
LOVABLE_API_KEY=your_lovable_api_key_here
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
```

## Setup Instructions

1. **Get HuggingFace API Key:**
   - Go to https://huggingface.co/settings/tokens
   - Create a new token with "Read" permissions
   - Copy the token

2. **Add to Supabase:**
   - Go to your Supabase project dashboard
   - Navigate to Settings > Edge Functions
   - Add the `HUGGINGFACE_API_KEY` environment variable

3. **Deploy Edge Functions:**
   ```bash
   supabase functions deploy grammar-correction
   supabase functions deploy empathy-generation
   ```

## Testing the Integration

1. **Test Grammar Correction:**
   ```bash
   curl -X POST 'https://your-project.supabase.co/functions/v1/grammar-correction' \
     -H 'Authorization: Bearer your-anon-key' \
     -H 'Content-Type: application/json' \
     -d '{
       "userInput": "I am go to school",
       "language": "Spanish",
       "scenario": "General Conversation",
       "level": "Intermediate"
     }'
   ```

2. **Test Empathy Generation:**
   ```bash
   curl -X POST 'https://your-project.supabase.co/functions/v1/empathy-generation' \
     -H 'Authorization: Bearer your-anon-key' \
     -H 'Content-Type: application/json' \
     -d '{
       "userInput": "I am go to school",
       "language": "Spanish",
       "scenario": "General Conversation",
       "level": "Intermediate",
       "conversationHistory": []
     }'
   ```

## Features Implemented

### 1. Grammar Correction Pipeline
- Uses the fine-tuned Llama-2-7B model from HuggingFace
- Processes user input and provides corrected versions
- Handles errors gracefully with fallbacks

### 2. Adaptive Empathetic Feedback
- Analyzes emotional context of user input
- Adapts feedback based on learner level and scenario
- Provides encouraging, contextually appropriate responses

### 3. Enhanced UI
- Visual indicators for grammar corrections
- Side-by-side comparison of original vs corrected text
- Color-coded feedback messages
- Grammar helper avatar and styling

### 4. Conversation Flow Integration
- Seamlessly integrates grammar correction into existing conversation flow
- Maintains conversation context while providing corrections
- Uses corrected text for AI responses

## Usage in Your App

The integration works automatically in your conversation flow:

1. User speaks → Speech recognition converts to text
2. Text is sent to grammar correction service
3. If corrections are needed, empathetic feedback is generated
4. User sees grammar feedback with original/corrected comparison
5. Conversation continues with corrected text
6. AI responds naturally to the corrected input

## Customization Options

You can customize the integration by:

1. **Adjusting empathy prompts** in `empathy-generation/index.ts`
2. **Modifying UI styling** in `Conversation.tsx`
3. **Changing grammar correction parameters** in `grammar-correction/index.ts`
4. **Adding more languages** by updating the language mappings

## Troubleshooting

### Common Issues:

1. **HuggingFace API Rate Limits:**
   - The model may take time to load on first request
   - Consider implementing retry logic for production

2. **Grammar Correction Not Working:**
   - Check HuggingFace API key is correctly set
   - Verify the model is accessible: https://huggingface.co/sylviali/eracond_llama_2_grammar

3. **Empathy Generation Failing:**
   - Ensure Lovable API key is configured
   - Check Supabase function logs for errors

### Performance Considerations:

- Grammar correction adds ~2-3 seconds to response time
- Consider implementing caching for repeated inputs
- Monitor API usage and costs for both HuggingFace and Lovable
