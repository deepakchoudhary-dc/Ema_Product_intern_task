import json
import asyncio
import os
import re
from typing import Dict, Any, Optional, List, Type
from pydantic import BaseModel, Field
from llama_index.core.workflow import (
    Event,
    StartEvent,
    StopEvent,
    Context,
    Workflow,
    step
)
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.vector_stores.types import MetadataFilters

try:
    import google.generativeai as genai
except ImportError:  # Library is optional until Gemini mode enabled
    genai = None

# Comprehensive Schemas
class ClaimInfo(BaseModel):
    """Extracted Insurance claim information."""
    claim_number: str
    policy_number: str
    claimant_name: str
    date_of_loss: str
    loss_description: str
    estimated_repair_cost: float
    vehicle_details: Optional[str] = None

class PolicyQueries(BaseModel):
    queries: List[str] = Field(
        default_factory=list,
        description="A list of query strings to retrieve relevant policy sections."
    )

class PolicyRecommendation(BaseModel):
    """Policy recommendation regarding a given claim."""
    policy_section: str = Field(..., description="The policy section or clause that applies.")
    recommendation_summary: str = Field(..., description="A concise summary of coverage determination.")
    deductible: Optional[float] = Field(None, description="The applicable deductible amount.")
    settlement_amount: Optional[float] = Field(None, description="Recommended settlement payout.")

class ClaimDecision(BaseModel):
    claim_number: str
    covered: bool
    deductible: float
    recommended_payout: float
    notes: Optional[str] = None

class FNOLSummary(BaseModel):
    incident_summary: str
    impact_assessment: str
    severity_level: str
    recommended_actions: List[str] = Field(default_factory=list)

class TriageDecision(BaseModel):
    priority: str
    assignment: str
    rationale: str
    target_sla_hours: int

class FraudSignal(BaseModel):
    risk_score: float = Field(ge=0, le=1)
    flags: List[str] = Field(default_factory=list)
    recommendation: str

# Enhanced Parsing Functions
def parse_claim(file_path: str) -> ClaimInfo:
    """Parse claim data from JSON file and validate with ClaimInfo schema"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # Convert legacy format to new format if needed
        if 'damage_amount' in data:
            data['estimated_repair_cost'] = data.pop('damage_amount')
        if 'policyholder_name' in data:
            data['claimant_name'] = data.pop('policyholder_name')
        if 'date_of_incident' in data:
            data['date_of_loss'] = data.pop('date_of_incident')
        if 'description' in data:
            data['loss_description'] = data.pop('description')
            
        return ClaimInfo.model_validate(data)
    except FileNotFoundError:
        raise FileNotFoundError(f"Claim file not found: {file_path}")
    except Exception as e:
        raise ValueError(f"Error parsing claim file {file_path}: {e}")

def get_declarations_docs(policy_retriever, policy_number: str, top_k: int = 1):
    """Get declarations documents for a specific policy number"""
    try:
        if hasattr(policy_retriever, 'retrieve'):
            # Use filters if available
            filters = MetadataFilters.from_dicts([
                {"key": "policy_number", "value": policy_number}
            ])
            docs = policy_retriever.retrieve(
                f"declarations page for {policy_number}",
                filters=filters
            )
            return docs[:top_k] if docs else []
        else:
            # Fallback for mock implementation
            return []
    except Exception as e:
        print(f"Warning: Could not retrieve declarations for {policy_number}: {e}")
        return []

# Event Classes
class ClaimInfoEvent(Event):
    claim_info: ClaimInfo

class PolicyQueryEvent(Event):
    queries: PolicyQueries

class PolicyMatchedEvent(Event):
    policy_text: str

class RecommendationEvent(Event):
    recommendation: PolicyRecommendation

class DecisionEvent(Event):
    decision: ClaimDecision

class LogEvent(Event):
    msg: str
    delta: bool = False

# Prompts
FNOL_SUMMARY_PROMPT = """You are assisting a claims intake specialist.
Summarize the First Notice of Loss (FNOL) using the following structure:
1. incident_summary
2. impact_assessment (vehicle + human impact)
3. severity_level (Low, Medium, High)
4. recommended_actions (list of next steps for the carrier)

Claim Data:
{claim_info}

Return valid JSON matching the FNOLSummary schema."""

TRIAGE_PROMPT = """You are a virtual claims routing manager.
Decide how to triage the claim using:
- priority (Immediate, High, Standard, Low)
- assignment (Specialty adjuster, Desk adjuster, Express lane, etc.)
- rationale (1-2 sentences)
- target_sla_hours (integer)

Input:
Claim Info: {claim_info}
FNOL Summary: {fnol_summary}

Return JSON for TriageDecision."""

FRAUD_ANALYSIS_PROMPT = """You are part of the Special Investigations Unit.
Rate the fraud risk between 0 and 1, list up to 3 flags, and give a recommendation.

Consider:
- Loss description
- Vehicle usage
- Estimated repair cost vs vehicle type

Claim Info: {claim_info}
Triage Decision: {triage}

Respond with JSON for FraudSignal."""

GENERATE_POLICY_QUERIES_PROMPT = """\
You are an assistant tasked with determining what insurance policy sections to consult for a given auto claim.

**Instructions:**
1. Review the claim data, including the type of loss, estimated repair cost, and policy number.
2. Identify what aspects of the policy we need:
   - Coverage conditions for the type of damage
   - Deductible application
   - Any special endorsements related to the incident
   - Exclusions that might apply
3. Produce 3-5 queries that can be used against a vector index of insurance policies to find relevant clauses.

Claim Data:
{claim_info}

Return a JSON object matching the PolicyQueries schema.
"""

POLICY_RECOMMENDATION_PROMPT = """\
Given the retrieved policy sections for this claim, determine:
- If the incident is covered under the policy
- The applicable deductible amount
- Recommended settlement amount (repair cost minus deductible if covered)
- Which specific policy section applies
- Any exclusions or special conditions

Claim Info:
{claim_info}

Policy Text:
{policy_text}

Return a JSON object matching PolicyRecommendation schema.
"""

# Gemini client wrapper
class GeminiStructuredClient:
    def __init__(self, model: str = "gemini-2.5-flash", api_key: Optional[str] = None, temperature: float = 0.2):
        self.available = bool(api_key and genai)
        self._model_name = model
        self._temperature = temperature
        self._client = None
        if self.available:
            genai.configure(api_key=api_key)
            self._client = genai.GenerativeModel(
                model_name=model,
                generation_config={"temperature": temperature, "response_mime_type": "application/json"}
            )

    async def structured_predict(self, schema: Type[BaseModel], prompt_template: str, **kwargs) -> BaseModel:
        if not self.available or not self._client:
            raise RuntimeError("Gemini client not configured")
        prompt = prompt_template.format(**kwargs)

        def _call():
            return self._client.generate_content(prompt)

        response = await asyncio.to_thread(_call)
        text = self._extract_text(response)
        json_payload = self._extract_json_block(text)
        if json_payload is None:
            raise ValueError("Gemini response lacked JSON payload")
        return schema.model_validate_json(json_payload)

    @staticmethod
    def _extract_text(response: Any) -> str:
        if hasattr(response, "text") and response.text:
            return response.text
        parts = []
        for candidate in getattr(response, "candidates", []) or []:
            for part in getattr(candidate, "content", getattr(candidate, "parts", [])):
                text = getattr(part, "text", None)
                if text:
                    parts.append(text)
        return "\n".join(parts)

    @staticmethod
    def _extract_json_block(text: str) -> Optional[str]:
        if not text:
            return None
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = "\n".join(cleaned.split("\n")[1:-1])
        match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", cleaned)
        if not match:
            return None
        return match.group(1)


# Advanced Auto Insurance Workflow
class AutoInsuranceWorkflow(Workflow):
    def __init__(
        self, 
        policy_retriever: Optional[BaseRetriever] = None, 
        llm: Optional[GeminiStructuredClient] = None, 
        verbose: bool = False,
        timeout: Optional[float] = None,
        **kwargs
    ) -> None:
        super().__init__(verbose=verbose, timeout=timeout, **kwargs)
        
        # Use provided retriever or create default policy retriever
        if policy_retriever is None:
            try:
                from policy_retrieval import create_policy_retriever
                self.policy_retriever = create_policy_retriever()
                if self._verbose:
                    print("✅ Initialized policy retriever with vector store")
            except Exception as e:
                print(f"Warning: Could not initialize policy retriever: {e}")
                self.policy_retriever = None
        else:
            self.policy_retriever = policy_retriever
        
        self.llm = llm or self._init_gemini_client()
        self._verbose = verbose

    def _init_gemini_client(self) -> Optional[GeminiStructuredClient]:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        try:
            client = GeminiStructuredClient(api_key=api_key)
            return client if client.available else None
        except Exception as exc:
            print(f"Warning: Could not initialize Gemini client: {exc}")
            return None

    @step
    async def load_claim_info(self, ctx: Context, ev: StartEvent) -> ClaimInfoEvent:
        """Load and validate claim information from JSON file"""
        if self._verbose:
            ctx.write_event_to_stream(LogEvent(msg=">> Loading Claim Info"))
        
        claim_info = parse_claim(ev.claim_json_path)
        await ctx.set("claim_info", claim_info)
        
        if self._verbose:
            ctx.write_event_to_stream(LogEvent(msg=f">> Loaded claim: {claim_info.claim_number}"))

        fnol_summary = await self._record_fnol_summary(ctx, claim_info)
        await ctx.set("fnol_summary", fnol_summary)

        triage = await self._record_triage(ctx, claim_info, fnol_summary)
        await ctx.set("triage_decision", triage)

        await self._record_fraud_signal(ctx, claim_info, triage)
        
        return ClaimInfoEvent(claim_info=claim_info)

    @step
    async def generate_policy_queries(self, ctx: Context, ev: ClaimInfoEvent) -> PolicyQueryEvent:
        """Generate queries to retrieve relevant policy sections"""
        if self._verbose:
            ctx.write_event_to_stream(LogEvent(msg=">> Generating Policy Queries"))
        
        queries = await self._maybe_llm_predict(
            PolicyQueries,
            GENERATE_POLICY_QUERIES_PROMPT,
            fallback=self._generate_fallback_queries,
            ctx=ctx,
            fallback_kwargs={"claim_info": ev.claim_info},
            claim_info=ev.claim_info.model_dump_json(),
        )
        
        if self._verbose:
            ctx.write_event_to_stream(LogEvent(msg=f">> Generated {len(queries.queries)} queries"))
        
        return PolicyQueryEvent(queries=queries)

    def _generate_fallback_queries(self, claim_info: ClaimInfo) -> PolicyQueries:
        """Generate basic queries when LLM is not available"""
        queries = [
            f"Coverage conditions for {claim_info.policy_number}",
            f"Deductible application for collision damage",
            f"Settlement amount calculation for vehicle damage",
            f"Exclusions for {claim_info.loss_description.lower()}",
            f"Policy limits and coverage details"
        ]
        return PolicyQueries(queries=queries)

    @step
    async def retrieve_policy_text(self, ctx: Context, ev: PolicyQueryEvent) -> PolicyMatchedEvent:
        """Retrieve relevant policy sections based on queries"""
        if self._verbose:
            ctx.write_event_to_stream(LogEvent(msg=">> Retrieving policy sections"))

        claim_info = await ctx.get("claim_info")
        combined_docs = {}
        
        if self.policy_retriever:
            try:
                # Check if using PolicyRetriever (has retrieve method) or LlamaIndex BaseRetriever
                if hasattr(self.policy_retriever, 'retrieve') and not hasattr(self.policy_retriever, 'aretrieve'):
                    # Custom PolicyRetriever with vector store
                    for query in ev.queries.queries:
                        if self._verbose:
                            ctx.write_event_to_stream(LogEvent(msg=f">> Query: {query}"))
                        
                        # Retrieve policy text directly
                        policy_text_chunk = self.policy_retriever.retrieve(query, top_k=3)
                        
                        # Create pseudo-document for compatibility
                        combined_docs[query] = type('Doc', (), {
                            'id_': query,
                            'get_content': lambda self=policy_text_chunk: self
                        })()
                else:
                    # Standard LlamaIndex retriever
                    for query in ev.queries.queries:
                        if self._verbose:
                            ctx.write_event_to_stream(LogEvent(msg=f">> Query: {query}"))
                        
                        # Fetch policy text
                        if hasattr(self.policy_retriever, 'aretrieve'):
                            docs = await self.policy_retriever.aretrieve(query)
                        else:
                            docs = self.policy_retriever.retrieve(query)
                        
                        for d in docs:
                            combined_docs[d.id_] = d

                    # Try to fetch declarations page
                    declarations_docs = get_declarations_docs(
                        self.policy_retriever, 
                        claim_info.policy_number
                    )
                    for d_doc in declarations_docs:
                        combined_docs[d_doc.id_] = d_doc
                    
            except Exception as e:
                if self._verbose:
                    ctx.write_event_to_stream(LogEvent(msg=f">> Policy retrieval failed: {e}"))
        
        if combined_docs:
            # Handle both custom PolicyRetriever docs and LlamaIndex docs
            policy_chunks = []
            for doc in combined_docs.values():
                if hasattr(doc, 'get_content'):
                    content = doc.get_content()
                    # If get_content returns a string, use it; otherwise get text attribute
                    policy_chunks.append(content if isinstance(content, str) else str(content))
                elif hasattr(doc, 'text'):
                    policy_chunks.append(doc.text)
                else:
                    policy_chunks.append(str(doc))
            policy_text = "\n\n".join(policy_chunks)
        else:
            # Fallback policy text for demo purposes
            policy_text = self._get_fallback_policy_text(claim_info)
        
        await ctx.set("policy_text", policy_text)
        
        if self._verbose:
            ctx.write_event_to_stream(LogEvent(msg=f">> Retrieved {len(policy_text)} characters of policy text"))
        
        return PolicyMatchedEvent(policy_text=policy_text)

    def _get_fallback_policy_text(self, claim_info: ClaimInfo) -> str:
        """Generate fallback policy text for demo purposes"""
        return f"""
CALIFORNIA PERSONAL AUTO POLICY
Policy Number: {claim_info.policy_number}

PART D - COVERAGE FOR DAMAGE TO YOUR AUTO
COLLISION COVERAGE
We will pay for direct and accidental loss to your covered auto caused by collision with another object or by upset of your covered auto.

DEDUCTIBLE
For each loss, our limit of liability will be reduced by the applicable deductible amount shown in the Declarations.
Standard collision deductible: $500
Comprehensive deductible: $250

LIMITS OF LIABILITY
Our limit of liability for loss will be the lesser of:
1. The actual cash value of the stolen or damaged property; or
2. The amount necessary to repair or replace the property.

EXCLUSIONS
We do not provide coverage for:
1. Loss to your covered auto which occurs while it is used to carry persons or property for compensation
2. Loss due to wear and tear, freezing, mechanical breakdown
3. Loss to equipment designed for the reproduction of sound
        """

    @step
    async def generate_recommendation(self, ctx: Context, ev: PolicyMatchedEvent) -> RecommendationEvent:
        """Generate policy recommendation based on claim and policy text"""
        if self._verbose:
            ctx.write_event_to_stream(LogEvent(msg=">> Generating Policy Recommendation"))
        
        claim_info = await ctx.get("claim_info")
        
        recommendation = await self._maybe_llm_predict(
            PolicyRecommendation,
            POLICY_RECOMMENDATION_PROMPT,
            fallback=self._generate_fallback_recommendation,
            ctx=ctx,
            fallback_kwargs={"claim_info": claim_info, "policy_text": ev.policy_text},
            claim_info=claim_info.model_dump_json(),
            policy_text=ev.policy_text,
        )
        recommendation.recommendation_summary = self._sanitize_text(recommendation.recommendation_summary)
        
        if self._verbose:
            ctx.write_event_to_stream(LogEvent(msg=f">> Recommendation: {recommendation.model_dump_json()}"))
        
        return RecommendationEvent(recommendation=recommendation)

    def _generate_fallback_recommendation(self, claim_info: ClaimInfo, policy_text: str) -> PolicyRecommendation:
        """Generate fallback recommendation using rule-based logic"""
        # Simple rule-based logic for demo
        covered = claim_info.estimated_repair_cost < 15000  # Coverage limit
        deductible = 500.0  # Standard deductible
        settlement_amount = max(0, claim_info.estimated_repair_cost - deductible) if covered else 0.0
        
        summary = (
            f"Claim {claim_info.claim_number} on policy {claim_info.policy_number} for ${claim_info.estimated_repair_cost:.2f}"
        )
        if covered:
            summary += (
                f" is covered under Part D – Collision. Recommend paying ${settlement_amount:.2f}"
                f" after the ${deductible:.2f} deductible."
            )
        else:
            summary += " exceeds collision limits; recommend denying coverage."
        summary = self._sanitize_text(summary)
        
        return PolicyRecommendation(
            policy_section="PART D - COLLISION COVERAGE",
            recommendation_summary=summary,
            deductible=deductible,
            settlement_amount=settlement_amount
        )

    @step
    async def finalize_decision(self, ctx: Context, ev: RecommendationEvent) -> DecisionEvent:
        """Finalize the claim decision based on policy recommendation"""
        if self._verbose:
            ctx.write_event_to_stream(LogEvent(msg=">> Finalizing Decision"))
        
        claim_info = await ctx.get("claim_info")
        rec = ev.recommendation
        fnol_summary = await self._safe_ctx_get(ctx, "fnol_summary")
        triage = await self._safe_ctx_get(ctx, "triage_decision")
        fraud_signal = await self._safe_ctx_get(ctx, "fraud_signal")
        
        covered = (
            (
                "covered" in rec.recommendation_summary.lower()
                and "not covered" not in rec.recommendation_summary.lower()
            )
            or (rec.settlement_amount is not None and rec.settlement_amount > 0)
        )
        
        deductible = rec.deductible if rec.deductible is not None else 0.0
        recommended_payout = rec.settlement_amount if rec.settlement_amount else 0.0

        notes_lines = []
        if rec.policy_section:
            notes_lines.append(f"Policy {claim_info.policy_number} · {rec.policy_section}")
        if fnol_summary:
            notes_lines.append(
                f"FNOL severity {fnol_summary.severity_level}: {fnol_summary.incident_summary}"
            )
        if triage:
            notes_lines.append(
                f"Triage ⇒ {triage.priority} priority · {triage.assignment} (SLA {triage.target_sla_hours}h)"
            )
        if fraud_signal:
            risk_pct = fraud_signal.risk_score * 100
            notes_lines.append(f"Fraud risk {risk_pct:.0f}% ({fraud_signal.recommendation})")
        notes_lines.append(f"Settlement rationale: {rec.recommendation_summary}")
        notes = "\n".join(notes_lines)
        
        decision = ClaimDecision(
            claim_number=claim_info.claim_number,
            covered=covered,
            deductible=deductible,
            recommended_payout=recommended_payout,
            notes=notes
        )
        
        if self._verbose:
            ctx.write_event_to_stream(LogEvent(msg=f">> Final Decision: Covered={covered}, Payout=${recommended_payout:.2f}"))
        
        return DecisionEvent(decision=decision)

    @step
    async def output_result(self, ctx: Context, ev: DecisionEvent) -> StopEvent:
        """Output the final decision result"""
        if self._verbose:
            ctx.write_event_to_stream(LogEvent(msg=f">> Decision: {ev.decision.model_dump_json()}"))
        fnol_summary = await self._safe_ctx_get(ctx, "fnol_summary")
        triage = await self._safe_ctx_get(ctx, "triage_decision")
        fraud_signal = await self._safe_ctx_get(ctx, "fraud_signal")
        return StopEvent(
            result={
                "decision": ev.decision,
                "fnol_summary": fnol_summary,
                "triage": triage,
                "fraud_signal": fraud_signal,
            }
        )

    # Compatibility method for the Streamlit app
    async def run(self, claim_json_path: str) -> Dict[str, Any]:
        """Run the workflow with a claim JSON file path"""
        try:
            handler = super().run(claim_json_path=claim_json_path)
            result = await handler
            return result
        except Exception as e:
            if self._verbose:
                print(f"Workflow error: {e}")
            raise e

    async def _maybe_llm_predict(
        self,
        schema: Type[BaseModel],
        prompt_template: str,
        *,
        fallback,
        ctx: Context,
        fallback_kwargs: Optional[Dict[str, Any]] = None,
        **prompt_kwargs,
    ) -> BaseModel:
        if self.llm and self.llm.available:
            try:
                return await self.llm.structured_predict(schema, prompt_template, **prompt_kwargs)
            except Exception as exc:
                if self._verbose:
                    ctx.write_event_to_stream(LogEvent(msg=f">> Gemini call failed, using fallback: {exc}"))
        fallback_kwargs = fallback_kwargs or {}
        return fallback(**fallback_kwargs)

    def _sanitize_text(self, text: Optional[str]) -> str:
        if not text:
            return ""
        squashed = re.sub(r"\s+", " ", text)
        squashed = squashed.replace(" ,", ",").replace(" .", ".")
        return squashed.strip()

    async def _safe_ctx_get(self, ctx: Context, key: str) -> Optional[Any]:
        try:
            return await ctx.get(key)
        except KeyError:
            return None

    def _generate_fallback_fnol_summary(self, claim_info: ClaimInfo) -> FNOLSummary:
        return FNOLSummary(
            incident_summary=f"Collision reported for {claim_info.claimant_name} on {claim_info.date_of_loss}.",
            impact_assessment=f"Vehicle damage estimated at ${claim_info.estimated_repair_cost:,.2f} with description: {claim_info.loss_description}.",
            severity_level="High" if claim_info.estimated_repair_cost > 10000 else "Medium",
            recommended_actions=[
                "Verify policy coverage and endorsements",
                "Collect repair shop estimate",
                "Schedule adjuster inspection" if claim_info.estimated_repair_cost > 5000 else "Offer express settlement",
            ],
        )

    def _generate_fallback_triage(self, claim_info: ClaimInfo, **_) -> TriageDecision:
        high_value = claim_info.estimated_repair_cost >= 10000
        priority = "Immediate" if high_value else "Standard"
        assignment = "Field adjuster" if high_value else "Desk adjuster"
        sla = 8 if high_value else 24
        rationale = (
            "High severity impact; route to senior field adjuster for on-site estimate."
            if high_value
            else "Standard collision claim with moderate damage; handle via desk team."
        )
        return TriageDecision(priority=priority, assignment=assignment, rationale=rationale, target_sla_hours=sla)

    def _generate_fallback_fraud_signal(self, claim_info: ClaimInfo, **_) -> FraudSignal:
        risk = 0.2
        flags = []
        if "delivery" in claim_info.loss_description.lower():
            risk += 0.2
            flags.append("Commercial use disclosed")
        if claim_info.estimated_repair_cost > 15000:
            risk += 0.2
            flags.append("High repair estimate vs. vehicle value")
        recommendation = "No SIU referral" if risk < 0.5 else "Escalate for SIU desk review"
        return FraudSignal(risk_score=min(risk, 1.0), flags=flags, recommendation=recommendation)

    async def _record_fnol_summary(self, ctx: Context, claim_info: ClaimInfo) -> FNOLSummary:
        if self._verbose:
            ctx.write_event_to_stream(LogEvent(msg=">> Summarizing FNOL"))
        summary = await self._maybe_llm_predict(
            FNOLSummary,
            FNOL_SUMMARY_PROMPT,
            fallback=self._generate_fallback_fnol_summary,
            ctx=ctx,
            fallback_kwargs={"claim_info": claim_info},
            claim_info=claim_info.model_dump_json(),
        )
        return summary

    async def _record_triage(self, ctx: Context, claim_info: ClaimInfo, fnol_summary: FNOLSummary) -> TriageDecision:
        if self._verbose:
            ctx.write_event_to_stream(LogEvent(msg=">> Computing Triage"))
        triage = await self._maybe_llm_predict(
            TriageDecision,
            TRIAGE_PROMPT,
            fallback=self._generate_fallback_triage,
            ctx=ctx,
            fallback_kwargs={"claim_info": claim_info},
            claim_info=claim_info.model_dump_json(),
            fnol_summary=fnol_summary.model_dump_json(),
        )
        return triage

    async def _record_fraud_signal(self, ctx: Context, claim_info: ClaimInfo, triage: TriageDecision) -> None:
        if self._verbose:
            ctx.write_event_to_stream(LogEvent(msg=">> Running Fraud Scan"))
        fraud_signal = await self._maybe_llm_predict(
            FraudSignal,
            FRAUD_ANALYSIS_PROMPT,
            fallback=self._generate_fallback_fraud_signal,
            ctx=ctx,
            fallback_kwargs={"claim_info": claim_info},
            claim_info=claim_info.model_dump_json(),
            triage=triage.model_dump_json(),
        )
        await ctx.set("fraud_signal", fraud_signal)