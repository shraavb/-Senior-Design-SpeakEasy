# Grammar Correction Integration - Manual Setup Guide

## Step 1: Get Supabase Access Token

1. Go to https://supabase.com/dashboard
2. Click on your profile icon (top right)
3. Go to "Access Tokens"
4. Click "Generate new token"
5. Give it a name like "Grammar Integration"
6. Copy the generated token

## Step 2: Set Environment Variables

Run these commands in your terminal:

```bash
cd /Users/shraavastibhat/-Senior-Design-SpeakEasy

# Set your Supabase access token
export SUPABASE_ACCESS_TOKEN=your_supabase_access_token_here

# Set the HuggingFace API key
export HUGGINGFACE_API_KEY=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
```

## Step 3: Deploy the Functions

```bash
# Deploy grammar correction function
supabase functions deploy grammar-correction --project-ref goyhiczyiwsosgyzkboq

# Deploy empathy generation function  
supabase functions deploy empathy-generation --project-ref goyhiczyiwsosgyzkboq
```

## Step 4: Set Environment Variables in Supabase Dashboard

1. Go to https://supabase.com/dashboard/project/goyhiczyiwsosgyzkboq
2. Navigate to Settings > Edge Functions
3. Add these environment variables:
   - `HUGGINGFACE_API_KEY` = `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`
   - `LOVABLE_API_KEY` = (your existing Lovable API key)

## Step 5: Test the Integration

```bash
# Test grammar correction
node test-grammar-integration.js
```

## Alternative: Manual Function Creation

If deployment fails, you can manually create the functions in the Supabase dashboard:

1. Go to https://supabase.com/dashboard/project/goyhiczyiwsosgyzkboq/functions
2. Click "Create a new function"
3. Name it "grammar-correction"
4. Copy the code from `supabase/functions/grammar-correction/index.ts`
5. Repeat for "empathy-generation"

## Verification

Once deployed, test with:

```bash
curl -X POST 'https://goyhiczyiwsosgyzkboq.supabase.co/functions/v1/grammar-correction' \
  -H 'Authorization: Bearer YOUR_ANON_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "userInput": "I am go to school",
    "language": "Spanish",
    "scenario": "General Conversation",
    "level": "Intermediate"
  }'
```

Replace `YOUR_ANON_KEY` with your Supabase anon key from the project settings.
