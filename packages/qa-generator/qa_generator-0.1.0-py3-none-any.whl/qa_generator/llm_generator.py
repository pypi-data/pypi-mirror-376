import json
import re
import requests
from typing import List, Tuple, Optional, Dict, Any
from .preprocessor import TextPreprocessor


class LLMQAGenerator:
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model: str = "gpt-3.5-turbo",
                 base_url: Optional[str] = None,
                 preprocessor: Optional[TextPreprocessor] = None,
                 timeout: int = 30,
                 **request_kwargs):
        """
        Initialize LLM QA Generator with support for any OpenAI-compatible endpoint.
        
        Args:
            api_key: API key for authentication (can be dummy for local models)
            model: Model name to use
            base_url: Custom endpoint URL (e.g., "http://localhost:8000/v1")
            preprocessor: Text preprocessor instance
            timeout: Request timeout in seconds
            **request_kwargs: Additional arguments for HTTP requests (headers, etc.)
        """
        self.api_key = api_key or "dummy-key"
        self.model = model
        self.base_url = base_url or "https://api.openai.com/v1"
        self.preprocessor = preprocessor or TextPreprocessor()
        self.timeout = timeout
        
        # Ensure base_url ends without trailing slash for consistent URL building
        self.base_url = self.base_url.rstrip('/')
        
        # Default headers
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Update headers with any custom ones provided
        if 'headers' in request_kwargs:
            self.headers.update(request_kwargs.pop('headers'))
        
        # Store additional request kwargs
        self.request_kwargs = request_kwargs
        
    def generate(self, text: str, max_pairs: int = 10, difficulty: str = "medium") -> List[Tuple[str, str]]:
        """Generate QA pairs from text using LLM."""
        chunks = self._chunk_text(text, max_chunk_size=2000)
        all_qa_pairs = []
        
        for chunk in chunks:
            pairs_for_chunk = max(1, max_pairs // len(chunks))
            pairs = self._generate_from_chunk(chunk, pairs_for_chunk, difficulty)
            all_qa_pairs.extend(pairs)
            
            if len(all_qa_pairs) >= max_pairs:
                break
                
        return all_qa_pairs[:max_pairs]
    
    def _chunk_text(self, text: str, max_chunk_size: int = 2000) -> List[str]:
        """Split text into manageable chunks."""
        sentences = self.preprocessor.segment_sentences(text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += " " + sentence
                
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
            
        return chunks
    
    def _generate_from_chunk(self, text: str, num_pairs: int, difficulty: str) -> List[Tuple[str, str]]:
        """Generate QA pairs from a text chunk."""
        difficulty_instructions = {
            "easy": "Generate simple, straightforward questions that can be answered directly from the text.",
            "medium": "Generate questions that require some understanding and inference from the text.",
            "hard": "Generate complex questions that require deep analysis and synthesis of information from the text."
        }
        
        prompt = f"""Generate {num_pairs} high-quality question-answer pairs from the following text. 

{difficulty_instructions.get(difficulty, difficulty_instructions["medium"])}

Text:
{text}

Requirements:
1. Questions should be diverse in type (factual, conceptual, analytical)
2. Answers should be complete and accurate based on the text
3. Avoid yes/no questions
4. Make questions specific and clear
5. Ensure answers are found in or can be inferred from the text

Return the result as a JSON array of objects, each with "question" and "answer" fields.

Example format:
[
    {{"question": "What is the main purpose of...", "answer": "The main purpose is..."}},
    {{"question": "How does... work?", "answer": "It works by..."}}
]
"""
        
        try:
            response_content = self._make_chat_request(prompt)
            return self._parse_qa_response(response_content)
        except Exception as e:
            print(f"Error generating QA pairs: {e}")
            return []
    
    def _make_chat_request(self, prompt: str) -> str:
        """Make a chat completion request to the LLM endpoint."""
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system", 
                    "content": "You are an expert at creating educational question-answer pairs from text. Always respond with valid JSON."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        response = requests.post(
            url,
            headers=self.headers,
            json=payload,
            timeout=self.timeout,
            **self.request_kwargs
        )
        
        response.raise_for_status()
        result = response.json()
        
        if 'choices' not in result or not result['choices']:
            raise ValueError("Invalid response format from LLM endpoint")
        
        return result['choices'][0]['message']['content']
    
    def _parse_qa_response(self, content: str) -> List[Tuple[str, str]]:
        """Parse the LLM response to extract QA pairs."""
        # First try to extract JSON
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            try:
                json_str = json_match.group(0)
                qa_data = json.loads(json_str)
                return [(item["question"], item["answer"]) for item in qa_data 
                       if "question" in item and "answer" in item]
            except json.JSONDecodeError:
                pass
        
        # Fallback to manual parsing
        return self._parse_fallback_format(content)
    
    def _parse_fallback_format(self, content: str) -> List[Tuple[str, str]]:
        """Parse non-JSON response formats."""
        qa_pairs = []
        lines = content.split('\n')
        current_question = None
        current_answer = ""
        
        for line in lines:
            line = line.strip()
            if line.startswith('Q:') or line.startswith('Question:'):
                if current_question and current_answer:
                    qa_pairs.append((current_question, current_answer.strip()))
                current_question = line.split(':', 1)[1].strip()
                current_answer = ""
            elif line.startswith('A:') or line.startswith('Answer:'):
                current_answer = line.split(':', 1)[1].strip()
            elif current_answer and line:
                current_answer += " " + line
                
        if current_question and current_answer:
            qa_pairs.append((current_question, current_answer.strip()))
            
        return qa_pairs
    
    def generate_by_type(self, text: str, question_types: List[str], max_pairs: int = 10) -> List[Tuple[str, str]]:
        """Generate QA pairs focusing on specific question types."""
        type_descriptions = {
            "factual": "questions asking for specific facts, names, dates, or definitions",
            "conceptual": "questions asking about concepts, explanations, or meanings", 
            "analytical": "questions requiring analysis, comparison, or evaluation",
            "application": "questions about how to apply or use the information",
            "synthesis": "questions requiring combining multiple pieces of information"
        }
        
        valid_types = [t for t in question_types if t in type_descriptions]
        if not valid_types:
            valid_types = ["factual", "conceptual"]
            
        type_list = ", ".join([f"{t} ({type_descriptions[t]})" for t in valid_types])
        
        prompt = f"""Generate {max_pairs} question-answer pairs from the following text, focusing on these question types:
{type_list}

Text:
{text}

Requirements:
1. Distribute questions across the specified types
2. Make questions clear and specific
3. Ensure answers are accurate and complete
4. Avoid yes/no questions

Return as JSON array with "question", "answer", and "type" fields.
"""
        
        try:
            response_content = self._make_chat_request(prompt)
            return self._parse_qa_response(response_content)
        except Exception as e:
            print(f"Error generating typed QA pairs: {e}")
            return []
    
    def list_models(self) -> List[str]:
        """List available models from the endpoint."""
        try:
            url = f"{self.base_url}/models"
            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.timeout,
                **self.request_kwargs
            )
            response.raise_for_status()
            result = response.json()
            
            if 'data' in result:
                return [model.get('id', 'unknown') for model in result['data']]
            else:
                return []
        except Exception as e:
            print(f"Error listing models: {e}")
            return []