from playwright.sync_api import sync_playwright
from agent.supervisor import run_agent
from agent import tools
from config import BROWSER_WIDTH, BROWSER_HEIGHT, SLOW_MO, USER_DATA_DIR
from rich import print as rprint
import os

def main():
    # Get task from user
    rprint("[bold cyan]╔══════════════════════════════════════════════════╗[/bold cyan]")
    rprint("[bold cyan]║   🤖 Autonomous Browser Agent by Claude AI      ║[/bold cyan]")
    rprint("[bold cyan]╚══════════════════════════════════════════════════╝[/bold cyan]\n")

    task = input("📝 Enter task for the agent: ").strip()
    if not task:
        task = "Go to github.com and find the repository xai-org/grok-1"
        rprint(f"[yellow]Using default task: {task}[/yellow]\n")

    # Launch browser with persistent session
    with sync_playwright() as pw:
        # Create user data directory if it doesn't exist
        os.makedirs(USER_DATA_DIR, exist_ok=True)

        rprint(f"[dim]💾 Session data: {USER_DATA_DIR}[/dim]")
        rprint("[dim]🔄 Using persistent session (cookies, login state preserved)[/dim]\n")

        # Launch browser with persistent context
        browser = pw.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            slow_mo=SLOW_MO,
            viewport={"width": BROWSER_WIDTH, "height": BROWSER_HEIGHT},
            args=[
                "--disable-blink-features=AutomationControlled",  # Avoid detection
            ]
        )

        # Get or create the first page
        if len(browser.pages) > 0:
            page = browser.pages[0]
        else:
            page = browser.new_page()

        # Initialize global page reference
        tools.page = page

        # Navigate to starting page
        page.goto("https://google.com")

        rprint("[bold green]✓ Browser opened (persistent session)[/bold green]")
        rprint("[bold green]✓ Agent starting...[/bold green]\n")
        rprint("[dim]" + "─" * 60 + "[/dim]\n")

        # Run the agent
        try:
            result = run_agent(task)

            rprint("\n[dim]" + "─" * 60 + "[/dim]")
            rprint("\n[bold magenta]✓ Task completed![/bold magenta]")
            if result:
                rprint(f"\n[bold white]📊 Result:[/bold white]\n{result}")
        except KeyboardInterrupt:
            rprint("\n[bold red]⚠️  Interrupted by user[/bold red]")
        except Exception as e:
            rprint(f"\n[bold red]❌ Error: {str(e)}[/bold red]")

        # Keep browser open for inspection
        input("\n[bold cyan]Press Enter to close browser...[/bold cyan]")
        browser.close()

if __name__ == "__main__":
    main()
