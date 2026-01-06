import sys
import os
import unittest

# Add project root to path
# Add project root to path
# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jarvis.cognitive.semantic_router import get_semantic_router
from jarvis.cognitive import CognitiveAction

class TestSemanticRouter(unittest.TestCase):
    def setUp(self):
        self.router = get_semantic_router()
        
    def test_remember_intent(self):
        """Test implicit memory commands."""
        queries = [
            "store this information",
            "keep a note of this fact",
            "I want you to know that the sky is blue"
        ]
        for q in queries:
            action, conf = self.router.route(q)
            print(f"Query: '{q}' -> {action} ({conf:.2f})")
            self.assertEqual(action, CognitiveAction.REMEMBER, f"Failed for: {q}")
            
    def test_automation_intent(self):
        """Test automation commands."""
        queries = [
            "click on the submit button",
            "launch chrome browser",
            "scroll down the page"
        ]
        for q in queries:
            action, conf = self.router.route(q)
            print(f"Query: '{q}' -> {action} ({conf:.2f})")
            self.assertEqual(action, CognitiveAction.ACT, f"Failed for: {q}")

if __name__ == "__main__":
    unittest.main()
