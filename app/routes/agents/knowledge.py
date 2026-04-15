"""
Knowledge base routes for the agents experience.
"""

from __future__ import annotations

import uuid
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Query
from pydantic import BaseModel

from app.services.agents.knowledge_service import knowledge_base_service, SUPPORTED_CONTENT_TYPES
from app.utils.auth import get_current_user


router = APIRouter(prefix="/knowledge-bases", tags=["Agents"])


class KnowledgeBaseCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    embedding_model: Optional[str] = None
    chunk_size: Optional[int] = 1000
    chunk_overlap: Optional[int] = 100


class KnowledgeBaseSearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 5


@router.get("")
async def list_knowledge_bases(current_user: Dict[str, Any] = Depends(get_current_user)):
    bases = await knowledge_base_service.list_knowledge_bases(current_user["user_id"])
    return {"knowledge_bases": bases}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(
    payload: KnowledgeBaseCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    try:
        base = await knowledge_base_service.create_knowledge_base(
            owner_identifier=current_user["user_id"],
            name=payload.name,
            description=payload.description,
            embedding_model=payload.embedding_model,
            chunk_size=payload.chunk_size or 1000,
            chunk_overlap=payload.chunk_overlap or 100,
        )
        return base
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/{knowledge_base_id}")
async def get_knowledge_base(
    knowledge_base_id: uuid.UUID,
    include_documents: bool = Query(False, description="Include uploaded documents"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    record = await knowledge_base_service.get_knowledge_base(current_user["user_id"], knowledge_base_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found")

    base_dict = knowledge_base_service.serialize_base(record)
    if include_documents:
        documents = await knowledge_base_service.list_documents(current_user["user_id"], knowledge_base_id)
        base_dict["documents"] = documents
    return base_dict


@router.delete("/{knowledge_base_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base(
    knowledge_base_id: uuid.UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    deleted = await knowledge_base_service.delete_knowledge_base(current_user["user_id"], knowledge_base_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found")
    return {}


@router.get("/{knowledge_base_id}/documents")
async def list_knowledge_documents(
    knowledge_base_id: uuid.UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    documents = await knowledge_base_service.list_documents(current_user["user_id"], knowledge_base_id)
    return {"documents": documents}


@router.post("/{knowledge_base_id}/documents", status_code=status.HTTP_201_CREATED)
async def upload_knowledge_document(
    knowledge_base_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required")

    content_type = file.content_type or "application/octet-stream"
    if content_type not in SUPPORTED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported content type '{content_type}'. Supported: {', '.join(SUPPORTED_CONTENT_TYPES.keys())}",
        )

    file_bytes = await file.read()
    try:
        document = await knowledge_base_service.add_document(
            owner_identifier=current_user["user_id"],
            knowledge_base_id=knowledge_base_id,
            filename=file.filename,
            content_type=content_type,
            file_bytes=file_bytes,
        )
        return document
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/{knowledge_base_id}/search")
async def search_knowledge_base(
    knowledge_base_id: uuid.UUID,
    payload: KnowledgeBaseSearchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    try:
        results = await knowledge_base_service.search(
            owner_identifier=current_user["user_id"],
            knowledge_base_id=knowledge_base_id,
            query=payload.query,
            limit=payload.limit or 5,
        )
        return {"results": results}
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
