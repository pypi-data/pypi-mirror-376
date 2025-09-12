# -*- coding: utf-8 -*-
from dotenv import load_dotenv
from .shared.utils import str_to_bool
import os
load_dotenv()

TOP_K = int(os.environ.get("DEFAULT_TOP_K", 3))
DISTANCE_THRESHOLD = float(os.environ.get("DEFAULT_DISTANCE_THRESHOLD", 0.30))
REDIS_URL = os.environ.get("REDIS_URL",  "redis://:redis@192.168.65.166:6377")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
CHUNK_SIZE = int(os.environ.get("DEFAULT_CHUNK_SIZE", 500))
CHUNKING_TECHNIQUE = os.environ.get(
            "DEFAULT_CHUNKING_TECHNIQUE", "Recursive Character"
        )
USE_SEMANTIC_CACHE = str_to_bool(
            os.environ.get("DEFAULT_USE_SEMANTIC_CACHE")
        )
USE_RERANKERS = str_to_bool(os.environ.get("DEFAULT_USE_RERANKERS"))
RERANKER_MODEL = os.environ.get("DEFAULT_RERANKER_MODEL", "D:/model/Qwen3-Reranker-0.6B")
RERANKER_TYPE = os.environ.get("DEFAULT_RERANKER_TYPE", "HuggingFace")
USE_CHAT_HISTORY = str_to_bool(os.environ.get("DEFAULT_USE_CHAT_HISTORY"))
USE_RAGAS = str_to_bool(os.environ.get("DEFAULT_USE_RAGAS"))
EMBEDDING_MODEL_PROVIDER = "openai"
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "D:/model/Qwen3-Embedding-0.6B")