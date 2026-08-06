import re
import os
from typing import List, Dict
from groq import Groq

class RAGDiagnosticEngine:
    """
    Takes retrieved log context, applies PII guardrails, and orchestrates 
    the LLM prompt for root-cause analysis.
    """
    def __init__(self, api_key: str = None):
        # Initialize Groq client (or fallback to environment variable)
        self.client = Groq(api_key=api_key or os.environ.get("GROQ_API_KEY"))
        self.model_name = "llama-3.3-70b-versatile" 

    def _apply_guardrails(self, text: str) -> str:
        """
        RESPONSIBLE AI GUARDRAIL: 
        Masks IP addresses and email addresses in the log text to prevent 
        sensitive data leakage to the LLM provider.
        """
        # Mask IP addresses (e.g., 10.11.10.1 -> [REDACTED_IP])
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        safe_text = re.sub(ip_pattern, '[REDACTED_IP]', text)
        
        # Mask Emails (e.g., user@company.com -> [REDACTED_EMAIL])
        email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        safe_text = re.sub(email_pattern, '[REDACTED_EMAIL]', safe_text)
        
        return safe_text

    def _build_prompt(self, user_query: str, retrieved_chunks: List[Dict]) -> str:
        """
        CONTEXT GROUNDING:
        Constructs a strict prompt forcing the LLM to rely ONLY on the provided logs.
        """
        # 1. Clean the retrieved text using our guardrails
        context_blocks = []
        for i, chunk in enumerate(retrieved_chunks):
            safe_chunk = self._apply_guardrails(chunk['text'])
            context_blocks.append(f"--- LOG SNIPPET {i+1} ---\n{safe_chunk}")
            
        combined_context = "\n\n".join(context_blocks)
        
        # 2. Build the final prompt string
        prompt = f"""You are a Senior Site Reliability Engineer (SRE) diagnosing a microservice failure.
        
Your task is to analyze the following sanitized server logs and answer the user's query.
If the answer is not contained in the logs, you must reply: "Insufficient log data to determine root cause." Do not guess.

USER QUERY: {user_query}

SYSTEM LOGS (CONTEXT):
{combined_context}

Provide your analysis in the following format:
1. Root Cause Summary (1-2 sentences)
2. Suspected Failing Service (e.g., nova.compute)
3. Recommended Fix
"""
        return prompt

    def generate_analysis(self, user_query: str, retrieved_chunks: List[Dict]) -> str:
        """
        Executes the final LLM call.
        """
        if not retrieved_chunks:
            return "No relevant logs found in the system for this query."
            
        final_prompt = self._build_prompt(user_query, retrieved_chunks)
        
        print("🧠 Sending grounded context to LLM...")
        
        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a precise, technical DevOps assistant."},
                {"role": "user", "content": final_prompt}
            ],
            model=self.model_name,
            temperature=0.1, # Low temperature to prevent creative hallucinations
        )
        
        return response.choices[0].message.content