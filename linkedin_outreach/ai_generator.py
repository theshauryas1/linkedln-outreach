import os
import re
import logging
from typing import Dict, Any, Optional
from openai import OpenAI

logger = logging.getLogger("outreach.ai")

class NvidiaNimGenerator:
    """
    NVIDIA NIM integration for fast, agentic reasoning and outreach message personalization.
    Supports Nemotron 3.5 Lightning, Nemotron 3 Super 120B, and Nemotron 3 Ultra.
    """

    NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
    
    @property
    def DEFAULT_API_KEY(self) -> str:
        from dotenv import load_dotenv
        load_dotenv()
        return os.getenv("NVIDIA_API_KEY", "")

    AVAILABLE_MODELS = {
        "lightning": "nvidia/nemotron-3.5-lightning-30b-a3b",
        "super": "nvidia/nemotron-3-ultra-550b-a55b",
        "ultra": "nvidia/nemotron-3-ultra-550b-a55b",
        "vl_browser": "nvidia/nemotron-3.5-super-vl-120b-a12b",
    }

    VERBATIM_SOURCE_BLOCKS = """
**NexusSwarm (Personal Project)** - 28-agent hierarchical platform of executive, manager and worker agents that automates requirements to deployment. Built with AutoGen, FastAPI, React and TypeScript, NVIDIA NIM and MCP servers, and has a dynamic model router, an LLM gateway and guardrails against prompt injection, secret leakage and hallucinated imports. The router cut average task time by 62% on NVIDIA NIM's free tier, from roughly 45 seconds to roughly 17, and the message must always say free tier. The eval suite has 107 tasks across 9 categories, with 100 used per run. The resilience suite blocked 4 attack tests, covering hallucination traps, prompt injection, remote code execution patterns and a CVE plus fake package combo, plus one deployment-penalty scoring check. (Never say 4 of 5 attacks blocked. Never say NexusSwarm is deployed or live, because it isn't right now).

**Greybox (Current Professional Role as AI Product Developer)** - Designing and deploying an agentic AI system on Google Cloud combining hybrid keyword-and-semantic retrieval, scaling to roughly 2,000 video transcripts for on-brand content generation. Validated in a pilot study achieving 66.7% top-3 retrieval accuracy, 100% groundedness with zero hallucinated techniques, and an 81.4/100 persona-fidelity score.

**Brain MRI Tumor Classification (Personal Project - Computer Vision)** - Owned the full pipeline for an 18,000-plus image brain MRI dataset, training and benchmarking five CNN architectures. Built an AI agent that ranks models by reliability rather than raw accuracy, selecting EfficientNet-B4 over the highest-accuracy model, with Grad-CAM explainability added for clinical interpretability.

**Clinical Reasoning Engine (Personal Project - Healthcare NLP)** - Built a clinical NLP reasoning engine turning unstructured discharge summaries into structured timelines with LLM-driven differential diagnosis, hitting 94.2% top-1 and 100% top-3 diagnostic accuracy across a 1,000-case benchmark, with every flagged finding grounded to exact source text and zero hallucinated evidence.

**IIIT Pune (Education / Academic Background)** - B.Tech in Computer Science and Engineering from Indian Institute of Information Technology, Pune (IIIT Pune).
"""

    def __init__(self, api_key: Optional[str] = None, model_tier: str = "ultra"):
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY", self.DEFAULT_API_KEY)
        self.client = OpenAI(base_url=self.NIM_BASE_URL, api_key=self.api_key)
        self.model_id = self.AVAILABLE_MODELS.get(model_tier, self.AVAILABLE_MODELS["ultra"])

    def detect_role_archetype(self, title: str, headline: str) -> str:
        """
        Classifies professional into one of 4 role archetypes:
        - engineering_leadership
        - senior_ic
        - product
        - recruiter
        """
        text = f"{title or ''} {headline or ''}".lower()

        if re.search(r"\b(recruiter|talent|people partner|head of talent|talent acquisition|hiring)\b", text):
            return "recruiter"
        if re.search(r"\b(cto|vp of eng|vp engineering|head of eng|engineering manager|director of eng|head of ai)\b", text):
            return "engineering_leadership"
        if re.search(r"\b(product manager|vp product|head of product|pm|product lead|director of product)\b", text):
            return "product"
        if re.search(r"\b(staff|principal|lead|senior|architect|engineer|developer|researcher)\b", text):
            return "senior_ic"
        return "engineering_leadership"

    def personalize_intro(self, contact: Dict[str, Any], sender_profile: Dict[str, Any]) -> str:
        """
        Uses Nemotron to craft a punchy, low-pressure, humanized LinkedIn cold intro message.
        """
        prompt = f"""You are drafting a LinkedIn connection acceptance intro message for {sender_profile.get('name', 'Shaurya Sharma')} ({sender_profile.get('headline', 'AI Engineer')}).

Recipient:
- Name: {contact.get('First Name', '')} {contact.get('Last Name', '')}
- Title: {contact.get('Title', 'Professional')}
- Company: {contact.get('Company', 'their company')}

Rules:
1. Max 2-4 sentences. Extremely concise and genuine.
2. NO pitch, NO calendar link, NO sales slop, NO em dashes (-).
3. Low-pressure ask (a quick question or 10-minute chat about their experience/challenges).
4. Output ONLY the message text.
"""
        return self._call_llm(prompt, fallback=f"Hi {contact.get('First Name', 'there')}, nice to connect. Noticed your focus on {contact.get('Company', 'your company')}'s engineering systems and would love to exchange perspectives on AI agent reliability if you ever have a moment. Thanks in advance.")

    def generate_connection_career_opener(
        self,
        contact: Dict[str, Any],
        sender_profile: Dict[str, Any],
        archetype: Optional[str] = None,
        company_intel: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generates a non-pitch career discovery opener to an EXISTING 1st-degree connection.
        Treats the 4 source blocks as fixed verbatim material and preserves all exact figures.
        """
        title = contact.get("Title", "")
        headline = contact.get("Headline", "")
        role_type = archetype or self.detect_role_archetype(title, headline)
        first_name = contact.get("First Name", "there")
        company = contact.get("Company", "your team")
        location = contact.get("Location", "abroad")

        if company_intel is None:
            try:
                from .company_researcher import company_researcher
                company_intel = company_researcher.research_company(company, headline, title)
            except Exception:
                company_intel = {
                    "industry": "technology",
                    "core_business": f"{company} engineering systems",
                    "ai_angle": "production AI agents and workflow orchestration",
                }

        industry = company_intel.get("industry", "technology")
        core_business = company_intel.get("core_business", "")
        ai_angle = company_intel.get("ai_angle", "production AI agents and workflow orchestration")
        about_summary = str(contact.get("About", "")).strip()
        about_context = f"\n- Profile About Section (their background/focus): {about_summary[:700]}" if about_summary else ""

        prompt = f"""You are drafting a concise LinkedIn direct message from Shaurya Sharma to an existing 1st-degree connection.

SENDER PROFILE:
- Name: Shaurya Sharma
- Identity: Junior AI Engineer / Early-Career AI Engineer
- Current Role: AI Product Developer at Greybox
- Education: B.Tech in Computer Science and Engineering from IIIT Pune (Indian Institute of Information Technology, Pune)

VERIFIED SOURCE BLOCKS FOR SHAURYA SHARMA (USE ONLY THESE FACTS):
{self.VERBATIM_SOURCE_BLOCKS}

RECIPIENT:
- First Name: {first_name}
- Title: {title}
- Company: {company}
- Location: {location}
- Role Archetype: {role_type}
- Industry / Focus: {industry} ({core_business}){about_context}

ROLE-MATCHING INSTRUCTION:
Select 1 or 2 projects or experiences from the verified source blocks above that directly fit the recipient's role, company, or technical domain:
- Multi-Agent Systems / LLM Routing / Distributed Infra / AI Engineering: Feature NexusSwarm (28-agent platform, 62% latency cut on NVIDIA NIM's free tier from ~45s to ~17s, guardrails blocking 4 attack tests). Optionally pair with Greybox or IIIT Pune.
- AI Product Management / Content / RAG / Enterprise GenAI / Cloud: Feature Greybox (current role as AI Product Developer, agentic GCP system, ~2,000 transcripts, 66.7% top-3 accuracy, 100% groundedness) and/or NexusSwarm.
- Healthcare / Health Tech / Biotech / Clinical NLP: Feature the Clinical Reasoning Engine (94.2% top-1, 100% top-3, 1,000 cases, zero hallucinated evidence) and/or Brain MRI Tumor Classification.
- Computer Vision / Medical Imaging / Radiology / Deep Learning: Feature Brain MRI Tumor Classification (18,000-plus image dataset, 5 CNN architectures, Grad-CAM).
- IIIT Pune Alumni / Academic / Indian tech ecosystem: You may also mention his Computer Science background from IIIT Pune.

MESSAGE FORMATION RULES (MANDATORY ORDER & STRUCTURE):
1. Personalized Opening (1 sentence):
   Open with a direct, concrete observation from their profile:
   * "Hi {first_name}, noticed your focus on [specific tech/system] at {company}."
   * "Hi {first_name}, saw your work on [specific system/domain] at {company}."
   * Strictly forbid: "I've been following your work", "impressed by", or false familiarity.
2. Experience/Project Body (1 or 2 sentences):
   Feature 1 or 2 verified projects/experiences from the source blocks above that directly fit their role.
   * If mentioning NexusSwarm: Name the 28-agent platform, router/guardrails, and verified result (62% cut on NVIDIA NIM's free tier, from roughly 45 seconds to roughly 17, or 4 attack tests blocked). NEVER say deployed or live.
   * If mentioning Greybox: Clarify it is his current role as AI Product Developer (~2,000 video transcripts, 66.7% top-3, 100% groundedness).
   * If mentioning Brain MRI: 18,000-plus image dataset, 5 CNNs, reliability ranking, Grad-CAM.
   * If mentioning Clinical NLP: 94.2% top-1 / 100% top-3 diagnostic accuracy, 1,000 cases, zero hallucinated evidence.
   * Strict attribution: NexusSwarm, Brain MRI, and Clinical Reasoning Engine are personal/independent projects; Greybox is his current professional role; IIIT Pune is education. Never say NexusSwarm was built at Greybox.
3. The Ask:
   "I'm exploring junior AI engineering roles, open to remote or relocation, and wondered if your team has openings."

CRITICAL CONSTRAINTS:
- No em dashes (never use '—', use hyphens '-' or commas ',').
- No links/URLs.
- Strictly junior AI engineer / early-career builder (never use 'senior').
- Never state a number that isn't listed in the verified facts above. Never round up or invent metrics.
- Output ONLY the raw message text itself. Do not output reasoning, commentary, planning notes, or checklist. Start directly with the greeting: "Hi {first_name},".
"""
        # Determine archetype/domain for intelligent deterministic fallback
        text_context = f"{title} {headline} {company} {industry} {about_summary}".lower()
        if any(k in text_context for k in ["clinic", "health", "med", "hospital", "pharma", "biotech"]):
            fallback_msg = (
                f"Hi {first_name}, noticed your focus on {industry} at {company}. "
                f"Independently, I built a clinical NLP reasoning engine hitting 94.2% top-1 and 100% top-3 diagnostic accuracy "
                f"across a 1,000-case benchmark with zero hallucinated evidence, and trained CNNs for an 18,000-plus image brain MRI dataset "
                f"ranked by model reliability. I'm exploring junior AI engineering roles, open to remote or relocation, and wondered if your team has openings."
            )
        elif any(k in text_context for k in ["vision", "imaging", "radiology", "mri", "scan", "cnn"]):
            fallback_msg = (
                f"Hi {first_name}, noticed your focus on {industry} at {company}. "
                f"As a personal project, I owned the full pipeline for an 18,000-plus image brain MRI dataset, training five CNN architectures "
                f"with an AI agent that ranks models by reliability over raw accuracy and added Grad-CAM explainability. "
                f"I'm exploring junior AI engineering roles, open to remote or relocation, and wondered if your team has openings."
            )
        elif any(k in text_context for k in ["product", "growth", "content", "rag", "retrieval", "search", "marketing"]):
            fallback_msg = (
                f"Hi {first_name}, noticed your focus on {industry} at {company}. "
                f"At Greybox, where I work as an AI Product Developer, I designed an agentic AI system on Google Cloud combining hybrid retrieval "
                f"across roughly 2,000 video transcripts, achieving 66.7% top-3 retrieval accuracy and 100% groundedness. "
                f"I'm exploring junior AI engineering roles, open to remote or relocation, and wondered if your team has openings."
            )
        elif any(k in text_context for k in ["iiit", "pune", "alumn", "college", "campus"]):
            fallback_msg = (
                f"Hi {first_name}, great to connect. "
                f"With a Computer Science background from IIIT Pune, I built NexusSwarm, a 28-agent hierarchical platform of executive, manager and worker agents, "
                f"with a dynamic model router that cut average task time by 62% on NVIDIA NIM's free tier, from roughly 45 seconds to roughly 17. "
                f"I'm exploring junior AI engineering roles, open to remote or relocation, and wondered if your team has openings."
            )
        else:
            fallback_msg = (
                f"Hi {first_name}, noticed your focus on {industry} at {company}. "
                f"I built NexusSwarm, a 28-agent hierarchical platform of executive, manager and worker agents that automates requirements to deployment, "
                f"with a dynamic model router, an LLM gateway and guardrails against prompt injection, secret leakage and hallucinated imports. "
                f"Routing cut average task time by 62% on NVIDIA NIM's free tier, from roughly 45 seconds to roughly 17, so simple tasks no longer wait on a large model. "
                f"It is evaluated on a suite across 9 categories, and its resilience tests blocked 4 attack tests. "
                f"I'm exploring junior AI engineering roles, open to remote or relocation, and wondered if your team has openings."
            )

        return self._call_llm(prompt, fallback=fallback_msg)

    def generate_connection_followup(
        self,
        contact: Dict[str, Any],
        sender_profile: Dict[str, Any],
    ) -> str:
        """
        Generates a 4-5 day low-pressure follow-up for an existing connection.
        Follows li-dm rules: adds something new or removes all pressure.
        """
        first_name = contact.get("First Name", "there")
        company = contact.get("Company", "your team")

        prompt = f"""You are drafting a follow-up LinkedIn direct message to an existing connection who did not reply to the first message sent 4 days ago.

Sender: Shaurya Sharma (Junior AI Engineer / AI Product Developer at GreyBox)
Recipient: {first_name} ({contact.get('Title', '')} at {company})

Rules:
1. Max 2 sentences.
2. Low-pressure, respectful. Acknowledge they are likely busy.
3. NEVER say 'just bumping this' or 'following up on my last email'.
4. Mention that you'd love to stay connected regardless.
5. No em dashes (-).
6. Output ONLY the message text.
"""
        fallback_msg = f"Hi {first_name}, no worries at all if you're swamped right now. Just wanted to keep in touch and follow {company}'s updates. Wishing you and the team continued momentum."
        return self._call_llm(prompt, fallback=fallback_msg)

    def _sanitize_and_humanize(self, text: str) -> str:
        """Cleans and humanizes message text using li-human rules, stripping em dashes and recruiter jargon."""
        if not text:
            return ""

        # Remove <think>...</think> tags if present
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

        # Check if the model put the final message inside quotes (common when models draft after thinking)
        quoted_blocks = re.findall(r'"(Hi\s+[A-Z][^"]{40,})"', text, flags=re.DOTALL)
        if quoted_blocks:
            text = quoted_blocks[-1]
        elif "Let me draft:" in text:
            text = text.split("Let me draft:", 1)[1].strip()
            if "Hi " in text:
                text = "Hi " + text.split("Hi ", 1)[1]
        elif "Hi " in text:
            # If multiple "Hi " blocks exist (e.g. revisions/drafts), pick the last complete one that contains the ask
            candidates = [("Hi " + chunk) for chunk in text.split("Hi ")[1:]]
            valid_candidates = [c for c in candidates if any(k in c.lower() for k in ["openings", "opening", "chat", "conversation", "radar"])]
            if valid_candidates:
                text = valid_candidates[-1]
            else:
                text = "Hi " + text.split("Hi ", 1)[1]

        # Clean trailing internal checklist / commentary (e.g. "Check constraints:", "Wait, need to...", "\n\n1. Name...")
        for stop_marker in ["\nCheck constraints:", "\nWait, need to", "\n1. Name NexusSwarm", "\nRecipient:", "\nStructure:"]:
            if stop_marker in text:
                prefix = text.split(stop_marker, 1)[0].strip()
                if len(prefix) > 140 and any(k in prefix.lower() for k in ["opening", "openings", "team", "hiring"]):
                    text = prefix
                elif stop_marker in ["\nCheck constraints:", "\nWait, need to"]:
                    # If it's pure model reasoning commentary, remove the trailing chunk even if prefix was shorter
                    text = prefix

        # Typography and unicode normalizations
        clean = (
            text.strip()
            .replace("—", "-")
            .replace("–", "-")
            .replace("\u2011", "-")
            .replace("\u2013", "-")
            .replace("\u2014", "-")
            .replace("\u2018", "'")
            .replace("\u2019", "'")
            .replace("\u201c", '"')
            .replace("\u201d", '"')
            .strip('"')
            .strip("'")
        )

        # Enforce Junior AI Engineer level (strip and replace any inadvertent 'senior' phrasing)
        clean = re.sub(r"\bsenior\s+ai\s+engineering\s+roles?\b", "junior AI engineering roles", clean, flags=re.IGNORECASE)
        clean = re.sub(r"\bsenior\s+ai\s+engineer\b", "junior AI engineer", clean, flags=re.IGNORECASE)
        clean = re.sub(r"\bsenior\s+engineering\s+roles?\b", "junior AI engineering roles", clean, flags=re.IGNORECASE)
        clean = re.sub(r"\bsenior\s+roles?\b", "junior AI engineering roles", clean, flags=re.IGNORECASE)
        clean = re.sub(r"\bsenior\s+positions?\b", "junior AI engineering positions", clean, flags=re.IGNORECASE)
        clean = re.sub(r"\bsenior\s+opportunities\b", "junior AI engineering opportunities", clean, flags=re.IGNORECASE)

        # Remove awkward third-person agency phrasing
        clean = re.sub(r"\b(remote or relocated AI engineering talent)\b", "a junior AI engineer (open to remote or relocation)", clean, flags=re.IGNORECASE)
        clean = re.sub(r"\b(talent for upcoming cycles)\b", "junior openings for upcoming cycles", clean, flags=re.IGNORECASE)
        clean = re.sub(r"\b(discussing AI engineering talent)\b", "discussing potential junior AI engineering openings", clean, flags=re.IGNORECASE)

        # Strip unverified familiarity and false history claims (e.g. "I've been following your work")
        clean = re.sub(
            r"\bI(?:'ve| have) been following\s+([A-Z][a-zA-Z0-9\s&,.'-]+?'s work)\b",
            r"saw \1",
            clean,
            flags=re.IGNORECASE
        )
        clean = re.sub(
            r"\bI(?:'ve| have) been following\s+your work\s+(?:on|in|with|at)?\b",
            "saw your work on",
            clean,
            flags=re.IGNORECASE
        )
        clean = re.sub(
            r"\bI(?:'ve| have) been following\s+(the work (?:your team is doing in|at|coming out of))\b",
            r"saw \1",
            clean,
            flags=re.IGNORECASE
        )
        clean = re.sub(
            r"\bI(?:'ve| have) been following\b",
            "saw",
            clean,
            flags=re.IGNORECASE
        )
        clean = re.sub(
            r"\bI(?:'ve| have) been watching\s+(?:how\s+)?",
            "noticed ",
            clean,
            flags=re.IGNORECASE
        )
        clean = re.sub(
            r"\bI(?:'ve| have) been impressed by\s+",
            "noticed ",
            clean,
            flags=re.IGNORECASE
        )
        clean = re.sub(
            r"\b(?:I\s+)?came across your work in\s+",
            "noticed your focus on ",
            clean,
            flags=re.IGNORECASE
        )
        clean = re.sub(
            r"\b(?:I\s+)?came across your work at\s+",
            "saw your work at ",
            clean,
            flags=re.IGNORECASE
        )
        clean = re.sub(
            r"\b(?:I\s+)?came across your work\s+",
            "saw your work ",
            clean,
            flags=re.IGNORECASE
        )
        clean = re.sub(
            r"\byour work at [^,]+ stands out\b",
            "noticed your role",
            clean,
            flags=re.IGNORECASE
        )

        # Ensure NexusSwarm is never described as deployed or live
        clean = re.sub(r"\b(?:deployed|deploying)\s+NexusSwarm\b", "built NexusSwarm", clean, flags=re.IGNORECASE)
        clean = re.sub(r"\bNexusSwarm\s+is\s+deployed\b", "NexusSwarm is built", clean, flags=re.IGNORECASE)
        clean = re.sub(r"\bdeployed\s+and\s+live\b", "built", clean, flags=re.IGNORECASE)

        # Enforce resilience test phrasing: never say "4 of 5 attacks blocked"
        clean = re.sub(r"\b4\s+(?:of|out\s+of)\s+5\s+attack\s+tests?\s+(?:were\s+)?blocked\b", "blocked 4 attack tests", clean, flags=re.IGNORECASE)
        clean = re.sub(r"\b4\s+(?:of|out\s+of)\s+5\s+attacks?\s+(?:were\s+)?blocked\b", "blocked 4 attack tests", clean, flags=re.IGNORECASE)

        # Run through li-human slop filter if available
        try:
            import sys
            from pathlib import Path
            skill_dir = Path(__file__).resolve().parent.parent / "linkedin-agent-skill" / "skills" / "li-human"
            if str(skill_dir) not in sys.path and skill_dir.exists():
                sys.path.insert(0, str(skill_dir))
            from humanize import humanize as li_humanize, load_lexicon
            slop_file = skill_dir / "slop.json"
            if slop_file.exists():
                lex = load_lexicon(str(slop_file))
                clean, _ = li_humanize(clean, lex)
        except Exception:
            pass

        return clean.strip()

    def _call_llm(self, prompt: str, fallback: str) -> str:
        """Executes LLM call with multi-tier fallback (NVIDIA NIM -> Ollama -> Template)."""
        # 1. Primary: NVIDIA NIM Cloud Models (Nemotron)
        try:
            resp = self.client.chat.completions.create(
                model=self.model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1500,
                timeout=35,
            )
            msg = resp.choices[0].message
            content = msg.content
            if not content and hasattr(msg, "reasoning_content"):
                reasoning = msg.reasoning_content or ""
                quoted = re.findall(r'"([^"]{30,})"', reasoning)
                if quoted:
                    content = quoted[-1]

            if content:
                logger.info(f"Generated text using NVIDIA NIM ({self.model_id})!")
                return self._sanitize_and_humanize(content)
        except Exception as nim_err:
            logger.warning(f"NVIDIA NIM error ({nim_err}). Attempting fallback to local Ollama...")

        # 2. Secondary Fallback: Local Ollama (qwen3.5:2b)
        try:
            ollama_client = OpenAI(base_url="http://127.0.0.1:11434/v1", api_key="ollama")
            resp = ollama_client.chat.completions.create(
                model="qwen3.5:2b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300,
                timeout=15,
            )
            content = resp.choices[0].message.content
            if content:
                logger.info("Generated text using local Ollama (qwen3.5:2b) fallback!")
                return self._sanitize_and_humanize(content)
        except Exception as ollama_err:
            logger.warning(f"Local Ollama error ({ollama_err}). Falling back to template...")

        # 3. Tertiary: Deterministic template fallback
        return self._sanitize_and_humanize(fallback)

    def visual_browser_inspect(
        self,
        screenshot_b64: str,
        task_prompt: str,
    ) -> Dict[str, Any]:
        """
        Uses nvidia/nemotron-3.5-super-vl-120b-a12b for multimodal screen inspection.
        Analyzes page screenshot to detect state, popups, modals, checkpoints, or buttons.
        """
        # Format base64 data URI if not already prefixed
        if not screenshot_b64.startswith("data:image"):
            screenshot_b64 = f"data:image/png;base64,{screenshot_b64}"

        full_prompt = f"""You are an autonomous browser control agent analyzing a screenshot of LinkedIn.
Task: {task_prompt}

Analyze the visual interface carefully.
Return valid JSON only with keys:
- "detected": boolean (true if the element/state was found, false otherwise)
- "state": string summary of the page state (e.g. "normal_profile", "weekly_limit_modal", "2fa_checkpoint", "chat_open")
- "description": clear explanation of what is visually visible
- "suggested_action": recommended browser action ("click", "wait", "close_modal", "type", "none")
"""
        try:
            resp = self.client.chat.completions.create(
                model=self.AVAILABLE_MODELS["vl_browser"],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": full_prompt},
                            {"type": "image_url", "image_url": {"url": screenshot_b64}}
                        ]
                    }
                ],
                temperature=0.1,
                max_tokens=500,
                timeout=25,
            )
            msg = resp.choices[0].message
            content = msg.content or ""
            # If content is empty but reasoning is present, extract json from reasoning
            if not content and hasattr(msg, "reasoning_content"):
                content = msg.reasoning_content or ""

            # Extract JSON block
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return {
                "detected": True,
                "state": "unknown",
                "description": content.strip(),
                "suggested_action": "none"
            }
        except Exception as e:
            logger.error(f"Error in visual_browser_inspect via Nemotron VL: {e}")
            return {
                "detected": False,
                "error": str(e),
                "state": "error",
                "suggested_action": "none"
            }

    def visual_locate_element(
        self,
        screenshot_b64: str,
        element_description: str,
        viewport_width: int = 1280,
        viewport_height: int = 800,
    ) -> Optional[Dict[str, int]]:
        """
        Uses nvidia/nemotron-3.5-super-vl-120b-a12b to visually locate element coordinates (x, y)
        on screen when DOM selectors are broken, obfuscated, or inside shadow DOM.
        """
        if not screenshot_b64.startswith("data:image"):
            screenshot_b64 = f"data:image/png;base64,{screenshot_b64}"

        prompt = f"""You are an autonomous browser control agent.
Screen Resolution: {viewport_width}x{viewport_height}.
Target Element: "{element_description}"

Locate the center pixel coordinates (x, y) of the target element in the screenshot.
Output valid JSON only with keys:
- "found": true/false
- "x": integer pixel coordinate (0 to {viewport_width})
- "y": integer pixel coordinate (0 to {viewport_height})
- "confidence": float between 0.0 and 1.0
- "element_label": string text visible on the element
"""
        try:
            resp = self.client.chat.completions.create(
                model=self.AVAILABLE_MODELS["vl_browser"],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": screenshot_b64}}
                        ]
                    }
                ],
                temperature=0.1,
                max_tokens=400,
                timeout=25,
            )
            msg = resp.choices[0].message
            content = msg.content or getattr(msg, "reasoning_content", "") or ""
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                if data.get("found") and "x" in data and "y" in data:
                    return {"x": int(data["x"]), "y": int(data["y"])}
            return None
        except Exception as e:
            logger.error(f"Error in visual_locate_element via Nemotron VL: {e}")
            return None

nim_generator = NvidiaNimGenerator()
