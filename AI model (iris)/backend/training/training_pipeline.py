"""
TrainingPipeline — Fine-tuning pipeline for the Jarvis AI model.

Supports:
  - Loading conversation datasets
  - Formatting for fine-tuning (LLaMA, Mistral, etc.)
  - Running training with configurable hyperparameters
  - Saving and exporting model checkpoints

Dependencies (optional):
  - transformers, datasets, torch, peft, trl
"""

import json
import os
import logging
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger("iris.training")


@dataclass
class TrainingConfig:
    model_name: str = "llama3.2"
    base_model: str = "llama3.2"
    output_dir: str = "./training_output"
    dataset_path: str = ""
    epochs: int = 3
    batch_size: int = 4
    learning_rate: float = 2e-5
    max_seq_length: int = 2048
    warmup_steps: int = 100
    logging_steps: int = 10
    save_steps: int = 500
    eval_steps: int = 500
    use_lora: bool = True
    lora_r: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.05


class TrainingPipeline:
    """
    Manages the full training lifecycle.
    Can run locally or prepare data for cloud training.
    """

    def __init__(self, config: Optional[TrainingConfig] = None):
        self.config = config or TrainingConfig()
        self._has_dependencies = self._check_dependencies()
        logger.info(f"Training pipeline initialized (model={self.config.base_model})")

    def _check_dependencies(self) -> bool:
        deps = ["transformers", "datasets", "torch"]
        missing = []
        for dep in deps:
            try:
                __import__(dep)
            except ImportError:
                missing.append(dep)
        if missing:
            logger.warning(f"Missing training dependencies: {missing}")
            return False
        return True

    def load_dataset(self, path: Optional[str] = None) -> list[dict]:
        """Load a conversation dataset from JSON or JSONL."""
        path = path or self.config.dataset_path
        if not path or not os.path.exists(path):
            logger.warning(f"Dataset not found: {path}")
            return []

        data = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                if path.endswith(".jsonl"):
                    for line in f:
                        if line.strip():
                            data.append(json.loads(line))
                else:
                    data = json.load(f)
            logger.info(f"Loaded {len(data)} examples from {path}")
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
        return data

    def format_conversations(self, raw_data: list[dict]) -> list[dict]:
        """Format raw conversations into training examples."""
        formatted = []
        for item in raw_data:
            if isinstance(item, dict):
                if "messages" in item:
                    formatted.append({
                        "text": self._format_messages(item["messages"]),
                        "source": item.get("source", "custom"),
                    })
                elif "conversation" in item:
                    formatted.append({
                        "text": self._format_messages(item["conversation"]),
                        "source": item.get("source", "custom"),
                    })
                elif "instruction" in item and "response" in item:
                    formatted.append({
                        "text": f"<s>[INST] {item['instruction']} [/INST] {item['response']} </s>",
                        "source": item.get("source", "custom"),
                    })
        logger.info(f"Formatted {len(formatted)} training examples")
        return formatted

    def _format_messages(self, messages: list[dict]) -> str:
        parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                parts.append(f"<s>[SYS] {content} [/SYS]")
            elif role == "user":
                parts.append(f"<s>[INST] {content} [/INST]")
            elif role == "assistant":
                parts.append(f" {content} </s>")
        return "\n".join(parts)

    def run_training(self, dataset: Optional[list[dict]] = None) -> dict:
        """Execute the training run."""
        if not self._has_dependencies:
            return {"success": False, "error": "Missing training dependencies. Install: transformers, datasets, torch"}

        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            TrainingArguments,
            Trainer,
        )
        from datasets import Dataset

        data = dataset or self.load_dataset()
        if not data:
            return {"success": False, "error": "No training data available"}

        formatted = self.format_conversations(data)
        texts = [item["text"] for item in formatted]

        hf_dataset = Dataset.from_dict({"text": texts})
        tokenizer = AutoTokenizer.from_pretrained(self.config.base_model)
        model = AutoModelForCausalLM.from_pretrained(self.config.base_model)

        def tokenize_fn(examples):
            return tokenizer(
                examples["text"],
                truncation=True,
                padding="max_length",
                max_length=self.config.max_seq_length,
            )

        tokenized_dataset = hf_dataset.map(tokenize_fn, batched=True)

        training_args = TrainingArguments(
            output_dir=self.config.output_dir,
            num_train_epochs=self.config.epochs,
            per_device_train_batch_size=self.config.batch_size,
            learning_rate=self.config.learning_rate,
            warmup_steps=self.config.warmup_steps,
            logging_steps=self.config.logging_steps,
            save_steps=self.config.save_steps,
            eval_steps=self.config.eval_steps,
            save_total_limit=2,
            report_to="none",
        )

        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized_dataset,
        )

        try:
            trainer.train()
            trainer.save_model(os.path.join(self.config.output_dir, "final"))
            tokenizer.save_pretrained(os.path.join(self.config.output_dir, "final"))
            logger.info(f"Training complete. Model saved to {self.config.output_dir}/final")
            return {
                "success": True,
                "output_dir": os.path.join(self.config.output_dir, "final"),
                "epochs": self.config.epochs,
                "samples": len(tokenized_dataset),
            }
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return {"success": False, "error": str(e)}

    def get_status(self) -> dict:
        return {
            "model": self.config.base_model,
            "dependencies_ready": self._has_dependencies,
            "dataset": self.config.dataset_path,
            "output_dir": self.config.output_dir,
            "epochs": self.config.epochs,
            "batch_size": self.config.batch_size,
            "learning_rate": self.config.learning_rate,
        }
