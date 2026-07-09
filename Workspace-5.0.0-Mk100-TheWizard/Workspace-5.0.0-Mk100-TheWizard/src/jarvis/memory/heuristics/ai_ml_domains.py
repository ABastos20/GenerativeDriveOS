"""AI and machine learning domain mappings.

Covers ML fundamentals, deep learning, NLP, LLMs, transformers, embeddings,
RAG, AI agents, computer vision, reinforcement learning, and AI ethics.
"""

from __future__ import annotations

from typing import Dict

# Keyword-based classification for AI & ML
AI_ML_KEYWORD_MAP: Dict[str, str] = {
    # General AI/ML (existing from GD tags)
    " ai ": "ai.core",
    "artificial intelligence": "ai.core",
    "inteligência artificial": "ai.core",
    "inteligencia artificial": "ai.core",
    "machine learning": "ai.machine_learning",
    "aprendizagem automática": "ai.machine_learning",
    "aprendizagem automatica": "ai.machine_learning",
    "ml model": "ai.machine_learning",
    "supervised learning": "ai.machine_learning",
    "unsupervised learning": "ai.machine_learning",
    "semi-supervised": "ai.machine_learning",

    # Deep Learning & Neural Networks
    "deep learning": "ai.deep_learning",
    "neural network": "ai.deep_learning",
    "deep neural network": "ai.deep_learning",
    "dnn ": "ai.deep_learning",
    "convolutional neural": "ai.deep_learning",
    "cnn ": "ai.deep_learning",
    "recurrent neural": "ai.deep_learning",
    "rnn ": "ai.deep_learning",
    "lstm": "ai.deep_learning",
    "gru ": "ai.deep_learning",
    "backpropagation": "ai.deep_learning",
    "gradient descent": "ai.deep_learning",

    # Natural Language Processing
    "nlp ": "ai.nlp",
    "natural language processing": "ai.nlp",
    "text processing": "ai.nlp",
    "tokenization": "ai.nlp",
    "named entity recognition": "ai.nlp",
    "ner ": "ai.nlp",
    "sentiment analysis": "ai.nlp",
    "language model": "ai.nlp",
    "text classification": "ai.nlp",
    "text generation": "ai.nlp",

    # Large Language Models (existing from GD tags)
    "large language model": "ai.llm",
    "llm ": "ai.llm",
    "gpt ": "ai.llm",
    "gpt-3": "ai.llm",
    "gpt-4": "ai.llm",
    "claude": "ai.llm",
    "gemini": "ai.llm",
    "llama": "ai.llm",
    "mistral": "ai.llm",
    "language generation": "ai.llm",

    # Transformers & Attention
    "transformer": "ai.transformers",
    "transformers": "ai.transformers",
    "attention mechanism": "ai.transformers",
    "self-attention": "ai.transformers",
    "multi-head attention": "ai.transformers",
    "bert ": "ai.transformers",
    "encoder-decoder": "ai.transformers",

    # Embeddings & Vector Search
    "embedding": "ai.embeddings",
    "vector embedding": "ai.embeddings",
    "word embedding": "ai.embeddings",
    "sentence embedding": "ai.embeddings",
    "word2vec": "ai.embeddings",
    "glove": "ai.embeddings",
    "fasttext": "ai.embeddings",
    "semantic similarity": "ai.embeddings",
    "cosine similarity": "ai.embeddings",
    "vector space": "ai.embeddings",

    # RAG & Retrieval Systems
    "rag ": "ai.rag",
    "retrieval augmented": "ai.rag",
    "retrieval-augmented": "ai.rag",
    "context retrieval": "ai.rag",
    "knowledge retrieval": "ai.rag",
    "semantic search": "ai.rag",
    "hybrid search": "ai.rag",
    "dense retrieval": "ai.rag",
    "sparse retrieval": "ai.rag",

    # AI Agents & Multi-Agent Systems
    "ai agent": "ai.agent",
    "autonomous agent": "ai.agent",
    "multi-agent": "ai.agent",
    "agent framework": "ai.agent",
    "tool use": "ai.agent",
    "function calling": "ai.agent",
    "chain of thought": "ai.agent",
    "reasoning": "ai.agent",

    # Reinforcement Learning
    "reinforcement learning": "ai.reinforcement",
    "rl ": "ai.reinforcement",
    "q-learning": "ai.reinforcement",
    "policy gradient": "ai.reinforcement",
    "reward function": "ai.reinforcement",
    "markov decision": "ai.reinforcement",
    "mdp ": "ai.reinforcement",
    "deep reinforcement": "ai.reinforcement",

    # Computer Vision
    "computer vision": "ai.computer_vision",
    "image recognition": "ai.computer_vision",
    "object detection": "ai.computer_vision",
    "image classification": "ai.computer_vision",
    "semantic segmentation": "ai.computer_vision",
    "instance segmentation": "ai.computer_vision",
    "yolo": "ai.computer_vision",
    "resnet": "ai.computer_vision",
    "opencv": "ai.computer_vision",

    # Prompt Engineering
    "prompt engineering": "ai.prompt_engineering",
    "prompt design": "ai.prompt_engineering",
    "few-shot learning": "ai.prompt_engineering",
    "zero-shot": "ai.prompt_engineering",
    "chain-of-thought prompting": "ai.prompt_engineering",
    "prompt optimization": "ai.prompt_engineering",

    # Model Training & Fine-tuning
    "model training": "ai.training",
    "fine-tuning": "ai.training",
    "transfer learning": "ai.training",
    "pre-training": "ai.training",
    "hyperparameter": "ai.training",
    "learning rate": "ai.training",
    "overfitting": "ai.training",
    "regularization": "ai.training",
    "dropout": "ai.training",

    # Inference & Optimization
    "inference": "ai.inference",
    "model inference": "ai.inference",
    "quantization": "ai.inference",
    "model compression": "ai.inference",
    "pruning": "ai.inference",
    "distillation": "ai.inference",
    "onnx": "ai.inference",

    # AI Ethics & Safety
    "ai ethics": "ai.ethics",
    "ai alignment": "ai.ethics",
    "ai safety": "ai.ethics",
    "bias in ai": "ai.ethics",
    "fairness": "ai.ethics",
    "interpretability": "ai.ethics",
    "explainable ai": "ai.ethics",
    "xai ": "ai.ethics",
    "responsible ai": "ai.ethics",
}
