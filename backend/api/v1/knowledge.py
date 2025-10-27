from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from services.knowledge_service import KnowledgeService
from core.database import get_db

router = APIRouter(prefix="/knowledge", tags=["知识库管理"])


@router.post("/", summary="创建知识库")
async def create_knowledge_base(name: str, description: str = None, db: AsyncSession = Depends(get_db)):
    service = KnowledgeService(db)
    return await service.create_knowledge_base(name, description)


@router.post("/{knowledge_base_id}/documents/{document_id}", summary="将文档关联到知识库")
async def add_document_to_knowledge_base(knowledge_base_id: str, document_id: str, db: AsyncSession = Depends(get_db)):
    service = KnowledgeService(db)
    await service.add_document_to_knowledge_base(document_id, knowledge_base_id)
    return {"message": f"文档 {document_id} 已关联到知识库 {knowledge_base_id}"}


@router.get("/{knowledge_base_id}/documents", summary="列出知识库中的所有文档")
async def list_documents_in_knowledge_base(knowledge_base_id: str, db: AsyncSession = Depends(get_db)):
    service = KnowledgeService(db)
    return await service.list_documents_in_knowledge_base(knowledge_base_id)


@router.get("/documents/{document_id}/knowledge-bases", summary="列出文档所属的所有知识库")
async def list_knowledge_bases_for_document(document_id: str, db: AsyncSession = Depends(get_db)):
    service = KnowledgeService(db)
    return await service.list_knowledge_bases_for_document(document_id)
