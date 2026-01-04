"""
BRO Smart Shopping Agent
Advanced AI-powered shopping that can:
- Read grocery lists from images (OCR/Vision)
- Compare prices across multiple platforms
- Auto-add items to cart
- Find cheapest options per item

Supports:
- Groceries: BigBasket, Blinkit, Zepto, Amazon Fresh, JioMart
- Electronics: Amazon, Flipkart, Croma
- General: Amazon, Flipkart
"""

import os
import sys
import json
import time
import base64
import urllib.request
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# =============================================================================
# CONFIGURATION
# =============================================================================

# Grocery platforms
GROCERY_PLATFORMS = {
    "bigbasket": {
        "name": "BigBasket",
        "search_url": "https://www.bigbasket.com/ps/?q=",
        "type": "grocery"
    },
    "blinkit": {
        "name": "Blinkit",
        "search_url": "https://blinkit.com/s/?q=",
        "type": "grocery"
    },
    "zepto": {
        "name": "Zepto",
        "search_url": "https://www.zeptonow.com/search?query=",
        "type": "grocery"
    },
    "jiomart": {
        "name": "JioMart",
        "search_url": "https://www.jiomart.com/search/",
        "type": "grocery"
    },
    "amazon_fresh": {
        "name": "Amazon Fresh",
        "search_url": "https://www.amazon.in/s?k=",
        "type": "grocery"
    }
}

ELECTRONICS_PLATFORMS = {
    "amazon": {
        "name": "Amazon",
        "search_url": "https://www.amazon.in/s?k=",
        "type": "electronics"
    },
    "flipkart": {
        "name": "Flipkart", 
        "search_url": "https://www.flipkart.com/search?q=",
        "type": "electronics"
    },
    "croma": {
        "name": "Croma",
        "search_url": "https://www.croma.com/searchB?q=",
        "type": "electronics"
    }
}

ALL_PLATFORMS = {**GROCERY_PLATFORMS, **ELECTRONICS_PLATFORMS}

# =============================================================================
# MOBILE APP PACKAGES (for Android phone shopping)
# =============================================================================

MOBILE_APPS = {
    "blinkit": {
        "package": "com.grofers.customerapp",
        "name": "Blinkit",
        "search_activity": None,  # Will use UI automation
        "type": "grocery"
    },
    "zepto": {
        "package": "com.zeptoconsumerapp",
        "name": "Zepto",
        "search_activity": None,
        "type": "grocery"
    },
    "bigbasket": {
        "package": "com.bigbasket.mobileapp",
        "name": "BigBasket",
        "search_activity": None,
        "type": "grocery"
    },
    "jiomart": {
        "package": "com.jio.jiomart.customer",
        "name": "JioMart", 
        "search_activity": None,
        "type": "grocery"
    },
    "amazon": {
        "package": "in.amazon.mShop.android.shopping",
        "name": "Amazon",
        "search_activity": None,
        "type": "general"
    },
    "flipkart": {
        "package": "com.flipkart.android",
        "name": "Flipkart",
        "search_activity": None,
        "type": "general"
    },
    "swiggy_instamart": {
        "package": "in.swiggy.android",
        "name": "Swiggy Instamart",
        "search_activity": None,
        "type": "grocery"
    }
}


# =============================================================================
# SHOPPING LIST ITEM
# =============================================================================

@dataclass
class ShoppingItem:
    """A single item to shop for."""
    name: str
    quantity: str = "1"
    unit: str = ""
    category: str = "general"
    best_price: float = 0.0
    best_platform: str = ""
    prices: Dict[str, float] = field(default_factory=dict)
    added_to_cart: bool = False
    notes: str = ""


@dataclass  
class ShoppingList:
    """A complete shopping list."""
    items: List[ShoppingItem] = field(default_factory=list)
    source: str = "manual"  # "manual", "image", "voice"
    created_at: str = ""
    total_estimated: float = 0.0
    optimized_carts: Dict[str, List[str]] = field(default_factory=dict)


# =============================================================================
# IMAGE ANALYSIS (Read grocery list from photo)
# =============================================================================

def analyze_grocery_image(image_path: str) -> List[ShoppingItem]:
    """
    Analyze an image of a grocery list and extract items.
    Uses local Ollama vision model (moondream/llava).
    
    Args:
        image_path: Path to the image file (.jpg, .png)
        
    Returns:
        List of ShoppingItem objects
    """
    path = Path(image_path)
    if not path.exists():
        print(f"[!] Image not found: {image_path}")
        return []
    
    # Read and encode image
    with open(path, "rb") as f:
        img_bytes = f.read()
    img_b64 = base64.b64encode(img_bytes).decode()
    
    prompt = """Look at this image of a grocery/shopping list.
Extract every item from the list.

For each item, provide:
- Item name
- Quantity (if mentioned, otherwise "1")
- Unit (kg, liters, pieces, etc if mentioned)

Format your response as a JSON array like this:
[
  {"name": "Rice", "quantity": "5", "unit": "kg"},
  {"name": "Milk", "quantity": "2", "unit": "liters"},
  {"name": "Eggs", "quantity": "12", "unit": "pieces"}
]

Only output the JSON array, nothing else."""

    try:
        payload = json.dumps({
            "model": "moondream",  # Using moondream for vision
            "messages": [{
                "role": "user",
                "content": prompt,
                "images": [img_b64]
            }],
            "stream": False,
            "options": {"temperature": 0.1}
        }).encode()
        
        req = urllib.request.Request(
            "http://localhost:11434/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print("[*] Analyzing image with AI vision...")
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode())
            content = result["message"]["content"]
            
            # Try to parse JSON from response
            # Find JSON array in response
            start = content.find("[")
            end = content.rfind("]") + 1
            
            if start >= 0 and end > start:
                json_str = content[start:end]
                items_data = json.loads(json_str)
                
                items = []
                for item in items_data:
                    items.append(ShoppingItem(
                        name=item.get("name", "Unknown"),
                        quantity=str(item.get("quantity", "1")),
                        unit=item.get("unit", ""),
                        category="grocery"
                    ))
                
                print(f"[+] Found {len(items)} items in image")
                return items
            else:
                print("[!] Could not parse items from image")
                print(f"    AI response: {content[:200]}")
                return []
                
    except Exception as e:
        print(f"[!] Vision analysis error: {e}")
        return []


def parse_text_list(text: str) -> List[ShoppingItem]:
    """
    Parse a text grocery list.
    Accepts formats like:
    - "Rice 5kg, Milk 2L, Eggs 12"
    - "1. Rice\n2. Milk\n3. Eggs"
    """
    items = []
    
    # Split by common delimiters
    lines = text.replace(",", "\n").split("\n")
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Remove numbering
        if line[0].isdigit() and (line[1] == "." or line[1] == ")"):
            line = line[2:].strip()
        
        # Try to extract quantity
        parts = line.split()
        name = line
        quantity = "1"
        unit = ""
        
        # Look for patterns like "5kg", "2L", "12 pieces"
        for i, part in enumerate(parts):
            # Check if it's a number with unit
            for u in ["kg", "g", "l", "ml", "liters", "pieces", "pcs", "dozen"]:
                if u in part.lower():
                    # Extract number
                    num = "".join(c for c in part if c.isdigit() or c == ".")
                    if num:
                        quantity = num
                        unit = u
                        # Remove this from name
                        name = " ".join(parts[:i] + parts[i+1:])
                        break
        
        if name:
            items.append(ShoppingItem(
                name=name.strip(),
                quantity=quantity,
                unit=unit,
                category="grocery"
            ))
    
    return items


# =============================================================================
# PRICE COMPARISON
# =============================================================================

def search_item_prices(item: ShoppingItem, platforms: List[str] = None) -> ShoppingItem:
    """
    Search for item prices across platforms.
    Currently generates search URLs - actual scraping requires browser automation.
    """
    if platforms is None:
        platforms = list(GROCERY_PLATFORMS.keys())
    
    item.prices = {}
    
    for platform_key in platforms:
        platform = ALL_PLATFORMS.get(platform_key)
        if not platform:
            continue
        
        search_query = f"{item.name} {item.quantity}{item.unit}".strip()
        search_url = platform["search_url"] + search_query.replace(" ", "+")
        
        # Store the search URL (actual price fetching requires web automation)
        item.prices[platform_key] = {
            "url": search_url,
            "platform_name": platform["name"],
            "price": None  # Will be filled by browser automation
        }
    
    return item


def generate_comparison_report(shopping_list: ShoppingList) -> str:
    """Generate a comparison report for the shopping list."""
    output = f"""
🛒 SHOPPING LIST ANALYSIS
{'='*50}
Items: {len(shopping_list.items)}
Source: {shopping_list.source}
{'='*50}

📋 ITEMS TO BUY:
"""
    
    for i, item in enumerate(shopping_list.items, 1):
        output += f"\n{i}. {item.name}"
        if item.quantity != "1" or item.unit:
            output += f" ({item.quantity} {item.unit})"
    
    output += f"""

🔍 SEARCH ON MULTIPLE PLATFORMS:
"""
    
    # Group by platform
    for platform_key, platform in GROCERY_PLATFORMS.items():
        output += f"\n📦 {platform['name']}:\n"
        for item in shopping_list.items:
            if platform_key in item.prices:
                url = item.prices[platform_key]["url"]
                output += f"   • {item.name}: {url}\n"
    
    output += """
💡 TIP: I can open these links for you or use browser automation 
   to compare actual prices and add to cart.
"""
    
    return output


# =============================================================================
# CART AUTOMATION
# =============================================================================

def add_to_cart_instructions(item: ShoppingItem, platform: str) -> Dict:
    """
    Generate instructions for adding item to cart.
    To be used with browser automation (Playwright).
    """
    instructions = {
        "platform": platform,
        "item": item.name,
        "steps": []
    }
    
    platform_info = ALL_PLATFORMS.get(platform)
    if not platform_info:
        return instructions
    
    search_query = f"{item.name} {item.quantity}{item.unit}".strip()
    search_url = platform_info["search_url"] + search_query.replace(" ", "+")
    
    instructions["steps"] = [
        {"action": "navigate", "url": search_url},
        {"action": "wait", "seconds": 2},
        {"action": "find", "selector": "[data-testid='product-card'], .product-item, .product-card", "description": "Find first product"},
        {"action": "click", "selector": "button:contains('Add'), .add-to-cart, [data-testid='add-to-cart']", "description": "Click Add to Cart"},
        {"action": "wait", "seconds": 1},
    ]
    
    return instructions


# =============================================================================
# SMART SHOPPING AGENT
# =============================================================================

class SmartShoppingAgent:
    """
    AI-powered shopping agent that can:
    - Read lists from images
    - Compare prices
    - Optimize cart across platforms
    - Auto-add items
    """
    
    def __init__(self):
        self.current_list: Optional[ShoppingList] = None
        self.cart_items: Dict[str, List[ShoppingItem]] = {}  # platform -> items
    
    def create_list_from_image(self, image_path: str) -> str:
        """Create shopping list from an image."""
        print(f"\n📸 Reading shopping list from: {image_path}")
        
        items = analyze_grocery_image(image_path)
        
        if not items:
            return "❌ Could not read items from image. Please try a clearer photo."
        
        self.current_list = ShoppingList(
            items=items,
            source="image",
            created_at=datetime.now().isoformat()
        )
        
        # Search prices for each item
        for item in self.current_list.items:
            search_item_prices(item)
        
        return self._format_list()
    
    def create_list_from_text(self, text: str) -> str:
        """Create shopping list from text."""
        items = parse_text_list(text)
        
        if not items:
            return "❌ No items found in the text."
        
        self.current_list = ShoppingList(
            items=items,
            source="text",
            created_at=datetime.now().isoformat()
        )
        
        for item in self.current_list.items:
            search_item_prices(item)
        
        return self._format_list()
    
    def add_item(self, name: str, quantity: str = "1", unit: str = "") -> str:
        """Add a single item to the current list."""
        if not self.current_list:
            self.current_list = ShoppingList(
                source="manual",
                created_at=datetime.now().isoformat()
            )
        
        item = ShoppingItem(name=name, quantity=quantity, unit=unit)
        search_item_prices(item)
        self.current_list.items.append(item)
        
        return f"✅ Added: {name} ({quantity} {unit})"
    
    def _format_list(self) -> str:
        """Format the current list for display."""
        if not self.current_list:
            return "No shopping list created yet."
        
        output = f"""
🛒 SHOPPING LIST ({len(self.current_list.items)} items)
{'='*50}
"""
        
        for i, item in enumerate(self.current_list.items, 1):
            qty = f"{item.quantity} {item.unit}".strip() or "1"
            output += f"\n  {i}. {item.name} - {qty}"
        
        output += f"""

{'='*50}
📦 AVAILABLE PLATFORMS:

🥬 Groceries:
   • BigBasket, Blinkit, Zepto, JioMart, Amazon Fresh

📱 Actions:
   • 'compare' - Compare prices across platforms
   • 'open bigbasket' - Open platform with your list
   • 'add [item]' - Add more items
   • 'cart all' - Add all items to cart
"""
        return output
    
    def compare_prices(self) -> str:
        """Generate price comparison (opens search pages)."""
        if not self.current_list:
            return "No shopping list. Create one first!"
        
        return generate_comparison_report(self.current_list)
    
    def open_platform(self, platform: str) -> str:
        """Open a platform with the shopping list search."""
        import webbrowser
        
        platform = platform.lower().strip()
        
        if platform not in ALL_PLATFORMS:
            return f"Unknown platform. Available: {', '.join(ALL_PLATFORMS.keys())}"
        
        if not self.current_list or not self.current_list.items:
            return "No items in shopping list."
        
        # Open search for first few items
        platform_info = ALL_PLATFORMS[platform]
        
        for item in self.current_list.items[:3]:  # Open first 3 items
            search_query = item.name.replace(" ", "+")
            url = platform_info["search_url"] + search_query
            webbrowser.open(url)
            time.sleep(0.5)
        
        return f"✅ Opened {platform_info['name']} with searches for your items!"
    
    def get_cart_automation_script(self, platform: str) -> str:
        """Generate automation script for adding items to cart."""
        if not self.current_list:
            return "No shopping list."
        
        script = f"""
# Browser Automation Script for {platform}
# Run with: python -c "exec(open('cart_script.py').read())"

from playwright.sync_api import sync_playwright

items = {json.dumps([{"name": i.name, "qty": i.quantity} for i in self.current_list.items])}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    for item in items:
        # Search for item
        page.goto("{ALL_PLATFORMS.get(platform, {}).get('search_url', '')}" + item["name"])
        page.wait_for_timeout(2000)
        
        # Try to click first product's add button
        try:
            page.click("text=Add", timeout=5000)
            print(f"Added: {{item['name']}}")
        except:
            print(f"Could not add: {{item['name']}}")
    
    print("\\nDone! Check your cart.")
    input("Press Enter to close browser...")
    browser.close()
"""
        return script
    
    # =========================================================================
    # PHONE SHOPPING (Android)
    # =========================================================================
    
    def shop_on_phone(self, app: str = "blinkit") -> str:
        """
        Open a shopping app on your Android phone and search for items.
        Uses the Android controller (ADB).
        
        Args:
            app: App name (blinkit, zepto, bigbasket, amazon, flipkart)
        """
        app = app.lower().strip()
        
        if app not in MOBILE_APPS:
            return f"Unknown app. Available: {', '.join(MOBILE_APPS.keys())}"
        
        if not self.current_list or not self.current_list.items:
            return "No items in shopping list. Create one first!"
        
        app_info = MOBILE_APPS[app]
        
        try:
            from tools.android_control import AndroidController
            
            ctrl = AndroidController()
            if not ctrl.connect():
                return "❌ Could not connect to phone. Make sure:\n  1. Phone is connected via USB or WiFi\n  2. USB Debugging is enabled"
            
            # Open the app
            print(f"📱 Opening {app_info['name']} on your phone...")
            ctrl.device.shell(f"monkey -p {app_info['package']} -c android.intent.category.LAUNCHER 1")
            time.sleep(3)  # Wait for app to load
            
            # Take screenshot to verify
            ctrl.capture_screen("phone_shop_screen.png")
            
            return f"""✅ Opened {app_info['name']} on your phone!

📋 Your Shopping List ({len(self.current_list.items)} items):
{chr(10).join([f"  • {item.name} ({item.quantity} {item.unit})" for item in self.current_list.items])}

📱 Next Steps:
  1. The app is now open on your phone
  2. Say 'phone search [item]' to search for an item
  3. Say 'phone tap [x] [y]' to tap on screen
  4. Say 'phone swipe up' to scroll
  5. Say 'phone add [item]' to auto-add item to cart

💡 Or say 'phone auto' to let BRO handle it automatically!
"""
        except ImportError:
            return "❌ Android control module not available."
        except Exception as e:
            return f"❌ Error: {e}"
    
    def phone_search(self, item_name: str) -> str:
        """Search for an item in the current phone app."""
        try:
            from tools.android_control import AndroidController
            
            ctrl = AndroidController()
            if not ctrl.connect():
                return "❌ Phone not connected"
            
            # Type in search
            # First, try to tap on search bar (usually at top)
            ctrl.tap(ctrl.screen_size[0] // 2, 150)  # Tap near top center
            time.sleep(1)
            
            # Type the item name
            ctrl.type_text(item_name)
            time.sleep(0.5)
            
            # Press enter
            ctrl.press_key("enter")
            time.sleep(2)
            
            # Take screenshot
            ctrl.capture_screen("phone_search_result.png")
            
            return f"🔍 Searched for: {item_name}\n📸 Screenshot saved: phone_search_result.png"
            
        except Exception as e:
            return f"❌ Error: {e}"
    
    def phone_add_to_cart(self) -> str:
        """Try to add the first visible item to cart on phone."""
        try:
            from tools.android_control import AndroidController
            
            ctrl = AndroidController()
            if not ctrl.connect():
                return "❌ Phone not connected"
            
            # Use vision to find Add button
            # For now, tap common "Add" button locations
            # Most apps have Add button on the right side of product cards
            
            # Tap in the area where Add buttons usually are
            ctrl.tap(int(ctrl.screen_size[0] * 0.85), int(ctrl.screen_size[1] * 0.4))
            time.sleep(1)
            
            # Take screenshot to verify
            ctrl.capture_screen("phone_cart.png")
            
            return "🛒 Tapped Add button. Check your phone to verify!"
            
        except Exception as e:
            return f"❌ Error: {e}"
    
    def phone_auto_shop(self, app: str = "blinkit") -> str:
        """
        Automatically shop all items from the list on phone.
        This opens the app and adds each item one by one.
        """
        if not self.current_list or not self.current_list.items:
            return "No shopping list!"
        
        results = []
        
        # Open the app first
        open_result = self.shop_on_phone(app)
        results.append(open_result)
        
        if "❌" in open_result:
            return open_result
        
        try:
            from tools.android_control import AndroidController
            
            ctrl = AndroidController()
            ctrl.connect()
            
            for item in self.current_list.items:
                print(f"\n🔍 Searching for: {item.name}")
                
                # Go to home/search
                ctrl.press_key("home")
                time.sleep(1)
                ctrl.device.shell(f"monkey -p {MOBILE_APPS[app]['package']} -c android.intent.category.LAUNCHER 1")
                time.sleep(2)
                
                # Tap search area
                ctrl.tap(ctrl.screen_size[0] // 2, 150)
                time.sleep(1)
                
                # Type item name
                ctrl.type_text(item.name.replace(" ", "%s"))
                time.sleep(0.5)
                ctrl.press_key("enter")
                time.sleep(3)
                
                # Try to add first result
                ctrl.tap(int(ctrl.screen_size[0] * 0.85), int(ctrl.screen_size[1] * 0.35))
                time.sleep(1)
                
                results.append(f"  ✅ Added: {item.name}")
            
            return f"""
🛒 AUTO-SHOPPING COMPLETE!

{chr(10).join(results)}

📱 Please check your phone's cart to verify all items.
💳 Ready to checkout when you are!
"""
        except Exception as e:
            return f"❌ Auto-shop error: {e}"
    
    def compare_prices_phone(self, item_name: str, apps: List[str] = None) -> str:
        """
        Compare prices for an item across multiple phone apps.
        Uses AI vision to read prices from screenshots.
        
        Args:
            item_name: The item to search for
            apps: List of apps to compare (default: blinkit, zepto, bigbasket)
        """
        if apps is None:
            apps = ["blinkit", "zepto", "bigbasket"]
        
        results = {}
        screenshots = {}
        
        try:
            from tools.android_control import AndroidController
            
            ctrl = AndroidController()
            if not ctrl.connect():
                return "❌ Phone not connected"
            
            print(f"\n💰 Comparing prices for: {item_name}")
            print("="*50)
            
            for app in apps:
                if app not in MOBILE_APPS:
                    continue
                
                app_info = MOBILE_APPS[app]
                print(f"\n📱 Checking {app_info['name']}...")
                
                # Open the app
                ctrl.device.shell(f"monkey -p {app_info['package']} -c android.intent.category.LAUNCHER 1")
                time.sleep(3)
                
                # Tap search area (top of screen)
                ctrl.tap(ctrl.screen_size[0] // 2, 150)
                time.sleep(1)
                
                # Clear any existing text and type new search
                ctrl.press_key("delete")  # Clear field
                time.sleep(0.3)
                ctrl.type_text(item_name.replace(" ", "%s"))
                time.sleep(0.5)
                ctrl.press_key("enter")
                time.sleep(3)  # Wait for results
                
                # Take screenshot
                screenshot_path = f"price_{app}_{item_name.replace(' ', '_')}.png"
                ctrl.capture_screen(screenshot_path)
                screenshots[app] = screenshot_path
                
                # Use AI vision to read the price
                price = self._read_price_from_screenshot(screenshot_path, item_name)
                results[app] = {
                    "app_name": app_info["name"],
                    "price": price,
                    "screenshot": screenshot_path
                }
                
                print(f"   {app_info['name']}: {price}")
                
                # Go home before next app
                ctrl.press_key("home")
                time.sleep(1)
            
            # Generate comparison report
            return self._format_price_comparison(item_name, results)
            
        except Exception as e:
            return f"❌ Comparison error: {e}"
    
    def _read_price_from_screenshot(self, screenshot_path: str, item_name: str) -> str:
        """Use AI vision to read price from screenshot."""
        try:
            with open(screenshot_path, "rb") as f:
                img_bytes = f.read()
            img_b64 = base64.b64encode(img_bytes).decode()
            
            prompt = f"""You are reading a shopping app screenshot.
Your task: Find and report the price shown for a product.
Look for numbers with rupee symbol (₹) or Rs.

IMPORTANT: Reply with ONLY the price number, nothing else.
Example responses: ₹68, ₹125, Rs.99

What is the price shown?"""
            
            payload = json.dumps({
                "model": "llava:7b",
                "messages": [{
                    "role": "user",
                    "content": prompt,
                    "images": [img_b64]
                }],
                "stream": False,
                "options": {"temperature": 0.1}
            }).encode()
            
            req = urllib.request.Request(
                "http://localhost:11434/api/chat",
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
                price_text = result["message"]["content"].strip()
                
                # Extract price (look for ₹ or numbers)
                if "₹" in price_text:
                    # Find the price pattern
                    import re
                    match = re.search(r'₹\s*[\d,]+\.?\d*', price_text)
                    if match:
                        return match.group()
                
                return price_text if price_text else "NOT_FOUND"
                
        except Exception as e:
            return f"Error: {e}"
    
    def _format_price_comparison(self, item_name: str, results: dict) -> str:
        """Format price comparison results."""
        output = f"""
💰 PRICE COMPARISON: {item_name}
{'='*50}

"""
        # Sort by price (lowest first)
        sorted_results = []
        for app, data in results.items():
            price_str = data["price"]
            # Extract numeric value for sorting
            try:
                import re
                match = re.search(r'[\d,]+\.?\d*', price_str.replace(',', ''))
                price_num = float(match.group()) if match else 9999
            except:
                price_num = 9999
            sorted_results.append((app, data, price_num))
        
        sorted_results.sort(key=lambda x: x[2])
        
        # Format output
        best_app = None
        for i, (app, data, price_num) in enumerate(sorted_results):
            icon = "🏆" if i == 0 and price_num < 9999 else "📦"
            if i == 0:
                best_app = data["app_name"]
            output += f"{icon} {data['app_name']}: {data['price']}\n"
        
        if best_app and sorted_results[0][2] < 9999:
            output += f"""
{'='*50}
✅ BEST DEAL: {best_app}

💡 Say 'phone shop {sorted_results[0][0]}' to buy from there!
"""
        else:
            output += "\n⚠️ Could not determine best price. Check screenshots manually."
        
        return output
    
    def compare_all_items(self, apps: List[str] = None) -> str:
        """Compare prices for all items in the shopping list."""
        if not self.current_list or not self.current_list.items:
            return "No shopping list!"
        
        if apps is None:
            apps = ["blinkit", "zepto", "bigbasket"]
        
        output = f"""
🏪 MULTI-PLATFORM PRICE COMPARISON
{'='*50}
Items: {len(self.current_list.items)}
Comparing: {', '.join(apps)}
{'='*50}
"""
        
        all_results = {}
        
        for item in self.current_list.items:
            print(f"\n📊 Comparing: {item.name}")
            result = self.compare_prices_phone(item.name, apps)
            all_results[item.name] = result
            output += f"\n{result}\n"
        
        # Suggest optimal cart
        output += f"""
{'='*50}
📊 OPTIMIZATION TIP:
Based on prices, you might want to split your order
across apps to get the best deals on each item!

💡 Or pick one app for convenience.
"""
        return output


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_agent = SmartShoppingAgent()

def shop_from_image(image_path: str) -> str:
    """Read and create shopping list from image."""
    return _agent.create_list_from_image(image_path)

def shop_from_text(text: str) -> str:
    """Create shopping list from text."""
    return _agent.create_list_from_text(text)

def add_to_list(item: str, quantity: str = "1", unit: str = "") -> str:
    """Add item to shopping list."""
    return _agent.add_item(item, quantity, unit)

def compare_shopping() -> str:
    """Compare prices across platforms."""
    return _agent.compare_prices()

def open_shop(platform: str) -> str:
    """Open a shopping platform with current list."""
    return _agent.open_platform(platform)

# Phone shopping functions
def phone_shop(app: str = "blinkit") -> str:
    """Open shopping app on phone."""
    return _agent.shop_on_phone(app)

def phone_search(item: str) -> str:
    """Search for item on phone app."""
    return _agent.phone_search(item)

def phone_add() -> str:
    """Add visible item to cart on phone."""
    return _agent.phone_add_to_cart()

def phone_auto_shop(app: str = "blinkit") -> str:
    """Automatically shop all items on phone."""
    return _agent.phone_auto_shop(app)

# Price comparison functions
def compare_item(item: str, apps: list = None) -> str:
    """Compare price of a single item across apps."""
    return _agent.compare_prices_phone(item, apps)

def compare_all(apps: list = None) -> str:
    """Compare prices for entire shopping list across apps."""
    return _agent.compare_all_items(apps)

def get_list() -> str:
    """Get current shopping list."""
    return _agent._format_list() if _agent.current_list else "No shopping list yet."

def clear_list() -> str:
    """Clear the shopping list."""
    _agent.current_list = None
    return "✅ Shopping list cleared."


# =============================================================================
# CLI
# =============================================================================

def main():
    """Interactive shopping agent CLI."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║          BRO SMART SHOPPING AGENT                         ║
╠══════════════════════════════════════════════════════════════╣
║  • Read grocery lists from images                            ║
║  • Compare prices across platforms                           ║
║  • Auto-add to cart                                          ║
╚══════════════════════════════════════════════════════════════╝

Commands:
  image <path>     - Read list from image
  text <items>     - Create list from text
  add <item>       - Add item to list
  list             - Show current list
  compare          - Compare prices
  open <platform>  - Open platform (bigbasket, blinkit, etc.)
  clear            - Clear list
  quit             - Exit
""")
    
    agent = SmartShoppingAgent()
    
    while True:
        try:
            cmd = input("\n🛒 > ").strip()
            
            if not cmd:
                continue
            
            parts = cmd.split(maxsplit=1)
            action = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""
            
            if action == "quit":
                print("Happy shopping! 🛍️")
                break
            
            elif action == "image":
                print(agent.create_list_from_image(arg))
            
            elif action == "text":
                print(agent.create_list_from_text(arg))
            
            elif action == "add":
                print(agent.add_item(arg))
            
            elif action == "list":
                print(agent._format_list() if agent.current_list else "No list yet.")
            
            elif action == "compare":
                print(agent.compare_prices())
            
            elif action == "open":
                print(agent.open_platform(arg))
            
            elif action == "clear":
                agent.current_list = None
                print("✅ List cleared.")
            
            else:
                # Try as item addition
                print(agent.add_item(cmd))
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
