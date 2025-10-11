# Welcome to your Lovable project

## Project info

**URL**: https://lovable.dev/projects/41304ac3-1da0-4d5d-bb53-e0e95ca2bdb3

## SpeakEasy - Language Learning Platform

A conversational AI-powered language learning platform that helps users achieve fluency through natural speech-to-speech practice.

### Features

- 🎤 **Speech-to-Speech Conversations**: Practice real conversations with AI in your target language
- 🌍 **Multiple Languages**: Spanish, French, German, Italian, Japanese, Mandarin
- 📚 **Hover Translations**: Hover over any word to see instant English translations
- 🎯 **Scenario-Based Learning**: Practice real-world situations (tourism, social, professional)
- 📊 **Progress Tracking**: Monitor your fluency scores, streaks, and achievements
- 🏆 **Leaderboard**: Compete with other learners and stay motivated

### Tech Stack

- **Frontend**: React, TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: Lovable Cloud (Supabase)
- **AI**: Lovable AI Gateway (Google Gemini)
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

## How can I edit this code?

There are several ways of editing your application.

**Use Lovable**

Simply visit the [Lovable Project](https://lovable.dev/projects/41304ac3-1da0-4d5d-bb53-e0e95ca2bdb3) and start prompting.

Changes made via Lovable will be committed automatically to this repo.

**Use your preferred IDE**

If you want to work locally using your own IDE, you can clone this repo and push changes. Pushed changes will also be reflected in Lovable.

The only requirement is having Node.js & npm installed - [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)

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

**Edit a file directly in GitHub**

- Navigate to the desired file(s).
- Click the "Edit" button (pencil icon) at the top right of the file view.
- Make your changes and commit the changes.

**Use GitHub Codespaces**

- Navigate to the main page of your repository.
- Click on the "Code" button (green button) near the top right.
- Select the "Codespaces" tab.
- Click on "New codespace" to launch a new Codespace environment.
- Edit files directly within the Codespace and commit and push your changes once you're done.

## What technologies are used for this project?

This project is built with:

- Vite
- TypeScript
- React
- shadcn-ui
- Tailwind CSS

## How can I deploy this project?

Simply open [Lovable](https://lovable.dev/projects/41304ac3-1da0-4d5d-bb53-e0e95ca2bdb3) and click on Share -> Publish.

## Can I connect a custom domain to my Lovable project?

Yes, you can!

To connect a domain, navigate to Project > Settings > Domains and click Connect Domain.

Read more here: [Setting up a custom domain](https://docs.lovable.dev/features/custom-domain#custom-domain)
