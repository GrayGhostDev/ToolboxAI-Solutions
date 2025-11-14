"""Vector embedding tool for Supabase migration with pgvector support."""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional

import aiofiles
import asyncpg
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class EmbeddingStatus(Enum):
    """Embedding generation status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CACHED = "cached"


@dataclass
class EmbeddingBatch:
    """Batch of content for embedding generation."""

    batch_id: int
    content_items: list[dict[str, Any]]
    status: EmbeddingStatus
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error_message: Optional[str] = None


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""

    table_name: str
    total_items: int
    processed_items: int
    cached_items: int
    failed_items: int
    duration_seconds: float
    status: EmbeddingStatus
    index_created: bool = False


class VectorEmbeddingTool:
    """
    Tool for generating and managing vector embeddings for Supabase.

    Features:
    - OpenAI ada-002 integration
    - Batch embedding generation
    - Caching mechanism
    - Similarity search setup
    - Index management
    - Performance optimization
    """

    def __init__(
        self,
        openai_api_key: str,
        batch_size: int = 50,
        max_concurrent_batches: int = 3,
        embedding_model: str = "text-embedding-ada-002",
        cache_embeddings: bool = True,
    ):
        """
        Initialize the vector embedding tool.

        Args:
            openai_api_key: OpenAI API key
            batch_size: Number of items per batch
            max_concurrent_batches: Maximum concurrent requests
            embedding_model: OpenAI embedding model to use
            cache_embeddings: Whether to cache embeddings
        """
        self.client = AsyncOpenAI(api_key=openai_api_key)
        self.batch_size = batch_size
        self.max_concurrent_batches = max_concurrent_batches
        self.embedding_model = embedding_model
        self.cache_embeddings = cache_embeddings
        self.embedding_cache: dict[str, list[float]] = {}
        self.progress_callback: Optional[Callable] = None

    async def generate_embeddings(
        self,
        conn_string: str,
        table_name: str,
        text_columns: list[str],
        embedding_column: str = "embedding",
        batch_size: Optional[int] = None,
        where_clause: str = "TRUE",
        progress_callback: Optional[Callable] = None,
    ) -> EmbeddingResult:
        """
        Generate embeddings for text content in a table.

        Args:
            conn_string: Database connection string
            table_name: Name of table containing text
            text_columns: List of text columns to embed
            embedding_column: Column name for storing embeddings
            batch_size: Override default batch size
            where_clause: Filter clause for rows to process
            progress_callback: Optional progress callback

        Returns:
            Embedding generation result
        """
        logger.info(f"Generating embeddings for {table_name}")
        start_time = time.time()

        if progress_callback:
            self.progress_callback = progress_callback

        if batch_size:
            self.batch_size = batch_size

        try:
            # Setup embedding column
            await self._setup_embedding_column(conn_string, table_name, embedding_column)

            # Get content to embed
            content_items = await self._get_content_items(
                conn_string, table_name, text_columns, embedding_column, where_clause
            )

            if not content_items:
                logger.info(f"No content to embed in {table_name}")
                return EmbeddingResult(
                    table_name=table_name,
                    total_items=0,
                    processed_items=0,
                    cached_items=0,
                    failed_items=0,
                    duration_seconds=time.time() - start_time,
                    status=EmbeddingStatus.COMPLETED,
                )

            # Load cache if enabled
            if self.cache_embeddings:
                await self._load_embedding_cache(table_name)

            # Create batches
            batches = self._create_embedding_batches(content_items)

            # Process batches
            result = await self._process_embedding_batches(
                conn_string, table_name, embedding_column, batches
            )

            # Save cache if enabled
            if self.cache_embeddings:
                await self._save_embedding_cache(table_name)

            # Create vector index
            index_created = await self._create_vector_index(
                conn_string, table_name, embedding_column
            )

            result.index_created = index_created
            result.duration_seconds = time.time() - start_time

            logger.info(f"Embedding generation completed for {table_name}")
            return result

        except Exception as e:
            logger.error(f"Embedding generation failed for {table_name}: {str(e)}")
            return EmbeddingResult(
                table_name=table_name,
                total_items=0,
                processed_items=0,
                cached_items=0,
                failed_items=0,
                duration_seconds=time.time() - start_time,
                status=EmbeddingStatus.FAILED,
            )

    async def setup_vector_search(
        self,
        conn_string: str,
        table_name: str,
        embedding_column: str = "embedding",
        similarity_function: str = "cosine",
    ) -> bool:
        """
        Setup vector similarity search infrastructure.

        Args:
            conn_string: Database connection string
            table_name: Table with embeddings
            embedding_column: Column containing embeddings
            similarity_function: Similarity function (cosine, l2, inner_product)

        Returns:
            Success status
        """
        logger.info(f"Setting up vector search for {table_name}")

        try:
            conn = await asyncpg.connect(conn_string)

            # Enable pgvector extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

            # Create similarity search function
            function_name = f"search_{table_name}_by_similarity"
            await self._create_similarity_function(
                conn, function_name, table_name, embedding_column, similarity_function
            )

            # Create index for performance
            await self._create_vector_index(conn_string, table_name, embedding_column)

            await conn.close()

            logger.info(f"Vector search setup completed for {table_name}")
            return True

        except Exception as e:
            logger.error(f"Vector search setup failed: {str(e)}")
            return False

    async def similarity_search(
        self,
        conn_string: str,
        table_name: str,
        query_text: str,
        embedding_column: str = "embedding",
        limit: int = 10,
        similarity_threshold: float = 0.5,
        similarity_function: str = "cosine",
    ) -> list[dict[str, Any]]:
        """
        Perform similarity search using embeddings.

        Args:
            conn_string: Database connection string
            table_name: Table to search
            query_text: Text to search for
            embedding_column: Column containing embeddings
            limit: Number of results to return
            similarity_threshold: Minimum similarity score
            similarity_function: Similarity function to use

        Returns:
            List of similar items with scores
        """
        logger.info(f"Performing similarity search in {table_name}")

        try:
            # Generate embedding for query
            query_embedding = await self._generate_single_embedding(query_text)

            if not query_embedding:
                return []

            # Perform search
            conn = await asyncpg.connect(conn_string)

            # Build similarity query
            if similarity_function == "cosine":
                similarity_expr = f"1 - ({embedding_column} <=> $1)"
            elif similarity_function == "l2":
                similarity_expr = f"1 / (1 + ({embedding_column} <-> $1))"
            else:  # inner_product
                similarity_expr = f"{embedding_column} <#> $1"

            query = f"""
            SELECT *,
                   {similarity_expr} as similarity_score
            FROM {table_name}
            WHERE {embedding_column} IS NOT NULL
              AND {similarity_expr} >= $2
            ORDER BY {similarity_expr} DESC
            LIMIT $3
            """

            results = await conn.fetch(query, query_embedding, similarity_threshold, limit)

            await conn.close()

            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Similarity search failed: {str(e)}")
            return []

    async def update_embeddings(
        self,
        conn_string: str,
        table_name: str,
        text_columns: list[str],
        embedding_column: str = "embedding",
        updated_since: Optional[str] = None,
    ) -> EmbeddingResult:
        """
        Update embeddings for modified content.

        Args:
            conn_string: Database connection string
            table_name: Table to update
            text_columns: Text columns to embed
            embedding_column: Embedding column
            updated_since: Only update items modified since this timestamp

        Returns:
            Update result
        """
        logger.info(f"Updating embeddings for {table_name}")

        # Build where clause for updates
        where_clause = f"{embedding_column} IS NULL"
        if updated_since:
            where_clause += f" OR updated_at > '{updated_since}'"

        return await self.generate_embeddings(
            conn_string,
            table_name,
            text_columns,
            embedding_column,
            where_clause=where_clause,
        )

    async def migrate_embeddings(
        self,
        source_conn_string: str,
        target_conn_string: str,
        table_name: str,
        embedding_column: str = "embedding",
    ) -> bool:
        """
        Migrate embeddings from source to target database.

        Args:
            source_conn_string: Source database connection
            target_conn_string: Target database connection
            table_name: Table to migrate
            embedding_column: Embedding column name

        Returns:
            Success status
        """
        logger.info(f"Migrating embeddings for {table_name}")

        try:
            # Setup target embedding column
            await self._setup_embedding_column(target_conn_string, table_name, embedding_column)

            # Get embeddings from source
            source_conn = await asyncpg.connect(source_conn_string)
            query = f"""
            SELECT id, {embedding_column}
            FROM {table_name}
            WHERE {embedding_column} IS NOT NULL
            """
            embeddings = await source_conn.fetch(query)
            await source_conn.close()

            if not embeddings:
                logger.info(f"No embeddings to migrate for {table_name}")
                return True

            # Update target database
            target_conn = await asyncpg.connect(target_conn_string)

            update_query = f"""
            UPDATE {table_name}
            SET {embedding_column} = $2
            WHERE id = $1
            """

            for row in embeddings:
                await target_conn.execute(update_query, row["id"], row[embedding_column])

            await target_conn.close()

            logger.info(f"Embedding migration completed for {table_name}")
            return True

        except Exception as e:
            logger.error(f"Embedding migration failed: {str(e)}")
            return False

    async def _setup_embedding_column(
        self, conn_string: str, table_name: str, embedding_column: str
    ):
        """Setup embedding column in table."""
        conn = await asyncpg.connect(conn_string)
        try:
            # Enable pgvector extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

            # Check if column exists
            check_query = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = $1 AND column_name = $2
            """
            exists = await conn.fetchrow(check_query, table_name, embedding_column)

            if not exists:
                # Add embedding column
                alter_query = f"""
                ALTER TABLE {table_name}
                ADD COLUMN {embedding_column} vector(1536)
                """
                await conn.execute(alter_query)
                logger.info(f"Added embedding column to {table_name}")

        finally:
            await conn.close()

    async def _get_content_items(
        self,
        conn_string: str,
        table_name: str,
        text_columns: list[str],
        embedding_column: str,
        where_clause: str,
    ) -> list[dict[str, Any]]:
        """Get content items that need embeddings."""
        conn = await asyncpg.connect(conn_string)
        try:
            # Build select query
            columns = ["id"] + text_columns
            column_list = ", ".join(columns)

            query = f"""
            SELECT {column_list}
            FROM {table_name}
            WHERE ({where_clause})
              AND ({embedding_column} IS NULL OR {embedding_column} = '[]'::vector)
            """

            rows = await conn.fetch(query)
            return [dict(row) for row in rows]

        finally:
            await conn.close()

    def _create_embedding_batches(
        self, content_items: list[dict[str, Any]]
    ) -> list[EmbeddingBatch]:
        """Create batches for embedding generation."""
        batches = []
        batch_id = 0

        for i in range(0, len(content_items), self.batch_size):
            batch_items = content_items[i : i + self.batch_size]
            batch = EmbeddingBatch(
                batch_id=batch_id,
                content_items=batch_items,
                status=EmbeddingStatus.PENDING,
            )
            batches.append(batch)
            batch_id += 1

        return batches

    async def _process_embedding_batches(
        self,
        conn_string: str,
        table_name: str,
        embedding_column: str,
        batches: list[EmbeddingBatch],
    ) -> EmbeddingResult:
        """Process embedding batches."""
        start_time = time.time()
        processed_items = 0
        cached_items = 0
        failed_items = 0

        # Create semaphore for rate limiting
        semaphore = asyncio.Semaphore(self.max_concurrent_batches)

        async def process_batch(batch: EmbeddingBatch) -> dict[str, int]:
            async with semaphore:
                return await self._process_single_embedding_batch(
                    conn_string, table_name, embedding_column, batch
                )

        # Process batches concurrently
        tasks = [process_batch(batch) for batch in batches]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        total_items = sum(len(batch.content_items) for batch in batches)

        for result in results:
            if isinstance(result, Exception):
                failed_items += self.batch_size  # Estimate
                logger.error(f"Batch processing failed: {str(result)}")
            else:
                processed_items += result.get("processed", 0)
                cached_items += result.get("cached", 0)
                failed_items += result.get("failed", 0)

        # Determine status
        if failed_items == 0:
            status = EmbeddingStatus.COMPLETED
        elif processed_items > 0:
            status = EmbeddingStatus.COMPLETED  # Partial success
        else:
            status = EmbeddingStatus.FAILED

        return EmbeddingResult(
            table_name=table_name,
            total_items=total_items,
            processed_items=processed_items,
            cached_items=cached_items,
            failed_items=failed_items,
            duration_seconds=time.time() - start_time,
            status=status,
        )

    async def _process_single_embedding_batch(
        self,
        conn_string: str,
        table_name: str,
        embedding_column: str,
        batch: EmbeddingBatch,
    ) -> dict[str, int]:
        """Process a single embedding batch."""
        batch.started_at = time.time()
        batch.status = EmbeddingStatus.IN_PROGRESS

        processed = 0
        cached = 0
        failed = 0

        try:
            # Prepare texts for embedding
            texts_to_embed = []
            item_map = {}

            for item in batch.content_items:
                # Combine text columns
                combined_text = self._combine_text_fields(item)
                text_hash = self._hash_text(combined_text)

                # Check cache
                if self.cache_embeddings and text_hash in self.embedding_cache:
                    # Update database with cached embedding
                    await self._update_embedding(
                        conn_string,
                        table_name,
                        embedding_column,
                        item["id"],
                        self.embedding_cache[text_hash],
                    )
                    cached += 1
                else:
                    texts_to_embed.append(combined_text)
                    item_map[len(texts_to_embed) - 1] = (item["id"], text_hash)

            # Generate embeddings for non-cached items
            if texts_to_embed:
                embeddings = await self._generate_embeddings_batch(texts_to_embed)

                for idx, embedding in enumerate(embeddings):
                    if embedding:
                        item_id, text_hash = item_map[idx]

                        # Update database
                        await self._update_embedding(
                            conn_string,
                            table_name,
                            embedding_column,
                            item_id,
                            embedding,
                        )

                        # Cache embedding
                        if self.cache_embeddings:
                            self.embedding_cache[text_hash] = embedding

                        processed += 1
                    else:
                        failed += 1

            batch.status = EmbeddingStatus.COMPLETED
            batch.completed_at = time.time()

            # Progress callback
            if self.progress_callback:
                await self.progress_callback(
                    {
                        "table": table_name,
                        "batch_id": batch.batch_id,
                        "processed": processed,
                        "cached": cached,
                        "failed": failed,
                    }
                )

            return {"processed": processed, "cached": cached, "failed": failed}

        except Exception as e:
            batch.status = EmbeddingStatus.FAILED
            batch.error_message = str(e)
            logger.error(f"Embedding batch {batch.batch_id} failed: {str(e)}")
            return {"processed": 0, "cached": 0, "failed": len(batch.content_items)}

    async def _generate_embeddings_batch(self, texts: list[str]) -> list[Optional[list[float]]]:
        """Generate embeddings for a batch of texts."""
        try:
            response = await self.client.embeddings.create(input=texts, model=self.embedding_model)

            embeddings = []
            for embedding_data in response.data:
                embeddings.append(embedding_data.embedding)

            return embeddings

        except Exception as e:
            logger.error(f"OpenAI embedding generation failed: {str(e)}")
            return [None] * len(texts)

    async def _generate_single_embedding(self, text: str) -> Optional[list[float]]:
        """Generate embedding for a single text."""
        try:
            response = await self.client.embeddings.create(input=[text], model=self.embedding_model)
            return response.data[0].embedding

        except Exception as e:
            logger.error(f"Single embedding generation failed: {str(e)}")
            return None

    def _combine_text_fields(self, item: dict[str, Any]) -> str:
        """Combine text fields into a single string."""
        text_parts = []
        for key, value in item.items():
            if key != "id" and value and isinstance(value, str):
                text_parts.append(value.strip())

        return " ".join(text_parts)

    def _hash_text(self, text: str) -> str:
        """Generate hash for text caching."""
        return hashlib.md5(text.encode()).hexdigest()

    async def _update_embedding(
        self,
        conn_string: str,
        table_name: str,
        embedding_column: str,
        item_id: Any,
        embedding: list[float],
    ):
        """Update embedding in database."""
        conn = await asyncpg.connect(conn_string)
        try:
            query = f"""
            UPDATE {table_name}
            SET {embedding_column} = $2
            WHERE id = $1
            """
            await conn.execute(query, item_id, embedding)

        finally:
            await conn.close()

    async def _create_vector_index(
        self, conn_string: str, table_name: str, embedding_column: str
    ) -> bool:
        """Create vector index for similarity search."""
        try:
            conn = await asyncpg.connect(conn_string)

            # Create HNSW index for cosine similarity
            index_name = f"idx_{table_name}_{embedding_column}_cosine"
            create_index_query = f"""
            CREATE INDEX IF NOT EXISTS {index_name}
            ON {table_name}
            USING hnsw ({embedding_column} vector_cosine_ops)
            """

            await conn.execute(create_index_query)
            await conn.close()

            logger.info(f"Created vector index {index_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create vector index: {str(e)}")
            return False

    async def _create_similarity_function(
        self,
        conn: asyncpg.Connection,
        function_name: str,
        table_name: str,
        embedding_column: str,
        similarity_function: str,
    ):
        """Create similarity search function."""
        if similarity_function == "cosine":
            distance_op = "<=>"
        elif similarity_function == "l2":
            distance_op = "<->"
        else:  # inner_product
            distance_op = "<#>"

        function_sql = f"""
        CREATE OR REPLACE FUNCTION {function_name}(
            query_embedding vector(1536),
            match_count int DEFAULT 10,
            similarity_threshold float DEFAULT 0.5
        )
        RETURNS TABLE(
            id int,
            content text,
            similarity float
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN QUERY
            SELECT
                t.id,
                t.content,
                1 - (t.{embedding_column} {distance_op} query_embedding) as similarity
            FROM {table_name} t
            WHERE t.{embedding_column} IS NOT NULL
              AND 1 - (t.{embedding_column} {distance_op} query_embedding) >= similarity_threshold
            ORDER BY t.{embedding_column} {distance_op} query_embedding
            LIMIT match_count;
        END;
        $$;
        """

        await conn.execute(function_sql)
        logger.info(f"Created similarity function {function_name}")

    async def _load_embedding_cache(self, table_name: str):
        """Load embedding cache from file."""
        if not self.cache_embeddings:
            return

        cache_file = f"embedding_cache_{table_name}.json"
        try:
            async with aiofiles.open(cache_file) as f:
                cache_data = json.loads(await f.read())
                self.embedding_cache.update(cache_data)
                logger.info(f"Loaded {len(cache_data)} cached embeddings")

        except FileNotFoundError:
            logger.info("No embedding cache found, starting fresh")
        except Exception as e:
            logger.warning(f"Failed to load embedding cache: {str(e)}")

    async def _save_embedding_cache(self, table_name: str):
        """Save embedding cache to file."""
        if not self.cache_embeddings or not self.embedding_cache:
            return

        cache_file = f"embedding_cache_{table_name}.json"
        try:
            async with aiofiles.open(cache_file, "w") as f:
                await f.write(json.dumps(self.embedding_cache))
                logger.info(f"Saved {len(self.embedding_cache)} embeddings to cache")

        except Exception as e:
            logger.warning(f"Failed to save embedding cache: {str(e)}")

    def get_embedding_stats(self) -> dict[str, Any]:
        """Get embedding generation statistics."""
        return {
            "cache_size": len(self.embedding_cache),
            "embedding_model": self.embedding_model,
            "batch_size": self.batch_size,
            "max_concurrent_batches": self.max_concurrent_batches,
        }
