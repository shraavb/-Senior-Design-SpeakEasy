# SpeakEasy

> A conversational AI-powered language learning platform

## Overview

SpeakEasy helps users achieve language fluency through natural speech-to-speech practice with AI conversation partners. The platform provides immersive, scenario-based learning experiences across multiple languages.

## Features

- **Speech-to-Speech Conversations** - Practice real conversations with AI in your target language
- **Multiple Languages** - Spanish, French, German, Italian, Japanese, Mandarin
- **Hover Translations** - Instant English translations on any word
- **Scenario-Based Learning** - Real-world situations (tourism, social, professional)
- **Progress Tracking** - Monitor fluency scores, streaks, and achievements
- **Leaderboard** - Compete with other learners and stay motivated

### Tech Stack

- **Frontend**: React, TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: Supabase
- **AI**: Google Gemini via AI Gateway
- **Speech**: Browser Web Speech API (default) or ElevenLabs (optional)

### Optional: ElevenLabs Premium Voices

To use ElevenLabs for higher-quality AI voices:

1. Get your API key from [elevenlabs.io](https://elevenlabs.io)
2. Add it as a secret in your backend:
   - Go to Backend → Secrets
   - Add new secret: `ELEVENLABS_API_KEY`
   - Paste your API key
3. Create a Conversational AI agent in your [ElevenLabs dashboard](https://elevenlabs.io/app/conversational-ai)
4. Note your agent ID for use in conversations
5. Update the edge function to use your agent ID when the ElevenLabs option is selected

The app works perfectly with the default browser speech - ElevenLabs is entirely optional for premium voice quality.

## Development Setup

### Prerequisites

- Node.js & npm installed - [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)

### Local Development

Follow these steps:

```sh
# Step 1: Clone the repository using the project's Git URL.
git clone <YOUR_GIT_URL>

# Step 2: Navigate to the project directory.
cd <YOUR_PROJECT_NAME>

# Step 3: Install the necessary dependencies.
npm i

# Step 4: Start the development server with auto-reloading and an instant preview.
npm run dev
```


## What technologies are used for this project?

This project is built with:

- Vite
- TypeScript
- React
- shadcn-ui
- Tailwind CSS

## Deployment

This project can be deployed to any static hosting service that supports React applications:

- Vercel
- Netlify
- GitHub Pages
- AWS Amplify
- Your preferred hosting platform

**Note about Lovable API Key:** The `LOVABLE_API_KEY` used in your edge functions only works within Lovable Cloud. If you need AI features after migrating, you'll need to replace those edge function calls with direct API calls to OpenAI, Google AI, or other providers using your own API keys.
