# Free Deployment Guide: GitHub Pages + Render

This guide shows you how to deploy SpeakEasy completely free using GitHub Pages (frontend) and Render (backend).

## Part 1: Deploy Backend to Render (5 minutes)

### Step 1: Create Render Account
1. Go to [render.com](https://render.com)
2. Click "Get Started for Free"
3. Sign up with GitHub

### Step 2: Create Web Service
1. Click "New +" → "Web Service"
2. Connect your GitHub account if not already connected
3. Select your repository: `shraavb/-Senior-Design-SpeakEasy`
4. Click "Connect"

### Step 3: Configure Service
Fill in these settings:
- **Name**: `speakeasy-backend` (or any name you like)
- **Region**: Choose closest to you
- **Branch**: `main`
- **Root Directory**: `server`
- **Runtime**: `Node`
- **Build Command**: `npm install`
- **Start Command**: `node index.js`
- **Instance Type**: `Free`

### Step 4: Add Environment Variables
Click "Advanced" → "Add Environment Variable" and add these:

```
PORT=3001
GROQ_API_KEY=<your-groq-api-key>
USE_GROQ=true
USE_ELEVENLABS=false
```

Optional (if you want Google Gemini as fallback):
```
GOOGLE_AI_API_KEY=<your-google-api-key>
```

Optional (if you want to enable ElevenLabs later):
```
ELEVENLABS_API_KEY=<your-elevenlabs-key>
```

### Step 5: Deploy
1. Click "Create Web Service"
2. Wait 2-3 minutes for deployment
3. **Copy your backend URL** - it will look like:
   `https://speakeasy-backend.onrender.com`

**Important**: Keep this URL - you'll need it in the next step!

## Part 2: Deploy Frontend to GitHub Pages (5 minutes)

### Step 1: Enable GitHub Pages
1. Go to your GitHub repository: https://github.com/shraavb/-Senior-Design-SpeakEasy
2. Click "Settings" tab
3. Scroll down to "Pages" in the left sidebar
4. Under "Source", select:
   - Source: **GitHub Actions**

### Step 2: Add Backend URL Secret
1. Still in Settings, click "Secrets and variables" → "Actions"
2. Click "New repository secret"
3. Add:
   - **Name**: `VITE_API_BASE_URL`
   - **Value**: Your Render backend URL (e.g., `https://speakeasy-backend.onrender.com`)
4. Click "Add secret"

### Step 3: Trigger Deployment
The deployment will happen automatically when you push the code!

Let's push the changes:

```bash
# Make sure you're in the project directory
cd /Users/shraavastibhat/-Senior-Design-SpeakEasy-3

# Add all changes
git add .

# Commit
git commit -m "Add GitHub Pages deployment"

# Push to trigger deployment
git push origin main
```

### Step 4: Wait for Deployment
1. Go to your repository on GitHub
2. Click the "Actions" tab
3. You'll see a workflow running "Deploy to GitHub Pages"
4. Wait 2-3 minutes for it to complete (green checkmark)

### Step 5: Access Your Site
Your site will be live at:
```
https://shraavb.github.io/-Senior-Design-SpeakEasy/
```

## Verification Checklist

Test these features on your deployed site:

- [ ] Site loads at https://shraavb.github.io/-Senior-Design-SpeakEasy/
- [ ] Can select a language
- [ ] Can choose a goal (Tourism/Social/Professional)
- [ ] Conversation page loads
- [ ] Can click microphone and speak
- [ ] AI responds with text
- [ ] AI voice plays (browser TTS)
- [ ] Feedback toggle works
- [ ] Hover over words to see translations

## Troubleshooting

### Frontend Issues

**Problem**: Page shows 404
- **Solution**: Make sure GitHub Pages is enabled in Settings → Pages
- **Solution**: Check that the workflow completed successfully in Actions tab

**Problem**: Can't connect to backend
- **Solution**: Verify `VITE_API_BASE_URL` secret is set correctly
- **Solution**: Make sure your Render backend is running (check Render dashboard)

**Problem**: CORS errors in console
- **Solution**: The backend is configured to allow all origins with `cors()`, this should work

### Backend Issues

**Problem**: Render service failing to start
- **Solution**: Check logs in Render dashboard
- **Solution**: Verify all environment variables are set
- **Solution**: Make sure `GROQ_API_KEY` is valid

**Problem**: "Missing API key" errors
- **Solution**: Double-check environment variables in Render dashboard
- **Solution**: Redeploy after adding missing keys

## Free Tier Limits

### GitHub Pages
- ✅ 1GB storage
- ✅ 100GB bandwidth/month
- ✅ Unlimited builds

### Render Free Tier
- ✅ 750 hours/month (enough for 24/7)
- ⚠️ Spins down after 15 minutes of inactivity
- ⚠️ Takes 30-60 seconds to wake up on first request

**Note**: The backend may be slow on first load due to Render's free tier spin-down. Subsequent requests will be fast!

## Updating Your Site

Whenever you make changes:

```bash
git add .
git commit -m "Your update message"
git push origin main
```

- **Frontend**: Automatically redeploys via GitHub Actions (2-3 minutes)
- **Backend**: Automatically redeploys via Render (2-3 minutes)

## Getting API Keys (Free)

### Groq API (Required)
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up for free
3. Create an API key
4. Free tier: 30 requests/minute

### ElevenLabs (Optional)
1. Go to [elevenlabs.io](https://elevenlabs.io)
2. Sign up for free
3. Get your API key
4. Free tier: 10,000 characters/month

### Google Gemini (Optional Fallback)
1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Create API key
3. Free tier available

## Cost Summary

**Total Monthly Cost: $0**

- GitHub Pages: Free
- Render Backend: Free (750 hours)
- Groq API: Free (30 req/min)
- Browser TTS: Free

**Optional:**
- ElevenLabs: $0 (free tier) or $5/month for more credits

## Support

- Check Render logs for backend issues
- Check GitHub Actions for frontend build issues
- Check browser console (F12) for frontend errors

Your site is now live and completely free!
