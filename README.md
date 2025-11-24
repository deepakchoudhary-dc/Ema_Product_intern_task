# 🚗 Ema Agentic Claims Orchestrator

An AI-native vehicle insurance claims experience built for the Ema PM Take-Home brief. Streamlit + LlamaIndex workflows + Gemini 2.5 Flash collaborate to showcase how agentic automation can reshape FNOL → triage → investigation → payout with explainable intelligence.

## 🚀 Features

### Core Functionality
- **Multi-Page Web Application**: Streamlit-based UI with Claims Manager Dashboard, Appraiser Portal, and Adjuster Override
- **Agentic AI Reasoning**: Gemini 2.5 Flash orchestrates FNOL intelligence, triage, fraud scanning, and settlement drafting
- **Policy Vector Store**: Real semantic retrieval from policy documents using LlamaIndex embeddings
- **Structured Decision Making**: Comprehensive claim evaluation with detailed reasoning
- **Real-time Processing**: Asynchronous workflow with live progress tracking
- **Batch Processing**: Parallel claim processing with progress tracking
- **REST API Layer**: FastAPI endpoints for B2B integration (single claim, batch, override, metrics)

### Advanced Capabilities
- **Event-Driven Workflow**: Multi-step processing pipeline with clear event handling
- **FNOL Intelligence Agent**: Summarizes intake narrative, severity, and next best actions
- **Smart Triage Agent**: Assigns adjusters, service levels, and workload routing
- **Fraud Radar Agent**: Generates SIU signals before settlement
- **Coverage Brain Agent**: Aligns policy sections, deductibles, and payouts
- **Human-in-the-Loop**: Adjuster override UI with feedback capture for continuous improvement
- **Claims Manager Dashboard**: Queue management, KPI tracking, workload distribution, SLA monitoring
- **Appraiser Integration**: Inspection assignment, photo upload, damage assessment workflow
- **Comprehensive Analytics**: Before/after metrics, ROI calculator, performance KPIs
- **Diverse Sample Claims**: 7 edge-case scenarios (commercial use, total loss, fraud, injury, vandalism, multi-vehicle, denied claims)

## 👥 Key Stakeholders
- **Claimant / Policyholder** – submits FNOL data that feeds the FNOL Intelligence agent.
- **Claims Intake Specialist** – validates and augments agent output before routing.
- **Claims Adjuster** – consumes Smart Triage + Coverage Brain insights, can override agent decisions.
- **Appraiser / Estimator** – leverages severity scoring to prioritize inspections, uploads damage photos.
- **SIU (Special Investigations Unit)** – monitors Fraud Radar risk scores and flags.
- **Claims Manager** – tracks SLA promises, routing decisions, payer exposure via dashboard.

## 🔄 High-Level Processes Covered
1. **First Notice of Loss (FNOL)** – structured summaries plus recommended follow-up actions.
2. **Triage & Assignment** – priority, adjuster persona, and SLA recommendations.
3. **Investigation & Adjudication** – policy clause retrieval, fraud analysis, and reasoning trace.
4. **Settlement & Payout** – deductible and payout recommendations with contextual notes.
5. **Human Review & Override** – adjusters can modify agent decisions with feedback.
6. **Appraiser Workflow** – inspection scheduling, photo documentation, repair vs total loss assessment.
7. **Analytics & KPIs** – real-time performance metrics, workload distribution, ROI tracking.

### Data Processing
- **Structured JSON Input**: Standardized claim data format
- **Pydantic Validation**: Type-safe data handling and validation
- **Multi-source Analysis**: Integration of claim data, policy documents, and declarations
- **Intelligent Querying**: AI-generated queries for relevant policy section retrieval
- **Vector Search**: Semantic retrieval from policy knowledge base

## 🛠️ Technology Stack

- **Frontend**: Streamlit (multi-page app with dashboard, appraiser, override pages)
- **API Layer**: FastAPI + Uvicorn (REST endpoints for B2B integration)
- **AI/ML**: Gemini 2.5 Flash (via Google Generative AI SDK), LlamaIndex workflows
- **Data Processing**: Pydantic, AsyncIO, Pandas
- **Visualization**: Plotly (interactive charts and metrics)
- **Document Retrieval**: LlamaIndex VectorStoreIndex with sentence splitting
- **Language**: Python 3.10+

## 📋 Installation

### Prerequisites
- Python 3.10 or higher
- Gemini / Google AI Studio API key (optional but recommended for live agentic mode)

### Setup
1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd work
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.template .env  # Create .env file
   # Edit .env and add:
   GEMINI_API_KEY="your-google-ai-studio-key"
   ```

4. **Run the main application**
   ```bash
   streamlit run streamlit_app.py
   ```

5. **Run the Claims Manager Dashboard**
   ```bash
   streamlit run dashboard.py --server.port=8503
   ```

6. **Run the Appraiser Portal**
   ```bash
   streamlit run appraiser.py --server.port=8504
   ```

7. **Run the REST API (optional for B2B integration)**
   ```bash
   uvicorn api:app --reload --port 8000
   ```

8. **View the presentation deck**
   - Open `docs/presentation.html` in your browser
   - Use arrow keys or buttons to navigate slides

9. **Test the system** (optional)
   ```bash
   python demo.py
   ```
   ```bash
   python demo.py
   ```

### Providing Gemini API Keys

- **Local / Instructor review**: drop your key into a local `.env` (based on `.env.template`) or export it before launching Streamlit. The app auto-loads `.env` via `python-dotenv`.
- **Hosted via Streamlit Cloud**: open the project’s **Secrets** panel and add `GEMINI_API_KEY="your-key"`. Visitors use Gemini instantly without seeing the secret.
- **No key?** Leave the toggle off and the workflow runs in deterministic fallback mode so evaluators can still verify functionality.

## 🎯 Usage

### Basic Usage
1. **Access the web interface** at `http://localhost:8501`
2. **Select a claim file** from the dropdown or upload your own JSON file
3. **Optionally enable Gemini Agentic AI** with your API key for live reasoning
4. **Click "Process Claim"** to watch FNOL → Triage → Fraud → Settlement agents run
5. **Review the results** including coverage decision, deductible, recommended payout, severity, triage plan, and SIU signals

### Agentic Mode (Gemini)
1. **Enable "Use Gemini Agentic AI"** in the sidebar
2. **Enter your Google AI Studio key** (Gemini 2.5 Flash)
3. **Toggle verbose mode** to stream every workflow step
4. **Process claims** with live FNOL summaries, routing, fraud checks, and coverage reasoning

## 📁 Project Structure

```
Ema_project_manager_task/
├── streamlit_app.py          # Main Streamlit application
├── workflow.py               # Core workflow and business logic
├── demo.py                   # Demo script for testing
├── requirements.txt          # Python dependencies
├── README.md                # Project documentation
├── .env.template            # Environment variables template
├── .gitignore              # Git ignore rules
├── data/                    # Sample data, claims, and policy documents
│   ├── john.json           # Sample claim: pizza delivery collision (commercial use)
│   ├── alice.json          # Sample claim: single vehicle accident
│   ├── denied-claim.json   # Sample claim: rideshare exclusion scenario
│   ├── total-loss.json     # Sample claim: vehicle totaled, ACV < repair cost
│   ├── multi-vehicle.json  # Sample claim: not-at-fault, subrogation opportunity
│   ├── injury-claim.json   # Sample claim: bodily injury, litigation risk
│   ├── vandalism.json      # Sample claim: comprehensive coverage, police report
│   ├── john-declarations.md # Policy declarations for John
│   ├── alice-declarations.md # Policy declarations for Alice
│   └── policy_documents.md # Policy corpus for vector store retrieval
├── .streamlit/             # Streamlit configuration
│   └── config.toml         # App configuration
├── docs/                   # Documentation and presentations
│   ├── presentation.md     # Text-based pitch deck (5 slides)
│   └── presentation.html   # Visual presentation deck (interactive HTML)
├── workflow.py             # Core agentic workflow (4 agents + orchestration)
├── streamlit_app.py        # Main Streamlit UI (claim upload and processing)
├── dashboard.py            # Claims Manager Dashboard (queue, metrics, batch processing)
├── appraiser.py            # Appraiser Portal (inspections, photo upload, damage assessment)
├── api.py                  # FastAPI REST endpoints (B2B integration, batch, override)
├── policy_retrieval.py     # Policy vector store implementation
├── demo.py                 # Test script for workflow validation
└── .idea/                  # IDE configuration (PyCharm/IntelliJ)
```

## 📊 Sample Data

### Claim Files
The application includes 7 diverse sample claim files demonstrating different scenarios:

**john.json** - Pizza delivery collision
- Claim involving commercial use (food delivery)
- Rear-end collision with parked vehicle
- Tests commercial use exclusions and endorsements

**alice.json** - Single vehicle accident
- Personal use vehicle
- Highway accident during adverse weather
- Standard collision coverage scenario

**denied-claim.json** - Rideshare exclusion
- Uber driver accident during active ride
- Tests commercial use policy exclusions
- Expected outcome: Claim denial

**total-loss.json** - Vehicle totaled
- Repair cost exceeds 75% of ACV
- Tests total loss threshold logic
- Settlement: ACV minus deductible

**multi-vehicle.json** - Subrogation opportunity
- Not-at-fault collision with identified at-fault party
- Tests subrogation workflow
- Deductible waiver, recovery pursuit

**injury-claim.json** - Bodily injury with litigation risk
- Soft tissue injuries, attorney involvement
- Tests SIU referral for injury fraud patterns
- High medical costs + early legal representation

**vandalism.json** - Comprehensive coverage
- Vandalism damage (keying, broken windows)
- Tests police report requirement
- Comprehensive deductible applies

### Policy Declarations
Each claim includes corresponding policy declarations pages with:
- Coverage limits and deductibles
- Policy endorsements and exclusions
- Vehicle and policyholder information
- Premium and discount details

### Policy Knowledge Base
`data/policy_documents.md` contains:
- 5 sample policies (standard, premium, commercial, basic liability, high-risk)
- Coverage definitions and exclusions
- Fraud detection guidelines
- Subrogation policy
- Total loss valuation guidelines

## 🔧 Configuration

### Workflow Settings
- **Verbose Mode**: Enable detailed logging of processing steps
- **AI Integration**: Toggle between Gemini agentic mode and deterministic fallback
- **Timeout Settings**: Configure processing timeout limits
- **Policy Retrieval**: Vector store automatically initialized on startup

### API Configuration
- **Gemini 2.5 Flash**: Primary LLM powering FNOL, triage, fraud, and coverage agents
- **Policy Vector Store**: Automatic semantic retrieval from `data/policy_documents.md`
- **Environment Variables**: Secure storage via `.env` for API keys

### Multi-Page Applications
- **Main App** (`streamlit_app.py`): Single claim processing with agent toggles
- **Dashboard** (`dashboard.py`): Claims queue, batch processing, KPIs, adjuster overrides
- **Appraiser** (`appraiser.py`): Inspection workflow, photo upload, damage assessment

### REST API Endpoints
FastAPI server (`api.py`) provides:
- `POST /api/v1/claims/process`: Single claim processing
- `POST /api/v1/claims/batch`: Parallel batch processing
- `GET /api/v1/claims/{claim_number}`: Retrieve claim details
- `GET /api/v1/claims`: List all claims (paginated)
- `POST /api/v1/claims/{claim_number}/override`: Adjuster override (human-in-loop)
- `GET /api/v1/metrics`: KPI metrics (processing time, fraud rate, approval rate)
- `GET /health`: Health check endpoint

## 🧪 Development

### Running Tests
```bash
python demo.py  # Test workflow with sample claims
```

### Testing Policy Retrieval
```bash
python policy_retrieval.py  # Test vector store queries
```

### Code Style
```bash
black .
flake8 .
```

### Type Checking
```bash
mypy workflow.py
```

## 🚀 Deployment to Streamlit Cloud

### Prerequisites
1. GitHub account
2. Streamlit Cloud account (free at [streamlit.io/cloud](https://streamlit.io/cloud))
3. Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

### Deployment Steps

1. **Push code to GitHub** (ensure `.env` is NOT committed):
   ```bash
   git add .
   git commit -m "Add Ema Agentic Claims MVP"
   git push origin main
   ```

2. **Deploy to Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Select your GitHub repository: `deepakchoudhary-dc/Ema_Product_intern_task`
   - Set main file path: `work/streamlit_app.py`
   - Click "Advanced settings"

3. **Configure Secrets** (Critical for API key security):
   - In "Secrets" section, paste:
     ```toml
     GEMINI_API_KEY = "your-actual-gemini-api-key-here"
     ```
   - Click "Save"

4. **Deploy**:
   - Click "Deploy!"
   - Wait 2-3 minutes for deployment
   - Your app will be live at `https://your-app-name.streamlit.app`

### Deploy Additional Apps (Optional)

**Dashboard:**
- Main file: `work/dashboard.py`
- Same secrets configuration

**Appraiser Portal:**
- Main file: `work/appraiser.py`
- Same secrets configuration

### Security Checklist ✅
- ✅ `.env` file is in `.gitignore` and NOT committed
- ✅ API keys stored in Streamlit Cloud secrets (encrypted)
- ✅ No hardcoded keys in source code
- ✅ `.streamlit/secrets.toml` excluded from git
- ✅ Only `.streamlit/secrets.toml.example` committed (template)

### Verification
After deployment:
1. Open your Streamlit Cloud app
2. Check sidebar shows: "✅ Gemini key detected via Streamlit secrets"
3. Process a sample claim (e.g., `john.json`)
4. Verify all 4 agents produce output

### Troubleshooting Deployment

**Issue: "No module named 'X'"**
- Solution: Ensure all dependencies in `requirements.txt`

**Issue: "GEMINI_API_KEY not found"**
- Solution: Double-check secrets in Streamlit Cloud dashboard (exact format):
  ```toml
  GEMINI_API_KEY = "your-key-here"
  ```

**Issue: Policy retrieval warnings**
- Solution: Expected behavior - app uses fallback mode (keyword matching) without OpenAI embeddings
- No impact on functionality

## 📈 Workflow Architecture

The event-driven workflow now mirrors the carrier journey:

1. **Load Claim Info** → Parse & validate FNOL JSON (Pydantic safeguards)
2. **FNOL Intelligence Agent** → Gemini summarizes incident, impact, severity, and next actions
3. **Smart Triage Agent** → Determines priority, adjuster persona, and target SLA
4. **Fraud Radar Agent** → Produces SIU risk score + flags
5. **Policy Query Agent** → Generates retrieval queries (or uses fallback library text)
6. **Coverage Brain** → Crafts deductible + payout recommendation tied to policy section
7. **Decision Formatter** → Surfaces claim decision alongside agentic insights in UI + API

Each agent falls back to deterministic heuristics when Gemini is unavailable, ensuring the prototype always runs.

## 🔮 Future Enhancements

- **Batch Processing**: Handle multiple claims simultaneously
- **Advanced Analytics**: Claim pattern analysis and reporting
- **Integration APIs**: REST API for external system integration
- **Multi-language Support**: Internationalization capabilities
- **Advanced Visualizations**: Interactive charts and claim analytics
- **Adjuster Co-Pilot**: Surface recommended questions and negotiation levers during live calls
- **Automated Repair Partnering**: Trigger DRP shop selection and digital payments

## 🖼️ Presentation Deck

A concise 5-slide briefing that covers agentic opportunities, MVP scope, product story, and next steps is available at `docs/presentation.md`.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [LlamaIndex](https://www.llamaindex.ai/) workflow primitives
- Powered by [Gemini / Google AI Studio](https://ai.google.dev/) for agentic intelligence
- UI created with [Streamlit](https://streamlit.io/)
- Inspired by industry claim-automation playbooks

## 📞 Support

For questions, issues, or contributions:
- Create an issue on GitHub
- Check the documentation
- Review sample implementations

---

**🚗 Drive safe, claim smart!**
