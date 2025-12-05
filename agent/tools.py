from playwright.sync_api import Page
from typing import Annotated, Optional
from bs4 import BeautifulSoup
import base64
from config import DESTRUCTIVE_KEYWORDS

page: Page = None

def goto_url(url: Annotated[str, "Full URL including https://"]) -> str:
    """Navigate to the specified URL"""
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(1000)  # Wait for dynamic content
        return f"Successfully navigated to {url}"
    except Exception as e:
        return f"Error navigating to {url}: {str(e)}"

def get_page_content(
    scroll_to_load: Annotated[bool, "Whether to scroll page to trigger lazy loading (default: True)"] = True
) -> str:
    """
    CRITICAL: Intelligent full-page content extraction. Returns structured text from ENTIRE page.

    Features:
    - Triggers lazy loading by scrolling to bottom
    - Captures dynamically loaded content
    - Returns hierarchical structure (sections with headings)
    - Token-optimized: semantic filtering, deduplication, length limits
    - Works on Russian SPAs

    Use this as PRIMARY tool for understanding any page.
    """
    try:
        # Step 1: Trigger lazy loading if needed
        if scroll_to_load:
            page.evaluate(r"""
                async () => {
                    // Scroll to bottom in chunks to trigger lazy loading
                    const scrollStep = window.innerHeight * 0.8;
                    const scrollDelay = 300;
                    let currentPos = 0;
                    const maxHeight = Math.min(document.body.scrollHeight, window.innerHeight * 5); // Max 5 viewports

                    while (currentPos < maxHeight) {
                        window.scrollTo(0, currentPos);
                        await new Promise(resolve => setTimeout(resolve, scrollDelay));
                        currentPos += scrollStep;
                    }

                    // Scroll back to top
                    window.scrollTo(0, 0);
                    await new Promise(resolve => setTimeout(resolve, 200));
                }
            """)
            page.wait_for_timeout(500)  # Let content stabilize

        # Step 2: Extract structured content
        result = page.evaluate(r"""
            () => {
                const sections = [];
                const seenTexts = new Set();

                // Helper: clean and validate text
                function cleanText(text) {
                    if (!text) return null;
                    text = text.trim().replace(/\s+/g, ' ');

                    // Filter garbage
                    if (text.length < 3) return null;
                    if (text.length > 300) return null;
                    if (/^[\d\s\.,;:!?()\[\]{}\\/\|\-\+•·×]+$/.test(text)) return null;
                    if (seenTexts.has(text)) return null;

                    seenTexts.add(text);
                    return text;
                }

                // 1. PAGE TITLE AND URL
                sections.push(`URL: ${window.location.href}`);
                sections.push(`TITLE: ${document.title}`);
                sections.push('---');

                // 2. MAIN HEADINGS (h1-h3)
                const headings = [];
                document.querySelectorAll('h1, h2, h3').forEach(h => {
                    const text = cleanText(h.innerText);
                    if (text) headings.push(`[${h.tagName}] ${text}`);
                });
                if (headings.length > 0) {
                    sections.push('HEADINGS:');
                    sections.push(...headings.slice(0, 20));
                    sections.push('---');
                }

                // 3. INTERACTIVE ELEMENTS (buttons, links, inputs)
                const interactive = [];
                document.querySelectorAll('button, a[href], input, select, textarea, [role="button"], [role="link"]').forEach(el => {
                    if (!el.offsetParent && el.tagName !== 'INPUT') return; // Skip hidden (except inputs)

                    let text = cleanText(el.innerText || el.getAttribute('aria-label') || el.getAttribute('placeholder') || el.getAttribute('value'));
                    if (!text) return;

                    const tag = el.tagName.toLowerCase();
                    const type = el.getAttribute('type') || '';
                    const id = el.id ? `#${el.id}` : '';
                    const name = el.getAttribute('name') ? `[name=${el.getAttribute('name')}]` : '';

                    interactive.push(`<${tag}${type ? ` type=${type}` : ''}${id}${name}> ${text}`);
                });
                if (interactive.length > 0) {
                    sections.push('INTERACTIVE ELEMENTS:');
                    sections.push(...interactive.slice(0, 100));
                    sections.push('---');
                }

                // 4. IMPORTANT CONTENT BLOCKS (articles, cards, list items)
                const contentBlocks = [];
                document.querySelectorAll('article, [class*="card"], [class*="item"], [class*="vacancy"], [class*="product"], [class*="email"], [class*="letter"], li').forEach(el => {
                    if (!el.offsetParent) return; // Skip hidden
                    if (el.closest('nav, header, footer')) return; // Skip navigation

                    const text = cleanText(el.innerText);
                    if (text && text.length > 15 && text.length < 250) {
                        contentBlocks.push(`• ${text}`);
                    }
                });
                if (contentBlocks.length > 0) {
                    sections.push('CONTENT BLOCKS:');
                    sections.push(...contentBlocks.slice(0, 80));
                    sections.push('---');
                }

                // 5. VISIBLE TEXT (fallback - all other visible text)
                const otherText = [];
                document.querySelectorAll('p, span, div, td, label').forEach(el => {
                    if (!el.offsetParent) return;
                    if (el.querySelector('button, a, input')) return; // Skip containers

                    const text = cleanText(el.innerText);
                    if (text && text.length > 10 && otherText.length < 50) {
                        otherText.push(text);
                    }
                });
                if (otherText.length > 0) {
                    sections.push('OTHER TEXT:');
                    sections.push(...otherText);
                }

                return sections.join('\n');
            }
        """)

        if not result.strip():
            return "No content found. Page may be empty or still loading."

        # Truncate if too long (should rarely happen with filtering above)
        if len(result) > 12000:
            result = result[:12000] + "\n\n... [TRUNCATED - page is very large]"

        return f"=== PAGE CONTENT (FULL PAGE, TOKEN-OPTIMIZED) ===\n{result}\n=== END ==="

    except Exception as e:
        return f"Error in get_page_content: {str(e)}"

def take_screenshot() -> str:
    """
    Takes a screenshot of the current page and returns base64 encoded image.
    This allows Claude to visually understand the page layout.
    """
    try:
        screenshot_bytes = page.screenshot(full_page=False)  # libo mozhno vmesto viewport: Fullpage: full_page=True, type="png"
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        return f"data:image/png;base64,{screenshot_base64}"
    except Exception as e:
        return f"Error taking screenshot: {str(e)}"

def find_element(description: Annotated[str, "Natural language description of the element"]) -> str:
    try:
        result = page.evaluate("""
            (desc) => {
                const query = desc.toLowerCase().trim();
                const words = query.split(' ').filter(w => w.length > 2);
                const candidates = [];


                document.querySelectorAll('a, button, div, span, [role="button"], [role="link"], [role="checkbox"], [data-tooltip], [aria-label], [title], [id^=":"]')
                .forEach(el => {
                    if (!el.offsetParent && el.tagName !== 'INPUT') return;

                    const texts = [
                        el.innerText,
                        el.textContent,
                        el.getAttribute('aria-label'),
                        el.getAttribute('title'),
                        el.getAttribute('data-tooltip'),
                        el.getAttribute('alt'),
                        el.getAttribute('placeholder'),
                        el.id
                    ].filter(Boolean).map(t => t?.toLowerCase().trim()).filter(Boolean);

                    let bestScore = 0;
                    let bestText = '';

                    for (let text of texts) {
                        if (!text) continue;

                        let score = 0;

                        // Полное совпадение
                        if (text === query) score += 100;

                        // Все слова из запроса есть
                        const matched = words.filter(w => text.includes(w)).length;
                        if (matched === words.length && words.length >= 2) score += 50;

                        // Частичное совпадение
                        for (let word of words) {
                            if (text.includes(word)) score += 15;
                        }

                        // Бонус за короткий текст
                        if (text.length < 60) score += 10;

                        if (score > bestScore) {
                            bestScore = score;
                            bestText = text;
                        }
                    }

                    if (bestScore >= 30) {
                        let selector = '';

                        if (el.getAttribute('data-testid')) {
                            selector = `[data-testid="${el.getAttribute('data-testid')}"]`;
                        } else if (el.id) {
                            selector = `#${el.id.replace(/:/g, '\\:')}`;  // Экранируем : для CSS
                        } else if (el.getAttribute('aria-label')) {
                            selector = `[aria-label*="${el.getAttribute('aria-label')}"]`;
                        } else {
                            const clean = bestText.replace(/'/g, "\\'");
                            selector = `xpath=//*/contains(text(), '${clean}')/parent::*`;
                        }

                        candidates.push({
                            score: bestScore,
                            selector: selector,
                            text: bestText
                        });
                    }
                });

                if (candidates.length === 0) return "NOT_FOUND";

                candidates.sort((a, b) => b.score - a.score);
                const best = candidates[0];
                return `FOUND|${best.selector}|${best.text}|score:${best.score}`;
            }
        """, description)

        if "NOT_FOUND" in result:
            return f"Не найден элемент: '{description}'"

        parts = result.split("|")
        return f"Найден: «{parts[2]}» → селектор: {parts[1]}"

    except Exception as e:
        return f"Ошибка find_element: {str(e)}"

def click(selector: Annotated[str, "Любой селектор: text=, xpath=, css, aria-label и т.д."]) -> str:
    
    global page  # MUST be at the top before any use of 'page'

    try:
        if selector.startswith("text="):
            text = selector[5:].strip().strip('"\'')
            selector = f"xpath=//*/text()[normalize-space()='{text}'']/parent::*"

        if any(kw in selector.lower() for kw in DESTRUCTIVE_KEYWORDS):
            if input(f"Опасное действие: клик по {selector}. Продолжить? (yes/no): ").lower() != "yes":
                return "Отменено пользователем"

        # Get current context to detect new tabs
        context = page.context
        current_pages = len(context.pages)
        current_url = page.url

        locator = page.locator(selector).first

        # scrolll
        locator.scroll_into_view_if_needed(timeout=5000)

        # awaitin for clicable
        locator.wait_for(state="visible", timeout=10000)
        try:
            locator.click(delay=100, timeout=8000)
            page.wait_for_timeout(800)
        except:
            try:
                locator.click(force=True, timeout=6000)
                page.wait_for_timeout(800)
            except:
                page.eval_on_selector(selector, "el => el.click()")
                page.wait_for_timeout(1000)

        # CRITICAL: Check if new tab opened and switch to it
        page.wait_for_timeout(500)  # Give time for new tab to open
        new_pages = context.pages

        if len(new_pages) > current_pages:
            # New tab opened - switch to it
            page = new_pages[-1]  # Switch to the newest tab
            page.wait_for_load_state("domcontentloaded", timeout=10000)
            return f"✅ Клик успешен: {selector}\n🆕 Открылась новая вкладка: {page.url}"
        elif page.url != current_url:
            # Same tab, but navigated
            page.wait_for_load_state("domcontentloaded", timeout=5000)
            return f"✅ Клик успешен: {selector}\n➡️ Перешли на: {page.url}"
        else:
            # Click worked but no navigation (popup, dropdown, etc.)
            return f"✅ Клик успешен: {selector} (страница не изменилась)"

    except Exception as e:
        return f"Все попытки клика провалились: {str(e)}\nПопробуй: take_screenshot()"

def type_text(
    selector: Annotated[str, "CSS selector or XPath of the input field"],
    text: Annotated[str, "Text to type into the field"]
) -> str:
    """
    Types text into an input field. Clears existing content first.
    """
    try:
        page.fill(selector, "")  # Clear existing text
        page.type(selector, text, delay=50)  # Human-like typing
        return f"Typed '{text}' into {selector}"
    except Exception as e:
        return f"Error typing into '{selector}': {str(e)}"

def press_key(
    key: Annotated[str, "Key name (e.g., 'Enter', 'Tab', 'Escape', 'ArrowDown')"]
) -> str:
    """Press a keyboard key"""
    try:
        page.keyboard.press(key)
        return f"Pressed key: {key}"
    except Exception as e:
        return f"Error pressing key '{key}': {str(e)}"

def scroll(
    direction: Annotated[str, "Direction to scroll: 'down', 'up', or 'to_element'"],
    selector: Annotated[Optional[str], "CSS selector of element to scroll to (only if direction='to_element')"] = None
) -> str:
    """Scroll the page in the specified direction or to a specific element"""
    try:
        if direction == "to_element" and selector:
            page.locator(selector).scroll_into_view_if_needed()
            return f"Scrolled to element: {selector}"
        elif direction == "down":
            page.evaluate("window.scrollBy(0, window.innerHeight * 0.8)")
            return "Scrolled down"
        elif direction == "up":
            page.evaluate("window.scrollBy(0, -window.innerHeight * 0.8)")
            return "Scrolled up"
        else:
            return f"Invalid scroll direction: {direction}"
    except Exception as e:
        return f"Error scrolling: {str(e)}"

def wait_for_element(
    selector: Annotated[str, "CSS selector or XPath of the element to wait for"],
    timeout_ms: Annotated[int, "Maximum time to wait in milliseconds"] = 10000
) -> str:
    """Wait for an element to appear on the page"""
    try:
        page.wait_for_selector(selector, timeout=timeout_ms)
        return f"Element appeared: {selector}"
    except Exception as e:
        return f"Element did not appear within {timeout_ms}ms: {selector}"

def get_element_text(
    selector: Annotated[str, "CSS selector or XPath of the element"]
) -> str:
    """Get the text content of a specific element"""
    try:
        text = page.locator(selector).inner_text()
        return f"Text content: {text}"
    except Exception as e:
        return f"Error getting text from '{selector}': {str(e)}"

def go_back() -> str:
    """Navigate back to the previous page"""
    try:
        page.go_back(wait_until="domcontentloaded")
        return "Navigated back to previous page"
    except Exception as e:
        return f"Error going back: {str(e)}"

def ask_human(
    question: Annotated[str, "Question to ask the user (e.g., for CAPTCHA, 2FA, or clarification)"]
) -> str:
    """
    Ask the human user a question and wait for their response.
    Use this for CAPTCHAs, 2FA, login credentials, or when you need clarification.
    """
    print(f"\n🤖 Agent asks: {question}")
    answer = input("👤 Your answer: ")
    return f"User responded: {answer}"

# Tool definitions for Claude API
TOOLS = [
    {
        "name": "goto_url",
        "description": "Navigate to a specific URL. Always use full URLs with https://",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Full URL including protocol (https://)"}
            },
            "required": ["url"]
        }
    },
    {
        "name": "get_page_content",
        "description": "PRIMARY TOOL: Intelligent full-page content extraction. Auto-scrolls to trigger lazy loading, captures ALL content (jobs, products, emails), returns structured hierarchical text. Token-optimized (~2000-3000 tokens). Use this FIRST on every page - it sees everything a human sees by scrolling.",
        "input_schema": {
            "type": "object",
            "properties": {
                "scroll_to_load": {"type": "boolean", "description": "Whether to scroll to trigger lazy loading (default: true). Set false only for static pages."}
            },
            "required": []
        }
    },

    {
        "name": "take_screenshot",
        "description": "Take a screenshot of the current page to visually understand the layout. Use when text tools are not enough. Each screenshot costs ~2000 tokens, so use strategically.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "find_element",
        "description": "Find an element on the page using natural language description (e.g., 'search button', 'email input'). Returns the selector to use with click or type_text.",
        "input_schema": {
            "type": "object",
            "properties": {
                "description": {"type": "string", "description": "Natural language description of the element"}
            },
            "required": ["description"]
        }
    },
    {
        "name": "click",
        "description": "Click on an element using a selector. Supports CSS selectors (#id, .class), XPath, or text selectors (text=Login). Use find_element first if you need to search for an element.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector, XPath, or text selector"}
            },
            "required": ["selector"]
        }
    },
    {
        "name": "type_text",
        "description": "Type text into an input field. Clears existing content first.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector or XPath of input field"},
                "text": {"type": "string", "description": "Text to type"}
            },
            "required": ["selector", "text"]
        }
    },
    {
        "name": "press_key",
        "description": "Press a keyboard key (Enter, Tab, Escape, ArrowDown, etc.)",
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Key name: Enter, Tab, Escape, ArrowDown, etc."}
            },
            "required": ["key"]
        }
    },
    {
        "name": "scroll",
        "description": "Scroll the page down, up, or to a specific element",
        "input_schema": {
            "type": "object",
            "properties": {
                "direction": {"type": "string", "enum": ["down", "up", "to_element"], "description": "Scroll direction"},
                "selector": {"type": "string", "description": "CSS selector (only used when direction='to_element')"}
            },
            "required": ["direction"]
        }
    },
    {
        "name": "wait_for_element",
        "description": "Wait for an element to appear on the page (useful for dynamic content)",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector or XPath"},
                "timeout_ms": {"type": "integer", "description": "Timeout in milliseconds (default: 10000)"}
            },
            "required": ["selector"]
        }
    },
    {
        "name": "get_element_text",
        "description": "Extract text content from a specific element",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector or XPath"}
            },
            "required": ["selector"]
        }
    },
    {
        "name": "go_back",
        "description": "Navigate back to the previous page in browser history",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "ask_human",
        "description": "Ask the human user a question. Use sparingly - try to solve tasks autonomously first.",
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "Question for the user"}
            },
            "required": ["question"]
        }
    }
]
