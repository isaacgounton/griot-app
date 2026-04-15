"""
Knowledge base management for agent workflows.
"""

from __future__ import annotations

import os
import tempfile
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, delete, func, update
from sqlalchemy.exc import SQLAlchemyError

from agno.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector, SearchType
from agno.db.postgres import PostgresDb
from agno.knowledge.reader.pdf_reader import PDFReader
from agno.knowledge.chunking.recursive import RecursiveChunking

from app.database import (
    database_service,
    AgentKnowledgeBaseRecord,
    AgentKnowledgeDocumentRecord,
    AgentDocumentStatus,
)
from app.services.agents.utils import normalize_owner_identifier
from app.database import get_db_url
from loguru import logger


SUPPORTED_CONTENT_TYPES = {
    "application/pdf": ".pdf",
}


class KnowledgeBaseService:
    """Service responsible for managing knowledge bases and documents."""

    def __init__(self) -> None:
        self.db_url = get_db_url()
        self._pdf_reader = PDFReader(
            name="Agent PDF Reader",
            chunking_strategy=RecursiveChunking(chunk_size=1000, overlap=100),
        )

    # ------------------------------------------------------------------
    # Knowledge base management
    # ------------------------------------------------------------------
    async def list_knowledge_bases(self, owner_identifier: Optional[str]) -> List[Dict[str, Any]]:
        if not database_service.is_database_available():
            logger.warning("Database not available, returning empty knowledge bases list")
            return []
            
        owner_hash = normalize_owner_identifier(owner_identifier)
        if not owner_hash:
            return []

        try:
            async for session in database_service.get_session():
                result = await session.execute(
                    select(AgentKnowledgeBaseRecord)
                    .where(AgentKnowledgeBaseRecord.owner_hash == owner_hash)
                    .order_by(AgentKnowledgeBaseRecord.updated_at.desc())
                )
                bases = result.scalars().all()
                return [self._record_to_dict(base) for base in bases]
        except (SQLAlchemyError, RuntimeError) as exc:
            logger.exception("Failed to list knowledge bases: %s", exc)
        return []

    async def create_knowledge_base(
        self,
        owner_identifier: Optional[str],
        name: str,
        description: Optional[str] = None,
        embedding_model: Optional[str] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
    ) -> Dict[str, Any]:
        if not database_service.is_database_available():
            raise ValueError("Database is not available")
            
        owner_hash = normalize_owner_identifier(owner_identifier)
        if not owner_hash:
            raise ValueError("Owner identifier is required to create a knowledge base")

        base_record = AgentKnowledgeBaseRecord(
            owner_hash=owner_hash,
            name=name,
            description=description,
            vector_table=f"kb_vectors_{uuid.uuid4().hex}",
            contents_table=f"kb_contents_{uuid.uuid4().hex}",
            embedding_model=embedding_model,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            metadata={},
        )

        try:
            async for session in database_service.get_session():
                session.add(base_record)
                await session.commit()
                await session.refresh(base_record)
                return self._record_to_dict(base_record)
        except SQLAlchemyError as exc:
            logger.exception("Failed to create knowledge base: %s", exc)
            raise

    async def get_knowledge_base(
        self,
        owner_identifier: Optional[str],
        knowledge_base_id: uuid.UUID,
    ) -> Optional[AgentKnowledgeBaseRecord]:
        if not database_service.is_database_available():
            return None
            
        owner_hash = normalize_owner_identifier(owner_identifier)
        if not owner_hash:
            return None

        try:
            async for session in database_service.get_session():
                result = await session.execute(
                    select(AgentKnowledgeBaseRecord).where(
                        AgentKnowledgeBaseRecord.id == knowledge_base_id,
                        AgentKnowledgeBaseRecord.owner_hash == owner_hash,
                    )
                )
                return result.scalar_one_or_none()
        except SQLAlchemyError as exc:
            logger.exception("Failed to load knowledge base %s: %s", knowledge_base_id, exc)
        return None

    async def delete_knowledge_base(self, owner_identifier: Optional[str], knowledge_base_id: uuid.UUID) -> bool:
        if not database_service.is_database_available():
            return False
            
        owner_hash = normalize_owner_identifier(owner_identifier)
        if not owner_hash:
            return False

        try:
            async for session in database_service.get_session():
                result = await session.execute(
                    delete(AgentKnowledgeBaseRecord).where(
                        AgentKnowledgeBaseRecord.id == knowledge_base_id,
                        AgentKnowledgeBaseRecord.owner_hash == owner_hash,
                    )
                )
                await session.commit()
                return bool(result.rowcount)
        except SQLAlchemyError as exc:
            logger.exception("Failed to delete knowledge base %s: %s", knowledge_base_id, exc)
            return False

    # ------------------------------------------------------------------
    # Document management
    # ------------------------------------------------------------------
    async def list_documents(
        self,
        owner_identifier: Optional[str],
        knowledge_base_id: uuid.UUID,
    ) -> List[Dict[str, Any]]:
        if not database_service.is_database_available():
            return []
            
        base_record = await self.get_knowledge_base(owner_identifier, knowledge_base_id)
        if not base_record:
            return []

        try:
            async for session in database_service.get_session():
                result = await session.execute(
                    select(AgentKnowledgeDocumentRecord)
                    .where(AgentKnowledgeDocumentRecord.knowledge_base_id == knowledge_base_id)
                    .order_by(AgentKnowledgeDocumentRecord.created_at.desc())
                )
                docs = result.scalars().all()
                return [self._document_to_dict(doc) for doc in docs]
        except SQLAlchemyError as exc:
            logger.exception("Failed to list knowledge base documents: %s", exc)
        return []

    async def add_document(
        self,
        owner_identifier: Optional[str],
        knowledge_base_id: uuid.UUID,
        filename: str,
        content_type: str,
        file_bytes: bytes,
        metadata: Optional[dict] = None,
    ) -> Dict[str, Any]:
        if not database_service.is_database_available():
            raise ValueError("Database is not available")
            
        base_record = await self.get_knowledge_base(owner_identifier, knowledge_base_id)
        if not base_record:
            raise ValueError("Knowledge base not found")

        suffix = SUPPORTED_CONTENT_TYPES.get(content_type)
        if not suffix:
            raise ValueError(f"Unsupported content type: {content_type}")

        document_record = AgentKnowledgeDocumentRecord(
            knowledge_base_id=knowledge_base_id,
            filename=filename,
            content_type=content_type,
            size_bytes=len(file_bytes),
            storage_path=None,
            status=AgentDocumentStatus.PENDING,
            metadata=metadata or {},
        )

        try:
            async for session in database_service.get_session():
                session.add(document_record)
                await session.commit()
                await session.refresh(document_record)
                break
        except SQLAlchemyError as exc:
            logger.exception("Failed to persist knowledge document metadata: %s", exc)
            raise

        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(file_bytes)
                temp_path = temp_file.name

            knowledge = self._build_knowledge_client(base_record)
            await knowledge.add_content_async(
                path=temp_path,
                reader=self._pdf_reader,
                metadata={
                    "document_id": str(document_record.id),
                    "filename": filename,
                    "owner_hash": base_record.owner_hash,
                },
                skip_if_exists=True,
            )

            await self._update_document_status(
                document_id=document_record.id,
                status=AgentDocumentStatus.COMPLETED,
            )
            await self._update_base_stats(base_record.id)
            return await self._fetch_document_dict(document_record.id)

        except Exception as exc:  # pragma: no cover - safety net
            logger.exception("Failed to ingest knowledge base document: %s", exc)
            await self._update_document_status(
                document_id=document_record.id,
                status=AgentDocumentStatus.FAILED,
                metadata={"error": str(exc)},
            )
            raise
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    logger.debug("Temporary knowledge upload file already removed: %s", temp_path)

    async def search(
        self,
        owner_identifier: Optional[str],
        knowledge_base_id: uuid.UUID,
        query: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        if not database_service.is_database_available():
            return []
            
        base_record = await self.get_knowledge_base(owner_identifier, knowledge_base_id)
        if not base_record:
            raise ValueError("Knowledge base not found")

        knowledge = self._build_knowledge_client(base_record)
        results = await knowledge.async_search(query, max_results=limit)
        serialized = []
        for result in results:
            serialized.append(
                {
                    "id": getattr(result, "id", None),
                    "text": getattr(result, "content", None) or getattr(result, "text", None),
                    "score": getattr(result, "score", None),
                    "metadata": getattr(result, "metadata", {}) or {},
                }
            )
        return serialized

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_knowledge_client(self, base_record: AgentKnowledgeBaseRecord) -> Knowledge:
        vector_db = PgVector(
            table_name=base_record.vector_table,
            db_url=self.db_url,
            search_type=SearchType.hybrid,
        )
        contents_db = PostgresDb(
            db_url=self.db_url,
            knowledge_table=base_record.contents_table,
        )
        return Knowledge(
            name=base_record.name,
            description=base_record.description,
            vector_db=vector_db,
            contents_db=contents_db,
        )

    async def _update_document_status(
        self,
        document_id: uuid.UUID,
        status: AgentDocumentStatus,
        metadata: Optional[dict] = None,
    ) -> None:
        try:
            async for session in database_service.get_session():
                # Build update values - only include metadata if it's provided
                update_values = {
                    "status": status,
                    "updated_at": datetime.utcnow(),
                }
                if metadata is not None:
                    update_values["meta"] = metadata
                
                await session.execute(
                    update(AgentKnowledgeDocumentRecord)
                    .where(AgentKnowledgeDocumentRecord.id == document_id)
                    .values(**update_values)
                )
                await session.commit()
        except SQLAlchemyError as exc:
            logger.warning("Failed to update knowledge document status: %s", exc)

    async def _update_base_stats(self, knowledge_base_id: uuid.UUID) -> None:
        try:
            async for session in database_service.get_session():
                result = await session.execute(
                    select(
                        func.count(AgentKnowledgeDocumentRecord.id),
                        func.coalesce(func.sum(AgentKnowledgeDocumentRecord.size_bytes), 0),
                    ).where(AgentKnowledgeDocumentRecord.knowledge_base_id == knowledge_base_id)
                )
                count, total_size = result.one()
                await session.execute(
                    update(AgentKnowledgeBaseRecord)
                    .where(AgentKnowledgeBaseRecord.id == knowledge_base_id)
                    .values(
                        document_count=count,
                        total_size_bytes=total_size or 0,
                        updated_at=datetime.utcnow(),
                    )
                )
                await session.commit()
        except SQLAlchemyError as exc:
            logger.warning("Failed to update knowledge base stats: %s", exc)

    async def _fetch_document_dict(self, document_id: uuid.UUID) -> Dict[str, Any]:
        async for session in database_service.get_session():
            result = await session.execute(
                select(AgentKnowledgeDocumentRecord).where(AgentKnowledgeDocumentRecord.id == document_id)
            )
            record = result.scalar_one_or_none()
            if record:
                return self._document_to_dict(record)
        raise ValueError("Document not found")

    @staticmethod
    def _record_to_dict(record: AgentKnowledgeBaseRecord) -> Dict[str, Any]:
        return {
            "id": str(record.id),
            "name": record.name,
            "description": record.description,
            "document_count": record.document_count,
            "size": record.total_size_bytes,
            "enabled": record.enabled,
            "chunk_size": record.chunk_size,
            "chunk_overlap": record.chunk_overlap,
            "embedding_model": record.embedding_model,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
        }

    @staticmethod
    def _document_to_dict(record: AgentKnowledgeDocumentRecord) -> Dict[str, Any]:
        return {
            "id": str(record.id),
            "knowledge_base_id": str(record.knowledge_base_id),
            "filename": record.filename,
            "content_type": record.content_type,
            "size": record.size_bytes,
            "status": record.status.value,
            "metadata": record.meta or {},
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
        }

    def serialize_base(self, record: AgentKnowledgeBaseRecord) -> Dict[str, Any]:
        return self._record_to_dict(record)

    def serialize_document(self, record: AgentKnowledgeDocumentRecord) -> Dict[str, Any]:
        return self._document_to_dict(record)


knowledge_base_service = KnowledgeBaseService()
