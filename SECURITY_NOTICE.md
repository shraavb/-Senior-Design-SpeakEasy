# URGENT: Security Notice - API Key Rotation Required

## What Happened

Your API keys were accidentally committed to the Git repository in previous commits. While they have now been removed from future commits, they still exist in the Git history.

## Immediate Actions Required

### 1. Rotate ALL API Keys Immediately

Your exposed keys need to be regenerated. Follow these steps:

#### Groq API Key
1. Go to [console.groq.com](https://console.groq.com/keys)
2. Delete your old key (starts with `gsk_...`)
3. Create a new API key
4. Update `server/.env` with the new key

#### Google AI API Key
1. Go to [console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials)
2. Delete your old key (starts with `AIza...`)
3. Create a new API key
4. Restrict it to only Gemini API
5. Update `server/.env` with the new key

#### ElevenLabs API Key
1. Go to [elevenlabs.io/app/settings/api-keys](https://elevenlabs.io/app/settings/api-keys)
2. Delete your old key (starts with `sk_...`)
3. Create a new API key
4. Update `server/.env` with the new key

### 2. Update Local Environment Files

After rotating keys, update these files locally (they won't be committed):

```bash
# server/.env
GOOGLE_AI_API_KEY=<your_new_google_key>
GROQ_API_KEY=<your_new_groq_key>
USE_GROQ=true
USE_ELEVENLABS=false
ELEVENLABS_API_KEY=<your_new_elevenlabs_key>
PORT=3001
```

### 3. Update Render Environment Variables

When you deploy to Render, use your NEW API keys in the environment variables section.

## What I've Done to Secure Your Repository

✅ **Added comprehensive .gitignore rules** to prevent future .env commits
✅ **Removed .env files from Git tracking**
✅ **Committed the security fix**

## Why Git History Still Has Them

Git keeps a complete history of all commits. The old keys exist in previous commits forever unless you:
1. **Force rewrite history** (dangerous - can break things)
2. **Delete and recreate the repository** (nuclear option)

**Recommended**: Just rotate the keys (option above). It's simpler and safer.

## Optional: Clean Git History (Advanced)

If you really want to remove keys from Git history, you can use:

```bash
# WARNING: This rewrites history and can break things!
# Only do this if you know what you're doing

# Install BFG Repo-Cleaner
brew install bfg

# Remove all .env files from history
bfg --delete-files '.env'
bfg --delete-files 'server/.env'

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push (WARNING: This will affect anyone else using the repo)
git push origin main --force
```

**I DO NOT recommend this unless absolutely necessary.** Just rotate your keys instead.

## Going Forward

### Never Commit Secrets Again

1. Always check `.gitignore` includes `.env` files
2. Use `.env.example` files for documentation (without actual keys)
3. Before committing, run: `git status` to check what's being added
4. Use environment variables on hosting platforms (Render secrets, GitHub Actions secrets)

### Best Practices

- ✅ Keep API keys in `.env` files (local only)
- ✅ Use `.env.example` for templates
- ✅ Set keys as environment variables in hosting platforms
- ✅ Rotate keys regularly (every 90 days)
- ✅ Never share `.env` files via email/chat
- ❌ Never commit `.env` files to Git
- ❌ Never hardcode keys in source code
- ❌ Never post keys in public forums

## Questions?

If you're unsure about any step, stop and ask for help before proceeding.

## Current Status

- ✅ `.gitignore` updated to protect `.env` files
- ✅ `.env` files removed from Git tracking
- ⚠️ **ACTION REQUIRED**: Rotate all API keys
- ⚠️ Old keys still visible in Git history

**Priority**: Rotate keys today!
