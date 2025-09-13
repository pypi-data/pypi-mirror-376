import re
import nltk
from typing import List, Optional
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.tag import pos_tag
from nltk.chunk import ne_chunk
from nltk.tree import Tree


class TextPreprocessor:
    def __init__(self):
        self._download_nltk_data()
        try:
            self.stop_words = set(stopwords.words('english'))
        except LookupError:
            self.stop_words = set()
    
    def _download_nltk_data(self):
        required_data = ['punkt', 'averaged_perceptron_tagger', 'maxent_ne_chunker', 'words', 'stopwords']
        for data in required_data:
            try:
                nltk.data.find(f'tokenizers/{data}')
            except LookupError:
                try:
                    nltk.download(data, quiet=True)
                except:
                    pass
    
    def clean_text(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\.\?\!]', '', text)
        return text.strip()
    
    def segment_sentences(self, text: str) -> List[str]:
        text = self.clean_text(text)
        try:
            sentences = sent_tokenize(text)
        except:
            sentences = text.split('. ')
        
        return [sent.strip() for sent in sentences if len(sent.strip()) > 10]
    
    def extract_entities(self, text: str) -> List[str]:
        entities = []
        
        try:
            tokens = word_tokenize(text)
            pos_tags = pos_tag(tokens)
            tree = ne_chunk(pos_tags)
            
            for subtree in tree:
                if isinstance(subtree, Tree):
                    entity_name = ' '.join([token for token, pos in subtree.leaves()])
                    entities.append(entity_name)
        except:
            pass
        
        simple_entities = self._extract_simple_entities(text)
        entities.extend(simple_entities)
        
        return list(set(entities))
    
    def _extract_simple_entities(self, text: str) -> List[str]:
        entities = []
        
        capitalized_words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        entities.extend(capitalized_words)
        
        years = re.findall(r'\b(19|20)\d{2}\b', text)
        entities.extend(years)
        
        numbers = re.findall(r'\b\d+\b', text)
        entities.extend([num for num in numbers if len(num) <= 4])
        
        return entities
    
    def extract_keywords(self, text: str) -> List[str]:
        try:
            tokens = word_tokenize(text.lower())
            tokens = [token for token in tokens if token.isalpha() and token not in self.stop_words]
            
            pos_tags = pos_tag(tokens)
            keywords = [word for word, pos in pos_tags if pos.startswith(('NN', 'VB', 'JJ'))]
            
            return list(set(keywords))
        except:
            words = text.lower().split()
            return [word for word in words if word.isalpha() and len(word) > 3]