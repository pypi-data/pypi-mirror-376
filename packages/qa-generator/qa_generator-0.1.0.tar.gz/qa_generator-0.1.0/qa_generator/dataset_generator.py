"""
Dataset generation module for creating training-ready QA datasets that can be uploaded to Hugging Face.
"""

import json
import csv
import os
import random
import uuid
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Union
from pathlib import Path
import logging

from .generator import QAGenerator
from .llm_generator import LLMQAGenerator
from .preprocessor import TextPreprocessor


class DatasetGenerator:
    """
    Generates comprehensive QA datasets suitable for training and Hugging Face upload.
    """
    
    def __init__(self, 
                 rule_based_generator: Optional[QAGenerator] = None,
                 llm_generator: Optional[LLMQAGenerator] = None,
                 output_dir: str = "dataset_output"):
        """
        Initialize the dataset generator.
        
        Args:
            rule_based_generator: QAGenerator instance for rule-based generation
            llm_generator: LLMQAGenerator instance for LLM-based generation
            output_dir: Directory to save generated datasets
        """
        self.rule_generator = rule_based_generator or QAGenerator()
        self.llm_generator = llm_generator
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Default text sources for diverse QA generation
        self.text_sources = self._get_default_text_sources()
    
    def _get_default_text_sources(self) -> List[Dict[str, str]]:
        """Get diverse text sources covering multiple domains."""
        return [
            {
                "domain": "technology",
                "text": """
                Artificial Intelligence (AI) is revolutionizing industries worldwide. Machine learning algorithms 
                enable computers to learn from data without explicit programming. Deep learning uses neural networks 
                with multiple layers to process complex patterns. Natural language processing helps computers understand 
                human language. Computer vision allows machines to interpret visual information. Robotics combines AI 
                with mechanical engineering to create autonomous systems.
                """
            },
            {
                "domain": "science",
                "text": """
                DNA contains the genetic instructions for all living organisms. Photosynthesis converts sunlight into 
                chemical energy in plants. The periodic table organizes chemical elements by atomic number. Gravity is 
                a fundamental force that attracts objects with mass. Evolution explains how species change over time 
                through natural selection. Quantum mechanics describes the behavior of matter at atomic scales.
                """
            },
            {
                "domain": "history",
                "text": """
                The Renaissance period marked a cultural rebirth in Europe from the 14th to 17th centuries. 
                The Industrial Revolution transformed manufacturing and transportation in the 18th and 19th centuries. 
                World War II lasted from 1939 to 1945 and involved most nations. The American Civil War occurred 
                from 1861 to 1865. Ancient Egypt built pyramids as tombs for pharaohs. The Roman Empire controlled 
                much of Europe, Africa, and Asia for centuries.
                """
            },
            {
                "domain": "geography",
                "text": """
                The Amazon Rainforest is the largest tropical rainforest in the world, located in South America. 
                Mount Everest is the highest mountain peak on Earth at 29,029 feet. The Pacific Ocean is the largest 
                and deepest ocean. The Sahara Desert covers most of North Africa. The Nile River is the longest river 
                in the world. Antarctica is the coldest and driest continent.
                """
            },
            {
                "domain": "literature",
                "text": """
                William Shakespeare wrote famous plays like Hamlet, Romeo and Juliet, and Macbeth during the 
                Elizabethan era. Jane Austen authored Pride and Prejudice in 1813. Mark Twain wrote The Adventures 
                of Tom Sawyer and Adventures of Huckleberry Finn. Charles Dickens created memorable characters in 
                novels like Oliver Twist and A Christmas Carol. George Orwell wrote dystopian novels 1984 and Animal Farm.
                """
            },
            {
                "domain": "mathematics",
                "text": """
                Algebra uses symbols and letters to represent numbers in equations. Geometry studies shapes, sizes, 
                and properties of space. Calculus deals with rates of change and accumulation. Statistics analyzes 
                and interprets numerical data. Probability measures the likelihood of events occurring. Prime numbers 
                are natural numbers greater than 1 that have no positive divisors other than 1 and themselves.
                """
            },
            {
                "domain": "health",
                "text": """
                Regular exercise improves cardiovascular health and strengthens muscles. A balanced diet provides 
                essential nutrients for proper body function. Vaccines help prevent infectious diseases by building immunity. 
                Sleep is crucial for physical and mental recovery. Stress management techniques include meditation and 
                deep breathing. Preventive healthcare involves regular check-ups and screenings to detect problems early.
                """
            },
            {
                "domain": "environment",
                "text": """
                Climate change refers to long-term shifts in global temperatures and weather patterns. Renewable energy 
                sources include solar, wind, and hydroelectric power. Deforestation reduces the number of trees and 
                affects biodiversity. Recycling helps reduce waste and conserve natural resources. Carbon emissions 
                from fossil fuels contribute to greenhouse gas accumulation. Sustainable development meets present 
                needs without compromising future generations.
                """
            }
        ]
    
    def add_text_source(self, domain: str, text: str):
        """Add a new text source for QA generation."""
        self.text_sources.append({"domain": domain, "text": text})
    
    def generate_comprehensive_dataset(self, 
                                     total_samples: int = 1000,
                                     train_split: float = 0.8,
                                     val_split: float = 0.1,
                                     test_split: float = 0.1,
                                     include_metadata: bool = True,
                                     use_llm: bool = False,
                                     difficulty_levels: List[str] = None) -> Dict[str, List[Dict]]:
        """
        Generate a comprehensive QA dataset with train/validation/test splits.
        
        Args:
            total_samples: Total number of QA pairs to generate
            train_split: Proportion for training set
            val_split: Proportion for validation set  
            test_split: Proportion for test set
            include_metadata: Whether to include metadata about generation method
            use_llm: Whether to use LLM generator (requires llm_generator to be set)
            difficulty_levels: List of difficulty levels for LLM generation
            
        Returns:
            Dictionary with train, validation, and test splits
        """
        if abs(train_split + val_split + test_split - 1.0) > 0.001:
            raise ValueError("Split proportions must sum to 1.0")
        
        if difficulty_levels is None:
            difficulty_levels = ["easy", "medium", "hard"]
        
        self.logger.info(f"Generating {total_samples} QA pairs...")
        
        all_qa_pairs = []
        samples_per_domain = total_samples // len(self.text_sources)
        
        for source in self.text_sources:
            domain = source["domain"]
            text = source["text"]
            
            self.logger.info(f"Processing {domain} domain...")
            
            domain_pairs = []
            
            # Generate with rule-based method
            rule_pairs = self.rule_generator.generate(text, max_pairs=samples_per_domain // 2)
            for question, answer in rule_pairs:
                qa_item = {
                    "id": str(uuid.uuid4()),
                    "question": question,
                    "answer": answer,
                    "domain": domain,
                    "generation_method": "rule_based",
                    "difficulty": self._infer_difficulty_rule_based(question, answer),
                    "source_text": text.strip()
                }
                if include_metadata:
                    qa_item.update({
                        "generated_at": datetime.now().isoformat(),
                        "generator_version": "rule_based_v1.0"
                    })
                domain_pairs.append(qa_item)
            
            # Generate with LLM method if available
            if use_llm and self.llm_generator:
                try:
                    remaining_samples = samples_per_domain - len(domain_pairs)
                    samples_per_difficulty = remaining_samples // len(difficulty_levels)
                    
                    for difficulty in difficulty_levels:
                        llm_pairs = self.llm_generator.generate(
                            text, 
                            max_pairs=samples_per_difficulty, 
                            difficulty=difficulty
                        )
                        for question, answer in llm_pairs:
                            qa_item = {
                                "id": str(uuid.uuid4()),
                                "question": question,
                                "answer": answer,
                                "domain": domain,
                                "generation_method": "llm_based",
                                "difficulty": difficulty,
                                "source_text": text.strip()
                            }
                            if include_metadata:
                                qa_item.update({
                                    "generated_at": datetime.now().isoformat(),
                                    "generator_version": "llm_based_v1.0"
                                })
                            domain_pairs.append(qa_item)
                except Exception as e:
                    self.logger.warning(f"LLM generation failed for {domain}: {e}")
            
            all_qa_pairs.extend(domain_pairs)
        
        # Shuffle and split the data
        random.shuffle(all_qa_pairs)
        
        # Ensure we have the requested number of samples
        all_qa_pairs = all_qa_pairs[:total_samples]
        
        train_size = int(len(all_qa_pairs) * train_split)
        val_size = int(len(all_qa_pairs) * val_split)
        
        dataset_splits = {
            "train": all_qa_pairs[:train_size],
            "validation": all_qa_pairs[train_size:train_size + val_size],
            "test": all_qa_pairs[train_size + val_size:]
        }
        
        self.logger.info(f"Dataset generated: {len(dataset_splits['train'])} train, "
                        f"{len(dataset_splits['validation'])} validation, "
                        f"{len(dataset_splits['test'])} test samples")
        
        return dataset_splits
    
    def _infer_difficulty_rule_based(self, question: str, answer: str) -> str:
        """Infer difficulty level for rule-based questions."""
        if len(answer.split()) <= 10:
            return "easy"
        elif len(answer.split()) <= 25:
            return "medium"
        else:
            return "hard"
    
    def export_to_huggingface_format(self, dataset_splits: Dict[str, List[Dict]], 
                                   dataset_name: str = "qa_dataset",
                                   format_type: str = "json") -> Dict[str, str]:
        """
        Export dataset in Hugging Face compatible format.
        
        Args:
            dataset_splits: Dictionary with train/validation/test splits
            dataset_name: Name for the dataset
            format_type: Export format ('json', 'csv', 'parquet')
            
        Returns:
            Dictionary with file paths for each split
        """
        export_dir = self.output_dir / dataset_name
        export_dir.mkdir(exist_ok=True)
        
        file_paths = {}
        
        for split_name, data in dataset_splits.items():
            if format_type == "json":
                file_path = export_dir / f"{split_name}.json"
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            
            elif format_type == "csv":
                file_path = export_dir / f"{split_name}.csv"
                if data:
                    with open(file_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=data[0].keys())
                        writer.writeheader()
                        writer.writerows(data)
            
            elif format_type == "parquet":
                try:
                    import pandas as pd
                    file_path = export_dir / f"{split_name}.parquet"
                    df = pd.DataFrame(data)
                    df.to_parquet(file_path, index=False)
                except ImportError:
                    raise ImportError("pandas is required for parquet export")
            
            else:
                raise ValueError(f"Unsupported format: {format_type}")
            
            file_paths[split_name] = str(file_path)
            self.logger.info(f"Exported {split_name} split to {file_path}")
        
        # Create dataset metadata
        self._create_dataset_metadata(export_dir, dataset_splits)
        
        return file_paths
    
    def _create_dataset_metadata(self, export_dir: Path, dataset_splits: Dict[str, List[Dict]]):
        """Create comprehensive dataset metadata for Hugging Face."""
        
        # Calculate statistics
        total_samples = sum(len(split) for split in dataset_splits.values())
        domains = set()
        generation_methods = set()
        difficulties = set()
        
        for split_data in dataset_splits.values():
            for item in split_data:
                domains.add(item.get("domain", "unknown"))
                generation_methods.add(item.get("generation_method", "unknown"))
                difficulties.add(item.get("difficulty", "unknown"))
        
        # Create dataset card (README.md)
        readme_content = f"""# QA Dataset

## Dataset Description
This is a question-answering dataset generated using both rule-based and LLM-based methods across multiple domains.

## Dataset Statistics
- **Total samples**: {total_samples}
- **Training samples**: {len(dataset_splits.get('train', []))}
- **Validation samples**: {len(dataset_splits.get('validation', []))}
- **Test samples**: {len(dataset_splits.get('test', []))}

## Domains Covered
{', '.join(sorted(domains))}

## Generation Methods
{', '.join(sorted(generation_methods))}

## Difficulty Levels
{', '.join(sorted(difficulties))}

## Dataset Structure
Each example contains:
- `id`: Unique identifier
- `question`: The question text
- `answer`: The answer text
- `domain`: Subject domain
- `generation_method`: How the QA pair was generated
- `difficulty`: Difficulty level (easy/medium/hard)
- `source_text`: Original text used for generation

## Usage
```python
from datasets import load_dataset

dataset = load_dataset("path/to/dataset")
print(dataset['train'][0])
```

## Citation
If you use this dataset, please cite:
```
@misc{{qa_dataset_{datetime.now().year},
  title={{Generated QA Dataset}},
  year={{{datetime.now().year}}},
  note={{Generated using qa-generator package}}
}}
```
"""
        
        with open(export_dir / "README.md", 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        # Create dataset configuration
        config = {
            "dataset_info": {
                "description": "A comprehensive question-answering dataset",
                "features": {
                    "id": {"dtype": "string"},
                    "question": {"dtype": "string"},
                    "answer": {"dtype": "string"},
                    "domain": {"dtype": "string"},
                    "generation_method": {"dtype": "string"},
                    "difficulty": {"dtype": "string"},
                    "source_text": {"dtype": "string"}
                },
                "splits": {
                    split_name: {"num_examples": len(split_data)}
                    for split_name, split_data in dataset_splits.items()
                },
                "download_size": 0,
                "dataset_size": total_samples
            }
        }
        
        with open(export_dir / "dataset_infos.json", 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        
        self.logger.info(f"Created dataset metadata in {export_dir}")
    
    def create_instruction_tuning_format(self, dataset_splits: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """
        Convert QA dataset to instruction tuning format for training language models.
        
        Returns dataset in the format:
        {"instruction": "...", "input": "...", "output": "..."}
        """
        instruction_datasets = {}
        
        instruction_templates = [
            "Answer the following question based on the given context.",
            "Please provide an answer to this question.",
            "Based on the information provided, answer the question.",
            "Given the context, what is the answer to this question?",
            "Please answer the question using the provided information."
        ]
        
        for split_name, data in dataset_splits.items():
            instruction_data = []
            
            for item in data:
                instruction_item = {
                    "instruction": random.choice(instruction_templates),
                    "input": f"Context: {item['source_text']}\n\nQuestion: {item['question']}",
                    "output": item['answer'],
                    "id": item['id'],
                    "domain": item['domain'],
                    "difficulty": item['difficulty']
                }
                instruction_data.append(instruction_item)
            
            instruction_datasets[split_name] = instruction_data
        
        return instruction_datasets
    
    def validate_dataset(self, dataset_splits: Dict[str, List[Dict]]) -> Dict[str, any]:
        """Validate the generated dataset and return quality metrics."""
        validation_results = {
            "total_samples": 0,
            "avg_question_length": 0,
            "avg_answer_length": 0,
            "domain_distribution": {},
            "difficulty_distribution": {},
            "quality_issues": []
        }
        
        all_data = []
        for split_data in dataset_splits.values():
            all_data.extend(split_data)
        
        validation_results["total_samples"] = len(all_data)
        
        if not all_data:
            return validation_results
        
        # Calculate averages
        question_lengths = [len(item['question'].split()) for item in all_data]
        answer_lengths = [len(item['answer'].split()) for item in all_data]
        
        validation_results["avg_question_length"] = sum(question_lengths) / len(question_lengths)
        validation_results["avg_answer_length"] = sum(answer_lengths) / len(answer_lengths)
        
        # Distribution analysis
        for item in all_data:
            domain = item.get('domain', 'unknown')
            difficulty = item.get('difficulty', 'unknown')
            
            validation_results["domain_distribution"][domain] = \
                validation_results["domain_distribution"].get(domain, 0) + 1
            validation_results["difficulty_distribution"][difficulty] = \
                validation_results["difficulty_distribution"].get(difficulty, 0) + 1
            
            # Quality checks
            if len(item['question']) < 10:
                validation_results["quality_issues"].append(f"Short question: {item['id']}")
            if len(item['answer']) < 5:
                validation_results["quality_issues"].append(f"Short answer: {item['id']}")
            if not item['question'].endswith('?'):
                validation_results["quality_issues"].append(f"Question without '?': {item['id']}")
        
        return validation_results