import re
import random
from typing import List, Tuple, Optional
from .preprocessor import TextPreprocessor


class QAGenerator:
    def __init__(self, preprocessor: Optional[TextPreprocessor] = None):
        self.preprocessor = preprocessor or TextPreprocessor()
        self.question_templates = {
            'what': [
                "What is {entity}?",
                "What does {entity} do?",
                "What are {entity}?",
            ],
            'who': [
                "Who is {entity}?",
                "Who was {entity}?",
                "Who created {entity}?",
            ],
            'when': [
                "When was {entity} created?",
                "When did {entity} happen?",
                "When was {entity}?",
            ],
            'where': [
                "Where is {entity}?",
                "Where was {entity} created?",
                "Where did {entity} happen?",
            ],
            'why': [
                "Why is {entity} important?",
                "Why was {entity} created?",
                "Why does {entity} exist?",
            ],
            'how': [
                "How does {entity} work?",
                "How was {entity} created?",
                "How is {entity} used?",
            ]
        }
    
    def generate(self, text: str, max_pairs: int = 10) -> List[Tuple[str, str]]:
        sentences = self.preprocessor.segment_sentences(text)
        entities = self.preprocessor.extract_entities(text)
        
        qa_pairs = []
        
        for sentence in sentences:
            pairs = self._generate_from_sentence(sentence, entities)
            qa_pairs.extend(pairs)
            
            if len(qa_pairs) >= max_pairs:
                break
        
        return qa_pairs[:max_pairs]
    
    def _generate_from_sentence(self, sentence: str, entities: List[str]) -> List[Tuple[str, str]]:
        qa_pairs = []
        
        sentence_entities = [entity for entity in entities if entity.lower() in sentence.lower()]
        
        for entity in sentence_entities:
            question_type = self._determine_question_type(sentence, entity)
            question = self._generate_question(entity, question_type)
            answer = self._extract_answer(sentence, entity, question_type)
            
            if question and answer:
                qa_pairs.append((question, answer))
        
        if not sentence_entities and len(sentence.split()) > 5:
            question = self._generate_general_question(sentence)
            if question:
                qa_pairs.append((question, sentence.strip()))
        
        return qa_pairs
    
    def _determine_question_type(self, sentence: str, entity: str) -> str:
        sentence_lower = sentence.lower()
        
        if any(word in sentence_lower for word in ['created', 'founded', 'established', 'born']):
            if any(word in sentence_lower for word in ['when', 'in', 'during']):
                return 'when'
            else:
                return 'who'
        
        if any(word in sentence_lower for word in ['is', 'are', 'was', 'were']):
            return 'what'
        
        if any(word in sentence_lower for word in ['where', 'located', 'place']):
            return 'where'
        
        if any(word in sentence_lower for word in ['why', 'because', 'reason']):
            return 'why'
        
        if any(word in sentence_lower for word in ['how', 'method', 'process']):
            return 'how'
        
        return random.choice(['what', 'who', 'when', 'where', 'why', 'how'])
    
    def _generate_question(self, entity: str, question_type: str) -> Optional[str]:
        if question_type not in self.question_templates:
            question_type = 'what'
        
        template = random.choice(self.question_templates[question_type])
        return template.format(entity=entity)
    
    def _extract_answer(self, sentence: str, entity: str, question_type: str) -> Optional[str]:
        sentence = sentence.strip()
        if not sentence.endswith('.'):
            sentence += '.'
        
        if question_type == 'when':
            date_match = re.search(r'\b(in )?(\d{4}|\d{1,2}/\d{1,2}/\d{4}|\d{1,2}-\d{1,2}-\d{4})\b', sentence)
            if date_match:
                return date_match.group(0).strip()
        
        return sentence
    
    def _generate_general_question(self, sentence: str) -> Optional[str]:
        sentence_lower = sentence.lower()
        
        if any(word in sentence_lower for word in ['is', 'are', 'was', 'were']):
            subject = self._extract_subject(sentence)
            if subject:
                return f"What is {subject}?"
        
        if any(word in sentence_lower for word in ['created', 'founded', 'established']):
            return "When was this created?"
        
        if any(word in sentence_lower for word in ['because', 'reason', 'purpose']):
            return "Why is this important?"
        
        return None
    
    def _extract_subject(self, sentence: str) -> Optional[str]:
        words = sentence.split()
        if len(words) < 3:
            return None
        
        verb_indices = []
        for i, word in enumerate(words):
            if word.lower() in ['is', 'are', 'was', 'were']:
                verb_indices.append(i)
        
        if verb_indices:
            verb_idx = verb_indices[0]
            subject_words = words[:verb_idx]
            if subject_words:
                return ' '.join(subject_words)
        
        return words[0] if words else None