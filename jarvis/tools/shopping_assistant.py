"""
BRO Smart Shopping Assistant
Handles complex tasks like online shopping with intelligent preference gathering.
"""

import os
import sys
import json
import webbrowser
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# =============================================================================
# PRODUCT SPECIFICATIONS
# =============================================================================

PRODUCT_SPECS = {
    "pendrive": {
        "name": "Pen Drive / USB Flash Drive",
        "questions": [
            {
                "key": "capacity",
                "question": "What storage capacity do you need?",
                "options": ["16GB", "32GB", "64GB", "128GB", "256GB", "512GB", "1TB"],
                "default": "64GB"
            },
            {
                "key": "usb_type",
                "question": "Which USB type?",
                "options": ["USB 2.0 (slower, cheaper)", "USB 3.0 (fast)", "USB 3.1/3.2 (fastest)", "USB-C"],
                "default": "USB 3.0 (fast)"
            },
            {
                "key": "brand",
                "question": "Preferred brand?",
                "options": ["SanDisk", "Samsung", "Kingston", "HP", "Transcend", "Any"],
                "default": "Any"
            },
            {
                "key": "budget",
                "question": "What's your budget?",
                "options": ["Under ₹300", "₹300-500", "₹500-1000", "₹1000-2000", "Above ₹2000"],
                "default": "₹500-1000"
            }
        ],
        "search_template": "{brand} {capacity} {usb_type} pendrive"
    },
    
    "laptop": {
        "name": "Laptop",
        "questions": [
            {
                "key": "purpose",
                "question": "What's the primary use?",
                "options": ["Basic/Office work", "Programming/Development", "Gaming", "Video Editing", "Student"],
                "default": "Programming/Development"
            },
            {
                "key": "brand",
                "question": "Preferred brand?",
                "options": ["Apple MacBook", "Dell", "HP", "Lenovo", "ASUS", "Acer", "Any"],
                "default": "Any"
            },
            {
                "key": "ram",
                "question": "How much RAM?",
                "options": ["8GB", "16GB", "32GB", "64GB"],
                "default": "16GB"
            },
            {
                "key": "budget",
                "question": "Budget range?",
                "options": ["Under ₹40,000", "₹40,000-60,000", "₹60,000-80,000", "₹80,000-1,00,000", "Above ₹1,00,000"],
                "default": "₹60,000-80,000"
            }
        ],
        "search_template": "{brand} laptop {ram} RAM {purpose}"
    },
    
    "headphones": {
        "name": "Headphones / Earbuds",
        "questions": [
            {
                "key": "type",
                "question": "What type do you prefer?",
                "options": ["Over-ear headphones", "On-ear headphones", "TWS earbuds", "Wired earphones", "Neckband"],
                "default": "TWS earbuds"
            },
            {
                "key": "feature",
                "question": "Must-have feature?",
                "options": ["Active Noise Cancellation", "Long battery life", "Gaming (low latency)", "Bass heavy", "Microphone quality"],
                "default": "Active Noise Cancellation"
            },
            {
                "key": "brand",
                "question": "Preferred brand?",
                "options": ["Sony", "JBL", "boAt", "Samsung", "Apple AirPods", "OnePlus", "Any"],
                "default": "Any"
            },
            {
                "key": "budget",
                "question": "Budget?",
                "options": ["Under ₹1,000", "₹1,000-3,000", "₹3,000-5,000", "₹5,000-10,000", "Above ₹10,000"],
                "default": "₹1,000-3,000"
            }
        ],
        "search_template": "{brand} {type} {feature}"
    },
    
    "phone": {
        "name": "Smartphone",
        "questions": [
            {
                "key": "brand",
                "question": "Preferred brand?",
                "options": ["Samsung", "Apple iPhone", "OnePlus", "Xiaomi/Redmi", "Realme", "Vivo", "OPPO", "Any"],
                "default": "Any"
            },
            {
                "key": "priority",
                "question": "What's most important?",
                "options": ["Camera quality", "Gaming performance", "Battery life", "Display quality", "5G support"],
                "default": "Camera quality"
            },
            {
                "key": "budget",
                "question": "Budget range?",
                "options": ["Under ₹15,000", "₹15,000-25,000", "₹25,000-40,000", "₹40,000-60,000", "Above ₹60,000"],
                "default": "₹25,000-40,000"
            }
        ],
        "search_template": "{brand} smartphone {priority} {budget}"
    },
    
    "mouse": {
        "name": "Mouse",
        "questions": [
            {
                "key": "type",
                "question": "Wired or wireless?",
                "options": ["Wired", "Wireless (USB dongle)", "Bluetooth", "Wireless + Bluetooth"],
                "default": "Wireless (USB dongle)"
            },
            {
                "key": "purpose",
                "question": "Primary use?",
                "options": ["Office/General", "Gaming", "Design/Creative"],
                "default": "Office/General"
            },
            {
                "key": "brand",
                "question": "Preferred brand?",
                "options": ["Logitech", "Razer", "HP", "Dell", "Any"],
                "default": "Logitech"
            },
            {
                "key": "budget",
                "question": "Budget?",
                "options": ["Under ₹500", "₹500-1,000", "₹1,000-2,000", "Above ₹2,000"],
                "default": "₹500-1,000"
            }
        ],
        "search_template": "{brand} {type} {purpose} mouse"
    },
    
    "keyboard": {
        "name": "Keyboard",
        "questions": [
            {
                "key": "type",
                "question": "What type?",
                "options": ["Membrane (quiet, cheap)", "Mechanical (clicky)", "Mechanical (silent)", "Wireless"],
                "default": "Mechanical (clicky)"
            },
            {
                "key": "layout",
                "question": "Layout preference?",
                "options": ["Full-size (with numpad)", "Tenkeyless (TKL)", "60% compact", "75% compact"],
                "default": "Full-size (with numpad)"
            },
            {
                "key": "brand",
                "question": "Preferred brand?",
                "options": ["Logitech", "Razer", "Keychron", "Corsair", "Any"],
                "default": "Any"
            },
            {
                "key": "budget",
                "question": "Budget?",
                "options": ["Under ₹1,000", "₹1,000-3,000", "₹3,000-5,000", "Above ₹5,000"],
                "default": "₹1,000-3,000"
            }
        ],
        "search_template": "{brand} {type} keyboard {layout}"
    }
}

# Shopping sites
SHOPPING_SITES = {
    "amazon": "https://www.amazon.in/s?k=",
    "flipkart": "https://www.flipkart.com/search?q=",
    "croma": "https://www.croma.com/searchB?q=",
}


# =============================================================================
# SHOPPING ASSISTANT
# =============================================================================

class ShoppingAssistant:
    """Interactive shopping assistant that gathers preferences and searches."""
    
    def __init__(self):
        self.current_product = None
        self.preferences = {}
        self.current_question = 0
        
    def start_shopping(self, product: str) -> str:
        """Start a new shopping session."""
        product_lower = product.lower().strip()
        
        # Find matching product
        matched_product = None
        for key, spec in PRODUCT_SPECS.items():
            if key in product_lower or product_lower in key:
                matched_product = key
                break
            if product_lower in spec["name"].lower():
                matched_product = key
                break
        
        if not matched_product:
            available = ", ".join(PRODUCT_SPECS.keys())
            return f"""I don't have specifications for '{product}' yet.

Available products I can help with:
{available}

Or tell me what you're looking for and I'll do a general search!"""
        
        self.current_product = matched_product
        self.preferences = {}
        self.current_question = 0
        
        spec = PRODUCT_SPECS[matched_product]
        first_q = spec["questions"][0]
        
        return self._format_question(spec["name"], first_q)
    
    def _format_question(self, product_name: str, question: dict) -> str:
        """Format a question with options."""
        output = f"🛒 Shopping for: {product_name}\n\n"
        output += f"❓ {question['question']}\n\n"
        
        for i, opt in enumerate(question["options"], 1):
            if opt == question["default"]:
                output += f"  {i}. {opt} ⭐ (recommended)\n"
            else:
                output += f"  {i}. {opt}\n"
        
        output += f"\n💡 Reply with a number (1-{len(question['options'])}) or type your preference."
        return output
    
    def answer(self, response: str) -> str:
        """Process user's answer and continue or complete."""
        if not self.current_product:
            return "No shopping session active. Say 'shop for [product]' to start."
        
        spec = PRODUCT_SPECS[self.current_product]
        questions = spec["questions"]
        current_q = questions[self.current_question]
        
        # Parse response
        response = response.strip()
        if response.isdigit():
            idx = int(response) - 1
            if 0 <= idx < len(current_q["options"]):
                answer = current_q["options"][idx]
            else:
                answer = current_q["default"]
        elif response.lower() in ["skip", "default", "any", ""]:
            answer = current_q["default"]
        else:
            answer = response
        
        # Store answer
        self.preferences[current_q["key"]] = answer
        
        # Move to next question or complete
        self.current_question += 1
        
        if self.current_question < len(questions):
            next_q = questions[self.current_question]
            return self._format_question(spec["name"], next_q)
        else:
            return self._generate_results()
    
    def _generate_results(self) -> str:
        """Generate search results based on preferences."""
        spec = PRODUCT_SPECS[self.current_product]
        
        # Build search query
        search_terms = spec["search_template"].format(**self.preferences)
        search_terms = search_terms.replace("Any", "").strip()
        search_terms = " ".join(search_terms.split())  # Clean extra spaces
        
        # Generate summary
        output = f"""✅ Perfect! Here's what I found based on your preferences:

🛒 **{spec['name']}**

📋 **Your Requirements:**
"""
        for key, value in self.preferences.items():
            output += f"  • {key.replace('_', ' ').title()}: {value}\n"
        
        output += f"\n🔍 **Search Query:** `{search_terms}`\n\n"
        output += "🛍️ **Shop Now:**\n"
        
        # Generate links
        encoded_query = search_terms.replace(" ", "+")
        for site, base_url in SHOPPING_SITES.items():
            url = base_url + encoded_query
            output += f"  • [{site.title()}]({url})\n"
        
        output += "\n💡 Shall I open any of these in your browser?"
        
        # Reset session
        self.current_product = None
        self.preferences = {}
        self.current_question = 0
        
        return output
    
    def quick_search(self, query: str, site: str = "amazon") -> str:
        """Quick search without preferences."""
        encoded = query.replace(" ", "+")
        url = SHOPPING_SITES.get(site, SHOPPING_SITES["amazon"]) + encoded
        
        webbrowser.open(url)
        return f"🛒 Opened {site.title()} search for: {query}"


# =============================================================================
# TASK PLANNER
# =============================================================================

@dataclass
class Task:
    """A multi-step task."""
    name: str
    steps: List[str]
    current_step: int = 0
    status: str = "pending"
    results: Dict = field(default_factory=dict)


class TaskPlanner:
    """Handles complex multi-step tasks."""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.shopping = ShoppingAssistant()
    
    def create_task(self, task_type: str, details: str = "") -> str:
        """Create a new task based on type."""
        
        if "shop" in task_type.lower() or "buy" in task_type.lower():
            # Extract product from details
            product = details or self._extract_product(task_type)
            return self.shopping.start_shopping(product)
        
        elif "compare" in task_type.lower():
            return self._create_comparison_task(details)
        
        elif "research" in task_type.lower():
            return self._create_research_task(details)
        
        else:
            return f"I can help with:\n• Shopping (say: 'shop for pendrive')\n• Price comparison\n• Product research"
    
    def _extract_product(self, text: str) -> str:
        """Extract product name from text."""
        # Remove common words
        words = text.lower().split()
        skip = {"shop", "for", "buy", "a", "an", "the", "me", "please", "find", "search"}
        product_words = [w for w in words if w not in skip]
        return " ".join(product_words)
    
    def _create_comparison_task(self, products: str) -> str:
        return f"📊 Comparison feature coming soon for: {products}"
    
    def _create_research_task(self, topic: str) -> str:
        return f"🔬 Research feature coming soon for: {topic}"
    
    def answer(self, response: str) -> str:
        """Handle response in current task."""
        if self.shopping.current_product:
            return self.shopping.answer(response)
        return "No active task. Start one with 'shop for [product]'."
    
    def open_link(self, site: str = "amazon", query: str = "") -> str:
        """Open shopping site with current search."""
        return self.shopping.quick_search(query, site)


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_planner = TaskPlanner()

def shop(product: str) -> str:
    """Start shopping for a product."""
    return _planner.create_task("shop", product)

def answer(response: str) -> str:
    """Answer a question in the shopping flow."""
    return _planner.answer(response)

def quick_shop(query: str, site: str = "amazon") -> str:
    """Quick search on a shopping site."""
    return _planner.shopping.quick_search(query, site)

def list_products() -> str:
    """List products with smart specifications."""
    output = "🛒 Products I can help you shop for:\n\n"
    for key, spec in PRODUCT_SPECS.items():
        output += f"  • {spec['name']}\n"
    output += "\nSay: 'shop for [product]' to start!"
    return output


# =============================================================================
# CLI
# =============================================================================

def main():
    """Interactive CLI for shopping assistant."""
    print("\n" + "="*50)
    print("🛒 BRO Shopping Assistant")
    print("="*50)
    print("\nI'll help you find the perfect product!")
    print("Type 'shop for pendrive' or any product to start.")
    print("Type 'quit' to exit.\n")
    
    planner = TaskPlanner()
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["quit", "exit", "bye"]:
                print("Goodbye! Happy shopping! 🛍️")
                break
            
            # Check if it's a new task or continuation
            if any(word in user_input.lower() for word in ["shop", "buy", "find", "search"]):
                product = planner._extract_product(user_input)
                response = planner.create_task("shop", product)
            elif user_input.lower() in ["list", "products", "help"]:
                response = list_products()
            elif planner.shopping.current_product:
                response = planner.answer(user_input)
            else:
                response = "Say 'shop for [product]' to start, or 'list' for available products."
            
            print(f"\nBRO: {response}\n")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    main()
