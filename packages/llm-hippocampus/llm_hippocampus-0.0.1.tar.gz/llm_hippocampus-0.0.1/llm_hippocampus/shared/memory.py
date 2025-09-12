# -*- coding: utf-8 -*-
from typing import List

from langchain_core.prompts import ChatPromptTemplate
from langchain_redis import RedisVectorStore
from redisvl.index import SearchIndex
from . import logger

class Memory:
    index: SearchIndex
    def __init__(self, redis_url: str):
        logger.info(f"初始化记忆模块，Redis URL: {redis_url}")
        self.redis_url = redis_url

    @property
    def client(self):
        """Redis client accessor."""
        return self.index.client

    def _check_vector_store_exists(self, index_name: str) -> bool:
        """Check if a vector store exists for the given index name."""
        try:
            self.client.ft(index_name).info()
            return True
        except Exception:
            return False

    def _cleanup_vector_store(self, index_name: str) -> bool:
        """Clean up the vector store index and its documents."""
        if not self._check_vector_store_exists(index_name):
            return True

        try:
            self.client.ft(index_name).dropindex(delete_documents=True)
            logger.info(f"Successfully cleaned up vector store: {index_name}")
            return True
        except Exception as e:
            logger.warning(f"Could not clean up vector store {index_name}: {e}")
            return False

    def get_chat_history(chat_history, use_chat_history: bool):
        if chat_history and use_chat_history:
            messages = chat_history.messages
            formatted_history = []
            for msg in messages:
                if msg.type == "human":
                    formatted_history.append(f"👤 **Human**: {msg.content}\n")
                elif msg.type == "ai":
                    formatted_history.append(f"🤖 **AI**: {msg.content}\n")
            return "\n".join(formatted_history)
        return "No chat history available."


    def build_chain(self, history: List[any]):
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

        # combine_docs_chain = create_stuff_documents_chain(self.cached_llm, prompt)
        # rag_chain = create_retrieval_chain(retriever, combine_docs_chain)

        # return rag_chain

    def load_vector_store(self, index_name: str, embeddings)  -> RedisVectorStore:
        try:
            # Get the metadata
            metadata = self.get_pdf_metadata(index_name)
            if not metadata:
                # Try to reprocess from file
                return self._reprocess_from_file(index_name, embeddings)

            # Check if vector store exists
            documents = None
            if not self._check_vector_store_exists(index_name):
                logger.info(f"Vector store missing for {index_name}, reprocessing")
                vector_store = RedisVectorStore.from_documents(
                    documents,
                    embeddings,
                    redis_url=self.redis_url,
                    index_name=index_name,
                    key_prefix=f"pdf:{index_name}",
                )
                logger.info(f"Created vector store during reprocessing for {index_name}")

            # Vector store exists, load it
            vector_store = RedisVectorStore(
                embeddings,
                redis_url=self.redis_url,
                index_name=index_name,
                key_prefix=f"pdf:{index_name}",
            )

            logger.info(f"Successfully loaded PDF: {metadata.filename}")
            return vector_store

        except Exception as e:
            logger.error(f"Failed to load PDF {index_name}: {e}")
            raise

if __name__ == '__main__':
    None
