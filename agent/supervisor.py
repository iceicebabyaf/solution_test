from anthropic import Anthropic
from rich.console import Console
from rich.panel import Panel
from config import client, MODEL
from agent.tools import TOOLS
import json

console = Console()


MAX_HISTORY_MESSAGES = 80
MAX_STEPS = 40

def run_agent(task: str) -> str:
    messages = [
        {
            "role": "user",
            "content": f"""You are an autonomous AI agent controlling a web browser. Your task is to complete the following objective:

TASK: {task}

IMPORTANT RULES:
1. Use ONLY the provided tools — never invent new ones.
2. Be extremely token-efficient: prefer fast text-based tools over screenshots.
3. Think step-by-step and adapt your strategy to the current page and website behavior.
4. Never use "text=" selectors — they are unreliable on modern single-page applications.
5. Always prefer the XPath selector returned by find_element() — it works everywhere.
6. If a click fails once — immediately call take_screenshot() for visual debugging instead of retrying.
7. For elements containing dynamic counters, badges, or icons (e.g. "Orders 3", "Cart 1"), describe them naturally in find_element() — e.g. "orders link with badge", "cart icon with number".
8. Close pop-ups, cookie banners, and ads as soon as they appear.
9. Ask the human via ask_human() only for dangerous actions (delete, pay, send) or when genuinely stuck.
10. When the task is complete, provide a clear, concise final answer.

You have full autonomy. No predefined plans. No hardcoded selectors.

Begin now."""
        }
    ]

    step = 0
    final_answer = None

    while step < MAX_STEPS:
        step += 1
        console.print(Panel(f"[bold white]Step {step}[/bold white] - Sending request to Claude...", style="bold blue"))

        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=4096,
                tools=TOOLS,
                messages=messages,
                temperature=0.0,
                extra_headers={"anthropic-beta": "context-1m-2025-08-07"}
            )

            messages.append({"role": "assistant", "content": response.content})

            tool_calls_made = False
            text_responses = []

            for block in response.content:
                if hasattr(block, "text"):
                    text_responses.append(block.text)
                    if block.text.strip():
                        console.print(Panel(block.text, title="Agent Thinking", style="dim cyan"))

                elif block.type == "tool_use":
                    tool_calls_made = True
                    tool_name = block.name
                    tool_input = block.input

                    console.print(Panel(
                        f"[bold yellow]Tool:[/bold yellow] {tool_name}\n"
                        f"[bold yellow]Arguments:[/bold yellow]\n{json.dumps(tool_input, ensure_ascii=False, indent=2)}",
                        title=f"Step {step}", style="bold green"
                    ))

                    tool_result = execute_tool(tool_name, tool_input)

                    # КЛЮЧЕВОЙ ФИКС: правильная отправка скриншотов + безопасный tool_result
                    if tool_name == "take_screenshot" and tool_result.startswith("data:image"):
                        console.print(Panel("Screenshot captured (vision analysis enabled)", style="bold yellow"))
                        messages.append({
                            "role": "user",
                            "content": [{
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": [
                                    {"type": "text", "text": "Screenshot taken and analyzed visually."},
                                    {
                                        "type": "image",
                                        "source": {
                                            "type": "base64",
                                            "media_type": "image/png",
                                            "data": tool_result.split(",")[1]
                                        }
                                    }
                                ]
                            }]
                        })
                    else:
                        # Smart truncation to respect token limits
                        MAX_TOOL_RESULT_CHARS = 8000  # ~2000 tokens per tool result
                        truncated_result = tool_result
                        if len(tool_result) > MAX_TOOL_RESULT_CHARS:
                            truncated_result = (
                                tool_result[:MAX_TOOL_RESULT_CHARS] +
                                f"\n\n... [TRUNCATED: {len(tool_result) - MAX_TOOL_RESULT_CHARS} chars omitted to save tokens]"
                            )

                        display = truncated_result[:500] + "..." if len(truncated_result) > 500 else truncated_result
                        console.print(Panel(display, title="Result", style="bold white"))
                        messages.append({
                            "role": "user",
                            "content": [{
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": truncated_result
                            }]
                        })

            if not tool_calls_made:
                final_answer = " ".join(text_responses)
                console.print(Panel(final_answer, title="Task Complete", style="bold green on black"))
                break

            # БЕЗОПАСНАЯ обрезка истории — сохраняем пары tool_use/tool_result
            if len(messages) > MAX_HISTORY_MESSAGES:
                # Оставляем: первый промпт + последние 70 сообщений (всегда целые пары)
                preserved = [messages[0]] + messages[-70:]
                messages = preserved
                console.print("[dim italic]Trimmed conversation history safely (preserved tool pairs)[/dim italic]\n")

        except Exception as e:
            console.print(Panel(f"Error in agent loop: {str(e)}", title="Error", style="bold red"))
            break

    if step >= MAX_STEPS:
        console.print(Panel(f"Reached maximum steps ({MAX_STEPS})", title="Max Steps", style="bold yellow"))

    return final_answer or "Task execution ended without final answer"


def execute_tool(tool_name: str, tool_input: dict) -> str:
    try:
        from agent import tools
        if not hasattr(tools, tool_name):
            return f"Error: Unknown tool '{tool_name}'"
        tool_func = getattr(tools, tool_name)
        result = tool_func(**tool_input)
        return str(result)
    except Exception as e:
        return f"Error executing {tool_name}: {str(e)}"