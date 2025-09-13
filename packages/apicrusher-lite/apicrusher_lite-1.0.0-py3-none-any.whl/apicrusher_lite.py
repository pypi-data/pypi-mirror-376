# apicrusher_lite.py
# Path: apicrusher_lite.py
# Basic open-source router for AI model optimization

class Router:
    """Simple complexity-based router for AI models"""
    
    def __init__(self):
        # September 2025 model mappings
        self.model_map = {
            # OpenAI
            "gpt-5": "gpt-5-nano",
            "gpt-5-turbo": "gpt-5-nano",
            "gpt-4": "gpt-4o-mini",
            "gpt-4-turbo": "gpt-4o-mini",
            "gpt-4o": "gpt-4o-mini",
            
            # Anthropic
            "claude-opus-4.1-20250805": "claude-3-haiku-20240307",
            "claude-opus-4-20250805": "claude-3-haiku-20240307",
            "claude-sonnet-4-20250222": "claude-3-haiku-20240307",
            "claude-3-opus-20240229": "claude-3-haiku-20240307",
            
            # Google
            "gemini-2.5-pro": "gemini-2.5-flash-lite",
            "gemini-2.0-pro": "gemini-2.0-flash",
            
            # xAI
            "grok-4": "grok-3-mini",
            "grok-3": "grok-3-mini",
        }
    
    def analyze_complexity(self, messages):
        """
        Basic complexity analysis
        Returns float between 0.0 (simple) and 1.0 (complex)
        """
        text = str(messages).lower()
        complexity = 0.1  # Base complexity
        
        # Length check
        if len(text) > 500:
            complexity += 0.2
        if len(text) > 1500:
            complexity += 0.2
        
        # Code detection
        if "```" in text or "def " in text or "function" in text:
            complexity += 0.3
        
        # Reasoning keywords
        reasoning_words = ['analyze', 'explain', 'compare', 'evaluate', 
                          'summarize', 'complex', 'detailed', 'comprehensive']
        if any(word in text for word in reasoning_words):
            complexity += 0.3
        
        # Data processing
        if any(word in text for word in ['json', 'csv', 'parse', 'extract']):
            complexity += 0.2
        
        return min(complexity, 1.0)
    
    def route(self, model, messages):
        """
        Route to appropriate model based on complexity
        Returns optimized model name
        """
        complexity = self.analyze_complexity(messages)
        
        # Simple tasks go to cheaper models
        if complexity < 0.3 and model in self.model_map:
            return self.model_map[model]
        
        # Complex tasks keep original model
        return model
