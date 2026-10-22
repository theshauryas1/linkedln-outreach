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
**NexusSwarm** - 28-agent multi-agent platform on AutoGen, FastAPI, React and NVIDIA NIM. Executive/manager/worker hierarchy automating software and AI engineering from requirements through deployment. A dynamic model router cut average task time by 62% on NIM's free tier by routing tasks to right-sized models instead of one large model. Includes guardrails against prompt injection, secret leakage and hallucinated imports. Evaluated with a 100-task, 9-category benchmark suite and a resilience test report where 4 of 5 attack tests were blocked.

**Greybox (AI Product Developer, current role)** - Designing and deploying an agentic AI system on Google Cloud combining hybrid keyword-and-semantic retrieval, scaling to roughly 2,000 video transcripts for on-brand content generation. Validated in a pilot study achieving 66.7% top-3 retrieval accuracy, 100% groundedness with zero hallucinated techniques, and an 81.4/100 persona-fidelity score.

**Brain MRI Tumor Classification** - Owned the full pipeline for an 18,000-plus image brain MRI dataset, training and benchmarking five CNN architectures. Built an AI agent that ranks models by reliability rather than raw accuracy, selecting EfficientNet-B4 over the highest-accuracy model, with Grad-CAM explainability added for clinical interpretability.

**Clinical Reasoning Engine** - Built a clinical NLP pipeline turning unstructured discharge summaries into structured timelines with LLM-driven differential diagnosis, hitting 94.2% top-1 and 100% top-3 diagnostic accuracy across a 1,000-case benchmark, with every flagged finding grounded to exact source text and zero hallucinated evidence.
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

FIXED VERBATIM SOURCE BLOCKS FOR SHAURYA SHARMA:
{self.VERBATIM_SOURCE_BLOCKS}

INSTRUCTION TO NEMOTRON:
Treat these four blocks as fixed, verbatim source material - pull facts only from them, never from a fresh read or summary of the CV file, and never invent, round up, or infer numbers or features. Pick whichever one or two blocks best match the connection's role, background, or company domain, and write the message around those facts only.

Strict Fact Source Rules (Zero Invention / Rounding):
- Use ONLY the provided facts; never invent, round up, or infer others.
- NexusSwarm: 28-agent multi-agent platform on AutoGen, FastAPI, React and NVIDIA NIM. Executive/manager/worker hierarchy automating software and AI engineering from requirements through deployment. Dynamic model router cut average task time by 62% on NIM's free tier by routing tasks to right-sized models instead of one large model. Guardrails against prompt injection, secret leakage and hallucinated imports. Evaluated with a 100-task, 9-category benchmark suite and a resilience test report where 4 of 5 attack tests were blocked.
- Never cite 97 tasks or unverified benchmarks; it is strictly a 100-task, 9-category benchmark suite.

Strict Attribution Rules:
- NexusSwarm, Brain MRI Tumor Classification, and Clinical Reasoning Engine are Shaurya's personal/independent projects.
- Greybox (AI Product Developer) is his current professional role.
- Never mix them up. Never say or imply NexusSwarm was built at Greybox.

CRITICAL SENIORITY LEVEL (MANDATORY):
- Shaurya Sharma is a JUNIOR AI Engineer / Early-Career AI Engineer.
- NEVER use the word "senior" to describe Shaurya, his experience level, or the roles he is seeking.
- NEVER ask for senior roles. Ask for "junior AI engineering roles" or simply "junior AI engineering opportunities" (open to remote or relocation).

CRITICAL TRUTHFULNESS & GROUNDING (MANDATORY):
- NEVER claim an unverified relationship, prior familiarity, or history that isn't confirmed true.
- PROHIBITED PHRASES (Strictly Forbidden):
  * "I've been following your work..."
  * "I've been following [company]'s work..."
  * "I've been watching how [company]..."
  * "I came across your work..."
  * "I've been impressed by..."
  * "Your work stands out..."
  * Any other assumed, fabricated, or flattering familiarity.
- HOW TO OPEN INSTEAD (Concrete, Direct & Fact-Based):
  Open ONLY with a direct, concrete observation from their profile data (their role, specific tech stack, system they build, or domain mentioned in their headline or about section):
  * "Hi [Name], noticed your focus on [specific tech/system] at [Company]..."
  * "Hi [Name], saw that you lead [specific function] at [Company]..."
  * "Hi [Name], with your role building [specific product/area] at [Company]..."
  * "Hi [Name], saw your work on [specific open source/research/system mentioned in profile]..."
  Make it a clean, matter-of-fact observation based entirely on what is written on their profile, without pretending to have known them before today.

RECIPIENT:
- First Name: {first_name}
- Title: {title}
- Company: {company}
- Location: {location}
- Role Archetype: {role_type}
- Industry / Focus: {industry} ({core_business}){about_context}

MESSAGE FORMATION RULES:
1. Length: 2 to 3 sentences maximum. Clean, conversational, peer-to-peer.
2. Perspective: First-person builder ("I", "my"). Shaurya is reaching out directly as a junior/early-career AI engineer, NOT an agency or recruiter.
3. Structure:
   - Line 1: Direct, concrete observation from their profile data (e.g. "noticed your focus on [topic/area] at [Company]" or "saw that you lead [area] at [Company]"). NEVER claim unverified familiarity or say "I've been following your work" or "impressed by [company]".
   - Line 2: Integrate the matching facts from the chosen 1 or 2 source blocks with their exact figures.
   - Line 3: Direct, low-pressure ask: Shaurya is exploring junior AI engineering roles (open to remote or relocation). Ask if their team or network has upcoming openings or if they would be open to a brief conversation. (NEVER say "senior" and NEVER say "discussing AI engineering talent" or "talent for upcoming cycles").
4. Rhythm & Cadence: Vary sentence lengths naturally. Use natural contractions (I'm, I've) and follow a detailed technical sentence with a shorter punchy sentence.
5. Prohibited:
   - Absolutely NO claims of prior familiarity, following their work, watching their company, or fake admiration.
   - Absolutely NO mention of "senior" (Shaurya is a junior engineer).
   - Absolutely NO em dashes (never use '—', use hyphens '-' or commas ',').
   - No AI buzzwords (delve, leverage, robust, seamless, tapestry, crucial, moreover).
6. Output ONLY the raw message text. Start directly with the greeting: "Hi {first_name},".
"""
        # Determine archetype/domain fallback using exact verbatim blocks
        text_context = f"{title} {headline} {company} {industry} {about_summary}".lower()
        if any(k in text_context for k in ["clinic", "health", "med", "hospital", "pharma", "biotech"]):
            fallback_msg = (
                f"Hi {first_name}, noticed your focus on {industry} at {company}. "
                f"Independently, I built a clinical NLP reasoning engine hitting 94.2% top-1 and 100% top-3 diagnostic accuracy "
                f"across a 1,000-case benchmark with zero hallucinated evidence, and trained CNNs for an 18,000-plus image brain MRI dataset "
                f"ranked by model reliability. I'm exploring junior AI engineering roles (open to remote or relocation) and wanted "
                f"to check if your team has upcoming openings."
            )
        elif any(k in text_context for k in ["vision", "imaging", "radiology", "mri", "scan", "cnn"]):
            fallback_msg = (
                f"Hi {first_name}, noticed your focus on {industry} at {company}. "
                f"As a personal project, I owned the full pipeline for an 18,000-plus image brain MRI dataset, training five CNN architectures "
                f"with an AI agent that ranks models by reliability over raw accuracy and added Grad-CAM explainability. "
                f"I'm exploring junior AI engineering roles (open to remote or relocation) and wanted to see if your team is hiring."
            )
        else:
            # General tech / software engineering / AI
            fallback_msg = (
                f"Hi {first_name}, noticed your focus on {industry} at {company}. "
                f"At Greybox I design an agentic AI system on Google Cloud combining hybrid keyword-and-semantic retrieval across 2,000 video transcripts (100% groundedness), "
                f"and independently built NexusSwarm, a 28-agent multi-agent platform where a dynamic model router cut average task time by 62% on NIM's free tier (evaluated across a 100-task benchmark). "
                f"I'm exploring junior AI engineering roles (open to remote or relocation) and wanted to check if your team has upcoming openings."
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

        # Extract message start if preamble was included
        if "Hi " in text:
            text = "Hi " + text.split("Hi ", 1)[1]

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
