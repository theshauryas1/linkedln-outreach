"""
Company Domain & Industry Research Engine for LinkedIn Outreach.
Researches what target companies actually do (Healthcare, Logistics, Infra, Fintech, Transport, etc.)
and identifies the exact applied AI engineering angle for tailored message personalization.
Caches results to ./data/company_cache.json so lookups are fast and non-redundant.
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from openai import OpenAI

from .config import LOCAL_DATA_DIR

logger = logging.getLogger("outreach.company_researcher")

CACHE_FILE = LOCAL_DATA_DIR / "company_cache.json"

from dotenv import load_dotenv

load_dotenv()
DEFAULT_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL_ID = "nvidia/nemotron-3-ultra-550b-a55b"

# Pre-defined industry angles to guide the AI
INDUSTRY_AI_ANGLES = {
    "healthcare": "clinical data intelligence, HIPAA-compliant patient workflow automation, and medical agent tooling",
    "transportation": "route optimization, fleet dispatch automation, and autonomous logistics coordination",
    "logistics": "supply chain resilience, warehouse routing agents, and real-time shipment intelligence",
    "fintech": "financial document reasoning, fraud prevention workflows, and automated compliance auditing",
    "cloud_infra": "scalable agent infrastructure, developer platform tooling, and low-latency LLM orchestration",
    "manufacturing": "predictive maintenance systems, supply chain automation, and industrial computer vision",
    "ecommerce": "conversion intelligence, automated catalog enrichment, and personalized recommendation agents",
    "general_tech": "applied agent workflows, reliable tool-calling systems, and AI automation pipelines"
}

class CompanyResearcher:
    """
    Identifies what a company does and determines the specific applied AI angle
    to personalize outreach messages.
    """

    def __init__(self):
        self.client = OpenAI(
            base_url=NIM_BASE_URL,
            api_key=os.getenv("NVIDIA_API_KEY", DEFAULT_API_KEY)
        )
        self.cache: Dict[str, Dict[str, Any]] = self._load_cache()

    def _load_cache(self) -> Dict[str, Dict[str, Any]]:
        """Loads cached company profiles from disk."""
        if CACHE_FILE.exists():
            try:
                return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning(f"Failed to read company cache: {e}")
        return {}

    def _save_cache(self):
        """Saves cached company profiles."""
        try:
            CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            CACHE_FILE.write_text(json.dumps(self.cache, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to write company cache: {e}")

    def research_company(
        self,
        company_name: str,
        headline_hint: str = "",
        title_hint: str = "",
    ) -> Dict[str, Any]:
        """
        Analyzes a company to extract:
        - industry (e.g. Healthcare, Transport, Cloud Infra, Fintech)
        - core_business (1-sentence summary of what they do)
        - ai_angle (specific angle for how an AI engineer can contribute)
        """
        clean_name = (company_name or "").strip()
        if not clean_name or clean_name.lower() in ("your company", "stealth", "self-employed", "freelance", ""):
            return {
                "company_name": clean_name or "your team",
                "industry": "general_tech",
                "core_business": "technology and software engineering",
                "ai_angle": INDUSTRY_AI_ANGLES["general_tech"],
            }

        cache_key = clean_name.lower()
        if cache_key in self.cache:
            logger.info(f"Using cached research for company: {clean_name}")
            return self.cache[cache_key]

        logger.info(f"Researching company domain for: {clean_name} (hints: {headline_hint})")

        prompt = f"""You are a senior tech research analyst. Analyze this company:
Company Name: "{clean_name}"
Employee Context / Headline: "{headline_hint}"
Job Title: "{title_hint}"

Determine:
1. What industry does this company operate in? (e.g. Healthcare/Medical, Transport/Logistics, Cloud/DevOps, Fintech, CleanTech, E-commerce, Gaming, CyberSecurity, etc.)
2. What is their core business or product? (1 short sentence)
3. How would an applied AI Engineer (specializing in autonomous agents, LLM orchestration, and workflow automation) add value to their specific business?

Return valid JSON only in this exact format:
{{
  "industry": "short industry category",
  "core_business": "1 clear sentence of what the company builds or does",
  "ai_angle": "1 short phrase describing applied AI / agent workflows relevant to their domain"
}}
"""
        try:
            resp = self.client.chat.completions.create(
                model=MODEL_ID,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=300,
                timeout=15,
            )
            raw = resp.choices[0].message.content or ""
            # Extract JSON
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                result = {
                    "company_name": clean_name,
                    "industry": data.get("industry", "general_tech"),
                    "core_business": data.get("core_business", "technology solutions"),
                    "ai_angle": data.get("ai_angle", INDUSTRY_AI_ANGLES["general_tech"]),
                }
                self.cache[cache_key] = result
                self._save_cache()
                return result
        except Exception as e:
            logger.warning(f"Error researching company {clean_name} with Nemotron: {e}")

        # Fallback heuristic based on keywords
        name_lower = f"{clean_name} {headline_hint}".lower()
        detected_industry = "general_tech"
        if any(w in name_lower for w in ["health", "medical", "clinic", "pharma", "bio", "therapeutics", "care"]):
            detected_industry = "healthcare"
        elif any(w in name_lower for w in ["transport", "mobility", "fleet", "transit", "aviation", "ride"]):
            detected_industry = "transportation"
        elif any(w in name_lower for w in ["logistics", "freight", "cargo", "warehouse", "supply chain"]):
            detected_industry = "logistics"
        elif any(w in name_lower for w in ["fintech", "bank", "pay", "crypto", "trading", "capital", "invest"]):
            detected_industry = "fintech"
        elif any(w in name_lower for w in ["cloud", "infra", "devops", "kubernetes", "network", "server"]):
            detected_industry = "cloud_infra"

        result = {
            "company_name": clean_name,
            "industry": detected_industry,
            "core_business": f"{clean_name} solutions in {detected_industry}",
            "ai_angle": INDUSTRY_AI_ANGLES.get(detected_industry, INDUSTRY_AI_ANGLES["general_tech"]),
        }
        self.cache[cache_key] = result
        self._save_cache()
        return result

company_researcher = CompanyResearcher()
