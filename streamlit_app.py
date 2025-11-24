# Ema Agentic Claims MVP - Updated 2025-11-25
import streamlit as st
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from workflow import AutoInsuranceWorkflow, GeminiStructuredClient

load_dotenv()

st.set_page_config(
    page_title="Auto Insurance Claim Processor",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🚗 Auto Insurance Claim Processor")
st.markdown("### AI-Powered Claim Analysis & Settlement Recommendations")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

SAMPLE_FILES = [
    "john.json",
    "alice.json",
    "denied-claim.json",
    "total-loss.json",
    "multi-vehicle.json",
    "injury-claim.json",
    "vandalism.json"
]

# Sidebar Configuration
st.sidebar.header("⚙️ Configuration")

# API Key Configuration
def _ensure_gemini_key():
    env_key = os.environ.get("GEMINI_API_KEY")
    if env_key:
        return env_key, "environment/.env"
    secret_key = st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else None
    if secret_key:
        os.environ["GEMINI_API_KEY"] = secret_key
        return secret_key, "Streamlit secrets"
    return None, None


preconfigured_key, key_source = _ensure_gemini_key()

use_gemini = st.sidebar.checkbox(
    "Use Gemini Agentic AI",
    value=bool(preconfigured_key),
    help="Toggle to enable Gemini 2.5 Flash powered agents"
)

if use_gemini:
    preconfigured_key, key_source = _ensure_gemini_key()
    if preconfigured_key:
        st.sidebar.success(f"✅ Gemini key detected via {key_source}")
    else:
        gemini_api_key = st.sidebar.text_input(
            "Gemini API Key (Google AI Studio)",
            type="password",
            help="Enter your Gemini 2.5 Flash API key"
        )
        if gemini_api_key:
            os.environ["GEMINI_API_KEY"] = gemini_api_key
            st.sidebar.success("✅ Gemini key stored for this session")
        else:
            st.sidebar.warning("Gemini key required for agentic mode")
else:
    st.sidebar.info("Using deterministic fallback mode (no live Gemini calls)")

# Workflow Configuration
verbose_mode = st.sidebar.checkbox(
    "Verbose Mode",
    value=False,
    help="Show detailed processing steps"
)

def initialize_workflow(use_ai: bool, verbose: bool):
    llm_client = None
    if use_ai and os.environ.get("GEMINI_API_KEY"):
        try:
            llm_client = GeminiStructuredClient(api_key=os.environ["GEMINI_API_KEY"])
            if llm_client.available:
                st.sidebar.success("✅ Gemini ready")
            else:
                st.sidebar.warning("⚠️ Gemini SDK unavailable; using deterministic mode")
        except Exception as exc:
            st.sidebar.error(f"❌ Gemini initialization failed: {exc}")
            llm_client = None
    elif use_ai:
        st.sidebar.info("ℹ️ Provide a Gemini API key to enable live agents.")

    return AutoInsuranceWorkflow(
        policy_retriever=None,
        llm=llm_client if llm_client and llm_client.available else None,
        verbose=verbose,
        timeout=None,
    )

workflow = initialize_workflow(use_gemini, verbose_mode)

# Main Interface
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📄 Claim Processing")
    
    # File upload option
    uploaded_file = st.file_uploader(
        "Upload Claim JSON File",
        type=['json'],
        help="Upload a JSON file containing claim information"
    )
    
    # Or select from existing files
    claim_file_name = st.selectbox(
        "Or Select Existing Claim File",
        SAMPLE_FILES,
        help="Choose from sample claim files"
    )
    
    # Process button
    if st.button("🔍 Process Claim", type="primary"):
        try:
            # Determine which file to process
            if uploaded_file is not None:
                # Save uploaded file temporarily
                temp_path = DATA_DIR / f"temp_{uploaded_file.name}"
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                file_to_process = str(temp_path)
            else:
                file_to_process = str(DATA_DIR / claim_file_name)
            
            # Show processing status
            with st.spinner("Processing claim..."):
                
                # Create a container for verbose output
                if verbose_mode:
                    verbose_container = st.expander("🔍 Processing Details", expanded=True)
                    with verbose_container:
                        progress_placeholder = st.empty()
                
                # Run Workflow
                async def run_workflow():
                    return await workflow.run(claim_json_path=file_to_process)

                result_payload = asyncio.run(run_workflow())
                decision = result_payload["decision"]
            
            # Display Results
            st.success("✅ Claim processed successfully!")
            
            # Clean up temp file
            if uploaded_file is not None:
                try:
                    Path(file_to_process).unlink(missing_ok=True)
                except Exception:
                    pass

        except FileNotFoundError:
            st.error(f"❌ Error: Claim file '{file_to_process}' not found.")
        except Exception as e:
            st.error(f"❌ An error occurred: {e}")
            decision = None

with col2:
    st.subheader("📊 System Status")
    
    # System status indicators
    ai_connected = workflow.llm is not None and getattr(workflow.llm, "available", False)
    ai_status = "🟢 Gemini Agents" if ai_connected else ("🟡 Rule-Based" if use_gemini else "🔵 Deterministic")
    st.write(f"**Status:** {ai_status}")
    
    cloud_status = "🟢 Enabled" if ai_connected else "🔴 Off"
    st.write(f"**Gemini Connectivity:** {cloud_status}")
    
    st.write(f"**Verbose:** {'🟢 On' if verbose_mode else '🔴 Off'}")

# Display Decision Results
if 'decision' in locals() and decision:
    st.markdown("---")
    st.subheader("📋 Claim Decision")
    
    # Create result columns
    result_col1, result_col2, result_col3 = st.columns(3)
    
    with result_col1:
        st.metric(
            label="Coverage Status",
            value="COVERED" if decision.covered else "NOT COVERED",
            delta="Approved" if decision.covered else "Denied"
        )
    
    with result_col2:
        st.metric(
            label="Deductible",
            value=f"${decision.deductible:.2f}"
        )
    
    with result_col3:
        st.metric(
            label="Recommended Payout",
            value=f"${decision.recommended_payout:.2f}",
            delta=f"${decision.recommended_payout:.2f}" if decision.covered else "No payout"
        )
    
    # Detailed information
    st.subheader("📝 Details")
    
    details_col1, details_col2 = st.columns(2)
    
    with details_col1:
        st.write(f"**Claim Number:** {decision.claim_number}")
        st.write(f"**Coverage Decision:** {'✅ Covered' if decision.covered else '❌ Not Covered'}")
    
    with details_col2:
        st.write(f"**Deductible Amount:** ${decision.deductible:.2f}")
        st.write(f"**Settlement Amount:** ${decision.recommended_payout:.2f}")
    
    if decision.notes:
        st.subheader("💬 Analysis Notes")
        st.info(decision.notes)

    fnol_summary = result_payload.get("fnol_summary") if 'result_payload' in locals() else None
    triage = result_payload.get("triage") if 'result_payload' in locals() else None
    fraud_signal = result_payload.get("fraud_signal") if 'result_payload' in locals() else None

    if fnol_summary:
        st.subheader("🧠 FNOL Intelligence")
        st.write(f"**Incident Summary:** {fnol_summary.incident_summary}")
        st.write(f"**Impact:** {fnol_summary.impact_assessment}")
        st.write(f"**Severity Level:** {fnol_summary.severity_level}")
        if fnol_summary.recommended_actions:
            st.write("**Recommended Actions:**")
            st.markdown("\n".join([f"- {action}" for action in fnol_summary.recommended_actions]))

    if triage:
        st.subheader("🚦 Triage & Assignment")
        st.write(f"**Priority:** {triage.priority}")
        st.write(f"**Assignment:** {triage.assignment}")
        st.write(f"**SLA Target:** {triage.target_sla_hours} hours")
        st.info(triage.rationale)

    if fraud_signal:
        st.subheader("🕵️ Fraud Insights")
        st.metric("Fraud Risk", f"{fraud_signal.risk_score*100:.0f}%")
        if fraud_signal.flags:
            st.write("**Flags:**")
            st.markdown("\n".join([f"- {flag}" for flag in fraud_signal.flags]))
        st.warning(fraud_signal.recommendation)

# Instructions and Information
st.sidebar.markdown("---")
st.sidebar.header("📖 Instructions")
st.sidebar.markdown("""
### Quick Start
1. Pick a sample claim or upload a JSON FNOL file
2. Toggle **Gemini Agentic AI** to enable live reasoning
3. Click **Process Claim** to see FNOL → Triage → Settlement

### Agentic Workflow
- **FNOL Intelligence**: Summarizes intake details & severity
- **Smart Triage**: Assigns adjusters + SLA targets
- **Fraud Radar**: Flags anomalies for SIU review
- **Coverage Brain**: Aligns policy clauses & payout

### Sample Claim Skeleton
```json
{
    "claim_number": "CLAIM-001",
    "policy_number": "POLICY-123",
    "claimant_name": "John Doe",
    "date_of_loss": "2025-06-20",
    "loss_description": "Vehicle damage",
    "estimated_repair_cost": 5000,
    "vehicle_details": "2022 Honda Civic"
}
```
""")

st.sidebar.markdown("---")
st.sidebar.markdown("**Powered by Gemini & LlamaIndex**")
