# TODO: Fluency Metrics Integration

## Pending Tasks

### 1. Run Supabase Migrations

Run these in order via the Supabase Dashboard SQL Editor:

1. **First**: Run `001_create_user_profiles.sql` (creates base `user_profiles` table)
   - Go to: https://supabase.com/dashboard → Your Project → SQL Editor
   - Copy contents from: `supabase/migrations/001_create_user_profiles.sql`
   - Click "Run"

2. **Second**: Run `002_create_fluency_metrics.sql` (creates fluency tables)
   - Copy contents from: `supabase/migrations/002_create_fluency_metrics.sql`
   - Click "Run"

---

### 2. Deploy Fluency Service to Render

1. Go to https://render.com and sign in
2. Click "New" → "Web Service"
3. Connect your GitHub repo or use "Public Git repository"
4. Configure:
   - **Name**: `speakeasy-fluency-api`
   - **Root Directory**: `dataset-pipeline`
   - **Runtime**: Python
   - **Build Command**: `pip install -r src/fluency_service/requirements.txt`
   - **Start Command**: `uvicorn src.fluency_service.main:app --host 0.0.0.0 --port $PORT`

5. Add Environment Variables:
   - `PYTHON_VERSION` = `3.11`
   - `WHISPER_MODEL` = `tiny` (use tiny for free tier)
   - `WHISPER_DEVICE` = `cpu`

6. Click "Create Web Service"

7. Once deployed, copy your Render URL (e.g., `https://speakeasy-fluency-api.onrender.com`)

---

### 3. Update Environment Variable

After Render deployment, update `.env`:
```
VITE_FLUENCY_API_URL=https://your-actual-render-url.onrender.com
```

Current placeholder is set to: `https://speakeasy-fluency-api.onrender.com`

---

### 4. Test Frontend

```bash
npm run dev
```

Check for:
- [ ] No TypeScript errors on startup
- [ ] Progress page loads with 3-pillar system (Accuracy, Flow, Expression)
- [ ] Dashboard shows pillar indicators below fluency score
- [ ] No console errors

---

### 5. Test Full Integration

1. Start a conversation session
2. Complete it and check:
   - [ ] Session summary shows 3-pillar scores
   - [ ] Data saves to Supabase `session_evaluations` table
   - [ ] Progress page shows real data from evaluation

---

## Files Created/Modified

| File | Status |
|------|--------|
| `src/types/fluency.ts` | Created |
| `src/services/fluencyService.ts` | Created |
| `src/hooks/useFluencyMetrics.ts` | Created |
| `src/components/feedback-metrics/accuracy-pillar.tsx` | Created |
| `src/components/feedback-metrics/flow-pillar.tsx` | Created |
| `src/components/feedback-metrics/expression-pillar.tsx` | Created |
| `src/components/feedback-metrics/quick-summary.tsx` | Updated |
| `src/components/feedback-metrics/section-nav.tsx` | Updated |
| `src/components/feedback-metrics/vocabulary-insights.tsx` | Updated |
| `src/pages/Progress.tsx` | Updated |
| `src/pages/Dashboard.tsx` | Updated |
| `supabase/migrations/002_create_fluency_metrics.sql` | Created |
| `dataset-pipeline/src/fluency_service/requirements.txt` | Created |
| `dataset-pipeline/src/fluency_service/render.yaml` | Created |
| `dataset-pipeline/src/fluency_service/config.py` | Updated |
| `.env` | Updated |

---

## 3-Pillar System Reference

| Pillar | Icon | Components | Formula |
|--------|------|------------|---------|
| Accuracy | Target | Pronunciation + Lexical | `(pron × 0.25 + lex × 0.15) / 0.40` |
| Flow | Zap | Temporal + Disfluency (inverted) | `(temp × 0.20 + (100-disf) × 0.20) / 0.40` |
| Expression | Sparkles | Prosodic + Communicative | `(pros × 0.10 + comm × 0.10) / 0.20` |
