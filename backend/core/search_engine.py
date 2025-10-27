from typing import List, Dict, Any, Optional
from loguru import logger

from config import get_settings
from core.vector_store import get_vector_store


class SearchEngine:
    """
    文档搜索引擎
    
    负责文档检索、重排序、过滤等功能
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.vector_store = get_vector_store()
        logger.info("搜索引擎初始化完成")
    
    async def search(
        self,
        query: str,
        doc_type: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索文档
        
        Args:
            query: 查询文本
            doc_type: 文档类型过滤
            keywords: 关键词列表
            top_k: 返回结果数量
            filters: 其他过滤条件
        
        Returns:
            搜索结果列表
        """
        try:
            logger.info(f"执行搜索，查询：{query[:50]}...")
            
            # 1. 向量检索
            vector_results = await self._vector_search(
                query=query,
                doc_type=doc_type,
                top_k=top_k * 3  # 多检索一些，后续过滤
            )
            
            # 2. 关键词增强
            if keywords:
                vector_results = self._enhance_with_keywords(
                    results=vector_results,
                    keywords=keywords
                )
            
            # 3. 重排序
            ranked_results = self._rerank(
                results=vector_results,
                query=query,
                doc_type=doc_type,
                keywords=keywords
            )
            
            # 4. 过滤
            filtered_results = self._filter(
                results=ranked_results,
                filters=filters
            )
            
            # 5. 格式化输出
            formatted_results = self._format_results(
                results=filtered_results[:top_k]
            )
            
            logger.info(f"搜索完成，返回 {len(formatted_results)} 个结果")
            return formatted_results
            
        except Exception as e:
            logger.error(f"搜索失败: {str(e)}")
            raise
    
    async def _vector_search(
        self,
        query: str,
        doc_type: Optional[str],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """向量相似度搜索"""
        try:
            results = await self.vector_store.hybrid_search(
                query=query,
                doc_type=doc_type,
                top_k=top_k
            )
            logger.debug(f"向量搜索返回 {len(results)} 个结果")
            return results
        except Exception as e:
            logger.error(f"向量搜索失败: {str(e)}")
            return []
    
    def _enhance_with_keywords(
        self,
        results: List[Dict[str, Any]],
        keywords: List[str]
    ) -> List[Dict[str, Any]]:
        """使用关键词增强搜索结果"""
        for result in results:
            content = result.get("content", "").lower()
            title = result.get("title", "").lower()
            
            # 计算关键词匹配度
            matched_in_content = sum(1 for kw in keywords if kw.lower() in content)
            matched_in_title = sum(1 for kw in keywords if kw.lower() in title)
            
            # 标题匹配权重更高
            keyword_score = (matched_in_content + matched_in_title * 2) / len(keywords)
            result["keyword_score"] = keyword_score
        
        return results
    
    def _rerank(
        self,
        results: List[Dict[str, Any]],
        query: str,
        doc_type: Optional[str],
        keywords: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """
        重排序搜索结果
        
        综合考虑多个因素：
        1. 向量相似度
        2. 关键词匹配度
        3. 文档类型匹配
        4. 内容长度
        5. 文档质量
        """
        scored_results = []
        
        for result in results:
            # 基础分数：向量相似度
            base_score = result.get("score", 0)
            
            # 因素1：关键词匹配度
            keyword_bonus = result.get("keyword_score", 0) * 0.3
            
            # 因素2：文档类型匹配
            type_bonus = 0
            if doc_type and result.get("doc_type") == doc_type:
                type_bonus = 0.2
            
            # 因素3：内容长度（偏好适中长度）
            content_length = len(result.get("content", ""))
            length_score = self._calculate_length_score(content_length)
            
            # 因素4：文档新鲜度（如果有时间戳）
            freshness_score = self._calculate_freshness_score(result)
            
            # 计算最终分数
            final_score = (
                base_score * 0.5 +  # 向量相似度权重 50%
                keyword_bonus +      # 关键词匹配 30%
                type_bonus +         # 类型匹配 20%
                length_score * 0.1 + # 长度适中性 10%
                freshness_score * 0.05  # 新鲜度 5%
            )
            
            result["relevance_score"] = final_score
            scored_results.append(result)
        
        # 按相关性排序
        scored_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        logger.debug(f"重排序完成，最高分：{scored_results[0]['relevance_score']:.2f}")
        return scored_results
    
    def _calculate_length_score(self, length: int) -> float:
        """
        计算内容长度分数
        
        偏好 500-2000 字的文档
        """
        if length < 100:
            return 0.3  # 太短
        elif length < 500:
            return 0.7
        elif length <= 2000:
            return 1.0  # 理想长度
        elif length <= 5000:
            return 0.8
        else:
            return 0.6  # 太长
    
    def _calculate_freshness_score(self, result: Dict[str, Any]) -> float:
        """
        计算文档新鲜度分数
        
        较新的文档得分更高
        """
        # TODO: 如果有创建/更新时间，计算新鲜度
        metadata = result.get("metadata", {})
        if "created_at" in metadata:
            # 实现时间衰减逻辑
            pass
        return 0.5  # 默认中等新鲜度
    
    def _filter(
        self,
        results: List[Dict[str, Any]],
        filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        过滤搜索结果
        
        1. 相关性阈值过滤
        2. 自定义条件过滤
        3. 去重
        """
        # 1. 相关性阈值
        min_score = filters.get("min_score", 0.3) if filters else 0.3
        filtered = [r for r in results if r.get("relevance_score", 0) >= min_score]
        
        # 2. 自定义过滤条件
        if filters:
            if "exclude_ids" in filters:
                exclude_ids = set(filters["exclude_ids"])
                filtered = [r for r in filtered if r.get("id") not in exclude_ids]
            
            if "min_length" in filters:
                min_length = filters["min_length"]
                filtered = [r for r in filtered if len(r.get("content", "")) >= min_length]
            
            if "max_length" in filters:
                max_length = filters["max_length"]
                filtered = [r for r in filtered if len(r.get("content", "")) <= max_length]
        
        # 3. 去重（基于内容相似度）
        filtered = self._deduplicate(filtered)
        
        logger.debug(f"过滤后保留 {len(filtered)} 个结果")
        return filtered
    
    def _deduplicate(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        去重
        
        移除内容高度相似的文档
        """
        if len(results) <= 1:
            return results
        
        deduplicated = []
        seen_contents = []
        
        for result in results:
            content = result.get("content", "")
            
            # 简单的相似度检查（可以改用更复杂的算法）
            is_duplicate = False
            for seen in seen_contents:
                similarity = self._simple_similarity(content, seen)
                if similarity > 0.9:  # 90% 以上相似认为是重复
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduplicated.append(result)
                seen_contents.append(content)
        
        if len(deduplicated) < len(results):
            logger.debug(f"去重移除了 {len(results) - len(deduplicated)} 个文档")
        
        return deduplicated
    
    def _simple_similarity(self, text1: str, text2: str) -> float:
        """简单的文本相似度计算"""
        # 使用集合交集/并集的 Jaccard 相似度
        set1 = set(text1[:1000])  # 只比较前1000字符
        set2 = set(text2[:1000])
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def _format_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """格式化搜索结果"""
        formatted = []
        
        for result in results:
            formatted.append({
                "id": result.get("id"),
                "title": result.get("title"),
                "content": result.get("content"),
                "doc_type": result.get("doc_type"),
                "similarity": result.get("score", 0),
                "relevance_score": result.get("relevance_score", 0),
                "keyword_score": result.get("keyword_score", 0),
                "metadata": result.get("metadata", {})
            })
        
        return formatted
    
    async def search_similar_documents(
        self,
        document_id: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        查找相似文档
        
        Args:
            document_id: 文档ID
            top_k: 返回数量
        """
        try:
            # 获取原文档
            original_doc = await self.vector_store.get_document(document_id)
            if not original_doc:
                logger.warning(f"文档 {document_id} 不存在")
                return []
            
            # 使用原文档内容搜索相似文档
            query = original_doc.get("content", "")
            results = await self.search(
                query=query,
                doc_type=original_doc.get("doc_type"),
                top_k=top_k + 1,  # +1 因为会包含自己
                filters={"exclude_ids": [document_id]}  # 排除自己
            )
            
            return results
            
        except Exception as e:
            logger.error(f"查找相似文档失败: {str(e)}")
            return []


# 单例模式
_search_engine_instance: Optional[SearchEngine] = None


def get_search_engine() -> SearchEngine:
    """获取搜索引擎单例实例"""
    global _search_engine_instance
    
    if _search_engine_instance is None:
        logger.info("创建搜索引擎实例")
        _search_engine_instance = SearchEngine()
    
    return _search_engine_instance


def reset_search_engine():
    """重置搜索引擎实例（主要用于测试）"""
    global _search_engine_instance
    _search_engine_instance = None
    logger.info("搜索引擎实例已重置")
