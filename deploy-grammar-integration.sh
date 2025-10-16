#!/bin/bash

# Grammar Correction Integration Deployment Script
# Run this script after setting up your Supabase access token

echo "🚀 Deploying Grammar Correction Integration..."

# Check if required environment variables are set
if [ -z "$SUPABASE_ACCESS_TOKEN" ]; then
    echo "❌ SUPABASE_ACCESS_TOKEN not set. Please run:"
    echo "export SUPABASE_ACCESS_TOKEN=your_supabase_access_token_here"
    exit 1
fi

if [ -z "$HUGGINGFACE_API_KEY" ]; then
    echo "❌ HUGGINGFACE_API_KEY not set. Please run:"
    echo "export HUGGINGFACE_API_KEY=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"
    exit 1
fi

echo "✅ Environment variables are set"

# Deploy grammar correction function
echo "📦 Deploying grammar-correction function..."
supabase functions deploy grammar-correction --project-ref goyhiczyiwsosgyzkboq

if [ $? -eq 0 ]; then
    echo "✅ grammar-correction function deployed successfully"
else
    echo "❌ Failed to deploy grammar-correction function"
    exit 1
fi

# Deploy empathy generation function
echo "📦 Deploying empathy-generation function..."
supabase functions deploy empathy-generation --project-ref goyhiczyiwsosgyzkboq

if [ $? -eq 0 ]; then
    echo "✅ empathy-generation function deployed successfully"
else
    echo "❌ Failed to deploy empathy-generation function"
    exit 1
fi

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Set environment variables in Supabase dashboard:"
echo "   - Go to: https://supabase.com/dashboard/project/goyhiczyiwsosgyzkboq/settings/functions"
echo "   - Add HUGGINGFACE_API_KEY = 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"
echo ""
echo "2. Test the integration:"
echo "   node test-grammar-integration.js"
echo ""
echo "3. Try the grammar correction in your web app!"
