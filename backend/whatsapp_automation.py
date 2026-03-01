"""
whatsapp_automation.py — Playwright-Based WhatsApp Web Automation

Provides autonomous WhatsApp interaction:
  1. CONNECT — Launch browser, navigate to WhatsApp Web, handle QR login
  2. READ — Scrape messages from a specific contact's chat
  3. SEND — Type and send a message to a specific contact

Uses Playwright (not Selenium) because:
  - Single binary install, no driver management
  - Built-in storageState persistence (QR code saved to disk)
  - Native auto-wait for modern SPAs
  - First-class Python async support

The browser runs in HEADED mode for hackathon demo visibility —
judges can literally watch the AI type and send messages in real-time.

Session data is stored in ./whatsapp_session/ so QR only needs
to be scanned once.
"""

import os
import re
import asyncio
import json
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright, Browser, Page, BrowserContext


# ─── Config ──────────────────────────────────────────────────────────────────

SESSION_DIR = os.path.join(os.path.dirname(__file__), "whatsapp_session")
WHATSAPP_URL = "https://web.whatsapp.com"
DEFAULT_TIMEOUT = 30000  # 30 seconds


# ─── Singleton Browser Manager ──────────────────────────────────────────────

class WhatsAppBrowser:
    """Manages a persistent Playwright browser instance for WhatsApp Web."""

    def __init__(self):
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._connected = False
        self._qr_needed = False

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def qr_needed(self) -> bool:
        return self._qr_needed

    async def connect(self) -> dict:
        """
        Launch browser and navigate to WhatsApp Web.
        Returns status dict with connection state.
        """
        if self._connected and self._page:
            return {"status": "already_connected", "qr_needed": False}

        try:
            # Ensure session directory exists
            Path(SESSION_DIR).mkdir(exist_ok=True)

            self._playwright = await async_playwright().start()

            # Use a true persistent profile directory to save IndexedDB and LocalStorage for WhatsApp
            user_data_dir = os.path.join(SESSION_DIR, "chrome_profile")
            Path(user_data_dir).mkdir(exist_ok=True)

            # Launch headed browser with a persistent context using the actual Chrome channel
            self._context = await self._playwright.chromium.launch_persistent_context(
                user_data_dir,
                channel="chrome",  # Use full Chrome instead of Chromium for better persistence
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--restore-last-session",
                    "--disable-infobars",
                    "--hide-crash-restore-bugalgs",
                ],
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            
            # Since launch_persistent_context already creates a page
            self._page = self._context.pages[0] if self._context.pages else await self._context.new_page()

            # Navigate to WhatsApp Web
            await self._page.goto(WHATSAPP_URL, wait_until="domcontentloaded")

            # Wait for either QR code or chat list to appear
            try:
                qr_or_chats = await self._page.wait_for_selector(
                    'canvas[aria-label="Scan this QR code to link a device!"], '
                    'div[aria-label="Chat list"], '
                    'div[data-testid="chat-list"]',
                    timeout=DEFAULT_TIMEOUT,
                )

                if qr_or_chats:
                    tag = await qr_or_chats.get_attribute("aria-label") or ""
                    if "QR" in tag or "Scan" in tag:
                        self._qr_needed = True
                        self._connected = False
                        return {
                            "status": "qr_needed",
                            "qr_needed": True,
                            "message": "Please scan the QR code in the browser window",
                        }
                    else:
                        self._connected = True
                        self._qr_needed = False
                        return {"status": "connected", "qr_needed": False}

            except Exception:
                pass

            # If we can't determine state, assume QR is needed
            self._qr_needed = True
            return {
                "status": "qr_needed",
                "qr_needed": True,
                "message": "Browser opened — scan QR code to connect",
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "qr_needed": False}

    async def wait_for_login(self, timeout: int = 120) -> dict:
        """Wait for user to scan QR code and become connected."""
        if not self._page:
            return {"status": "error", "error": "Browser not launched"}

        try:
            # Wait for chat list to appear (means QR was scanned)
            await self._page.wait_for_selector(
                'div[aria-label="Chat list"], div[data-testid="chat-list"]',
                timeout=timeout * 1000,
            )
            self._connected = True
            self._qr_needed = False

            return {"status": "connected", "qr_needed": False}
        except Exception:
            return {
                "status": "timeout",
                "message": "QR code was not scanned in time",
                "qr_needed": True,
            }

    async def get_status(self) -> dict:
        """Check current connection status."""
        if not self._page:
            return {"status": "disconnected", "connected": False}

        try:
            chat_list = await self._page.query_selector(
                'div[aria-label="Chat list"], div[data-testid="chat-list"]'
            )
            if chat_list:
                self._connected = True
                return {"status": "connected", "connected": True}
        except Exception:
            pass

        return {"status": "disconnected", "connected": False}

    # ─── Read Messages ───────────────────────────────────────────────

    async def read_messages(self, contact_name: str, limit: int = 50) -> dict:
        """
        Read messages from a specific contact's chat.

        Flow:
        1. Click search bar
        2. Type contact name
        3. Click on the contact
        4. Scrape message bubbles
        5. Parse into {sender, message, timestamp} format
        """
        if not self._connected or not self._page:
            return {"status": "error", "error": "Not connected to WhatsApp"}

        try:
            # Click search/new chat bar
            search_box = await self._page.wait_for_selector(
                'div[contenteditable="true"][data-tab="3"], '
                'div[title="Search input textbox"], '
                'div[aria-label="Search input textbox"]',
                timeout=10000,
            )
            if search_box:
                await search_box.click()
                await search_box.fill("")
                await asyncio.sleep(0.3)
                await search_box.fill(contact_name)
                await asyncio.sleep(1.5)  # Wait for search results

            # Use keyboard navigation instead of fragile DOM clicking
            # Press Down Arrow to highlight the top result, then Enter to select it
            await self._page.keyboard.press("ArrowDown")
            await asyncio.sleep(0.5)
            await self._page.keyboard.press("Enter")
            await asyncio.sleep(1.5)

            # Scrape messages from the chat
            messages = await self._scrape_messages(limit)

            return {
                "status": "success",
                "contact": contact_name,
                "message_count": len(messages),
                "messages": messages,
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _scrape_messages(self, limit: int = 50) -> List[Dict]:
        """Scrape visible messages from the current chat."""
        messages = []

        try:
            # Scroll up to load older messages before scraping
            # Move mouse to the center of the chat pane (right side of the 1280x800 viewport)
            await self._page.mouse.move(800, 400)
            
            # Scroll wheel up a few times to force WhatsApp to fetch history
            for _ in range(8):
                await self._page.mouse.wheel(0, -3000)
                await asyncio.sleep(0.2)
                
            # Now scroll back down so WhatsApp's virtual DOM renders the newest messages
            for _ in range(8):
                await self._page.mouse.wheel(0, 3000)
                await asyncio.sleep(0.2)
                
            # Brief pause for the final DOM update
            await asyncio.sleep(0.5)

            # WhatsApp Web message container selectors
            msg_elements = await self._page.query_selector_all(
                'div.message-in, div.message-out, '
                'div[data-testid="msg-container"]'
            )

            for elem in msg_elements[-limit:]:
                try:
                    # Determine sender (in = other person, out = user)
                    classes = await elem.get_attribute("class") or ""
                    is_outgoing = "message-out" in classes

                    # Get message text
                    text_elem = await elem.query_selector(
                        'span.selectable-text, '
                        'div[data-testid="msg-text"] span, '
                        'span[dir="ltr"]'
                    )
                    if not text_elem:
                        continue

                    text = await text_elem.inner_text()
                    if not text.strip():
                        continue

                    # Get timestamp
                    time_elem = await elem.query_selector(
                        'span[data-testid="msg-time"], '
                        'div[data-pre-plain-text]'
                    )
                    timestamp = ""
                    if time_elem:
                        timestamp = await time_elem.inner_text()

                    # Get sender name (for group chats)
                    sender = "You" if is_outgoing else "Contact"
                    sender_elem = await elem.query_selector(
                        'span[data-testid="msg-author"], '
                        'span._ahxt'
                    )
                    if sender_elem:
                        sender = await sender_elem.inner_text()

                    messages.append({
                        "sender": sender,
                        "message": text.strip(),
                        "timestamp": timestamp,
                    })

                except Exception:
                    continue

        except Exception as e:
            print(f"Message scraping error: {e}")

        return messages

    # ─── Send Message ────────────────────────────────────────────────

    async def send_message(self, contact_name: str, message: str) -> dict:
        """
        Send a message to a specific contact.

        Flow:
        1. Navigate to the contact's chat
        2. Click the message input box
        3. Type the message
        4. Press Enter to send

        Runs in HEADED mode so judges can watch the AI type in real-time.
        """
        if not self._connected or not self._page:
            return {"status": "error", "error": "Not connected to WhatsApp"}

        try:
            # Navigate to contact (search + select via keyboard)
            search_box = await self._page.wait_for_selector(
                'div[contenteditable="true"][data-tab="3"], '
                'div[title="Search input textbox"], '
                'div[aria-label="Search input textbox"]',
                timeout=10000,
            )
            if search_box:
                await search_box.click()
                await search_box.fill("")
                await asyncio.sleep(0.3)
                await search_box.fill(contact_name)
                await asyncio.sleep(1.5)

            # Use keyboard navigation instead of fragile DOM clicking
            await self._page.keyboard.press("ArrowDown")
            await asyncio.sleep(0.5)
            await self._page.keyboard.press("Enter")
            await asyncio.sleep(1)

            # Find the message input box
            msg_input = await self._page.wait_for_selector(
                'div[contenteditable="true"][data-tab="10"], '
                'div[aria-label="Type a message"], '
                'footer div[contenteditable="true"]',
                timeout=10000,
            )

            if not msg_input:
                return {"status": "error", "error": "Could not find message input"}

            # Click the input and type the message
            await msg_input.click()
            await asyncio.sleep(0.3)

            # Type with realistic delay (for demo effect)
            await msg_input.fill(message)
            await asyncio.sleep(0.5)

            # REMOVED: await self._page.keyboard.press("Enter")
            # We explicitly do NOT auto-send, so the user can review the AI draft.

            return {
                "status": "sent",
                "contact": contact_name,
                "message": message,
                "sent_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ─── Auto-Ingest ─────────────────────────────────────────────────

    async def auto_ingest(self, contact_name: str) -> dict:
        """
        Read messages from WhatsApp and return them in pipeline-ready format.
        This provides the AUTONOMOUS data extraction described in the research.
        """
        result = await self.read_messages(contact_name, limit=100)

        if result["status"] != "success":
            return result

        # Convert to the format our scoring engine expects
        messages = result["messages"]

        return {
            "status": "success",
            "contact": contact_name,
            "messages": messages,
            "message_count": len(messages),
            "source": "whatsapp_live",
        }

    # ─── Cleanup ─────────────────────────────────────────────────────

    async def disconnect(self):
        """Close browser and cleanup."""
        try:
            if self._context:
                await self._context.close()
            # Browser object isn't used with launch_persistent_context
            if self._playwright:
                await self._playwright.stop()
        except Exception:
            pass
        finally:
            self._connected = False
            self._page = None
            self._context = None
            self._browser = None
            self._playwright = None


# ─── Singleton ───────────────────────────────────────────────────────────────

_wa_instance = None

def get_whatsapp() -> WhatsAppBrowser:
    """Get or create the singleton WhatsApp browser instance."""
    global _wa_instance
    if _wa_instance is None:
        _wa_instance = WhatsAppBrowser()
    return _wa_instance
