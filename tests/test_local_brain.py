import sys
import os
import unittest

# Add project root to path (one level up from this file)
# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jarvis.llm.cognitive_brain import CognitiveBrain

class TestLocalBrain(unittest.TestCase):
    def setUp(self):
        self.brain = CognitiveBrain()
        # Disable confirmation for test
        self.brain.confirmation_callback = None
        
    def test_init(self):
        """Test that brain initializes without Gemini."""
        self.assertFalse(hasattr(self.brain, 'gemini_model'), "Gemini model should not exist")
        
    def test_status(self):
        """Test status dictionary keys."""
        status = self.brain.get_status()
        self.assertIn("ollama_available", status)
        self.assertNotIn("gemini_available", status)
        self.assertEqual(status["active_mode"], "ollama" if status["ollama_available"] else "none")

if __name__ == "__main__":
    unittest.main()
