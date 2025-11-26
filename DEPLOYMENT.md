# SpeakEasy - Production Deployment Guide

This guide will help you deploy the SpeakEasy language learning application to production.

## Architecture Overview

The application consists of two parts:
1. **Frontend**: React + Vite application (deployed to Netlify/Vercel)
2. **Backend**: Express.js API server (deployed to Render/Railway/Fly.io)

## Prerequisites

- Node.js 18+ installed
- Git repository access
- API Keys:
  - Groq API key (for Llama 3.3 70B) OR Google Gemini API key
  - ElevenLabs API key (for text-to-speech)

## Backend Deployment

### Option 1: Deploy to Render (Recommended - Free Tier Available)

1. **Prepare your repository**:
   ```bash
   git add .
   git commit -m "Prepare for production deployment"
   git push origin main
   ```

2. **Create a Render account**: Go to [render.com](https://render.com) and sign up

3. **Create a new Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure the service:
     - **Name**: `speakeasy-backend`
     - **Root Directory**: `server`
     - **Environment**: `Node`
     - **Build Command**: `npm install`
     - **Start Command**: `node index.js`
     - **Instance Type**: Free

4. **Add Environment Variables** in Render dashboard:
   ```
   PORT=3001
   GROQ_API_KEY=your_actual_groq_api_key
   USE_GROQ=true
   ELEVENLABS_API_KEY=your_actual_elevenlabs_key
   GOOGLE_AI_API_KEY=your_actual_google_key (optional)
   ```

5. **Deploy**: Render will automatically deploy your backend

6. **Note your backend URL**: It will be something like `https://speakeasy-backend.onrender.com`

### Option 2: Deploy to Railway

1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Configure:
   - **Root Directory**: `/server`
   - Add the same environment variables as above
5. Railway will provide you a URL like `https://speakeasy-backend.up.railway.app`

### Option 3: Deploy to Fly.io

1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Login: `fly auth login`
3. Navigate to server directory: `cd server`
4. Launch app: `fly launch`
5. Set secrets:
   ```bash
   fly secrets set GROQ_API_KEY=your_key
   fly secrets set ELEVENLABS_API_KEY=your_key
   fly secrets set USE_GROQ=true
   ```
6. Deploy: `fly deploy`

## Frontend Deployment

### Option 1: Deploy to Netlify (Recommended)

1. **Update frontend environment variable**:
   - Create `.env.production` in the root directory:
     ```
     VITE_API_BASE_URL=https://your-backend-url.onrender.com
     ```

2. **Install Netlify CLI** (optional):
   ```bash
   npm install -g netlify-cli
   ```

3. **Deploy via Netlify Dashboard**:
   - Go to [netlify.com](https://netlify.com)
   - Click "Add new site" → "Import an existing project"
   - Connect to GitHub and select your repository
   - Configure build settings:
     - **Build command**: `npm run build`
     - **Publish directory**: `dist`
     - **Environment variables**: Add `VITE_API_BASE_URL` with your backend URL

4. **Deploy**: Netlify will build and deploy automatically

### Option 2: Deploy to Vercel

1. Go to [vercel.com](https://vercel.com)
2. Click "Add New" → "Project"
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Vite
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Environment Variables**: Add `VITE_API_BASE_URL`
5. Deploy

## Post-Deployment Steps

### 1. Test Your Deployment

Visit your frontend URL and test:
- ✅ Language selection works
- ✅ Goal selection navigates to correct module
- ✅ Conversation starts and AI responds
- ✅ Speech recognition works
- ✅ ElevenLabs voice playback works
- ✅ Feedback system shows corrections
- ✅ Word translation on hover works

### 2. Update CORS (if needed)

If you encounter CORS errors, update `server/index.js`:

```javascript
app.use(cors({
  origin: ['https://your-frontend-url.netlify.app', 'http://localhost:8080'],
  credentials: true
}));
```

### 3. Monitor Your Backend

- Check Render/Railway/Fly.io logs for errors
- Monitor API rate limits (Groq: 30 req/min, ElevenLabs: varies by plan)

## Environment Variables Reference

### Backend (.env in server/)
- `PORT`: Server port (default: 3001)
- `GROQ_API_KEY`: Groq API key for Llama 3.3 70B
- `GOOGLE_AI_API_KEY`: Google Gemini API key (fallback)
- `USE_GROQ`: Set to `true` to use Groq, `false` for Gemini
- `ELEVENLABS_API_KEY`: ElevenLabs API for natural voice synthesis

### Frontend (.env.production)
- `VITE_API_BASE_URL`: Your deployed backend URL

## Troubleshooting

### Backend Issues

**Error: Missing API keys**
- Ensure all environment variables are set in your hosting platform's dashboard

**Error: Module not found**
- Check that `package.json` is in the `server/` directory
- Verify build command runs `npm install` in the correct directory

### Frontend Issues

**Error: Failed to fetch from backend**
- Verify `VITE_API_BASE_URL` is set correctly
- Check CORS configuration in backend
- Ensure backend is running (check Render/Railway logs)

**Audio not playing**
- Check browser console for errors
- Verify ElevenLabs API key is valid
- Test by clicking "Enable Audio" button

## Cost Estimation

### Free Tier Limits
- **Render**: 750 hours/month (enough for 24/7 operation)
- **Netlify**: 100GB bandwidth/month
- **Groq API**: 30 requests/minute (free)
- **ElevenLabs**: 10,000 characters/month (free tier)

### Scaling Considerations
- If you exceed free tier limits, consider upgrading to paid plans
- Monitor usage through each provider's dashboard
- Consider implementing rate limiting in your backend

## Security Best Practices

1. **Never commit `.env` files** to Git
2. **Use HTTPS only** in production
3. **Rotate API keys** periodically
4. **Monitor API usage** to detect anomalies
5. **Implement rate limiting** to prevent abuse

## Support

For issues or questions:
- Check logs in your hosting provider's dashboard
- Review browser console for frontend errors
- Test API endpoints directly using curl or Postman

---

**Deployment Checklist**:
- [ ] Backend deployed and running
- [ ] Frontend deployed and accessible
- [ ] Environment variables configured
- [ ] API keys working
- [ ] CORS configured correctly
- [ ] All features tested
- [ ] Monitoring set up
