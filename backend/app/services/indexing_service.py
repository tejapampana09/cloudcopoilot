import os
import json
import math
import logging
from typing import List, Dict, Any, Tuple
from app.utils.database import SessionLocal
from app.models.analysis import RepositoryChunk
from langchain_openai import OpenAIEmbeddings

logger = logging.getLogger(__name__)

INDEXABLE_EXTENSIONS = {
    '.py', '.js', '.ts', '.tsx', '.jsx', '.go', '.rs', '.java', 
    '.kt', '.cs', '.cpp', '.c', '.h', '.rb', '.php', '.swift', 
    '.sh', '.tf', '.html', '.css', '.md', '.json', '.yaml', '.yml'
}

class IndexingService:
    @staticmethod
    def chunk_and_index_repo(task_id: str, clone_path: str, api_key: str) -> None:
        """
        Walks the repository files, breaks them into overlapping chunks, 
        generates embeddings via OpenAI, and stores them in SQLite.
        """
        if not api_key:
            logger.warning("No OpenAI API key provided. Skipping repository semantic indexing.")
            return

        try:
            # 1. Gather all indexable files
            documents: List[Tuple[str, str]] = []  # List of (relative_path, content)
            
            ignored_dirs = {'.git', 'node_modules', 'venv', '.venv', '__pycache__', 'dist', 'build', '.next', '.agents', '.pytest_cache', '.vscode', '.idea', 'temp_clones', 'temp', 'downloads'}
            
            for root, dirs, files in os.walk(clone_path):
                # Prune ignored directories in place to prevent walking into them
                dirs[:] = [d for d in dirs if d not in ignored_dirs]
                
                for file in files:
                    _, ext = os.path.splitext(file)
                    if ext.lower() in INDEXABLE_EXTENSIONS:
                        filepath = os.path.join(root, file)
                        rel_path = os.path.relpath(filepath, clone_path)
                        try:
                            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                            if content.strip():
                                documents.append((rel_path, content))
                        except Exception as e:
                            logger.error(f"Failed to read file {rel_path} for indexing: {e}")

            if not documents:
                logger.info("No indexable text files found in the repository.")
                return

            # 2. Break documents into chunks
            chunk_size = 800
            chunk_overlap = 150
            chunks_to_embed: List[Dict[str, Any]] = []
            
            for rel_path, content in documents:
                start = 0
                chunk_index = 0
                while start < len(content):
                    end = start + chunk_size
                    chunk_text = content[start:end]
                    chunks_to_embed.append({
                        "file_path": rel_path,
                        "chunk_index": chunk_index,
                        "content": chunk_text
                    })
                    start += (chunk_size - chunk_overlap)
                    chunk_index += 1

            # Cap maximum chunks to prevent API exhaustion for huge repos
            if len(chunks_to_embed) > 150:
                logger.warning(f"Repository has {len(chunks_to_embed)} chunks. Capping indexing to top 150 chunks.")
                chunks_to_embed = chunks_to_embed[:150]

            if not chunks_to_embed:
                return

            # 3. Generate embeddings batch-wise using LangChain OpenAIEmbeddings
            if api_key and api_key.startswith("sk-or-"):
                embeddings_model = OpenAIEmbeddings(
                    openai_api_key=api_key,
                    openai_api_base="https://openrouter.ai/api/v1",
                    model="openai/text-embedding-3-small"
                )
            else:
                embeddings_model = OpenAIEmbeddings(
                    openai_api_key=api_key,
                    model="text-embedding-3-small"
                )
            
            texts = [c["content"] for c in chunks_to_embed]
            
            # Batch embeddings in sizes of 50 to prevent rate limits or connection timeouts
            vectors = []
            batch_size = 50
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_vectors = embeddings_model.embed_documents(batch_texts)
                vectors.extend(batch_vectors)
            
            # 4. Save to database
            db = SessionLocal()
            try:
                for idx, chunk in enumerate(chunks_to_embed):
                    db_chunk = RepositoryChunk(
                        task_id=task_id,
                        file_path=chunk["file_path"],
                        content=chunk["content"],
                        embedding=json.dumps(vectors[idx])
                    )
                    db.add(db_chunk)
                db.commit()
                logger.info(f"Successfully indexed {len(chunks_to_embed)} code chunks for task {task_id}.")
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to save embeddings to database: {e}")
                raise e
            finally:
                db.close()

        except Exception as e:
            logger.exception(f"Semantic indexing crashed: {e}")

    @staticmethod
    def search_semantic(task_id: str, query: str, api_key: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Embeds the query, calculates cosine similarity with SQLite database vectors,
        and retrieves the top K matching chunks.
        """
        if not api_key or not query.strip():
            return []

        db = SessionLocal()
        try:
            # 1. Fetch all chunks for this task_id
            db_chunks = db.query(RepositoryChunk).filter(RepositoryChunk.task_id == task_id).all()
            if not db_chunks:
                return []

            # 2. Embed the search query
            if api_key and api_key.startswith("sk-or-"):
                embeddings_model = OpenAIEmbeddings(
                    openai_api_key=api_key,
                    openai_api_base="https://openrouter.ai/api/v1",
                    model="openai/text-embedding-3-small"
                )
            else:
                embeddings_model = OpenAIEmbeddings(
                    openai_api_key=api_key,
                    model="text-embedding-3-small"
                )
            query_vector = embeddings_model.embed_query(query)

            # 3. Calculate cosine similarity in Python
            results: List[Tuple[float, RepositoryChunk]] = []
            
            for chunk in db_chunks:
                try:
                    chunk_vector = json.loads(chunk.embedding)
                    sim = IndexingService._cosine_similarity(query_vector, chunk_vector)
                    results.append((sim, chunk))
                except Exception:
                    pass

            # Sort descending by similarity score
            results.sort(key=lambda x: x[0], reverse=True)
            
            # Formulate output list
            top_k = results[:k]
            retrieved = []
            for score, chunk in top_k:
                retrieved.append({
                    "file_path": chunk.file_path,
                    "content": chunk.content,
                    "score": round(score, 4)
                })
            return retrieved

        except Exception as e:
            logger.exception(f"Semantic search failed: {e}")
            return []
        finally:
            db.close()

    @staticmethod
    def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
        dot_product = sum(x * y for x, y in zip(v1, v2))
        magnitude1 = math.sqrt(sum(x * x for x in v1))
        magnitude2 = math.sqrt(sum(x * x for x in v2))
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        return dot_product / (magnitude1 * magnitude2)
