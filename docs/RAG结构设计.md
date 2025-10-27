# RAG（检索增强生成）技术架构文档

本文档详细描述了 Refantastic 系统中 RAG 技术的实现原理、架构设计和使用方法。

## 📋 目录

- [技术概述](#技术概述)
- [核心流程](#核心流程)
- [文档分片](#文档分片)
- [向量化处理](#向量化处理)
- [混合检索](#混合检索)
- [上下文构建](#上下文构建)
- [生成优化](#生成优化)
- [性能优化](#性能优化)
- [API 使用示例](#api-使用示例)

---

## 技术概述

### 什么是 RAG？

RAG（Retrieval-Augmented Generation，检索增强生成）是一种结合了信息检索和文本生成的 AI 技术。它通过在生成文本之前检索相关知识，为大语言模型提供更准确、更新、更相关的上下文信息。

### 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户输入                                  │
│                     (查询、主题、需求)                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       混合检索引擎                                │
│  ┌──────────────────┐              ┌──────────────────┐         │
│  │  关键词检索      │              │   向量检索       │         │
│  │  (BM25/TF-IDF)   │              │ (语义相似度)     │         │
│  └────────┬─────────┘              └────────┬─────────┘         │
│           │                                 │                   │
│           └─────────────┬───────────────────┘                   │
│                         ▼                                       │
│                   结果融合与排序                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     上下文构建器                                  │
│  • 筛选最相关的文档片段                                           │
│  • 控制上下文长度                                                 │
│  • 构建结构化 Prompt                                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      大语言模型 (LLM)                             │
│                   (GPT-4 / Claude / Qwen)                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      生成的公文内容                               │
└─────────────────────────────────────────────────────────────────┘
```

### 核心优势

1. **知识实时性**：无需重新训练模型，更新知识库即可获取最新信息
2. **可追溯性**：每次生成都能追溯到参考来源
3. **准确性提升**：基于真实文档生成，减少幻觉问题
4. **灵活性**：可根据不同场景调整检索策略
5. **成本效益**：相比微调大模型，成本更低

---

## 核心流程

### 1. 离线处理流程（文档入库）

```
原始文档 → 文档解析 → 文本分片 → 向量化 → 存储
   │           │          │         │        │
   │           │          │         │        ├─→ 向量数据库 (ChromaDB)
   │           │          │         │        └─→ 关系数据库 (PostgreSQL/SQLite)
   │           │          │         │
   │           │          │         └─→ 嵌入模型 (BGE-Large-ZH)
   │           │          │
   │           │          └─→ 文本分割器 (多种策略)
   │           │
   │           └─→ 文件解析器 (PDF/DOCX/HTML/TXT)
   │
   └─→ 上传接口 (FastAPI)
```

### 2. 在线检索流程（文档生成）

```
用户查询 → 查询理解 → 混合检索 → 结果重排序 → 上下文构建 → LLM 生成
    │          │          │           │            │            │
    │          │          │           │            │            └─→ 生成内容
    │          │          │           │            │
    │          │          │           │            └─→ Prompt 工程
    │          │          │           │
    │          │          │           └─→ 相关性评分
    │          │          │
    │          │          ├─→ 向量检索（语义相似度）
    │          │          └─→ 关键词检索（BM25）
    │          │
    │          └─→ 查询扩展、同义词识别
    │
    └─→ 生成接口 (FastAPI)
```

---

## 文档分片

文档分片是 RAG 系统的基础，合理的分片策略直接影响检索质量和生成效果。

### 为什么需要分片？

1. **嵌入模型限制**：大多数嵌入模型有 token 长度限制（通常 512-8192）
2. **检索粒度**：细粒度分片可以更精确地匹配相关内容
3. **上下文控制**：避免向 LLM 输入过长的无关内容
4. **性能优化**：较小的片段可以加快向量检索速度

### 分片策略

#### 1. 固定长度分片（Character-based）

按字符数量固定分割，最简单直接。

```python
from langchain.text_splitter import CharacterTextSplitter

splitter = CharacterTextSplitter(
    chunk_size=500,        # 每个片段 500 字符
    chunk_overlap=50,      # 重叠 50 字符，保持上下文连贯
    separator="\n"         # 优先在换行处分割
)

chunks = splitter.split_text(document_text)
```

**适用场景**：
- 格式统一的文档
- 段落分明的文本
- 简单快速的分片需求

**优点**：
- 实现简单，速度快
- 可预测的片段大小

**缺点**：
- 可能破坏语义完整性
- 不考虑文档结构

#### 2. 递归字符分片（Recursive Character-based）

**推荐使用**，按层级分隔符递归分割，保持语义完整性。

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,                    # 目标片段大小
    chunk_overlap=100,                 # 重叠部分
    separators=["\n\n", "\n", "。", "；", " ", ""],  # 分隔符优先级
    length_function=len                # 长度计算函数
)

chunks = splitter.split_text(document_text)
```

**分割优先级**：
1. 双换行（段落）
2. 单换行（句子）
3. 句号（完整句）
4. 分号（短句）
5. 空格（词）
6. 字符（最后手段）

**适用场景**：
- 大多数文本文档
- 需要保持语义完整性
- **公文文档（推荐）**

**优点**：
- 保持语义完整
- 适应多种文档结构
- 灵活可配置

**缺点**：
- 计算开销稍大
- 片段大小可能不均匀

#### 3. 基于 Token 分片（Token-based）

按模型 token 数量分割，精确控制输入长度。

```python
from langchain.text_splitter import TokenTextSplitter

splitter = TokenTextSplitter(
    chunk_size=512,        # 512 tokens
    chunk_overlap=50,      # 重叠 50 tokens
    encoding_name="cl100k_base"  # OpenAI 的 tokenizer
)

chunks = splitter.split_text(document_text)
```

**适用场景**：
- 需要精确控制 token 数
- 与特定模型配合使用
- 成本敏感的场景

**优点**：
- 精确的 token 控制
- 避免超出模型限制

**缺点**：
- 依赖特定 tokenizer
- 性能开销较大

#### 4. 语义分片（Semantic-based）

基于语义相似度进行智能分片。

```python
from langchain.text_splitter import SemanticChunker
from langchain_community.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-large-zh-v1.5")

splitter = SemanticChunker(
    embeddings=embeddings,
    breakpoint_threshold_type="percentile",  # 使用百分位阈值
    breakpoint_threshold_amount=95           # 95 百分位
)

chunks = splitter.create_documents([document_text])
```

**工作原理**：
1. 将文本按句子分割
2. 计算相邻句子的语义相似度
3. 在相似度低的位置分割

**适用场景**：
- 需要高质量语义分割
- 主题多样的长文档
- 对质量要求高的场景

**优点**：
- 语义完整性最好
- 智能主题边界识别

**缺点**：
- 计算成本高
- 速度较慢
- 片段大小不可控

#### 5. 结构化分片（Markdown/HTML）

针对结构化文档的特殊分片策略。

```python
from langchain.text_splitter import MarkdownHeaderTextSplitter

headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]

splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=headers_to_split_on
)

chunks = splitter.split_text(markdown_text)
```

**适用场景**：
- Markdown 格式文档
- HTML 网页
- 有明确章节结构的文档

**优点**：
- 保留文档结构
- 语义分组清晰

**缺点**：
- 仅适用于结构化文档
- 片段大小不均匀

### 分片策略选择指南

| 文档类型 | 推荐策略 | 理由 |
|---------|---------|------|
| 公文文档 | 递归字符分片 | 保持段落完整，适应格式 |
| 技术文档 | Markdown 分片 + 递归分片 | 保留结构，控制大小 |
| 长篇报告 | 语义分片 | 主题边界清晰 |
| 对话记录 | 固定长度分片 | 格式统一，简单高效 |
| 混合内容 | 递归字符分片 | 通用性强，质量好 |

### 分片参数配置建议

**公文文档推荐配置**：

```python
# Refantastic 系统默认配置
CHUNK_SIZE = 800           # 适合中文公文的段落长度
CHUNK_OVERLAP = 100        # 保持上下文连贯
SEPARATORS = [
    "\n\n",                # 段落
    "\n",                  # 句子
    "。",                  # 句号
    "；",                  # 分号
    "，",                  # 逗号
    " ",                   # 空格
    ""                     # 字符
]
```

**参数调优建议**：

- **chunk_size**：
  - 小（200-500）：精确检索，适合问答场景
  - 中（500-1000）：**推荐**，平衡检索质量和上下文
  - 大（1000-2000）：保留更多上下文，适合摘要场景

- **chunk_overlap**：
  - 通常设置为 chunk_size 的 10-20%
  - 避免关键信息在边界被切断
  - 过大会增加存储和检索成本

### 分片元数据

每个分片应包含以下元数据：

```python
{
    "chunk_id": "uuid",                    # 分片唯一标识
    "document_id": "parent_doc_id",        # 来源文档ID
    "chunk_index": 0,                      # 在文档中的位置
    "chunk_size": 750,                     # 实际大小
    "text": "分片内容...",                  # 文本内容
    "metadata": {
        "doc_type": "通知",                 # 文档类型
        "department": "办公室",             # 部门
        "date": "2024-01-15",              # 日期
        "title": "关于XXX的通知",           # 标题
        "page": 1,                         # 页码（如果有）
        "section": "主要内容",              # 章节（如果有）
        "keywords": ["会议", "通知"]        # 关键词
    }
}
```

---

## 向量化处理

将文本分片转换为数值向量，用于语义相似度计算。

### 嵌入模型选择

#### 当前使用：BAAI/bge-large-zh-v1.5

**规格**：
- 模型大小：1.3 GB
- 向量维度：1024
- Token 限制：512
- 语言支持：中文优先，多语言支持

**性能指标**：
- C-MTEB 排行榜 Top 3
- 中文检索任务 NDCG@10: 0.72
- 推理速度：~100 docs/s (CPU)

**选择理由**：
1. 中文效果优秀
2. 开源免费
3. 本地部署
4. 社区活跃

#### 其他可选模型

| 模型 | 维度 | 大小 | 特点 |
|------|------|------|------|
| text-embedding-ada-002 | 1536 | API | OpenAI 官方，效果好但收费 |
| m3e-large | 1024 | 1.3 GB | 中文优化，开源 |
| text2vec-large-chinese | 1024 | 1.3 GB | 轻量级，速度快 |
| multilingual-e5-large | 1024 | 2.2 GB | 多语言支持 |

### 向量化流程

```python
from sentence_transformers import SentenceTransformer
import numpy as np

# 1. 加载模型
model = SentenceTransformer('BAAI/bge-large-zh-v1.5')

# 2. 批量向量化
chunks = ["文本片段1", "文本片段2", ...]
embeddings = model.encode(
    chunks,
    batch_size=32,           # 批处理大小
    show_progress_bar=True,  # 显示进度
    normalize_embeddings=True  # L2 归一化
)

# 3. 存储到向量库
vector_store.add(
    ids=[chunk['id'] for chunk in chunks],
    embeddings=embeddings.tolist(),
    metadatas=[chunk['metadata'] for chunk in chunks],
    documents=[chunk['text'] for chunk in chunks]
)
```

### 向量存储

#### ChromaDB（当前使用）

```python
import chromadb
from chromadb.config import Settings

# 初始化客户端
client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./data/chroma"
))

# 创建集合
collection = client.create_collection(
    name="knowledge_base",
    metadata={"hnsw:space": "cosine"},  # 余弦相似度
    embedding_function=embedding_function
)

# 添加向量
collection.add(
    ids=["id1", "id2"],
    embeddings=[[0.1, 0.2, ...], [0.3, 0.4, ...]],
    documents=["文本1", "文本2"],
    metadatas=[{"type": "通知"}, {"type": "报告"}]
)

# 检索
results = collection.query(
    query_embeddings=[[0.1, 0.2, ...]],
    n_results=10,
    where={"type": "通知"}  # 元数据过滤
)
```

**优点**：
- 轻量级，易部署
- Python 原生支持
- 本地持久化
- 免费开源

**缺点**：
- 百万级向量后性能下降
- 单机部署

#### 其他向量库对比

| 向量库 | 适用规模 | 特点 | 推荐场景 |
|--------|---------|------|---------|
| ChromaDB | < 100万 | 轻量、易用 | 中小型部署 |
| Milvus | > 百万 | 分布式、高性能 | 企业级部署 |
| Qdrant | 百万级 | Rust 实现、快速 | 性能要求高 |
| Weaviate | 百万级 | GraphQL、多模态 | 复杂查询 |
| Pinecone | 不限 | 云服务、托管 | 快速上线 |

### 向量化优化

#### 1. 批量处理

```python
# 不推荐：逐个处理
for chunk in chunks:
    embedding = model.encode(chunk)
    store.add(embedding)

# 推荐：批量处理
batch_size = 32
for i in range(0, len(chunks), batch_size):
    batch = chunks[i:i+batch_size]
    embeddings = model.encode(batch, batch_size=batch_size)
    store.add_batch(embeddings)
```

#### 2. GPU 加速

```python
# 使用 GPU
model = SentenceTransformer('BAAI/bge-large-zh-v1.5', device='cuda')

# 或指定设备
import torch
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = SentenceTransformer('BAAI/bge-large-zh-v1.5', device=device)
```

#### 3. 模型量化

```python
# 使用量化模型（减少内存占用）
from optimum.onnxruntime import ORTModelForFeatureExtraction

model = ORTModelForFeatureExtraction.from_pretrained(
    'BAAI/bge-large-zh-v1.5',
    export=True
)
```

#### 4. 缓存策略

```python
from functools import lru_cache

@lru_cache(maxsize=10000)
def get_embedding(text: str):
    """缓存常用文本的向量"""
    return model.encode(text)
```

---

## 混合检索

结合关键词检索和向量检索，提高检索质量。

### 检索策略

#### 1. 向量检索（语义相似度）

基于嵌入向量的余弦相似度。

```python
def vector_search(query: str, top_k: int = 10):
    """向量检索"""
    # 1. 查询向量化
    query_embedding = model.encode(query)
    
    # 2. 相似度搜索
    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=top_k
    )
    
    return results
```

**优点**：
- 语义理解能力强
- 可以匹配同义词
- 支持跨语言检索

**缺点**：
- 对精确匹配不敏感
- 计算开销大

#### 2. 关键词检索（BM25）

基于词频和逆文档频率的统计方法。

```python
from rank_bm25 import BM25Okapi
import jieba

def keyword_search(query: str, documents: List[str], top_k: int = 10):
    """BM25 关键词检索"""
    # 1. 分词
    tokenized_docs = [list(jieba.cut(doc)) for doc in documents]
    tokenized_query = list(jieba.cut(query))
    
    # 2. 构建 BM25 索引
    bm25 = BM25Okapi(tokenized_docs)
    
    # 3. 检索
    scores = bm25.get_scores(tokenized_query)
    top_indices = np.argsort(scores)[::-1][:top_k]
    
    return [(i, scores[i]) for i in top_indices]
```

**优点**：
- 精确匹配
- 速度快
- 可解释性强

**缺点**：
- 无法理解语义
- 依赖分词质量

#### 3. 混合检索（推荐）

融合两种检索方法的优点。

```python
async def hybrid_search(
    query: str,
    doc_type: Optional[str] = None,
    top_k: int = 10,
    alpha: float = 0.5  # 向量检索权重
) -> List[Dict]:
    """
    混合检索
    
    Args:
        query: 查询文本
        doc_type: 文档类型过滤
        top_k: 返回结果数
        alpha: 向量检索权重 (0-1)，1-alpha 为关键词检索权重
    """
    # 1. 向量检索
    vector_results = await vector_search(query, top_k=top_k*2)
    
    # 2. 关键词检索
    keyword_results = await keyword_search(query, top_k=top_k*2)
    
    # 3. 结果融合（RRF - Reciprocal Rank Fusion）
    scores = {}
    
    # 向量检索结果
    for rank, result in enumerate(vector_results):
        doc_id = result['id']
        scores[doc_id] = scores.get(doc_id, 0) + alpha / (rank + 60)
    
    # 关键词检索结果
    for rank, result in enumerate(keyword_results):
        doc_id = result['id']
        scores[doc_id] = scores.get(doc_id, 0) + (1-alpha) / (rank + 60)
    
    # 4. 排序
    sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    # 5. 返回 top_k
    return sorted_results[:top_k]
```

**RRF 公式**：

```
score(d) = Σ 1 / (k + rank(d))
```

其中：
- `k` 是常数（通常 60）
- `rank(d)` 是文档在某个检索结果中的排名

### 检索优化

#### 1. 元数据过滤

```python
# 在向量检索前过滤
results = collection.query(
    query_embeddings=[embedding],
    n_results=top_k,
    where={
        "doc_type": "通知",
        "department": "办公室",
        "date": {"$gte": "2024-01-01"}
    }
)
```

#### 2. 重排序（Reranking）

```python
from sentence_transformers import CrossEncoder

# 使用交叉编码器重排序
reranker = CrossEncoder('BAAI/bge-reranker-large')

def rerank(query: str, candidates: List[str], top_k: int = 10):
    """重排序"""
    # 1. 构建查询-文档对
    pairs = [[query, doc] for doc in candidates]
    
    # 2. 计算相关性分数
    scores = reranker.predict(pairs)
    
    # 3. 排序
    sorted_indices = np.argsort(scores)[::-1][:top_k]
    
    return [candidates[i] for i in sorted_indices]
```

#### 3. 查询扩展

```python
def expand_query(query: str) -> List[str]:
    """查询扩展"""
    expanded = [query]
    
    # 1. 同义词扩展
    synonyms = get_synonyms(query)  # 从同义词词典
    expanded.extend(synonyms)
    
    # 2. 使用 LLM 生成相关查询
    related_queries = llm.generate(
        f"生成3个与'{query}'相关的搜索查询："
    )
    expanded.extend(related_queries)
    
    return expanded
```

---

## 上下文构建

将检索到的文档片段构建为 LLM 可用的上下文。

### Prompt 模板

```python
PROMPT_TEMPLATE = """你是一个专业的公文写作助手。请根据以下参考文档生成符合要求的公文。

## 参考文档

{reference_documents}

## 生成要求

- 文档类型：{doc_type}
- 主题：{theme}
- 目的：{purpose}
- 关键词：{keywords}
- 语气：{tone}
- 长度：{length}

## 格式要求

请严格按照中国公文写作规范，包括：
1. 标题居中，字体加粗
2. 主送机关顶格书写
3. 正文层次清晰，序号规范
4. 结尾用语恰当
5. 落款右下对齐

## 生成内容

"""

def build_context(
    references: List[Dict],
    doc_type: str,
    theme: str,
    purpose: str,
    keywords: List[str],
    max_tokens: int = 4000
) -> str:
    """构建上下文"""
    # 1. 格式化参考文档
    ref_texts = []
    current_tokens = 0
    
    for i, ref in enumerate(references, 1):
        ref_text = f"""
### 参考文档 {i}
**标题**: {ref['title']}
**类型**: {ref['doc_type']}
**相关度**: {ref['score']:.2f}

{ref['content']}

---
"""
        # 估算 token 数
        tokens = len(ref_text) // 2  # 粗略估计
        
        if current_tokens + tokens > max_tokens:
            break
        
        ref_texts.append(ref_text)
        current_tokens += tokens
    
    # 2. 填充模板
    context = PROMPT_TEMPLATE.format(
        reference_documents="\n".join(ref_texts),
        doc_type=doc_type,
        theme=theme,
        purpose=purpose,
        keywords=", ".join(keywords),
        tone="正式",
        length="中等"
    )
    
    return context
```

### 上下文优化策略

#### 1. 长度控制

```python
def truncate_context(context: str, max_tokens: int) -> str:
    """截断上下文"""
    import tiktoken
    
    enc = tiktoken.encoding_for_model("gpt-4")
    tokens = enc.encode(context)
    
    if len(tokens) <= max_tokens:
        return context
    
    # 截断并添加省略提示
    truncated_tokens = tokens[:max_tokens-50]
    truncated_text = enc.decode(truncated_tokens)
    
    return truncated_text + "\n\n[注：部分参考文档因长度限制已省略]"
```

#### 2. 相关性过滤

```python
def filter_by_relevance(results: List[Dict], threshold: float = 0.7) -> List[Dict]:
    """按相关性过滤"""
    return [r for r in results if r['score'] >= threshold]
```

#### 3. 去重

```python
def deduplicate_results(results: List[Dict], similarity_threshold: float = 0.9) -> List[Dict]:
    """去除高度相似的结果"""
    from sklearn.metrics.pairwise import cosine_similarity
    
    if len(results) <= 1:
        return results
    
    # 计算相似度矩阵
    embeddings = [r['embedding'] for r in results]
    sim_matrix = cosine_similarity(embeddings)
    
    # 保留不相似的结果
    keep = [True] * len(results)
    for i in range(len(results)):
        if not keep[i]:
            continue
        for j in range(i+1, len(results)):
            if sim_matrix[i][j] > similarity_threshold:
                keep[j] = False
    
    return [r for i, r in enumerate(results) if keep[i]]
```

---

## 生成优化

### LLM 参数调优

```python
response = llm.generate(
    prompt=context,
    temperature=0.7,      # 创造性：0.1-1.0，公文建议 0.5-0.7
    max_tokens=2000,      # 最大生成长度
    top_p=0.9,           # 核采样
    frequency_penalty=0.3,  # 降低重复
    presence_penalty=0.3,   # 鼓励多样性
    stop=["\n\n---"]     # 停止标记
)
```

**参数说明**：

- **temperature**：
  - 0.1-0.3：确定性强，适合格式化文档
  - 0.5-0.7：平衡，适合公文生成
  - 0.8-1.0：创造性强，适合创意写作

- **top_p**：
  - 控制词汇多样性
  - 0.9-0.95 为推荐值

### 后处理

```python
def post_process(generated_text: str) -> str:
    """后处理生成的文本"""
    # 1. 清理格式
    text = generated_text.strip()
    
    # 2. 移除多余空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 3. 统一标点符号
    text = text.replace('，，', '，')
    text = text.replace('。。', '。')
    
    # 4. 修正常见错误
    text = fix_common_errors(text)
    
    # 5. 格式规范化
    text = normalize_format(text)
    
    return text
```

---

## 性能优化

### 1. 缓存策略

```python
from functools import lru_cache
import redis

# 内存缓存
@lru_cache(maxsize=1000)
def cached_search(query: str, top_k: int):
    return hybrid_search(query, top_k)

# Redis 缓存
redis_client = redis.Redis(host='localhost', port=6379)

def cached_generation(query_hash: str, context: str):
    # 检查缓存
    cached = redis_client.get(query_hash)
    if cached:
        return cached.decode('utf-8')
    
    # 生成并缓存
    result = llm.generate(context)
    redis_client.setex(query_hash, 3600, result)  # 1小时过期
    
    return result
```

### 2. 异步处理

```python
import asyncio

async def async_generate(requests: List[Dict]):
    """异步批量生成"""
    tasks = [generate_document(**req) for req in requests]
    results = await asyncio.gather(*tasks)
    return results
```

### 3. 索引优化

```python
# ChromaDB HNSW 参数优化
collection = client.create_collection(
    name="optimized_collection",
    metadata={
        "hnsw:space": "cosine",
        "hnsw:construction_ef": 200,  # 构建时的搜索范围
        "hnsw:M": 16,                # 每层的连接数
        "hnsw:search_ef": 100         # 搜索时的范围
    }
)
```

---

## API 使用示例

### 1. 上传文档并向量化

```bash
curl -X POST "http://localhost:8000/api/v1/knowledge/upload" \
  -F "file=@document.pdf" \
  -F "title=2024年度工作通知" \
  -F "doc_type=通知" \
  -F "auto_vectorize=true"
```

### 2. 混合检索

```bash
curl -X POST "http://localhost:8000/api/v1/generation/search-references" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "关于组织年度工作会议",
    "doc_type": "通知",
    "top_k": 10,
    "search_type": "hybrid",
    "alpha": 0.6
  }'
```

### 3. RAG 生成

```bash
curl -X POST "http://localhost:8000/api/v1/generation/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "doc_type": "通知",
    "theme": "2024年度工作会议",
    "purpose": "通知各部门参加年度工作总结会议",
    "keywords": ["年度总结", "工作会议"],
    "use_rag": true,
    "top_k_references": 5
  }'
```

### 4. 批量向量化

```bash
curl -X POST "http://localhost:8000/api/v1/knowledge/documents/batch-vectorize" \
  -H "Content-Type: application/json" \
  -d '{
    "force": false
  }'
```

---

## 最佳实践

### 1. 文档准备

- ✅ 确保文档质量高、格式规范
- ✅ 添加完整的元数据（标题、类型、部门等）
- ✅ 定期清理过时文档
- ✅ 使用统一的文档命名规范

### 2. 分片配置

- ✅ 根据文档类型选择合适的分片策略
- ✅ 公文推荐使用递归字符分片，chunk_size=800
- ✅ 设置适当的 overlap（10-20%）避免信息丢失
- ✅ 保留重要的元数据

### 3. 检索优化

- ✅ 使用混合检索，alpha=0.5-0.7
- ✅ 启用元数据过滤提高准确性
- ✅ 适当增加 top_k 提高召回率
- ✅ 使用重排序提高精度

### 4. 生成质量

- ✅ 提供清晰的生成要求
- ✅ 控制上下文长度在模型限制内
- ✅ 使用适当的 temperature（公文建议 0.5-0.7）
- ✅ 对生成结果进行后处理和校验

### 5. 性能优化

- ✅ 启用缓存减少重复计算
- ✅ 使用 GPU 加速向量化
- ✅ 批量处理提高吞吐量
- ✅ 定期优化向量索引

---

## 常见问题

### Q1: 检索结果不准确怎么办？

**解决方案**：
1. 检查分片策略是否合适
2. 调整检索参数（top_k、alpha）
3. 使用重排序提高精度
4. 完善文档元数据

### Q2: 生成内容与参考文档偏差大？

**解决方案**：
1. 增加参考文档数量（top_k）
2. 提高相关性阈值
3. 优化 Prompt 模板
4. 降低 temperature

### Q3: 向量化速度慢？

**解决方案**：
1. 使用 GPU 加速
2. 批量处理文档
3. 考虑使用更小的模型
4. 启用模型量化

### Q4: 内存占用过高？

**解决方案**：
1. 减小 batch_size
2. 使用模型量化
3. 分批处理大型文档
4. 使用外部向量库（如 Milvus）

---

## 参考资料

- [LangChain Text Splitters](https://python.langchain.com/docs/modules/data_connection/document_transformers/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [BGE Embedding Models](https://github.com/FlagOpen/FlagEmbedding)
- [RAG Paper (Lewis et al.)](https://arxiv.org/abs/2005.11401)

---

[返回主文档](../README.md) | [数据库设计](DATABASE_DESIGN.md) | [API 文档](API.md)
