# QA Generator

Generate question-answer pairs from text using rule-based and LLM approaches.

## Installation

```bash
pip install qa-generator
```

## Quick Start

### Rule-based Generation
```python
from qa_generator import QAGenerator

qa_gen = QAGenerator()
text = "Python is a programming language created by Guido van Rossum in 1991."
qa_pairs = qa_gen.generate(text)

for question, answer in qa_pairs:
    print(f"Q: {question}")
    print(f"A: {answer}")
```

### LLM-based Generation
```python
from qa_generator import LLMQAGenerator

qa_gen = LLMQAGenerator(
    api_key="your-api-key",
    model="gpt-3.5-turbo"
)
qa_pairs = qa_gen.generate(text, max_pairs=5, difficulty="medium")
```

### Easy Provider Setup
```python
from qa_generator import create_qa_generator_from_provider

qa_gen = create_qa_generator_from_provider("openai")   # OpenAI
qa_gen = create_qa_generator_from_provider("ollama")   # Local Ollama
qa_gen = create_qa_generator_from_provider("together") # Together AI
```

## Dataset Generation
```python
from qa_generator import DatasetGenerator

dataset_gen = DatasetGenerator()
dataset_splits = dataset_gen.generate_comprehensive_dataset(
    total_samples=1000,
    use_llm=True
)

# Export for Hugging Face
file_paths = dataset_gen.export_to_huggingface_format(
    dataset_splits, 
    dataset_name="my_qa_dataset"
)
```

## Features

- **Rule-based**: Template questions with entity recognition
- **LLM-based**: High-quality questions via language models  
- **Multi-provider**: OpenAI, Ollama, Together, Groq, local endpoints
- **Dataset creation**: Hugging Face compatible exports
- **Difficulty levels**: Easy, medium, hard
- **Question types**: Factual, conceptual, analytical

## Requirements

Python 3.8+, NLTK, requests