import unittest
from apicrusher_lite import Router

class TestRouter(unittest.TestCase):
    
    def setUp(self):
        self.router = Router()
    
    def test_simple_query_routing(self):
        """Test that simple queries get routed to cheaper models"""
        simple_messages = [{"role": "user", "content": "What's 2+2?"}]
        result = self.router.route("gpt-5", simple_messages)
        self.assertEqual(result, "gpt-5-nano")
    
    def test_complex_query_no_routing(self):
        """Test that complex queries keep original model"""
        complex_messages = [{"role": "user", "content": """
        Analyze this complex Python code for security vulnerabilities,
        explain the issues in detail, and provide secure alternatives
        with comprehensive documentation and examples.
        """}]
        result = self.router.route("gpt-5", complex_messages)
        self.assertEqual(result, "gpt-5")
    
    def test_complexity_analysis(self):
        """Test complexity scoring"""
        simple = [{"role": "user", "content": "Hi"}]
        complex = [{"role": "user", "content": "```python\ndef analyze():\n    pass\n```\nExplain this code"}]
        
        self.assertLess(self.router.analyze_complexity(simple), 0.3)
        self.assertGreater(self.router.analyze_complexity(complex), 0.5)

if __name__ == '__main__':
    unittest.main()
