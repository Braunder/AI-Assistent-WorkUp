"""
Roadmap.sh ML Engineer Validator

Diagnostic questions organized by roadmap.sh ML Engineer categories.
Used for gap analysis and progressive scaffolding in diagnostic mode.
"""

from typing import TypedDict


class RoadmapQuestion(TypedDict):
    """Single diagnostic question with expected depth."""
    question: str
    context: str  # Why this matters for LLM engineers


# ============================================================================
# MATH FUNDAMENTALS
# ============================================================================

MATH_LINEAR_ALGEBRA: list[RoadmapQuestion] = [
    {
        "question": "What is the cosine similarity between two vectors [1, 0] and [0.707, 0.707]? Why is it preferred over Euclidean distance for embeddings?",
        "context": "RAG retrieval relies on cosine similarity in high-dimensional spaces; embeddings are normalized vectors.",
    },
    {
        "question": "Explain dot product and why it works for measuring relevance between query and document embeddings.",
        "context": "Core operation in vector databases (Pinecone, Qdrant, Weaviate) for similarity search.",
    },
    {
        "question": "What is the rank of a matrix and why does it matter for embeddings?",
        "context": "Low-rank structure in fine-tuning (LoRA) and understanding when dimensionality reduction helps.",
    },
    {
        "question": "What is L2 normalization and why is it applied to embeddings before storing in vector DBs?",
        "context": "Affects both query and document embeddings; enables efficient similarity computation at scale.",
    },
]

MATH_PROBABILITY_STATS: list[RoadmapQuestion] = [
    {
        "question": "Explain Bayes' theorem. How does P(H|E) relate to prior belief P(H) and evidence P(E|H)?",
        "context": "Foundation for understanding model confidence, posterior estimates, and why priors matter in prompting.",
    },
    {
        "question": "What is a normal (Gaussian) distribution? Why do we assume model logits follow approximately normal distributions?",
        "context": "Understanding token probability distributions helps debug unexpected model behaviors.",
    },
    {
        "question": "Explain variance vs bias. Why is high variance (overfitting) a risk when fine-tuning LLMs on small datasets?",
        "context": "Catastrophic forgetting is a high-variance phenomenon; L2 regularization and LoRA reduce variance.",
    },
    {
        "question": "What is k-fold cross-validation and when would you use it over a simple train/test split?",
        "context": "Essential for validating evaluation metrics repeatability before declaring model improvements.",
    },
]

# ============================================================================
# NLP FUNDAMENTALS
# ============================================================================

NLP_TOKENIZATION: list[RoadmapQuestion] = [
    {
        "question": "What is byte-pair encoding (BPE) tokenization? How does it differ from character-level tokenization?",
        "context": "LLMs use BPE variants (SentencePiece, WordPiece); affects context window length and embedding quality.",
    },
    {
        "question": "Why does token vocabulary size affect RAG retrieval? How do out-of-vocabulary tokens impact embedding quality?",
        "context": "Misalignment between query and document tokenization breaks retrieval; multilingual models need careful vocabulary design.",
    },
    {
        "question": "Explain the trade-off between larger and smaller vocabulary sizes in tokenization.",
        "context": "Larger vocabulary → fewer tokens per sequence but larger embedding matrix; smaller → more tokens, smaller matrix.",
    },
]

NLP_EMBEDDINGS: list[RoadmapQuestion] = [
    {
        "question": "What are contextual embeddings (BERT, GPT) vs static embeddings (Word2Vec, GloVe)? Why are contextual embeddings better for RAG?",
        "context": "Contextual embeddings capture word sense from context; critical for semantic retrieval when same word has multiple meanings.",
    },
    {
        "question": "Explain how transformer-based embedding models (sentence-transformers, ada, text-embedding-3) compute document similarity.",
        "context": "Understanding pooling (mean, CLS token), normalization, and dimensionality helps diagnose retrieval failures.",
    },
    {
        "question": "Why do we fine-tune embedding models on domain-specific data? What is triplet loss used for?",
        "context": "Domain adaptation improves RAG relevance; triplet loss teaches model to push relevant pairs closer than irrelevant ones.",
    },
]

NLP_ATTENTION: list[RoadmapQuestion] = [
    {
        "question": "Explain the attention mechanism: Query, Key, Value matrices and the softmax computation.",
        "context": "Core operation in transformers; understanding attention helps explain why position matters and how sequences are compared.",
    },
    {
        "question": "Why is self-attention differentiable and how does backpropagation flow through attention weights?",
        "context": "Gradient flow through attention is essential for training; vanishing gradients in deep transformers need layer norm and residual connections.",
    },
    {
        "question": "What is positional encoding and why can't transformers work without it?",
        "context": "Transformers have no notion of sequence order without positional encoding; affects context window design and long-context handling.",
    },
]

# ============================================================================
# SUPERVISED LEARNING
# ============================================================================

SUPERVISED_REGRESSION: list[RoadmapQuestion] = [
    {
        "question": "What is linear regression and why is the closed-form solution (w = (X^T X)^-1 X^T y) rarely used in practice?",
        "context": "Understanding gradient descent and why SGD is preferred at scale helps optimize LLM ranking and recommendation systems.",
    },
    {
        "question": "Explain L1 (Lasso) vs L2 (Ridge) regularization. When would you prefer one over the other?",
        "context": "L1 produces sparse solutions (feature selection); L2 penalizes large weights (stability). LoRA uses implicit L2 on adapter weights.",
    },
    {
        "question": "What is mean squared error (MSE) and when is it appropriate vs other loss functions?",
        "context": "MSE penalizes large errors heavily; used for regression tasks like predicting ranking scores or latency estimates.",
    },
]

SUPERVISED_CLASSIFICATION: list[RoadmapQuestion] = [
    {
        "question": "Explain cross-entropy loss and softmax. Why is cross-entropy more appropriate than MSE for classification?",
        "context": "LLMs use cross-entropy loss during training; understanding it helps diagnose training instability and learning plateaus.",
    },
    {
        "question": "What is logistic regression and how does it differ from linear regression?",
        "context": "Logistic regression outputs calibrated probabilities; useful for binary classification tasks (e.g., relevance scoring in RAG).",
    },
    {
        "question": "Explain the bias-variance tradeoff. How does regularization affect it?",
        "context": "Underfitting (high bias) vs overfitting (high variance); regularization shifts tradeoff toward bias for better generalization.",
    },
]

# ============================================================================
# MODEL EVALUATION
# ============================================================================

MODEL_EVAL_METRICS: list[RoadmapQuestion] = [
    {
        "question": "Define precision, recall, and F1 score. When would you optimize for each metric differently?",
        "context": "Precision matters for high-confidence predictions (fraud detection); recall matters for exhaustive search (clinical diagnosis); F1 balances both.",
    },
    {
        "question": "What is ROC-AUC and when is it better than accuracy?",
        "context": "ROC-AUC is threshold-agnostic; useful for ranking problems (recommenders, RAG relevance ranking) where threshold is often tuned post-hoc.",
    },
    {
        "question": "Explain confusion matrix. What does each quadrant (TP, FP, TN, FN) represent?",
        "context": "Visual tool for understanding type-I and type-II errors; helps diagnose which classes are confused and whether class imbalance is the issue.",
    },
    {
        "question": "For RAG systems, define retrieval metrics (NDCG, MAP) separately from generation metrics (BLEU, ROUGE). Why is this separation important?",
        "context": "RAG quality depends on both retrieval AND generation; evaluating separately helps localize failures.",
    },
]

MODEL_EVAL_VALIDATION: list[RoadmapQuestion] = [
    {
        "question": "Explain train/validation/test split. Why is it dangerous to tune hyperparameters on the test set?",
        "context": "Lookahead bias inflates evaluation metrics; separate validation set ensures hyperparameters generalize to unseen data.",
    },
    {
        "question": "What is k-fold cross-validation and when would you use it?",
        "context": "Reduces variance of evaluation estimate; useful when data is small or when you want multiple diverse evaluation runs.",
    },
]

# ============================================================================
# DEEP LEARNING FUNDAMENTALS
# ============================================================================

DL_FOUNDATIONS: list[RoadmapQuestion] = [
    {
        "question": "Explain backpropagation and the chain rule. Why is it essential for training deep networks?",
        "context": "Backpropagation computes gradients efficiently; without it, training deep networks would be prohibitively expensive.",
    },
    {
        "question": "What is a ReLU activation function? Why is it preferred over sigmoid/tanh in modern deep networks?",
        "context": "ReLU avoids vanishing gradient problem; enables training of very deep networks (100+ layers).",
    },
    {
        "question": "Explain gradient descent, SGD, and Adam optimizer. What are their trade-offs?",
        "context": "Full-batch gradient descent is stable but slow; SGD is noisy but escapes local minima; Adam adapts learning rates per parameter.",
    },
    {
        "question": "What is batch normalization and why does it improve training convergence?",
        "context": "Reduces internal covariate shift; enables higher learning rates and acts as mild regularization.",
    },
]

DL_REGULARIZATION: list[RoadmapQuestion] = [
    {
        "question": "Explain dropout. How does it reduce overfitting and why is it disabled during inference?",
        "context": "Dropout forces ensemble-like behavior during training; disabling it during inference ensures deterministic predictions.",
    },
    {
        "question": "What is weight decay (L2 regularization) and how does it relate to regularization coefficient λ?",
        "context": "Larger λ → more regularization → simpler model; LoRA uses implicit regularization by constraining adapter rank.",
    },
]

DL_ARCHITECTURES: list[RoadmapQuestion] = [
    {
        "question": "Explain convolutional neural networks (CNNs). Why are they effective for image tasks but less so for sequences?",
        "context": "CNNs exploit spatial locality; for sequences, transformers with attention are more effective because they capture long-range dependencies.",
    },
    {
        "question": "What is a recurrent neural network (RNN) and why does it fail to capture long-range dependencies?",
        "context": "RNNs suffer from vanishing/exploding gradients; LSTMs/GRUs mitigate this with gating, but transformers are now preferred for language.",
    },
    {
        "question": "Explain why transformers with self-attention are superior to RNNs for NLP.",
        "context": "Transformers process sequences in parallel (faster), capture long-range dependencies via attention, and enable efficient scaling.",
    },
]

# ============================================================================
# PRODUCTION LLM SYSTEMS (from KNOWLEDGE_RAG)
# ============================================================================

PROD_RAG_SYSTEMS: list[RoadmapQuestion] = [
    {
        "question": "Describe the canonical RAG pipeline: ingestion, chunking, embedding, retrieval, reranking, generation.",
        "context": "Each stage has failure modes; understanding them helps diagnose why RAG quality is low.",
    },
    {
        "question": "Why do retrieval quality and generation faithfulness need to be evaluated separately?",
        "context": "Poor RAG output could stem from bad retrieval (wrong context), bad reranking (correct context ranked low), or bad generation (hallucination despite good context).",
    },
    {
        "question": "Explain what is RAG-as-a-judge or LLM-as-a-judge. What are its limitations?",
        "context": "LLM-as-a-judge scales evaluation but requires calibration (few-shot examples) and periodic human audits to prevent metric drift.",
    },
]

PROD_SERVING: list[RoadmapQuestion] = [
    {
        "question": "Compare vLLM, TGI, and Triton for serving LLMs. What are their trade-offs?",
        "context": "vLLM: throughput-optimized (PagedAttention); TGI: production-friendly (HF ecosystem); Triton: general inference platform.",
    },
    {
        "question": "What is quantization and how does it affect latency, throughput, and accuracy?",
        "context": "INT8/FP8 reduce memory (4x), speed up inference, but lose calibration if not done properly; GGUF for efficient local serving.",
    },
    {
        "question": "Explain the difference between long-context (e.g., 100K tokens) and short-context (4K tokens) serving architectures.",
        "context": "Long-context requires attention optimizations (FlashAttention); affects batching strategy and GPU memory planning.",
    },
]

PROD_OBSERVABILITY: list[RoadmapQuestion] = [
    {
        "question": "What metrics would you track for a production LLM inference service?",
        "context": "p50/p95/p99 latency, TTFT (time-to-first-token), throughput (tokens/sec), error rates, queue depth, GPU/CPU/memory utilization.",
    },
    {
        "question": "Explain why stage-level tracing (retrieval latency, model latency, post-processing latency) is critical.",
        "context": "Without stage-level breakdown, you cannot localize bottlenecks; e.g., is slowness in retrieval or in generation?",
    },
    {
        "question": "What is SLO (Service Level Objective) and how would you define it for a RAG service?",
        "context": "SLO example: 'p95 latency < 2s, accuracy > 0.85'; violation triggers investigation and potential rollback.",
    },
]

# ============================================================================
# TOPIC MAPPING FOR DIAGNOSTIC MODE
# ============================================================================

ROADMAP_CATEGORIES = {
    "math": {
        "linear_algebra": MATH_LINEAR_ALGEBRA,
        "probability_stats": MATH_PROBABILITY_STATS,
    },
    "nlp": {
        "tokenization": NLP_TOKENIZATION,
        "embeddings": NLP_EMBEDDINGS,
        "attention": NLP_ATTENTION,
    },
    "supervised_learning": {
        "regression": SUPERVISED_REGRESSION,
        "classification": SUPERVISED_CLASSIFICATION,
    },
    "model_evaluation": {
        "metrics": MODEL_EVAL_METRICS,
        "validation": MODEL_EVAL_VALIDATION,
    },
    "deep_learning": {
        "foundations": DL_FOUNDATIONS,
        "regularization": DL_REGULARIZATION,
        "architectures": DL_ARCHITECTURES,
    },
    "production": {
        "rag_systems": PROD_RAG_SYSTEMS,
        "serving": PROD_SERVING,
        "observability": PROD_OBSERVABILITY,
    },
}


def get_random_roadmap_question(category: str | None = None) -> tuple[str, str]:
    """
    Sample a random diagnostic question from roadmap categories.
    If category is None, sample uniformly across all categories.
    Returns: (question, context_description)
    """
    import random

    if category is None:
        # Flatten all questions
        all_questions: list[RoadmapQuestion] = []
        for cat in ROADMAP_CATEGORIES.values():
            for subcat in cat.values():
                all_questions.extend(subcat)
    elif category in ROADMAP_CATEGORIES:
        all_questions = []
        for subcat in ROADMAP_CATEGORIES[category].values():
            all_questions.extend(subcat)
    else:
        raise ValueError(f"Unknown category: {category}. Choose from {list(ROADMAP_CATEGORIES.keys())}")

    if not all_questions:
        raise ValueError(f"No questions found for category: {category}")

    q = random.choice(all_questions)
    return q["question"], q["context"]


def get_roadmap_coverage() -> dict[str, int]:
    """Return count of questions per roadmap category."""
    coverage = {}
    for category, subcats in ROADMAP_CATEGORIES.items():
        total = sum(len(q) for q in subcats.values())
        coverage[category] = total
    return coverage


def get_category_suggestions(weak_topics: list[str]) -> list[str]:
    """
    Given a list of weak topics (from weak_topic tool calls),
    suggest which roadmap categories need reinforcement.
    """
    important_categories = {
        "linear_algebra": ["embeddings", "vector", "similarity", "norm"],
        "probability_stats": ["confidence", "probability", "distribution", "variance"],
        "tokenization": ["token", "vocabulary", "embedding", "sequence"],
        "embeddings": ["embedding", "vector", "semantic", "retrieval"],
        "attention": ["attention", "transformer", "sequence"],
        "regression": ["regression", "loss", "prediction"],
        "classification": ["classification", "cross-entropy", "probability"],
        "metrics": ["metric", "precision", "recall", "f1", "auc"],
        "foundations": ["gradient", "backprop", "activation", "learning rate"],
        "architectures": ["cnn", "rnn", "lstm", "transformer"],
        "rag_systems": ["rag", "retrieval", "context"],
        "serving": ["latency", "throughput", "quantization"],
    }

    weak_lower = [t.lower() for t in weak_topics]
    suggestions = set()

    for category, keywords in important_categories.items():
        if any(kw in weak for weak in weak_lower for kw in keywords):
            suggestions.add(category)

    return sorted(suggestions)
