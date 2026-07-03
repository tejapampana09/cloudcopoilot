import os
import json
import math
import logging
import fnmatch
from typing import List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor
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
    def parse_gitignore(gitignore_path: str) -> List[str]:
        """Parses gitignore file and returns list of path patterns."""
        patterns = []
        if os.path.exists(gitignore_path):
            try:
                with open(gitignore_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            patterns.append(line)
            except Exception as e:
                logger.warning(f"Failed to read .gitignore at {gitignore_path}: {e}")
        return patterns

    @staticmethod
    def is_ignored(path: str, gitignore_patterns: List[str], clone_path: str) -> bool:
        """Determines if a file path is ignored by gitignore or standard lists."""
        ignored_dirs = {'.git', 'node_modules', 'venv', '.venv', '__pycache__', 'dist', 'build', '.next', '.agents', '.pytest_cache', '.vscode', '.idea', 'temp_clones', 'temp', 'downloads'}
        
        # Check standard ignores
        parts = os.path.relpath(path, clone_path).split(os.sep)
        if any(p in ignored_dirs for p in parts):
            return True
            
        rel_path = os.path.relpath(path, clone_path).replace(os.sep, '/')
        for pat in gitignore_patterns:
            if pat.endswith('/'):
                pat_dir = pat.rstrip('/')
                if rel_path == pat_dir or rel_path.startswith(pat_dir + '/'):
                    return True
            else:
                if fnmatch.fnmatch(rel_path, pat) or fnmatch.fnmatch(os.path.basename(path), pat):
                    return True
        return False

    @staticmethod
    def is_binary_file(filepath: str) -> bool:
        """Checks if a file is binary by reading its first 1024 bytes."""
        try:
            with open(filepath, 'rb') as f:
                chunk = f.read(1024)
                return b'\x00' in chunk
        except Exception as e:
            logger.debug(f"Failed to check if {filepath} is binary: {e}")
            return True

    @staticmethod
    def get_smart_chunk_config(file_extension: str) -> Tuple[int, int]:
        """Returns dynamically-adjusted chunk size and overlap based on file types."""
        ext = file_extension.lower()
        if ext in {'.py', '.go', '.rs', '.java', '.cpp', '.c'}:
            # Code structure: Medium chunks
            return 800, 150
        elif ext in {'.ts', '.tsx', '.js', '.jsx'}:
            # Frontend code: Slightly smaller
            return 600, 100
        elif ext in {'.json', '.yaml', '.yml', '.tf'}:
            # Configs: Larger blocks
            return 1000, 100
        # Default
        return 700, 120

    @staticmethod
    def chunk_and_index_repo(task_id: str, clone_path: str, api_key: str) -> None:
        """
        Walks the repository files, breaks them into dynamic overlapping chunks,
        generates embeddings via OpenAI, and stores them in SQLite.
        Respects .gitignore, filters binary files, and parallelizes API requests.
        """
        if not api_key:
            logger.warning("No OpenAI API key provided. Skipping repository semantic indexing.")
            return

        try:
            # 1. Parse gitignore patterns
            gitignore_path = os.path.join(clone_path, '.gitignore')
            gitignore_patterns = IndexingService.parse_gitignore(gitignore_path)

            # 2. Gather indexable files
            documents: List[Tuple[str, str, str]] = []  # List of (relative_path, content, extension)
            
            for root, dirs, files in os.walk(clone_path):
                # Prune in place
                dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', 'venv', '.venv'}]
                
                for file in files:
                    filepath = os.path.join(root, file)
                    if IndexingService.is_ignored(filepath, gitignore_patterns, clone_path):
                        continue
                    
                    _, ext = os.path.splitext(file)
                    if ext.lower() in INDEXABLE_EXTENSIONS:
                        if IndexingService.is_binary_file(filepath):
                            continue
                            
                        rel_path = os.path.relpath(filepath, clone_path)
                        try:
                            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                            if content.strip():
                                documents.append((rel_path, content, ext))
                        except Exception as e:
                            logger.error(f"Failed to read file {rel_path} for indexing: {e}")

            if not documents:
                logger.info("No indexable text files found in the repository.")
                return

            # 3. Create chunks with dynamic size configs
            chunks_to_embed: List[Dict[str, Any]] = []
            
            for rel_path, content, ext in documents:
                chunk_size, chunk_overlap = IndexingService.get_smart_chunk_config(ext)
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

            # Cap maximum chunks to prevent token budgeting limits
            max_chunks_limit = 150
            if len(chunks_to_embed) > max_chunks_limit:
                logger.warning(f"Repository has {len(chunks_to_embed)} chunks. Capping indexing to top {max_chunks_limit} chunks.")
                chunks_to_embed = chunks_to_embed[:max_chunks_limit]

            if not chunks_to_embed:
                return

            # 4. Embeddings Setup
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

            # 5. Check Cache and collect new texts for embedding
            db = SessionLocal()
            vectors: List[Any] = [None] * len(chunks_to_embed)
            texts_to_embed_indices: List[int] = []
            texts_to_embed: List[str] = []

            try:
                for idx, chunk in enumerate(chunks_to_embed):
                    # Cache / Incremental Index Lookups: check if this chunk's content was embedded before
                    cached = db.query(RepositoryChunk).filter(RepositoryChunk.content == chunk["content"]).first()
                    if cached:
                        try:
                            vectors[idx] = json.loads(cached.embedding)
                        except Exception as parse_err:
                            logger.warning(f"Error parsing cached embedding: {parse_err}")
                            texts_to_embed_indices.append(idx)
                            texts_to_embed.append(chunk["content"])
                    else:
                        texts_to_embed_indices.append(idx)
                        texts_to_embed.append(chunk["content"])
                
                # Fetch remaining embeddings in parallel thread pools
                if texts_to_embed:
                    batch_size = 50
                    futures = []
                    
                    def embed_batch(batch_idx: int, batch_texts: List[str]):
                        batch_vectors = embeddings_model.embed_documents(batch_texts)
                        return batch_idx, batch_vectors

                    with ThreadPoolExecutor(max_workers=4) as executor:
                        for b_idx, i in enumerate(range(0, len(texts_to_embed), batch_size)):
                            batch_texts = texts_to_embed[i:i + batch_size]
                            futures.append(executor.submit(embed_batch, b_idx, batch_texts))

                        for fut in futures:
                            b_idx, batch_vectors = fut.result()
                            start_offset = b_idx * batch_size
                            for offset, vec in enumerate(batch_vectors):
                                global_text_idx = texts_to_embed_indices[start_offset + offset]
                                vectors[global_text_idx] = vec

                # 6. Save newly indexed chunks to database
                for idx, chunk in enumerate(chunks_to_embed):
                    if vectors[idx] is not None:
                        db_chunk = RepositoryChunk(
                            task_id=task_id,
                            file_path=chunk["file_path"],
                            content=chunk["content"],
                            embedding=json.dumps(vectors[idx])
                        )
                        db.add(db_chunk)
                db.commit()
                logger.info(f"Successfully indexed {len(chunks_to_embed)} code chunks for task {task_id} (Reused {len(chunks_to_embed) - len(texts_to_embed)} from cache).")
            except Exception as db_err:
                db.rollback()
                logger.error(f"Failed to save embeddings to database: {db_err}")
                raise db_err
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
                except Exception as sim_err:
                    logger.warning(f"Error calculating cosine similarity for chunk {chunk.id}: {sim_err}")

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
