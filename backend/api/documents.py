from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from loguru import logger

from core.database import get_db
from schemas.document import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentListResponse,
    DocumentVersionResponse
)
from services.document_service import DocumentService


router = APIRouter()


@router.post("/", response_model=DocumentResponse, summary="创建文档")
async def create_document(
    document: DocumentCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建新文档
    
    - **title**: 文档标题
    - **content**: 文档内容
    - **doc_type**: 文档类型
    - **creator_id**: 创建人ID
    - **template_id**: 使用的模板ID（可选）
    """
    try:
        service = DocumentService(db)
        result = await service.create_document(
            title=document.title,
            content=document.content,
            doc_type=document.doc_type,
            creator_id=document.creator_id,
            doc_number=document.doc_number,
            template_id=document.template_id,
            tags=document.tags,
            attachments=document.attachments,
            metadata=document.metadata
        )
        return result.to_dict()
    except Exception as e:
        logger.error(f"创建文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", response_model=DocumentResponse, summary="获取文档详情")
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取文档详细信息"""
    try:
        service = DocumentService(db)
        document = await service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        return document.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=DocumentListResponse, summary="获取文档列表")
async def list_documents(
    doc_type: Optional[str] = Query(None, description="文档类型（不传则返回所有类型）"),
    status: Optional[str] = Query(None, description="文档状态（不传则返回所有状态）"),
    creator_id: Optional[str] = Query(None, description="创建人ID"),
    is_public: Optional[bool] = Query(None, description="是否公开"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回记录数"),
    order_by: str = Query("created_at", description="排序字段"),
    order_desc: bool = Query(True, description="是否降序"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取文档列表
    
    支持按文档类型、状态、创建人等筛选
    
    **默认行为（不传任何参数）：**
    - 返回所有类型的文档
    - 返回所有状态的文档
    - 按创建时间降序排列
    - 每页20条记录
    
    **筛选参数：**
    - `doc_type`: 文档类型筛选（如：通用、通知、申请）
    - `status`: 状态筛选（如：draft、reviewing、published）
    - `creator_id`: 按创建人筛选
    - `is_public`: 按是否公开筛选
    
    **分页参数：**
    - `skip`: 跳过的记录数（用于分页）
    - `limit`: 每页返回的记录数（1-100）
    
    **排序参数：**
    - `order_by`: 排序字段（默认：created_at）
    - `order_desc`: 是否降序（默认：true）
    """
    logger.info("=" * 50)
    logger.info("收到文档列表请求")
    logger.info(f"参数: doc_type={doc_type}, status={status}, skip={skip}, limit={limit}")
    
    try:
        service = DocumentService(db)
        documents, total = await service.list_documents(
            doc_type=doc_type,
            status=status,
            creator_id=creator_id,
            is_public=is_public,
            skip=skip,
            limit=limit,
            order_by=order_by,
            order_desc=order_desc
        )
        
        logger.info(f"查询结果: 总数={total}, 返回={len(documents)}")
        logger.info("=" * 50)
        
        return {
            "items": [doc.to_dict() for doc in documents],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"获取文档列表失败: {str(e)}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{document_id}", response_model=DocumentResponse, summary="更新文档")
async def update_document(
    document_id: str,
    document: DocumentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    更新文档
    
    可更新内容、状态、标签等字段
    """
    try:
        service = DocumentService(db)
        
        # 构建更新数据
        update_data = document.dict(exclude_unset=True)
        
        result = await service.update_document(document_id, **update_data)
        if not result:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        return result.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}", summary="删除文档")
async def delete_document(
    document_id: str,
    soft_delete: bool = Query(True, description="是否软删除"),
    db: AsyncSession = Depends(get_db)
):
    """
    删除文档
    
    - **soft_delete**: True表示软删除（标记为已删除），False表示硬删除
    """
    try:
        service = DocumentService(db)
        success = await service.delete_document(document_id, soft_delete=soft_delete)
        if not success:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        return {"message": "删除成功", "document_id": document_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{document_id}/publish", response_model=DocumentResponse, summary="发布文档")
async def publish_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """发布文档（状态变更为 published）"""
    try:
        service = DocumentService(db)
        result = await service.publish_document(document_id)
        if not result:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        return result.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发布文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{document_id}/archive", response_model=DocumentResponse, summary="归档文档")
async def archive_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """归档文档（状态变更为 archived）"""
    try:
        service = DocumentService(db)
        result = await service.archive_document(document_id)
        if not result:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        return result.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"归档文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/versions", response_model=List[DocumentVersionResponse], summary="获取文档版本历史")
async def get_document_versions(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取文档的所有版本历史"""
    try:
        service = DocumentService(db)
        versions = await service.get_document_versions(document_id)
        return [version.to_dict() for version in versions]
    except Exception as e:
        logger.error(f"获取文档版本失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{document_id}/versions/{version_id}/restore", response_model=DocumentResponse, summary="恢复文档版本")
async def restore_document_version(
    document_id: str,
    version_id: str,
    db: AsyncSession = Depends(get_db)
):
    """将文档恢复到指定版本"""
    try:
        service = DocumentService(db)
        result = await service.restore_version(document_id, version_id)
        if not result:
            raise HTTPException(status_code=404, detail="文档或版本不存在")
        
        return result.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"恢复文档版本失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/overview", summary="获取文档统计")
async def get_document_stats(
    db: AsyncSession = Depends(get_db)
):
    """获取文档统计信息"""
    try:
        service = DocumentService(db)
        stats = await service.get_statistics()
        return stats
    except Exception as e:
        logger.error(f"获取文档统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
