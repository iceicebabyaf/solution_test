#!/usr/bin/env python3
"""
Login Helper - Manually login to websites and save sessions

This script opens a browser and lets you manually login to any website.
The session (cookies, tokens) is saved to .browser_session/ directory
and will be available to the agent in future runs.

Usage:
    ./venv/bin/python3 login_helper.py
"""

from playwright.sync_api import sync_playwright
from config import BROWSER_WIDTH, BROWSER_HEIGHT, SLOW_MO, USER_DATA_DIR
from rich import print as rprint
import os

def main():
    rprint("[bold cyan]╔══════════════════════════════════════════════════╗[/bold cyan]")
    rprint("[bold cyan]║        Login Helper - Session Manager           ║[/bold cyan]")
    rprint("[bold cyan]╚══════════════════════════════════════════════════╝[/bold cyan]\n")

    rprint("[yellow]This tool lets you manually login to websites.[/yellow]")
    rprint("[yellow]Sessions are saved and will be available to the agent.[/yellow]\n")

    url = input("🌐 Enter website URL (or press Enter for gmail.com): ").strip()
    if not url:
        url = "https://gmail.com"

    if not url.startswith("http"):
        url = "https://" + url

    rprint(f"\n[green]Opening browser to: {url}[/green]")
    rprint("[dim]You can manually login, navigate, and complete 2FA.[/dim]")
    rprint("[dim]All cookies and sessions will be saved.[/dim]\n")

    # Launch browser with persistent session
    with sync_playwright() as pw:
        # Create user data directory if it doesn't exist
        os.makedirs(USER_DATA_DIR, exist_ok=True)

        rprint(f"[dim]💾 Session data: {USER_DATA_DIR}[/dim]\n")

        # Launch browser with persistent context
        browser = pw.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            slow_mo=SLOW_MO,
            viewport={"width": BROWSER_WIDTH, "height": BROWSER_HEIGHT},
            args=[
                "--disable-blink-features=AutomationControlled",
            ]
        )

        # Get or create page
        if len(browser.pages) > 0:
            page = browser.pages[0]
        else:
            page = browser.new_page()

        # Navigate to URL
        page.goto(url)

        rprint("[bold green]✓ Browser opened[/bold green]")
        rprint("\n[bold yellow]Instructions:[/bold yellow]")
        rprint("1. Login to your account manually")
        rprint("2. Complete any 2FA/verification")
        rprint("3. Verify you're logged in")
        rprint("4. Press Enter here when done\n")

        input("[bold cyan]Press Enter when you've finished logging in...[/bold cyan]")

        # Test if we can access the page
        try:
            current_url = page.url
            rprint(f"\n[green]✓ Session saved![/green]")
            rprint(f"[dim]Current URL: {current_url}[/dim]")
            rprint(f"[dim]Session stored in: {USER_DATA_DIR}[/dim]\n")

            rprint("[bold green]Success![/bold green]")
            rprint("Next time you run the agent, it will use this logged-in session.\n")

            # Show session info
            cookies = browser.cookies()
            rprint(f"[dim]Saved {len(cookies)} cookies[/dim]")

        except Exception as e:
            rprint(f"[yellow]Note: {str(e)}[/yellow]")

        browser.close()

    rprint("\n[bold cyan]You can now run the agent with:[/bold cyan]")
    rprint("  ./run.sh\n")
    rprint("[dim]The agent will be logged in automatically![/dim]")

if __name__ == "__main__":
    main()
