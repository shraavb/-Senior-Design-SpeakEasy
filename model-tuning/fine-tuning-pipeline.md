# Model Fine-tuning Pipeline

## Overview
This pipeline fine-tunes language models on colloquial conversation data to make interactions more natural and engaging.

## Setup

### 1. Environment Setup
```bash
# Install required packages
pip install transformers datasets torch accelerate peft
pip install wandb  # for experiment tracking
```

### 2. Data Preparation
```python
# data_preparation.py
import pandas as pd
from datasets import Dataset
from transformers import AutoTokenizer

def prepare_colloquial_dataset():
    """
    Prepare colloquial conversation data for fine-tuning
    """
    # Load conversation data from Supabase
    conversations = load_conversation_data()
    
    # Filter for high-quality conversations
    quality_conversations = filter_quality_conversations(conversations)
    
    # Create training format
    training_data = format_for_training(quality_conversations)
    
    return Dataset.from_pandas(training_data)

def filter_quality_conversations(conversations):
    """
    Filter conversations based on quality metrics
    """
    return conversations[
        (conversations['userRating'] >= 4) |  # High user ratings
        (conversations['responseLength'] > 10) |  # Substantial responses
        (conversations['followUpQuestions'] > 0)  # Engaging responses
    ]

def format_for_training(conversations):
    """
    Format conversations for instruction tuning
    """
    formatted_data = []
    
    for _, row in conversations.iterrows():
        # Create instruction-following format
        instruction = f"Respond naturally in {row['language']} for a {row['level']} learner in a {row['scenario']} context."
        
        formatted_data.append({
            'instruction': instruction,
            'input': row['userMessage'],
            'output': row['aiResponse'],
            'context': {
                'language': row['language'],
                'level': row['level'],
                'scenario': row['scenario']
            }
        })
    
    return pd.DataFrame(formatted_data)
```

### 3. Model Fine-tuning
```python
# fine_tuning.py
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    TrainingArguments, 
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, TaskType
import torch

class ColloquialModelTrainer:
    def __init__(self, model_name="microsoft/DialoGPT-medium"):
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        
        # Add padding token if not present
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
    
    def setup_lora(self):
        """
        Setup LoRA (Low-Rank Adaptation) for efficient fine-tuning
        """
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=16,  # Rank
            lora_alpha=32,
            lora_dropout=0.1,
            target_modules=["q_proj", "v_proj", "k_proj", "o_proj"]
        )
        
        self.model = get_peft_model(self.model, lora_config)
        return self.model
    
    def prepare_dataset(self, dataset):
        """
        Tokenize and prepare dataset for training
        """
        def tokenize_function(examples):
            # Combine instruction, input, and output
            texts = []
            for i in range(len(examples['instruction'])):
                text = f"Instruction: {examples['instruction'][i]}\nInput: {examples['input'][i]}\nOutput: {examples['output'][i]}"
                texts.append(text)
            
            return self.tokenizer(
                texts,
                truncation=True,
                padding=True,
                max_length=512,
                return_tensors="pt"
            )
        
        return dataset.map(tokenize_function, batched=True)
    
    def train(self, train_dataset, eval_dataset=None):
        """
        Train the model on colloquial data
        """
        training_args = TrainingArguments(
            output_dir="./colloquial-model",
            num_train_epochs=3,
            per_device_train_batch_size=4,
            per_device_eval_batch_size=4,
            warmup_steps=100,
            weight_decay=0.01,
            logging_dir="./logs",
            logging_steps=10,
            evaluation_strategy="steps" if eval_dataset else "no",
            eval_steps=100 if eval_dataset else None,
            save_steps=500,
            save_total_limit=2,
            load_best_model_at_end=True if eval_dataset else False,
            report_to="wandb",  # Log to Weights & Biases
        )
        
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False
        )
        
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=data_collator,
        )
        
        trainer.train()
        return trainer
```

### 4. Model Evaluation
```python
# evaluation.py
import torch
from transformers import pipeline
import pandas as pd

class ModelEvaluator:
    def __init__(self, model_path):
        self.model = AutoModelForCausalLM.from_pretrained(model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.generator = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            device=0 if torch.cuda.is_available() else -1
        )
    
    def evaluate_naturalness(self, test_cases):
        """
        Evaluate how natural the responses are
        """
        results = []
        
        for case in test_cases:
            prompt = f"Instruction: {case['instruction']}\nInput: {case['input']}\nOutput:"
            
            response = self.generator(
                prompt,
                max_length=len(prompt.split()) + 50,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True
            )[0]['generated_text']
            
            # Extract just the output part
            output = response.split("Output:")[-1].strip()
            
            results.append({
                'input': case['input'],
                'expected': case['expected'],
                'generated': output,
                'naturalness_score': self.calculate_naturalness_score(output)
            })
        
        return pd.DataFrame(results)
    
    def calculate_naturalness_score(self, text):
        """
        Calculate naturalness score based on various metrics
        """
        # Simple heuristics for naturalness
        score = 0
        
        # Check for conversational markers
        conversational_markers = ['yeah', 'sure', 'okay', 'right', 'exactly', 'totally']
        if any(marker in text.lower() for marker in conversational_markers):
            score += 0.2
        
        # Check for contractions
        contractions = ["don't", "won't", "can't", "isn't", "aren't", "wasn't", "weren't"]
        if any(contraction in text.lower() for contraction in contractions):
            score += 0.2
        
        # Check for questions (engaging)
        if '?' in text:
            score += 0.2
        
        # Check for appropriate length (not too short, not too long)
        word_count = len(text.split())
        if 5 <= word_count <= 50:
            score += 0.2
        
        # Check for exclamations (enthusiasm)
        if '!' in text:
            score += 0.1
        
        # Check for informal language
        informal_words = ['cool', 'awesome', 'great', 'nice', 'sweet']
        if any(word in text.lower() for word in informal_words):
            score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0
```

### 5. Deployment Integration
```python
# deploy_model.py
import os
from huggingface_hub import HfApi, Repository

def deploy_to_huggingface(model_path, repo_name):
    """
    Deploy the fine-tuned model to Hugging Face Hub
    """
    api = HfApi()
    
    # Create repository
    api.create_repo(repo_name, exist_ok=True)
    
    # Upload model
    api.upload_folder(
        folder_path=model_path,
        repo_id=repo_name,
        repo_type="model"
    )
    
    print(f"Model deployed to: https://huggingface.co/{repo_name}")

# Usage
if __name__ == "__main__":
    # Train model
    trainer = ColloquialModelTrainer()
    trainer.setup_lora()
    
    dataset = prepare_colloquial_dataset()
    tokenized_dataset = trainer.prepare_dataset(dataset)
    
    trainer.train(tokenized_dataset)
    
    # Deploy model
    deploy_to_huggingface("./colloquial-model", "your-username/speak-easy-colloquial")
```

## Usage Instructions

1. **Collect Data**: Use the data collection function to gather conversation data
2. **Prepare Dataset**: Run `data_preparation.py` to format your data
3. **Train Model**: Run `fine_tuning.py` to fine-tune the model
4. **Evaluate**: Use `evaluation.py` to test model performance
5. **Deploy**: Upload to Hugging Face Hub for use in your app

## Next Steps
1. Set up data collection in your app
2. Gather initial dataset
3. Run fine-tuning pipeline
4. Integrate tuned model into conversation flow
