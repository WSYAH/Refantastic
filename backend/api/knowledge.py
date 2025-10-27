from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from loguru import logger

from services.knowledge_service import get_knowledge_service, KnowledgeService
from core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from services.file_service import get_file_service


router = APIRouter()


class CreateDocumentRequest(BaseModel):
    """创建文档请求"""
    title: str = Field(..., description="标题")
    content: str = Field(..., description="内容")
    doc_type: str = Field(..., description="文档类型")
    author: Optional[str] = Field(None, description="作者")
    department: Optional[str] = Field(None, description="部门")
    tags: Optional[List[str]] = Field(None, description="标签")
    keywords: Optional[List[str]] = Field(None, description="关键词")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    auto_vectorize: bool = Field(True, description="是否自动向量化")


class UpdateDocumentRequest(BaseModel):
    """更新文档请求"""
    title: Optional[str] = None
    content: Optional[str] = None
    doc_type: Optional[str] = None
    author: Optional[str] = None
    department: Optional[str] = None
    tags: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class SearchDocumentRequest(BaseModel):
    """搜索文档请求"""
    query: str = Field(..., description="搜索关键词")
    doc_type: Optional[str] = Field(None, description="文档类型")
    tags: Optional[List[str]] = Field(None, description="标签过滤")
    top_k: int = Field(10, description="返回数量", ge=1, le=50)


@router.post("/documents")
async def create_document(
    request: CreateDocumentRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    创建知识库文档
    
    支持自动向量化，文档创建后会自动添加到向量库以支持语义检索。
    """
    try:
        service = await get_knowledge_service(db)
        
        document = await service.create_document(
            title=request.title,
            content=request.content,
            doc_type=request.doc_type,
            author=request.author,
            department=request.department,
            tags=request.tags,
            keywords=request.keywords,
            metadata=request.metadata,
            auto_vectorize=request.auto_vectorize
        )
        
        return {
            "success": True,
            "document": document.to_dict()
        }
        
    except Exception as e:
        logger.error(f"创建文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.get("/documents/{doc_id}")
async def get_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取文档详情"""
    try:
        service = await get_knowledge_service(db)
        document = await service.get_document(doc_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        return {
            "success": True,
            "document": document.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/documents")
async def list_documents(
    doc_type: Optional[str] = None,
    status: str = "active",
    is_public: Optional[bool] = None,
    skip: int = 0,
    limit: int = 20,
    order_by: str = "created_at",
    order_desc: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    列出文档
    
    支持按文档类型、状态、可见性过滤，以及分页和排序。
    """
    try:
        service = await get_knowledge_service(db)
        
        documents, total = await service.list_documents(
            doc_type=doc_type,
            status=status,
            is_public=is_public,
            skip=skip,
            limit=limit,
            order_by=order_by,
            order_desc=order_desc
        )
        
        return {
            "success": True,
            "documents": [doc.to_dict() for doc in documents],
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"列出文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"列出失败: {str(e)}")


@router.put("/documents/{doc_id}")
async def update_document(
    doc_id: str,
    request: UpdateDocumentRequest,
    db: AsyncSession = Depends(get_db)
):
    """更新文档"""
    try:
        service = await get_knowledge_service(db)
        
        # 只更新非None的字段
        updates = {k: v for k, v in request.dict().items() if v is not None}
        
        document = await service.update_document(doc_id, **updates)
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        return {
            "success": True,
            "document": document.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    soft_delete: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """删除文档"""
    try:
        service = await get_knowledge_service(db)
        
        success = await service.delete_document(doc_id, soft_delete=soft_delete)
        
        if not success:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        return {
            "success": True,
            "message": "删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.post("/documents/search")
async def search_documents(
    request: SearchDocumentRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    搜索文档
    
    结合数据库关键词搜索和向量语义检索，提供更准确的搜索结果。
    """
    try:
        service = await get_knowledge_service(db)
        
        results = await service.search_documents(
            query=request.query,
            doc_type=request.doc_type,
            tags=request.tags,
            top_k=request.top_k
        )
        
        return {
            "success": True,
            "results": results,
            "total": len(results),
            "query": request.query
        }
        
    except Exception as e:
        logger.error(f"搜索文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.post("/documents/{doc_id}/vectorize")
async def vectorize_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db)
):
    """向量化单个文档"""
    try:
        service = await get_knowledge_service(db)
        
        success = await service.vectorize_document(doc_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="向量化失败")
        
        return {
            "success": True,
            "message": "向量化成功",
            "doc_id": doc_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"向量化失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"向量化失败: {str(e)}")


@router.post("/documents/batch-vectorize")
async def batch_vectorize_documents(
    doc_ids: Optional[List[str]] = None,
    force: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    批量向量化文档
    
    如果不指定 doc_ids，则向量化所有未向量化的文档。
    """
    try:
        service = await get_knowledge_service(db)
        
        result = await service.batch_vectorize(doc_ids=doc_ids, force=force)
        
        return {
            "success": True,
            **result
        }
        
    except Exception as e:
        logger.error(f"批量向量化失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量向量化失败: {str(e)}")


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    doc_type: str = Form(...),
    author: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    extract_images: bool = Form(True),
    extract_tables: bool = Form(True),
    table_format: str = Form("markdown"),
    auto_vectorize: bool = Form(True),
    db: AsyncSession = Depends(get_db)
):
    """
    上传文档文件
    
    支持格式：PDF、DOCX、HTML、TXT、图片（JPG、PNG等）
    自动提取内容、表格和图片信息。
    """
    try:
        file_service = get_file_service()
        
        # 检查文件类型
        if not file_service.is_supported(file.filename):
            supported = ", ".join(file_service.get_supported_extensions())
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型。支持的格式: {supported}"
            )
        
        # 读取文件内容
        content = await file.read()
        
        # 处理文件
        process_result = await file_service.process_upload(
            file_content=content,
            filename=file.filename,
            extract_images=extract_images,
            extract_tables=extract_tables,
            table_format=table_format
        )
        
        # 创建知识库文档
        service = await get_knowledge_service(db)
        
        document = await service.create_document(
            title=title,
            content=process_result["content"],
            doc_type=doc_type,
            author=author,
            department=department,
            metadata={
                **process_result["metadata"],
                "image_count": len(process_result["images"]),
                "table_count": len(process_result["tables"]),
                "has_images": len(process_result["images"]) > 0,
                "has_tables": len(process_result["tables"]) > 0,
            },
            auto_vectorize=auto_vectorize
        )
        
        return {
            "success": True,
            "document": document.to_dict(),
            "processing_info": {
                "text_length": len(process_result["content"]),
                "image_count": len(process_result["images"]),
                "table_count": len(process_result["tables"]),
                "file_size": process_result["file_size"],
                "file_hash": process_result["file_hash"]
            },
            "message": "上传成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/supported-formats")
async def get_supported_formats():
    """获取支持的文件格式"""
    file_service = get_file_service()
    
    formats = {
        "documents": ["pdf", "docx", "doc", "txt", "md"],
        "web": ["html", "htm"],
        "images": ["jpg", "jpeg", "png", "bmp", "gif"],
        "all": file_service.get_supported_extensions()
    }
    
    return {
        "success": True,
        "formats": formats,
        "total": len(formats["all"])
    }


# 分类管理
@router.get("/categories")
async def list_categories(db: AsyncSession = Depends(get_db)):
    """列出所有分类"""
    try:
        service = await get_knowledge_service(db)
        categories = await service.list_categories()
        
        return {
            "success": True,
            "categories": [cat.to_dict() for cat in categories]
        }
        
    except Exception as e:
        logger.error(f"列出分类失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"列出失败: {str(e)}")
