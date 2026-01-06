import sys
import os
import unittest

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm.cognitive_brain import CognitiveBrain
import llm.cognitive_brain

# Mock for execute_tool
def mock_execute_tool(name, args):
    return f"Executed {name} with {args}"

# Patch the execute_tool
llm.cognitive_brain.execute_tool = mock_execute_tool

class TestJSONParsing(unittest.TestCase):
    def setUp(self):
        self.brain = CognitiveBrain()
        # Disable confirm callback for tests
        self.brain.confirmation_callback = None

    def test_clean_json(self):
        response = """{
            "thought": "User wants to open chrome",
            "tool": "open_application",
            "args": {"app_name": "chrome"},
            "response": "Opening Chrome."
        }"""
        results = self.brain._extract_and_execute_tools(response)
        self.assertEqual(len(results), 1)
        self.assertIn("Executed open_application", results[0])
        self.assertIn("'app_name': 'chrome'", results[0])

    def test_markdown_json(self):
        response = """Here is the plan:
        ```json
        {
            "thought": "Type hello",
            "tool": "type_text",
            "args": {"text": "hello world"},
            "response": "Typing it."
        }
        ```
        """
        results = self.brain._extract_and_execute_tools(response)
        self.assertEqual(len(results), 1)
        self.assertIn("Executed type_text", results[0])
        self.assertIn("'text': 'hello world'", results[0])

    def test_special_characters(self):
        # Test quotes and special chars which broke regex
        response = """{
            "thought": "Type tricky string",
            "tool": "type_text",
            "args": {"text": "Dont stop! User said \\"Hello\\""},
            "response": "Typing."
        }"""
        results = self.brain._extract_and_execute_tools(response)
        self.assertEqual(len(results), 1)
        self.assertIn("Executed type_text", results[0])
        # Verify the text content is preserved correctly
        self.assertTrue("Dont stop!" in results[0])
        self.assertTrue('Hello' in results[0])

    def test_multi_tool(self):
        response = """{
            "thought": "Multi step",
            "response": "Doing both.",
            "tools": [
                {"name": "open_application", "args": {"app_name": "notepad"}},
                {"name": "type_text", "args": {"text": "notes"}}
            ]
        }"""
        results = self.brain._extract_and_execute_tools(response)
        self.assertEqual(len(results), 2)
        self.assertIn("Executed open_application", results[0])
        self.assertIn("Executed type_text", results[1])

if __name__ == '__main__':
    unittest.main()
