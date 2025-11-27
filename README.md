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
- **Backend**: Express.js + Node.js
- **AI**: Groq (Llama 3.3 70B) / Google Gemini
- **Text-to-Speech**: ElevenLabs (multilingual natural voices)
- **Speech Recognition**: Browser Web Speech API

### Key Features in Detail

#### Natural Voice Synthesis with ElevenLabs
- Authentic native speaker voices for 7 languages
- Dialect support (e.g., Latin American vs European Spanish)
- Automatic audio playback for immersive learning

#### AI-Powered Corrections
- Real-time grammar and usage feedback
- Contextual explanations for mistakes
- Toggle between direct feedback and soft corrections

#### Hover-to-Translate
- Instant word translations on hover
- Supports CJK (Chinese, Japanese, Korean) character-by-character
- Smart word segmentation for space-based languages

## Development Setup

### Prerequisites

- Node.js & npm installed - [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)

### Local Development

Follow these steps:

```sh
# Step 1: Clone the repository
git clone https://github.com/shraavb/-Senior-Design-SpeakEasy.git
cd -Senior-Design-SpeakEasy-3

# Step 2: Install frontend dependencies
npm install

# Step 3: Install backend dependencies
cd server
npm install
cd ..

# Step 4: Set up environment variables

# For backend (server/.env):
cd server
cp .env.example .env
# Edit .env and add your API keys:
# - GROQ_API_KEY
# - ELEVENLABS_API_KEY
# - GOOGLE_AI_API_KEY (optional)
cd ..

# For frontend (.env):
cp .env.example .env
# Use default: VITE_API_BASE_URL=http://localhost:3001

# Step 5: Start the backend server (in one terminal)
cd server
npm start
# Backend will run on http://localhost:3001

# Step 6: Start the frontend dev server (in another terminal)
npm run dev
# Frontend will run on http://localhost:8080
```

### API Keys Required

1. **Groq API**

2. **ElevenLabs API**

3. **Google Gemini**


## What technologies are used for this project?

This project is built with:

- Vite
- TypeScript
- React
- shadcn-ui
- Tailwind CSS

## Deployment

- Render
