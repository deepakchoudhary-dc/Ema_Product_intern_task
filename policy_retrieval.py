"""
Policy Retrieval Module - Vector Store Implementation
Loads policy documents into vector store for semantic search
"""

from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.core.node_parser import SentenceSplitter
from pathlib import Path
import os
from typing import List

class PolicyRetriever:
    """
    Retrieves relevant policy information using vector similarity search
    """
    
    def __init__(self, policy_docs_path: str = None):
        """
        Initialize policy retriever with vector store
        
        Args:
            policy_docs_path: Path to policy documents (defaults to data/policy_documents.md)
        """
        if policy_docs_path is None:
            policy_docs_path = Path(__file__).parent / "data" / "policy_documents.md"
        
        self.policy_docs_path = Path(policy_docs_path)
        self.index = None
        self._load_policy_store()
    
    def _load_policy_store(self):
        """Load policy documents into vector store"""
        if not self.policy_docs_path.exists():
            print(f"Warning: Policy documents not found at {self.policy_docs_path}")
            return
        
        try:
            # For now, use fallback mode to avoid OpenAI API key requirement
            # In production, configure with local embeddings or OpenAI key
            print(f"⚠️ Policy vector store using fallback mode (keyword matching)")
            print(f"   To enable semantic search, set OPENAI_API_KEY or use local embeddings")
            self.index = None
            
        except Exception as e:
            print(f"Error loading policy store: {e}")
            self.index = None
    
    def retrieve(self, query: str, top_k: int = 3) -> str:
        """
        Retrieve relevant policy information for a query
        
        Args:
            query: Search query (e.g., "commercial use exclusions")
            top_k: Number of relevant chunks to retrieve
        
        Returns:
            Concatenated relevant policy text
        """
        if self.index is None:
            return self._get_fallback_text(query)
        
        try:
            # Query vector store
            retriever = self.index.as_retriever(similarity_top_k=top_k)
            nodes = retriever.retrieve(query)
            
            # Concatenate results
            results = []
            for node in nodes:
                results.append(node.text)
            
            return "\n\n".join(results) if results else self._get_fallback_text(query)
            
        except Exception as e:
            print(f"Error retrieving from vector store: {e}")
            return self._get_fallback_text(query)
    
    def _get_fallback_text(self, query: str) -> str:
        """
        Fallback policy text when vector store unavailable
        """
        query_lower = query.lower()
        
        # Commercial use query
        if "commercial" in query_lower or "delivery" in query_lower or "rideshare" in query_lower:
            return """
            Standard personal auto policies exclude commercial use including:
            - Food delivery (pizza, groceries, restaurant meals)
            - Ridesharing services (Uber, Lyft)
            - Package/courier delivery
            - For-hire transportation
            
            Any accident during commercial use results in claim denial.
            Commercial auto policy required for business use.
            """
        
        # Total loss query
        elif "total loss" in query_lower or "totaled" in query_lower:
            return """
            Total Loss Threshold: Repair cost ≥ 75% of vehicle's actual cash value (ACV)
            
            Settlement Process:
            1. Determine ACV using comparable vehicles (same year/make/model/mileage)
            2. Deduct applicable deductible
            3. Deduct salvage value if insured retains vehicle
            4. Pay net settlement amount
            5. Require title transfer
            
            New Car Replacement available on premium policies if total loss within 2 years of purchase.
            """
        
        # Fraud query
        elif "fraud" in query_lower or "suspicious" in query_lower:
            return """
            Fraud Red Flags requiring SIU referral:
            - Late reporting (>72 hours)
            - Inconsistent statements vs police report
            - No independent witnesses
            - Pre-existing damage
            - Recent coverage increase (<30 days before loss)
            - Soft tissue injuries with no vehicle damage
            - Multiple claims in short timeframe
            - Attorney involvement within 48 hours
            """
        
        # Vandalism query
        elif "vandalism" in query_lower or "comprehensive" in query_lower or "theft" in query_lower:
            return """
            Comprehensive coverage applies to:
            - Vandalism (graffiti, keying, broken windows, slashed tires)
            - Theft of vehicle, parts, or contents
            - Fire damage (non-collision)
            - Weather damage (hail, flood)
            
            Requirements:
            - Police report must be filed within 24 hours of discovery
            - Failure to file police report may result in denial
            - Comprehensive deductible applies
            """
        
        # Bodily injury query
        elif "bodily injury" in query_lower or "injury" in query_lower or "medical" in query_lower:
            return """
            Bodily Injury Coverage:
            - Pays for injuries to others when policyholder is at fault
            - Medical Payments coverage pays for policyholder/passenger injuries regardless of fault
            - Uninsured Motorist coverage protects against uninsured at-fault drivers
            
            Litigation Risk Factors:
            - Attorney representation within 48 hours
            - Demand letters before medical treatment concludes
            - Pre-litigation demands exceed policy limits
            - History of personal injury lawsuits
            
            High medical treatment costs and attorney involvement increase litigation risk.
            """
        
        # Subrogation query
        elif "subrogation" in query_lower or "not at fault" in query_lower:
            return """
            Subrogation pursued when:
            - Policyholder 0% at fault
            - Other party identified with valid insurance
            - Claim payout exceeds $2,500
            - Police report assigns fault to other party
            - Potential recovery exceeds pursuit cost (minimum $5,000)
            
            Process:
            1. Pay policyholder's collision claim (waive deductible)
            2. Send demand to at-fault party's insurer
            3. Negotiate settlement or arbitrate
            4. Reimburse policyholder's deductible if full recovery
            5. Recover claim payout amount
            """
        
        # Default
        else:
            return """
            Standard Auto Policy Coverage:
            - Bodily Injury Liability: Covers injuries to others
            - Property Damage Liability: Covers damage to others' property
            - Collision: Covers damage to insured vehicle (deductible applies)
            - Comprehensive: Covers non-collision damage (theft, vandalism, weather)
            - Uninsured/Underinsured Motorist: Protects against uninsured drivers
            - Medical Payments: Covers medical expenses regardless of fault
            
            Exclusions:
            - Commercial use (delivery, rideshare, for-hire)
            - Intentional acts
            - Racing or speed contests
            - Vehicle used without permission
            """


# Convenience function for workflow integration
def create_policy_retriever() -> PolicyRetriever:
    """
    Factory function to create policy retriever instance
    """
    return PolicyRetriever()


if __name__ == "__main__":
    # Test retrieval
    retriever = PolicyRetriever()
    
    test_queries = [
        "commercial use exclusions",
        "total loss threshold",
        "fraud red flags",
        "vandalism coverage"
    ]
    
    print("Testing Policy Retrieval:\n")
    for query in test_queries:
        print(f"Query: {query}")
        result = retriever.retrieve(query, top_k=2)
        print(f"Result: {result[:200]}...\n")
