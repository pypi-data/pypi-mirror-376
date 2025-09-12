# -*- coding: utf-8 -*-
import os.path
from typing import List

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import (
    OpenAIEmbeddings,
)
from langchain_redis import RedisChatMessageHistory, RedisVectorStore
from langchain_core.messages.chat import ChatMessage
from redisvl.extensions.llmcache import SemanticCache
from redisvl.utils.rerank import HFCrossEncoderReranker
from redisvl.utils.utils import create_ulid
from .shared.cached_llm import CachedLLM
from .shared.logger import logger
from . import env

os.environ["TOKENIZERS_PARALLELISM"] = "false"

class Session:
    def __init__(self, llm, session_id = None, embedding = None, rerankers = None) -> None:
        missing_vars = []
        self.session_id = create_ulid() if session_id is None else session_id
        self.redis_url = env.REDIS_URL
        self.openai_api_key = env.OPENAI_API_KEY

        self.initialized = False
        self.RERANKERS = {}
        if rerankers and env.USE_RERANKERS:
            self.RERANKERS = rerankers

        # Initialize non-API dependent variables
        self.chunk_size = env.CHUNK_SIZE
        self.chunking_technique = env.CHUNKING_TECHNIQUE
        self.chat_history = None
        self.N = 0
        self.count = 0
        self.use_semantic_cache = env.USE_SEMANTIC_CACHE
        self.use_rerankers = env.USE_RERANKERS
        self.top_k = env.TOP_K
        self.distance_threshold = env.DISTANCE_THRESHOLD
        self.use_chat_history = env.USE_CHAT_HISTORY
        self.use_ragas = env.USE_RERANKERS
        self.reranker_type = env.RERANKER_TYPE
        logger.info("Initializing LLM")
        self.llm = llm.get('llm')
        self.llm_provider = llm.get('provider')
        if not self.llm or not self.llm_provider:
            missing_vars.append(llm)
        self.cached_llm = None
        self.vector_store = None
        self.llmcache = None
        self.index_name = None
        if embedding:
            self.embedding_model_provider = embedding['provider']
            self.embedding = embedding['embedding']
        else:
            self.embedding = self.get_embedding_model()
            self.embedding_model_provider = env.EMBEDDING_MODEL_PROVIDER

        if missing_vars:
            raise ValueError(f"模型初始化记忆发生异常，未设置必要的环境变量或传入的{missing_vars}不正确")

    def initialize(self):
        # Initialize rerankers
        if self.use_rerankers:
            logger.info("Initializing rerankers")

            self.RERANKERS = {
                "HuggingFace": HFCrossEncoderReranker(env.RERANKER_MODEL),
            }
            logger.info("Rerankers initialized")

        # Init chat history if use_chat_history is True
        if self.use_chat_history:
            self.chat_history = RedisChatMessageHistory(
                session_id=self.session_id,
                redis_url=self.redis_url,
                index_name="chat_history",  # Use a common index for all chat histories
            )
            chats = {"session_id": self.session_id, "chat_history": self.chat_history}
            logger.debug(f"加载对话历史，{chats}")
        else:
            self.chat_history = None

        self.initialized = True

    def get_embedding_model(self):
        """Get the right embedding model based on settings and config"""
        print(
            f"Embeddings for provider: {env.EMBEDDING_MODEL_PROVIDER} and model: {env.EMBEDDING_MODEL}"
        )
        match env.EMBEDDING_MODEL_PROVIDER.lower():
            case "openai":
                return OpenAIEmbeddings(model=env.EMBEDDING_MODEL)

        return None

    def build_chain(self, history: List[ChatMessage]):
        retriever = self.vector_store.as_retriever(search_kwargs={"k": self.top_k})

        messages = [
            (
                "system",
                """You are a helpful AI assistant. Use the following pieces of
                    context to answer the user's question. If you don't know the
                answer, just say that you don't know, don't try to make up an
                    answer. Please be as detailed as possible with your
                    answers.""",
            ),
            ("system", "Context: {context}"),
        ]

        if self.use_chat_history:
            for msg in history:
                messages.append((msg["role"], msg["content"]))

        messages.append(("human", "{input}"))
        messages.append(
            (
                "system",
                "Provide a helpful and accurate answer based on the given context and question:",
            )
        )
        prompt = ChatPromptTemplate.from_messages(messages)

        combine_docs_chain = create_stuff_documents_chain(self.cached_llm, prompt)
        rag_chain = create_retrieval_chain(retriever, combine_docs_chain)

        return rag_chain

    def update_chat_history(
        self, history: List[ChatMessage], use_chat_history: bool
    ):
        self.use_chat_history = use_chat_history

        if self.use_chat_history:
            if self.chat_history is None:
                self.chat_history = RedisChatMessageHistory(
                    session_id=self.session_id,
                    redis_url=self.redis_url,
                    index_name="chat_history",
                )

        else:
            if self.chat_history:
                try:
                    self.chat_history.clear()
                except Exception as e:
                    logger.debug(f"清理会话历史异常: {str(e)}")

        history.clear()

        return history

    def get_chat_history(self):
        if self.chat_history and self.use_chat_history:
            messages = self.chat_history.messages
            formatted_history = []
            for msg in messages:
                if msg.type == "human":
                    formatted_history.append(f"👤 **Human**: {msg.content}\n")
                elif msg.type == "ai":
                    formatted_history.append(f"🤖 **AI**: {msg.content}\n")
            return "\n".join(formatted_history)
        return "No chat history available."

    def update_top_k(self, new_top_k: int):
        self.top_k = new_top_k

    def make_semantic_cache(self) -> SemanticCache:
        semantic_cache_index_name = f"llmcache:{self.index_name}"
        return SemanticCache(
            name=semantic_cache_index_name,
            redis_url=self.redis_url,
            distance_threshold=self.distance_threshold,
        )

    def clear_semantic_cache(self):
        # Always make a new SemanticCache in case use_semantic_cache is False
        semantic_cache = self.make_semantic_cache()
        semantic_cache.clear()

    def update_semantic_cache(self, use_semantic_cache: bool):
        self.use_semantic_cache = use_semantic_cache
        if self.use_semantic_cache and self.index_name:
            self.llmcache = self.make_semantic_cache()
        else:
            self.llmcache = None


    def update_distance_threshold(self, new_threshold: float):
        self.distance_threshold = new_threshold
        if self.index_name:
            self.llmcache = self.make_semantic_cache()
            self.update_llm()

    def get_last_cache_status(self) -> bool:
        if isinstance(self.cached_llm, CachedLLM):
            return self.cached_llm.get_last_cache_status()
        return False

    def rerank_results(self, query, results):
        if not self.use_reranker:
            return results, None, None

        reranker = self.RERANKERS[self.reranker_type]
        original_results = [r.page_content for r in results]

        reranked_results, scores = reranker.rank(query=query, docs=original_results)

        # Reconstruct the results with reranked order, using fuzzy matching
        reranked_docs = []
        for reranked in reranked_results:
            reranked_content = (
                reranked["content"] if isinstance(reranked, dict) else reranked
            )
            best_match = max(
                results, key=lambda r: self.similarity(r.page_content, reranked_content)
            )
            reranked_docs.append(best_match)

        rerank_info = {
            "original_order": original_results,
            "reranked_order": [
                r["content"] if isinstance(r, dict) else r for r in reranked_results
            ],
            "original_scores": [1.0]
            * len(results),  # Assuming original scores are not available
            "reranked_scores": scores,
        }

        return reranked_docs, rerank_info, original_results

    def similarity(self, s1, s2):
        # Simple similarity measure based on common words
        words1 = set(s1.lower().split())
        words2 = set(s2.lower().split())
        return len(words1.intersection(words2)) / len(words1.union(words2))

    def rerankers(self):
        return self.RERANKERS

    def update_embedding_model_provider(self, new_provider: str):
        self.embedding_model_provider = new_provider
