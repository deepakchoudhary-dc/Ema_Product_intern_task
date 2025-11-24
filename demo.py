#!/usr/bin/env python3
"""
Demo script for testing the Auto Insurance Claim Processor workflow
"""

import asyncio
import os
from workflow import AutoInsuranceWorkflow, parse_claim

async def demo_workflow():
    """Run a demo of the workflow with sample data"""
    
    print("🚗 Auto Insurance Claim Processor Demo")
    print("=" * 50)
    
    # Initialize workflow (mock mode)
    workflow = AutoInsuranceWorkflow(
        policy_retriever=None,
        llm=None,
        verbose=True,
        timeout=None,
    )
    
    # Test cases
    test_cases = ["john.json", "alice.json"]
    
    for claim_file in test_cases:
        print(f"\n📄 Processing: {claim_file}")
        print("-" * 30)
        
        try:
            # Parse claim info first
            claim_info = parse_claim(f"data/{claim_file}")
            print(f"Claim Number: {claim_info.claim_number}")
            print(f"Claimant: {claim_info.claimant_name}")
            print(f"Estimated Cost: ${claim_info.estimated_repair_cost:,.2f}")
            
            # Run workflow
            result = await workflow.run(claim_json_path=f"data/{claim_file}")
            decision = result["decision"]
            
            # Display results
            print(f"\n✅ Results:")
            print(f"  Coverage: {'COVERED' if decision.covered else 'NOT COVERED'}")
            print(f"  Deductible: ${decision.deductible:,.2f}")
            print(f"  Payout: ${decision.recommended_payout:,.2f}")
            if decision.notes:
                print(f"  Notes: {decision.notes}")

            fnol_summary = result.get("fnol_summary")
            triage = result.get("triage")
            fraud_signal = result.get("fraud_signal")

            if fnol_summary:
                print("\n🧠 FNOL Intelligence")
                print(f"  Severity: {fnol_summary.severity_level}")
                print(f"  Summary: {fnol_summary.incident_summary}")
            if triage:
                print("\n🚦 Triage")
                print(f"  Priority: {triage.priority} | Assignment: {triage.assignment} | SLA: {triage.target_sla_hours}h")
            if fraud_signal:
                print("\n🕵️ Fraud Signal")
                print(f"  Risk Score: {fraud_signal.risk_score:.2f} | Recommendation: {fraud_signal.recommendation}")
                
        except Exception as e:
            print(f"❌ Error processing {claim_file}: {e}")
    
    print(f"\n🎉 Demo completed!")

if __name__ == "__main__":
    asyncio.run(demo_workflow())
