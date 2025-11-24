# ⚡ Quick Start Guide - Ema Agentic Claims

## 🚀 Get Running in 3 Minutes

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Set Up API Key (Optional)
```bash
# Copy template
cp .env.template .env

# Edit .env and add your Gemini API key:
# GEMINI_API_KEY=your-key-here

# Or skip this step - the app works in fallback mode without API keys
```

### Step 3: Launch Applications

#### Option A: Main Claim Processor
```bash
streamlit run streamlit_app.py
```
📍 Opens at `http://localhost:8501`

**Features**: Upload claim JSON, toggle Gemini mode, verbose logging, decision display

---

#### Option B: Claims Manager Dashboard
```bash
streamlit run dashboard.py --server.port=8503
```
📍 Opens at `http://localhost:8503`

**Features**: Claims queue, batch processing, KPIs, adjuster overrides, analytics

---

#### Option C: Appraiser Portal
```bash
streamlit run appraiser.py --server.port=8504
```
📍 Opens at `http://localhost:8504`

**Features**: Inspection queue, photo upload, damage assessment, repair/total loss logic

---

#### Option D: REST API (B2B Integration)
```bash
uvicorn api:app --reload --port 8000
```
📍 API at `http://localhost:8000`  
📍 Docs at `http://localhost:8000/docs`

**Endpoints**:
- `POST /api/v1/claims/process` - Process single claim
- `POST /api/v1/claims/batch` - Batch processing
- `GET /api/v1/claims` - List claims
- `POST /api/v1/claims/{id}/override` - Adjuster override
- `GET /api/v1/metrics` - KPI metrics

---

### Step 4: Test with Sample Data

#### Test Main App:
1. Open `http://localhost:8501`
2. Select a sample claim (e.g., `john.json` - commercial use scenario)
3. Click "Process Claim"
4. View 4-agent decision (FNOL → Triage → Fraud → Coverage)

#### Test Dashboard:
1. Open `http://localhost:8503`
2. Navigate to "Batch Processing" tab
3. Select multiple sample claims
4. Click "Process Batch"
5. View results in "Claims Queue" tab
6. Try adjuster override in "Adjuster Overrides" tab

#### Test Appraiser:
1. Open `http://localhost:8504`
2. Click "Add Test Inspection" in Queue tab
3. Go to "Photo Upload & Assessment" tab
4. Upload photos (optional), fill damage assessment
5. Submit assessment
6. View in "Completed Inspections" tab

---

## 📊 Sample Claims Explained

| File | Scenario | Key Test Case |
| --- | --- | --- |
| `john.json` | Pizza delivery collision | Commercial use exclusion (deny) |
| `alice.json` | Single vehicle accident | Standard coverage (approve) |
| `denied-claim.json` | Uber driver accident | Rideshare exclusion (deny) |
| `total-loss.json` | Vehicle totaled | Repair cost > 75% ACV (total loss) |
| `multi-vehicle.json` | Not-at-fault collision | Subrogation opportunity |
| `injury-claim.json` | Bodily injury + attorney | Litigation risk, SIU referral |
| `vandalism.json` | Keying, broken windows | Comprehensive + police report |

---

## 🎯 What to Expect

### With Gemini API Key:
- **FNOL Agent**: Extracts structured data, identifies severity
- **Triage Agent**: Assigns priority (Immediate/High/Standard/Low), routes to adjuster type
- **Fraud Agent**: Risk score 0.0-1.0, SIU referral triggers
- **Coverage Agent**: Retrieves policy sections via vector store, determines coverage + payout

### Without API Key (Fallback Mode):
- Deterministic logic based on claim attributes
- Commercial use detection → Deny
- Estimated damage > ACV * 0.75 → Total loss
- Still demonstrates full workflow pipeline

---

## 🔍 Troubleshooting

### Issue: `ModuleNotFoundError`
**Fix**: Run `pip install -r requirements.txt`

### Issue: Streamlit port already in use
**Fix**: Change port number:
```bash
streamlit run dashboard.py --server.port=8505
```

### Issue: API key not detected
**Fix**: 
1. Check `.env` file exists in project root
2. Verify key format: `GEMINI_API_KEY=your-key-here` (no quotes)
3. Restart Streamlit app after editing `.env`

### Issue: Policy retrieval errors
**Fix**: Ensure `data/policy_documents.md` exists (should be auto-created)

---

## 📖 View Presentation Deck

Open `docs/presentation.html` in your browser:
- Arrow keys to navigate
- 5 slides covering problem, solution, implementation, metrics
- Interactive charts and metrics

---

## 🧪 Test Workflow Programmatically

```bash
python demo.py
```

Runs workflow with sample claims and prints results.

---

## 🆘 Need Help?

1. **Check README.md** for full documentation
2. **Review QUALITY_REPORT.md** for compliance checklist
3. **Read IMPLEMENTATION_SUMMARY.md** for feature overview
4. **Check API docs** at `http://localhost:8000/docs` (if API running)

---

## ✅ Quick Verification Checklist

- [ ] Dependencies installed (`pip list` shows streamlit, fastapi, plotly, etc.)
- [ ] `.env` file created (optional for Gemini mode)
- [ ] Main app runs on port 8501
- [ ] Dashboard runs on port 8503
- [ ] Sample claims load without errors
- [ ] Can process `john.json` successfully
- [ ] Decision shows FNOL/Triage/Fraud/Coverage insights
- [ ] Batch processing works with multiple claims
- [ ] Presentation deck opens in browser

---

**You're all set! 🎉**

Start with the main app (`streamlit run streamlit_app.py`) and explore from there.
