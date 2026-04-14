# KNOWLEDGE RAG Corpus: LLM Engineer Middle (Your Stack)

Purpose: factual grounding corpus for interview preparation and adaptive coaching.
Policy: each section includes at least one credible source URL.
Last updated: 2026-04-01

## Market Expectations: Middle LLM Engineer (2025-2026)
Source: https://www.comet.com/site/blog/rag-evaluation/
Source: https://www.emesoft.net/careers/ai-engineer-middle-senior-level/
Source: https://careers.bitkraft.vc/companies/alethea-ai/jobs/66526627-senior-llm-engineer-agentic-ai-rag-systems

Typical Middle-level expectations combine strong Python backend engineering with practical LLM system delivery.
Core requirements usually include RAG architecture, LLM inference optimization, evaluation frameworks, and production reliability.
Hiring signals often emphasize retrieval quality control, observability, prompt/version management, and iterative improvement from eval results.
Security baseline increasingly includes prompt-injection awareness, data privacy handling, and safe deployment practices.

## Python Async for LLM Services
Source: https://docs.python.org/3/library/asyncio.html
Source: https://fastapi.tiangolo.com/async/

For LLM APIs, async I/O improves concurrency for network-bound operations like model gateway calls, vector DB queries, and rerank requests.
Use async endpoints when the call stack is mostly I/O and non-blocking.
Avoid blocking CPU-heavy work in the event loop; move it to workers/process pools.
Common interview point: async helps throughput under concurrent load but does not accelerate single-request pure CPU execution.

## FastAPI Production Basics
Source: https://fastapi.tiangolo.com/deployment/

FastAPI is commonly used for LLM backend APIs due to typing, validation, and high performance on ASGI.
Middle-level expectation: design stable API contracts, validate payloads, isolate inference dependencies, and expose health/readiness endpoints.
Critical production concerns include timeout policy, idempotency for retries, request-size limits, and structured error handling.

## gRPC for Internal LLM Microservices
Source: https://grpc.io/docs/what-is-grpc/introduction/

gRPC is a strong option for low-latency internal service communication with strict schemas and streaming support.
Use it where high request volume and typed contracts matter between internal services.
Typical trade-off vs REST: better performance and contracts, but harder external debugging and browser-native consumption.

## PostgreSQL + pgvector
Source: https://github.com/pgvector/pgvector

pgvector adds vector similarity search to PostgreSQL, enabling relational + vector workflows in one system.
Interview expectation: explain index choices (IVFFlat/HNSW where available), distance metrics, filtering with metadata, and scaling limits.
pgvector is strong for teams already standardized on PostgreSQL and moderate vector scale.

## Redis for LLM Workloads
Source: https://redis.io/docs/latest/

Redis is used for caching, rate-limiting, ephemeral chat state, and queue-like patterns.
In LLM apps, common wins come from caching embeddings, retrieval results, and deterministic prompt outputs.
Key interview point: define cache invalidation strategy and TTL policy; otherwise stale context can reduce answer quality.

## RAG Pipeline: Canonical Stages
Source: https://www.pinecone.io/learn/retrieval-augmented-generation/
Source: https://www.comet.com/site/blog/rag-evaluation/

Canonical pipeline: ingestion -> chunking -> embedding -> indexing -> retrieval -> reranking -> generation -> grounded answer with citation.
Middle-level candidate should diagnose whether failures are in retrieval quality, context assembly, or generation behavior.
RAG quality depends on both retriever relevance and generator faithfulness to provided context.

## LangChain and LangGraph in Production
Source: https://python.langchain.com/docs/introduction/
Source: https://langchain-ai.github.io/langgraph/

LangChain provides integrations and chain abstractions; LangGraph is used for stateful, graph-based, agentic workflows.
Production interview expectation: explain why graph/state model helps with retries, branching, and controllable multi-step reasoning.
Key risk: complex agent graphs without observability can become hard to debug.

## LlamaIndex for RAG Indexing
Source: https://docs.llamaindex.ai/en/stable/

LlamaIndex specializes in data connectors, indexing strategies, and retrieval composition for RAG systems.
Middle-level expectation: justify tool choice by data sources, latency target, and control over retrieval behavior.
Important trade-off: framework speed of development vs custom pipeline transparency.

## Vector Databases: Qdrant, Milvus, Weaviate, Chroma
Source: https://qdrant.tech/documentation/
Source: https://milvus.io/docs
Source: https://docs.weaviate.io/weaviate
Source: https://docs.trychroma.com/

Interview-ready understanding includes deployment model, filtering support, index types, replication options, and operational overhead.
Chroma is often used for prototyping or embedded local workflows.
Qdrant/Milvus/Weaviate are more common for scalable production retrieval stacks.

## vLLM / TGI / Triton for Serving
Source: https://docs.vllm.ai/en/latest/
Source: https://huggingface.co/docs/text-generation-inference/en/index
Source: https://docs.nvidia.com/deeplearning/triton-inference-server/

Expected Middle-level skill: explain serving choices by latency, throughput, model support, deployment complexity, and observability.
vLLM emphasizes throughput and memory efficiency (PagedAttention, continuous batching).
TGI focuses on production-friendly text generation serving around HF ecosystem.
Triton is a broader inference platform for multi-framework model serving.

## Quantization and Model Formats
Source: https://onnxruntime.ai/docs/
Source: https://github.com/ggerganov/llama.cpp/blob/master/docs/gguf.md

Quantization reduces memory footprint and can increase throughput at acceptable quality loss for many use-cases.
ONNX Runtime is often used for optimized cross-platform inference paths.
GGUF is common for efficient local/offline inference scenarios.
Interview expectation: articulate accuracy-latency-memory trade-offs, not only "it is faster".

## Fine-tuning: LoRA / QLoRA / PEFT
Source: https://huggingface.co/docs/peft/index
Source: https://huggingface.co/papers/2106.09685
Source: https://huggingface.co/papers/2305.14314

Middle-level candidate should distinguish when to use prompting, RAG, or finetuning.
LoRA/QLoRA reduce cost by training adapter parameters instead of full model weights.
Discuss risks: catastrophic forgetting, data quality issues, and evaluation leakage.

## RAG Evaluation and LLM-as-a-Judge
Source: https://www.comet.com/site/blog/rag-evaluation/
Source: https://docs.ragas.io/en/latest/
Source: https://deepeval.com/docs

Modern expectation is disaggregated eval: separate retriever quality from generator quality.
Useful dimensions: context relevance, answer faithfulness, answer correctness, and hallucination rate.
LLM-as-a-judge can scale evaluation but requires calibrated prompts, test sets, and periodic human audits.
Production teams use offline eval gates plus online monitoring.

## Prompt Injection and RAG Security
Source: https://owasp.org/www-project-top-10-for-large-language-model-applications/
Source: https://www.promptfoo.dev/docs/red-team/owasp-llm-top-10/

Prompt injection can override system intent or exfiltrate sensitive context.
Security baseline includes input sanitization, content filtering, permission boundaries, and retrieval trust policies.
Do not treat retrieved text as trusted instructions.
Middle-level expectation: know at least one defense-in-depth strategy and its limits.

## MCP and Tool Integrations
Source: https://modelcontextprotocol.io/introduction

MCP standardizes tool/context integration between models and external systems.
Interview point: explain why protocolized tool access improves interoperability and reduces one-off glue code.
Operationally, tool authorization and audit logging remain essential.

## CI/CD and Containerization
Source: https://docs.docker.com/get-started/docker-overview/
Source: https://docs.github.com/actions
Source: https://docs.gitlab.com/ee/ci/

Middle-level baseline: build reproducible Docker images, run tests in CI, and deploy with versioned artifacts.
For LLM services, include smoke tests for critical prompts and API contracts before rollout.
Deployment reliability improves with staged rollout and fast rollback strategy.

## Kubernetes for LLM Services
Source: https://kubernetes.io/docs/concepts/overview/
Source: https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/

Use requests/limits to avoid noisy-neighbor failures and unstable scheduling.
Interview expectation: explain OOMKilled, Pending due to resource requests, and autoscaling caveats.
LLM workloads need capacity planning by sequence length distribution, concurrency, and model memory profile.

## Observability: Prometheus + OpenTelemetry + Grafana
Source: https://prometheus.io/docs/introduction/overview/
Source: https://opentelemetry.io/docs/what-is-opentelemetry/
Source: https://grafana.com/docs/

Core metrics for LLM serving: p50/p95/p99 latency, TTFT, tokens/sec, error rates, timeout rates, queue depth, GPU/CPU/memory saturation.
Tracing should cover retrieval, reranking, model call, and post-processing stages.
Without stage-level observability, teams cannot localize bottlenecks quickly.

## Messaging and Async Pipelines (Kafka/RabbitMQ)
Source: https://kafka.apache.org/documentation/
Source: https://www.rabbitmq.com/documentation.html

Kafka is common for high-throughput event streams and replay.
RabbitMQ is common for task/work queues with flexible routing.
In LLM systems, messaging is useful for async ingestion, document processing, and deferred evaluation pipelines.

## Airflow, dbt, Spark in Data/LLM Pipelines
Source: https://airflow.apache.org/docs/apache-airflow/stable/index.html
Source: https://docs.getdbt.com/docs/introduction
Source: https://spark.apache.org/docs/latest/

Airflow orchestrates scheduled batch DAGs.
dbt handles SQL transformations with testable data models.
Spark handles distributed data processing at scale.
Interview expectation: explain where each tool fits and where it does not.

## AWS Baseline for Middle LLM Engineer
Source: https://docs.aws.amazon.com/

Minimum cloud baseline usually includes IAM basics, VPC/networking fundamentals, container deployment options, storage primitives, and monitoring.
For interview answers, show you understand secure secret handling, environment separation, and cost-aware scaling.
Even without deep hands-on AWS experience, a strong conceptual deployment plan is expected.

## Reliability Checklist for Interview Answers
Source: Aggregated from sections above

- Separate online and offline evaluation loops.
- Define SLOs: latency, quality, and availability targets.
- Use canary rollout and rollback for model/prompt changes.
- Instrument each pipeline stage with metrics and traces.
- Include failure-mode plan: model timeout, retriever outage, vector index lag, bad prompt release.

## Source Index
- https://www.comet.com/site/blog/rag-evaluation/
- https://www.emesoft.net/careers/ai-engineer-middle-senior-level/
- https://careers.bitkraft.vc/companies/alethea-ai/jobs/66526627-senior-llm-engineer-agentic-ai-rag-systems
- https://docs.python.org/3/library/asyncio.html
- https://fastapi.tiangolo.com/async/
- https://fastapi.tiangolo.com/deployment/
- https://grpc.io/docs/what-is-grpc/introduction/
- https://github.com/pgvector/pgvector
- https://redis.io/docs/latest/
- https://www.pinecone.io/learn/retrieval-augmented-generation/
- https://python.langchain.com/docs/introduction/
- https://langchain-ai.github.io/langgraph/
- https://docs.llamaindex.ai/en/stable/
- https://qdrant.tech/documentation/
- https://milvus.io/docs
- https://docs.weaviate.io/weaviate
- https://docs.trychroma.com/
- https://docs.vllm.ai/en/latest/
- https://huggingface.co/docs/text-generation-inference/en/index
- https://docs.nvidia.com/deeplearning/triton-inference-server/
- https://onnxruntime.ai/docs/
- https://github.com/ggerganov/llama.cpp/blob/master/docs/gguf.md
- https://huggingface.co/docs/peft/index
- https://huggingface.co/papers/2106.09685
- https://huggingface.co/papers/2305.14314
- https://docs.ragas.io/en/latest/
- https://deepeval.com/docs
- https://owasp.org/www-project-top-10-for-large-language-model-applications/
- https://www.promptfoo.dev/docs/red-team/owasp-llm-top-10/
- https://modelcontextprotocol.io/introduction
- https://docs.docker.com/get-started/docker-overview/
- https://docs.github.com/actions
- https://docs.gitlab.com/ee/ci/
- https://kubernetes.io/docs/concepts/overview/
- https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
- https://prometheus.io/docs/introduction/overview/
- https://opentelemetry.io/docs/what-is-opentelemetry/
- https://grafana.com/docs/
- https://kafka.apache.org/documentation/
- https://www.rabbitmq.com/documentation.html
- https://airflow.apache.org/docs/apache-airflow/stable/index.html
- https://docs.getdbt.com/docs/introduction
- https://spark.apache.org/docs/latest/
- https://docs.aws.amazon.com/
