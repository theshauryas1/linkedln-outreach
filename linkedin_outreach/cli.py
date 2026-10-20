import argparse
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .config import config, ensure_directories, USER_OUTREACH_DIR
from .csv_manager import CSVManager, sync_to_user_home
from .pipeline import OutreachPipeline
from .browser_engine import BrowserEngine
from .connections_pipeline import connections_pipeline

console = Console()

def cmd_login(args):
    """Launches Chrome for one-time LinkedIn authentication."""
    console.print(Panel.fit("[bold cyan]LinkedIn Session Setup[/bold cyan]\nLaunching Chrome to save your LinkedIn session cookies...", border_style="cyan"))
    ensure_directories()
    engine = BrowserEngine(headless=False)
    engine.start()
    success = engine.interactive_login()
    if success:
        console.print("[bold green][OK] Session successfully authenticated and saved![/bold green]")
    else:
        console.print("[bold red][X] Authentication incomplete or timed out.[/bold red]")
    engine.close()

def cmd_status(args):
    """Displays pipeline status and contact count breakdown."""
    csv_mgr = CSVManager()
    stats = csv_mgr.get_stats()

    table = Table(title="[bold blue]Cold LinkedIn Outreach Pipeline Status[/bold blue]", border_style="blue")
    table.add_column("Stage / Status", style="bold")
    table.add_column("Count", justify="right", style="cyan")
    table.add_column("Next Action Description", style="dim")

    table.add_row("(blank)", str(stats["blank"]), "Ready to receive connection request (Step 1)")
    table.add_row("INVITED", str(stats["invited"]), "Invite sent; checking acceptance after 3+ days (Step 2)")
    table.add_row("MSG1_SENT", str(stats["msg1_sent"]), "Intro sent; checking follow-up after 5+ days (Step 3)")
    table.add_row("MSG2_SENT", str(stats["msg2_sent"]), "Follow-up sent; awaiting contact response")
    table.add_row("REPLIED", str(stats["replied"]), "[bold green]Replied! Sequence halted; manual conversation[/bold green]")
    if stats["other"] > 0:
        table.add_row("Other / Review", str(stats["other"]), "Needs manual review")
    table.add_section()
    table.add_row("TOTAL LEADS", str(stats["total"]), f"Database: {csv_mgr.filepath}")

    console.print(table)

    # Connections Summary
    conn_summary = connections_pipeline.get_status_summary()
    conn_table = Table(title="[bold magenta]1st-Degree Connections Career Pipeline[/bold magenta]", border_style="magenta")
    conn_table.add_column("Category / Tier", style="bold")
    conn_table.add_column("Count", justify="right", style="yellow")

    for status, count in conn_summary.get("by_status", {}).items():
        conn_table.add_row(f"Status: {status}", str(count))
    conn_table.add_section()
    for tier, count in conn_summary.get("by_region_tier", {}).items():
        conn_table.add_row(f"Region: {tier}", str(count))
    conn_table.add_section()
    conn_table.add_row("TOTAL CONNECTIONS", str(conn_summary["total_connections"]))

    console.print(conn_table)

def cmd_run(args):
    """Executes the daily outreach workflow."""
    ensure_directories()
    pipeline = OutreachPipeline()
    console.print(Panel.fit(
        f"[bold cyan]Running LinkedIn Cold Outreach Pipeline[/bold cyan]\n"
        f"• Invites Limit: [green]{args.invites}[/green]\n"
        f"• Messages Limit: [green]{args.messages}[/green]\n"
        f"• Dry Run: [yellow]{args.dry_run}[/yellow]",
        border_style="cyan"
    ))
    res = pipeline.run(
        invite_limit=args.invites,
        message_limit=args.messages,
        dry_run=args.dry_run,
        progress_callback=lambda m: console.print(f"[dim]{m}[/dim]"),
    )
    if "error" in res:
        console.print(f"[bold red]Pipeline stopped with error:[/bold red] {res['error']}")
    else:
        console.print("[bold green][OK] Pipeline execution complete![/bold green]")

def cmd_connections(args):
    """Manages 1st-degree connections outreach extension."""
    subaction = args.action
    effective_limit = args.limit if args.limit is not None else (args.count if args.count is not None else 25)

    if subaction == "scrape":
        console.print(Panel.fit(
            f"[bold magenta]Scraping 1st-Degree LinkedIn Connections[/bold magenta]\n"
            f"Limit: {effective_limit} | Resolve Locations: {not args.no_resolve}",
            border_style="magenta"
        ))
        res = connections_pipeline.scrape_and_index(
            max_count=effective_limit,
            resolve_locations=not args.no_resolve,
            progress_callback=lambda m: console.print(f"[dim]{m}[/dim]"),
        )
        console.print(f"[bold green][OK] Scrape complete:[/bold green] {res}")

    elif subaction == "run":
        console.print(Panel.fit(
            f"[bold magenta]Running 1st-Degree Connections Outreach Batch[/bold magenta]\n"
            f"Max Messages: {effective_limit} | Dry Run: {args.dry_run}",
            border_style="magenta"
        ))
        res = connections_pipeline.run_outreach_batch(
            max_messages=effective_limit,
            dry_run=args.dry_run,
            progress_callback=lambda m: console.print(f"[dim]{m}[/dim]"),
        )
        console.print(f"[bold green][OK] Batch complete:[/bold green] {res}")

    else:
        # Default status
        cmd_status(args)

def cmd_mcp(args):
    """Runs the Custom Stdio MCP Server."""
    from .mcp_server import run_stdio_server
    run_stdio_server()

def cmd_test(args):
    """Step 6 Live Test: Runs exactly 3 invites to verify setup."""
    ensure_directories()
    console.print(Panel.fit(
        "[bold magenta]Step 6: Live 3-Contact Test Run[/bold magenta]\n"
        "Testing browser navigation, connect modal handling, and CSV updates on 3 contacts.",
        border_style="magenta"
    ))
    pipeline = OutreachPipeline()
    res = pipeline.run(
        invite_limit=3,
        message_limit=3,
        dry_run=args.dry_run,
        progress_callback=lambda m: console.print(f"[dim]{m}[/dim]"),
    )
    console.print("[bold green][OK] Test run completed![/bold green]")

def cmd_sync(args):
    """Copies contacts.csv and templates to ~/outreach/."""
    sync_to_user_home()
    console.print(f"[bold green][OK] Synced templates and contacts to {USER_OUTREACH_DIR}[/bold green]")

def cmd_serve(args):
    """Launches the modern web dashboard on port 8500."""
    import uvicorn
    console.print(Panel.fit(
        "[bold cyan]Starting LinkedIn Outreach Dashboard[/bold cyan]\n"
        f"Open in browser: [bold underline green]http://127.0.0.1:{args.port}[/bold underline green]",
        border_style="cyan"
    ))
    uvicorn.run("linkedin_outreach.server:app", host="127.0.0.1", port=args.port, reload=False)

def main():
    parser = argparse.ArgumentParser(description="Automated LinkedIn Outreach Agent & MCP Server")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # login
    subparsers.add_parser("login", help="Launch Chrome and log into LinkedIn once to save session")

    # status
    subparsers.add_parser("status", help="Show current pipeline counts and stats")

    # run
    p_run = subparsers.add_parser("run", help="Run the full daily cold outreach sequence")
    p_run.add_argument("--invites", type=int, default=config.daily_invite_limit, help="Max invites to send (default 20)")
    p_run.add_argument("--messages", type=int, default=config.daily_message_limit, help="Max messages to send (default 20)")
    p_run.add_argument("--dry-run", action="store_true", help="Simulate without actually sending")

    # connections
    p_conn = subparsers.add_parser("connections", help="Manage 1st-degree connections outreach pipeline")
    p_conn.add_argument("action", choices=["status", "scrape", "run"], default="status", nargs="?", help="Action to perform")
    p_conn.add_argument("count", type=int, nargs="?", default=None, help="Optional count or message limit (e.g. 'scrape 25')")
    p_conn.add_argument("--limit", type=int, default=None, help="Limit for scrape or messages")
    p_conn.add_argument("--no-resolve", action="store_true", help="Do not visit profiles to inspect location")
    p_conn.add_argument("--dry-run", action="store_true", help="Simulate without sending")

    # mcp
    subparsers.add_parser("mcp", help="Run the custom Stdio MCP server (JSON-RPC 2.0)")

    # test
    p_test = subparsers.add_parser("test", help="Test with 3 contacts as shown in Step 6")
    p_test.add_argument("--dry-run", action="store_true", help="Dry run test without sending")

    # sync
    subparsers.add_parser("sync", help="Sync contacts & templates to ~/outreach")

    # serve
    p_serve = subparsers.add_parser("serve", help="Launch local web control center dashboard")
    p_serve.add_argument("--port", type=int, default=8500, help="Web dashboard port (default 8500)")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    cmd_map = {
        "login": cmd_login,
        "status": cmd_status,
        "run": cmd_run,
        "connections": cmd_connections,
        "mcp": cmd_mcp,
        "test": cmd_test,
        "sync": cmd_sync,
        "serve": cmd_serve,
    }

    cmd_map[args.command](args)

if __name__ == "__main__":
    main()
