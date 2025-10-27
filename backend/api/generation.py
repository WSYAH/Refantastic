from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from loguru import logger

from core.rag_engine import get_rag_engine
from core.search_engine import get_search_engine


router = APIRouter()


class GenerationRequest(BaseModel):
    """公文生成请求"""
    doc_type: str = Field(..., description="文档类型")
    theme: str = Field(..., description="主题")
    purpose: str = Field(..., description="目的")
    keywords: Optional[List[str]] = Field(None, description="关键词")
    requirements: Dict[str, Any] = Field(default_factory=dict, description="其他要求")
    use_rag: bool = Field(True, description="是否使用 RAG")


class GenerationResponse(BaseModel):
    """公文生成响应"""
    content: str
    references: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str = Field(..., description="查询文本")
    doc_type: Optional[str] = Field(None, description="文档类型")
    keywords: Optional[List[str]] = Field(None, description="关键词")
    top_k: int = Field(5, description="返回数量", ge=1, le=20)
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")


@router.post("/generate", response_model=GenerationResponse)
async def generate_document(request: GenerationRequest):
    """
    生成公文
    
    使用 RAG 技术，基于知识库中的历史公文和模板，生成新的公文内容。
    """
    try:
        rag_engine = get_rag_engine()
        
        # 合并要求
        requirements = {
            "theme": request.theme,
            "purpose": request.purpose,
            **request.requirements
        }
        
        # 生成公文
        result = await rag_engine.generate_document_with_rag(
            doc_type=request.doc_type,
            requirements=requirements,
            keywords=request.keywords
        )
        
        return GenerationResponse(**result)
        
    except Exception as e:
        logger.error(f"公文生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.post("/search-references")
async def search_references(request: SearchRequest):
    """
    搜索参考文档
    
    在知识库中搜索相关的参考文档，用于辅助写作。
    """
    try:
        search_engine = get_search_engine()
        
        # 使用搜索引擎
        results = await search_engine.search(
            query=request.query,
            doc_type=request.doc_type,
            keywords=request.keywords,
            top_k=request.top_k,
            filters=request.filters
        )
        
        return {
            "results": results,
            "total": len(results),
            "query": request.query
        }
        
    except Exception as e:
        logger.error(f"搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/similar/{document_id}")
async def find_similar_documents(
    document_id: str,
    top_k: int = 5
):
    """
    查找相似文档
    
    根据文档ID查找相似的文档。
    """
    try:
        search_engine = get_search_engine()
        
        results = await search_engine.search_similar_documents(
            document_id=document_id,
            top_k=top_k
        )
        
        return {
            "document_id": document_id,
            "similar_documents": results,
            "total": len(results)
        }
        
    except Exception as e:
        logger.error(f"查找相似文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查找失败: {str(e)}")
