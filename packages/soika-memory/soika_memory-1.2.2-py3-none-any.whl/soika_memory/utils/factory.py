import importlib
from typing import Optional

from soika_memory.configs.embeddings.base import BaseEmbedderConfig
from soika_memory.configs.llms.base import BaseLlmConfig
from soika_memory.embeddings.mock import MockEmbeddings


def load_class(class_type):
    module_path, class_name = class_type.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


class LlmFactory:
    provider_to_class = {
        "soikastack": "soika_memory.llms.soikastack.SoikaStackLLM",
        "ollama": "soika_memory.llms.ollama.OllamaLLM",
        "openai": "soika_memory.llms.openai.OpenAILLM",
        "groq": "soika_memory.llms.groq.GroqLLM",
        "together": "soika_memory.llms.together.TogetherLLM",
        "aws_bedrock": "soika_memory.llms.aws_bedrock.AWSBedrockLLM",
        "azure_openai": "soika_memory.llms.azure_openai.AzureOpenAILLM",
        "openai_structured": "soika_memory.llms.openai_structured.OpenAIStructuredLLM",
        "anthropic": "soika_memory.llms.anthropic.AnthropicLLM",
        "azure_openai_structured": "soika_memory.llms.azure_openai_structured.AzureOpenAIStructuredLLM",
        "gemini": "soika_memory.llms.gemini.GeminiLLM",
        "deepseek": "soika_memory.llms.deepseek.DeepSeekLLM",
        "xai": "soika_memory.llms.xai.XAILLM",
    }

    @classmethod
    def create(cls, provider_name, config):
        class_type = cls.provider_to_class.get(provider_name)
        if class_type:
            llm_instance = load_class(class_type)
            base_config = BaseLlmConfig(**config)
            return llm_instance(base_config)
        else:
            raise ValueError(f"Unsupported Llm provider: {provider_name}")


class EmbedderFactory:
    provider_to_class = {
        "soikastack": "soika_memory.embeddings.soikastack.SoikaStackEmbedding",
        "openai": "soika_memory.embeddings.openai.OpenAIEmbedding",
        "ollama": "soika_memory.embeddings.ollama.OllamaEmbedding",
        "huggingface": "soika_memory.embeddings.huggingface.HuggingFaceEmbedding",
        "azure_openai": "soika_memory.embeddings.azure_openai.AzureOpenAIEmbedding",
        "gemini": "soika_memory.embeddings.gemini.GoogleGenAIEmbedding",
        "vertexai": "soika_memory.embeddings.vertexai.VertexAIEmbedding",
        "together": "soika_memory.embeddings.together.TogetherEmbedding",
        "lmstudio": "soika_memory.embeddings.lmstudio.LMStudioEmbedding",
        "langchain": "soika_memory.embeddings.langchain.LangchainEmbedding",
        "aws_bedrock": "soika_memory.embeddings.aws_bedrock.AWSBedrockEmbedding",
    }

    @classmethod
    def create(cls, provider_name, config, vector_config: Optional[dict]):
        if provider_name == "upstash_vector" and vector_config and vector_config.enable_embeddings:
            return MockEmbeddings()
        class_type = cls.provider_to_class.get(provider_name)
        if class_type:
            embedder_instance = load_class(class_type)
            base_config = BaseEmbedderConfig(**config)
            return embedder_instance(base_config)
        else:
            raise ValueError(f"Unsupported Embedder provider: {provider_name}")


class VectorStoreFactory:
    provider_to_class = {
        "qdrant": "soika_memory.vector_stores.qdrant.Qdrant",
        "chroma": "soika_memory.vector_stores.chroma.ChromaDB",
        "pgvector": "soika_memory.vector_stores.pgvector.PGVector",
        "milvus": "soika_memory.vector_stores.milvus.MilvusDB",
        "upstash_vector": "soika_memory.vector_stores.upstash_vector.UpstashVector",
        "azure_ai_search": "soika_memory.vector_stores.azure_ai_search.AzureAISearch",
        "pinecone": "soika_memory.vector_stores.pinecone.PineconeDB",
        "mongodb": "soika_memory.vector_stores.mongodb.MongoDB",
        "redis": "soika_memory.vector_stores.redis.RedisDB",
        "elasticsearch": "soika_memory.vector_stores.elasticsearch.ElasticsearchDB",
        "vertex_ai_vector_search": "soika_memory.vector_stores.vertex_ai_vector_search.GoogleMatchingEngine",
        "opensearch": "soika_memory.vector_stores.opensearch.OpenSearchDB",
        "supabase": "soika_memory.vector_stores.supabase.Supabase",
        "faiss": "soika_memory.vector_stores.faiss.FAISS",
        "langchain": "soika_memory.vector_stores.langchain.Langchain",
    }

    @classmethod
    def create(cls, provider_name, config):
        class_type = cls.provider_to_class.get(provider_name)
        if class_type:
            if not isinstance(config, dict):
                config = config.model_dump()
            vector_store_instance = load_class(class_type)
            return vector_store_instance(**config)
        else:
            raise ValueError(f"Unsupported VectorStore provider: {provider_name}")

    @classmethod
    def reset(cls, instance):
        instance.reset()
        return instance
