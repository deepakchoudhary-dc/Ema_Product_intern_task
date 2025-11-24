# Slide 1 – Problem & Stakeholders
- Ema PM take-home: reimagine vehicle claims with autonomous, agentic AI.
- Legacy claim centers require heavy manual summarization, routing, and documentation.
- Stakeholders: claimants, intake specialists, adjusters, appraisers, SIU, and managers all touch the flow.
- Goal: compress time-to-settlement while improving fraud vigilance and customer transparency.

# Slide 2 – Agentic Opportunity Map
- FNOL Intelligence agent normalizes narratives, flags missing data, and sets severity.
- Smart Triage agent scores priority, recommends adjuster persona, and targets SLA commitments.
- Fraud Radar agent surfaces SIU risk scores and anomaly flags before payouts.
- Coverage Brain agent grounds recommendations in policy clauses, deductibles, and payout math.

# Slide 3 – MVP Definition & Rationale
1. FNOL Intelligence (must) – every downstream step needs clean intake data.
2. Smart Triage (must) – instantly valuable to claims managers via workload routing.
3. Fraud Radar (should) – lightweight SIU alerting with clear ROI.
4. Coverage Brain (must) – ties insights to settlement, proving business value fast.
- Excludes: batch automation, telematics ingestion, and legacy-system integrations (Phase 2).

# Slide 4 – Prototype Journey
- Streamlit UI simulates carrier console (upload JSON or select sample claim).
- Agents run sequentially: FNOL summary → triage plan → fraud insights → settlement output.
- Toggle Gemini 2.5 Flash for live reasoning or use deterministic fallbacks for demos.
- Verbose mode streams each workflow event for transparency and auditability.

# Slide 5 – Success Metrics & Next Steps
- Primary KPIs: FNOL handling time (-50%), adjuster assignment accuracy (+30%), SIU referral precision (+10%), cycle time (-25%).
- Immediate roadmap: plug into carrier systems via REST, add photo/appraisal ingestion, and expand fraud libraries.
- Ask: pilot with de-identified claims to benchmark savings and co-design deeper integrations.
