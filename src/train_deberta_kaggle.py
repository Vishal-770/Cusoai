# ==============================================================================
# Kaggle Training Script for Customer Support Ticket Classifier (DeBERTa-v3-large)
# ==============================================================================
# Instructions:
# 1. Upload your train.csv and val.csv to Kaggle.
# 2. Change the DATA_DIR path below to point to your Kaggle Input folder.
# 3. Ensure GPUs (2x T4 or A100) are turned on in Kaggle session options.
# ==============================================================================

# 1. Install required libraries (Uncomment this line when running in a Kaggle notebook cell)
# !pip install -q transformers datasets evaluate accelerate sentencepiece

import pandas as pd
import numpy as np
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
import evaluate
import os

# 2. Define exactly where your files are uploaded
# IMPORTANT: Check the exact path under "Input" on the right sidebar in Kaggle!
DATA_DIR = "/kaggle/input/vishal-support-tickets-200k" 

print("Loading Dataset from cloud storage...")
dataset = load_dataset("csv", data_files={
    "train": f"{DATA_DIR}/train.csv",
    "validation": f"{DATA_DIR}/val.csv"
})

# 3. Define mapping (From text names to model numbers)
categories = ['Refund', 'Login', 'Delivery', 'Billing', 'Account', 'Other']
label2id = {label: i for i, label in enumerate(categories)}
id2label = {i: label for i, label in enumerate(categories)}

def encode_labels(example):
    # 'labels' MUST be plural for the Hugging Face Trainer to calculate loss
    example['labels'] = label2id[example['category']]
    return example

print("Converting text categories to numbers...")
dataset = dataset.map(encode_labels)

# 4. Initialize Tokenizer
model_name = "microsoft/deberta-v3-large"
print(f"Loading Tokenizer for {model_name}...")
# use_fast=False is safer for DeBERTa v3 sentencepiece tokenizers
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)

def tokenize_function(examples):
     # Max length 256 prevents Out Of Memory (OOM) errors on 16GB GPUs
    return tokenizer(examples['issue_description'], padding="max_length", truncation=True, max_length=256)

print("Tokenizing the 200,000 tickets... (This takes a few minutes)")
tokenized_datasets = dataset.map(tokenize_function, batched=True)


# 5. Initialize the Model
print("Loading the blank DeBERTa Large Model...")
model = AutoModelForSequenceClassification.from_pretrained(
    model_name, 
    num_labels=len(categories),
    id2label=id2label, 
    label2id=label2id
)

# 6. Set hardware training rules
training_args = TrainingArguments(
    output_dir="/kaggle/working/results", # Save files here during training
    learning_rate=2e-5,
    per_device_train_batch_size=16,       # Batch 16 on GPU1 + Batch 16 on GPU2 = 32
    per_device_eval_batch_size=16,
    num_train_epochs=3,                   # 3 Epochs is sufficient for a 200k dataset
    weight_decay=0.01,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    fp16=True,                            # CRITICAL: Use Mixed Precision to save GPU RAM
    report_to="none"                      # Disables Weights & Biases logging prompts
)

# 7. Function to calculate Accuracy during evaluation phases
metric = evaluate.load("accuracy")
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    return metric.compute(predictions=predictions, references=labels)

# 8. Start the Training Engine
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["validation"],
    tokenizer=tokenizer,
    compute_metrics=compute_metrics,
)

print("STARTING TRAINING NOW!")
trainer.train()


# 9. Save the Final Model outputs
# These are the files you will download back to your massive PC after training completes
save_path = "/kaggle/working/my-final-deberta-model"
trainer.save_model(save_path)
tokenizer.save_pretrained(save_path)

print(f"ALL DONE! Model saved locally on Kaggle to {save_path}")
print("Please go to the Output section on the right sidebar and download this folder to your PC.")
