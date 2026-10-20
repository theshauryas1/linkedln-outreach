"""
Custom Model Context Protocol (MCP) Server for LinkedIn Outreach & Connections.
Standard stdio JSON-RPC 2.0 server compliant with MCP specification (2024-11-05).
Compatible with Claude Desktop, Antigravity, Cursor, and any MCP client.

Exposed Tools:
1. LINKEDIN_GET_CONNECTIONS: Scrapes 1st-degree connections from LinkedIn.
2. LINKEDIN_FILTER_CONNECTIONS: Applies regional filtering rules (excludes India, prioritizes Europe, US, SG, Dubai).
3. LINKEDIN_GENERATE_CONNECTION_MSG: Crafts a role-archetype no-pitch opener via Nemotron.
4. LINKEDIN_SEND_CONNECTION_MESSAGE: Sends a DM to a 1st-degree connection via Playwright.
5. LINKEDIN_RUN_CONNECTIONS_OUTREACH: Runs the full batch (4-5d followups + openers).
6. LINKEDIN_GET_PIPELINE_STATUS: Reports real-time status across cold and connections pipelines.
"""

import sys
import json
import logging
import traceback
from typing import Dict, Any, List, Optional

# Ensure standard error is used for logging so stdout remains pure JSON-RPC
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("linkedin.mcp_server")

# Import local engines
from .connections_pipeline import connections_pipeline
from .region_filter import classify_location
from .ai_generator import nim_generator
from .csv_manager import CSVManager
from .browser_engine import BrowserEngine
from .connections_actions import send_connection_dm

TOOLS_MANIFEST = [
    {
        "name": "LINKEDIN_GET_CONNECTIONS",
        "description": "Scrapes your 1st-degree LinkedIn connections from /mynetwork/invite-connect/connections/ using your real Chrome session. Extracts Full Name, Title, Company, Headline, Location, and Profile URL and records them in connections.csv.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of connections to scrape (default: 50).",
                    "default": 50
                },
                "resolve_locations": {
                    "type": "boolean",
                    "description": "Whether to visit profiles with missing location to extract exact city/country (default: true).",
                    "default": True
                }
            }
        }
    },
    {
        "name": "LINKEDIN_FILTER_CONNECTIONS",
        "description": "Evaluates stored connections against the regional filter: strictly excludes India (domestic roles out of scope); prioritizes Tier 1 (Europe/UK/Ireland), Tier 2 (North America), Tier 3 (Singapore), and Tier 4 (Dubai/Middle East).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_tier": {
                    "type": "string",
                    "description": "Optional tier filter ('all', 'tier1', 'tier2', 'tier3', 'tier4').",
                    "default": "all"
                }
            }
        }
    },
    {
        "name": "LINKEDIN_GENERATE_CONNECTION_MSG",
        "description": "Uses NVIDIA NIM (Nemotron 3 Super 120B) to generate a personalized, no-pitch career outreach opener for an existing 1st-degree connection based on their role archetype (Engineering Leadership, Senior IC, Product, Recruiter).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Connection's full or first name."
                },
                "title": {
                    "type": "string",
                    "description": "Connection's job title."
                },
                "company": {
                    "type": "string",
                    "description": "Connection's company or team."
                },
                "headline": {
                    "type": "string",
                    "description": "Connection's full LinkedIn headline."
                },
                "location": {
                    "type": "string",
                    "description": "Connection's location (city/country)."
                },
                "archetype_override": {
                    "type": "string",
                    "description": "Optional archetype ('engineering_leadership', 'senior_ic', 'product', 'recruiter')."
                }
            },
            "required": ["name", "title", "company"]
        }
    },
    {
        "name": "LINKEDIN_SEND_CONNECTION_MESSAGE",
        "description": "Navigates to an existing 1st-degree connection profile in Chrome, checks message history for prior replies, types the message with human keystroke delays (40-110ms), and sends it.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "profile_url": {
                    "type": "string",
                    "description": "LinkedIn profile URL of the 1st-degree connection."
                },
                "message": {
                    "type": "string",
                    "description": "Message text to deliver."
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "If true, simulates typing and logs message without sending (default: false).",
                    "default": False
                }
            },
            "required": ["profile_url", "message"]
        }
    },
    {
        "name": "LINKEDIN_RUN_CONNECTIONS_OUTREACH",
        "description": "Executes the full daily connections outreach sequence: checks for 4-5 day follow-ups on previously messaged connections (halting if they replied), and dispatches personalized openers to eligible priority-region connections up to daily limit.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "max_messages": {
                    "type": "integer",
                    "description": "Maximum total messages (openers + follow-ups) to send today (default: 15).",
                    "default": 15
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "If true, runs full flow without actually clicking send (default: false).",
                    "default": False
                }
            }
        }
    },
    {
        "name": "LINKEDIN_GET_PIPELINE_STATUS",
        "description": "Returns current queue and pipeline metrics for both cold leads (contacts.csv) and 1st-degree connections (connections.csv).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pipeline": {
                    "type": "string",
                    "description": "'cold', 'connections', or 'all' (default: 'all').",
                    "default": "all"
                }
            }
        }
    }
]

def handle_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Executes requested tool and returns text output."""
    logger.info(f"Executing tool: {tool_name} with args: {arguments}")

    if tool_name == "LINKEDIN_GET_CONNECTIONS":
        limit = arguments.get("limit", 50)
        resolve_locations = arguments.get("resolve_locations", True)
        result = connections_pipeline.scrape_and_index(
            max_count=limit,
            resolve_locations=resolve_locations,
            progress_callback=lambda msg: logger.info(f"[Scraper] {msg}")
        )
        return json.dumps(result, indent=2)

    elif tool_name == "LINKEDIN_FILTER_CONNECTIONS":
        df = connections_pipeline.load_df()
        target_tier = arguments.get("target_tier", "all").lower()

        total = len(df)
        india_excluded = len(df[df["Status"] == "REGION_EXCLUDED"])
        eligible = df[df["Status"].isin(["FILTERED_ELIGIBLE", "RETRIEVED"])]

        breakdown = eligible["Region Tier"].value_counts().to_dict()
        summary = {
            "total_connections": total,
            "india_excluded_count": india_excluded,
            "eligible_priority_count": len(eligible),
            "priority_tier_breakdown": breakdown,
        }
        return json.dumps(summary, indent=2)

    elif tool_name == "LINKEDIN_GENERATE_CONNECTION_MSG":
        contact = {
            "Full Name": arguments.get("name", ""),
            "First Name": arguments.get("name", "").split()[0],
            "Title": arguments.get("title", ""),
            "Company": arguments.get("company", ""),
            "Headline": arguments.get("headline", ""),
            "Location": arguments.get("location", ""),
        }
        sender = {
            "name": "Shaurya Sharma",
            "headline": "Artificial Intelligence Product Developer at GreyBox Technologies",
        }
        archetype = arguments.get("archetype_override")
        text = nim_generator.generate_connection_career_opener(contact, sender, archetype=archetype)
        return json.dumps({
            "recipient": contact["Full Name"],
            "detected_archetype": archetype or nim_generator.detect_role_archetype(contact["Title"], contact["Headline"]),
            "message_text": text,
            "character_count": len(text)
        }, indent=2)

    elif tool_name == "LINKEDIN_SEND_CONNECTION_MESSAGE":
        url = arguments.get("profile_url", "")
        message = arguments.get("message", "")
        dry_run = arguments.get("dry_run", False)

        from .config import config
        engine = BrowserEngine(headless=config.headless)
        context, page = engine.start()
        try:
            status, reason = send_connection_dm(
                page, engine, {"LinkedIn URL": url, "Full Name": "Contact", "First Name": "there"}, message, dry_run=dry_run
            )
            engine.close()
            return json.dumps({"status": status, "message": reason, "profile_url": url}, indent=2)
        except Exception as e:
            engine.close()
            return json.dumps({"status": "ERROR", "error": str(e), "profile_url": url}, indent=2)

    elif tool_name == "LINKEDIN_RUN_CONNECTIONS_OUTREACH":
        max_messages = arguments.get("max_messages", 15)
        dry_run = arguments.get("dry_run", False)
        result = connections_pipeline.run_outreach_batch(
            max_messages=max_messages,
            dry_run=dry_run,
            progress_callback=lambda msg: logger.info(f"[Batch] {msg}")
        )
        return json.dumps(result, indent=2)

    elif tool_name == "LINKEDIN_GET_PIPELINE_STATUS":
        target = arguments.get("pipeline", "all").lower()
        output: Dict[str, Any] = {}

        if target in ("connections", "all"):
            output["connections_pipeline"] = connections_pipeline.get_status_summary()

        if target in ("cold", "all"):
            csv_mgr = CSVManager()
            output["cold_pipeline"] = csv_mgr.get_status_summary()

        return json.dumps(output, indent=2)

    else:
        raise ValueError(f"Unknown tool: {tool_name}")

def run_stdio_server():
    """Runs the main stdio JSON-RPC loop."""
    logger.info("Starting LinkedIn Outreach Custom MCP Stdio Server...")

    # Set binary/utf-8 io
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")

    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except Exception as e:
            logger.error(f"Failed to parse JSON-RPC request: {e}")
            continue

        req_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        logger.debug(f"Received request: {method} (id: {req_id})")

        response: Dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": req_id
        }

        try:
            if method == "initialize":
                response["result"] = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {
                            "listChanged": False
                        }
                    },
                    "serverInfo": {
                        "name": "linkedin-outreach-mcp",
                        "version": "2.1.0"
                    }
                }

            elif method == "notifications/initialized":
                # Notifications do not return a response
                continue

            elif method == "tools/list":
                response["result"] = {
                    "tools": TOOLS_MANIFEST
                }

            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                result_text = handle_tool_call(tool_name, arguments)
                response["result"] = {
                    "content": [
                        {
                            "type": "text",
                            "text": result_text
                        }
                    ]
                }

            elif method == "ping":
                response["result"] = {}

            else:
                response["error"] = {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }

        except Exception as err:
            logger.error(f"Error handling method {method}: {err}\n{traceback.format_exc()}")
            response["error"] = {
                "code": -32000,
                "message": str(err),
                "data": traceback.format_exc()
            }

        # Send response line to stdout
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()

if __name__ == "__main__":
    run_stdio_server()
