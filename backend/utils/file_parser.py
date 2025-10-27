from typing import Dict, Any, List, Optional, BinaryIO
from pathlib import Path
import io
from loguru import logger
from abc import ABC, abstractmethod

# PDF 处理
try:
    import PyPDF2
    import pdfplumber
    HAS_PDF = True
except ImportError:
    HAS_PDF = False
    logger.warning("PDF 支持未安装，请安装: pip install PyPDF2 pdfplumber")

# DOCX 处理
try:
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False
    logger.warning("DOCX 支持未安装，请安装: pip install python-docx")

# HTML 处理
try:
    from bs4 import BeautifulSoup
    HAS_HTML = True
except ImportError:
    HAS_HTML = False
    logger.warning("HTML 支持未安装，请安装: pip install beautifulsoup4")

# 图片处理
try:
    from PIL import Image
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    logger.warning("OCR 支持未安装，请安装: pip install pillow pytesseract")


class FileParser(ABC):
    """文件解析器基类"""
    
    @abstractmethod
    async def parse(self, file_content: bytes, **kwargs) -> Dict[str, Any]:
        """
        解析文件内容
        
        Returns:
            {
                "text": str,              # 提取的文本
                "images": List[dict],     # 图片信息
                "tables": List[list],     # 表格数据
                "metadata": dict          # 元数据
            }
        """
        pass


class PDFParser(FileParser):
    """PDF 文件解析器"""
    
    def __init__(self):
        if not HAS_PDF:
            raise ImportError("PDF 解析需要安装 PyPDF2 和 pdfplumber")
    
    async def parse(self, file_content: bytes, extract_images: bool = True, extract_tables: bool = True) -> Dict[str, Any]:
        """解析 PDF 文件"""
        try:
            pdf_file = io.BytesIO(file_content)
            
            # 使用 PyPDF2 提取基本文本
            text_parts = []
            metadata = {}
            
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # 提取元数据
            if pdf_reader.metadata:
                metadata = {
                    "title": pdf_reader.metadata.get("/Title", ""),
                    "author": pdf_reader.metadata.get("/Author", ""),
                    "subject": pdf_reader.metadata.get("/Subject", ""),
                    "creator": pdf_reader.metadata.get("/Creator", ""),
                    "producer": pdf_reader.metadata.get("/Producer", ""),
                    "creation_date": pdf_reader.metadata.get("/CreationDate", ""),
                }
            
            metadata["page_count"] = len(pdf_reader.pages)
            
            # 提取文本
            for page_num, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                if text:
                    text_parts.append(f"[第 {page_num + 1} 页]\n{text}\n")
            
            # 使用 pdfplumber 提取表格和更精确的内容
            images = []
            tables = []
            
            pdf_file.seek(0)  # 重置文件指针
            with pdfplumber.open(pdf_file) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # 提取表格
                    if extract_tables:
                        page_tables = page.extract_tables()
                        for table_idx, table in enumerate(page_tables):
                            tables.append({
                                "page": page_num + 1,
                                "table_index": table_idx,
                                "data": table,
                                "rows": len(table),
                                "cols": len(table[0]) if table else 0
                            })
                    
                    # 提取图片信息
                    if extract_images:
                        page_images = page.images
                        for img_idx, img in enumerate(page_images):
                            images.append({
                                "page": page_num + 1,
                                "image_index": img_idx,
                                "x0": img.get("x0"),
                                "y0": img.get("y0"),
                                "x1": img.get("x1"),
                                "y1": img.get("y1"),
                                "width": img.get("width"),
                                "height": img.get("height")
                            })
            
            full_text = "\n".join(text_parts)
            
            logger.info(f"PDF 解析完成: {len(full_text)} 字符, {len(tables)} 个表格, {len(images)} 张图片")
            
            return {
                "text": full_text,
                "images": images,
                "tables": tables,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"PDF 解析失败: {str(e)}")
            raise


class DOCXParser(FileParser):
    """DOCX 文件解析器"""
    
    def __init__(self):
        if not HAS_DOCX:
            raise ImportError("DOCX 解析需要安装 python-docx")
    
    async def parse(self, file_content: bytes, extract_images: bool = True, extract_tables: bool = True) -> Dict[str, Any]:
        """解析 DOCX 文件"""
        try:
            docx_file = io.BytesIO(file_content)
            doc = Document(docx_file)
            
            # 提取元数据
            core_properties = doc.core_properties
            metadata = {
                "title": core_properties.title or "",
                "author": core_properties.author or "",
                "subject": core_properties.subject or "",
                "keywords": core_properties.keywords or "",
                "comments": core_properties.comments or "",
                "created": str(core_properties.created) if core_properties.created else "",
                "modified": str(core_properties.modified) if core_properties.modified else "",
            }
            
            # 提取文本
            text_parts = []
            for para in doc.paragraphs:
                if para.text.strip():
                    # 保留段落样式信息
                    style = para.style.name if para.style else "Normal"
                    text_parts.append(f"{para.text}")
            
            # 提取表格
            tables = []
            if extract_tables:
                for table_idx, table in enumerate(doc.tables):
                    table_data = []
                    for row in table.rows:
                        row_data = [cell.text.strip() for cell in row.cells]
                        table_data.append(row_data)
                    
                    tables.append({
                        "table_index": table_idx,
                        "data": table_data,
                        "rows": len(table_data),
                        "cols": len(table_data[0]) if table_data else 0
                    })
            
            # 提取图片
            images = []
            if extract_images:
                for rel in doc.part.rels.values():
                    if "image" in rel.target_ref:
                        images.append({
                            "image_id": rel.rId,
                            "target": rel.target_ref,
                            "type": rel.reltype
                        })
            
            full_text = "\n".join(text_parts)
            
            logger.info(f"DOCX 解析完成: {len(full_text)} 字符, {len(tables)} 个表格, {len(images)} 张图片")
            
            return {
                "text": full_text,
                "images": images,
                "tables": tables,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"DOCX 解析失败: {str(e)}")
            raise


class HTMLParser(FileParser):
    """HTML 文件解析器"""
    
    def __init__(self):
        if not HAS_HTML:
            raise ImportError("HTML 解析需要安装 beautifulsoup4")
    
    async def parse(self, file_content: bytes, extract_images: bool = True, extract_tables: bool = True) -> Dict[str, Any]:
        """解析 HTML 文件"""
        try:
            html_content = file_content.decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取元数据
            metadata = {}
            if soup.title:
                metadata["title"] = soup.title.string
            
            # 提取 meta 标签
            for meta in soup.find_all('meta'):
                name = meta.get('name') or meta.get('property')
                content = meta.get('content')
                if name and content:
                    metadata[name] = content
            
            # 移除脚本和样式
            for script in soup(["script", "style"]):
                script.decompose()
            
            # 提取文本
            text = soup.get_text(separator='\n', strip=True)
            
            # 提取表格
            tables = []
            if extract_tables:
                for table_idx, table in enumerate(soup.find_all('table')):
                    table_data = []
                    for row in table.find_all('tr'):
                        row_data = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                        if row_data:
                            table_data.append(row_data)
                    
                    if table_data:
                        tables.append({
                            "table_index": table_idx,
                            "data": table_data,
                            "rows": len(table_data),
                            "cols": len(table_data[0]) if table_data else 0
                        })
            
            # 提取图片
            images = []
            if extract_images:
                for img_idx, img in enumerate(soup.find_all('img')):
                    images.append({
                        "image_index": img_idx,
                        "src": img.get('src'),
                        "alt": img.get('alt', ''),
                        "title": img.get('title', '')
                    })
            
            logger.info(f"HTML 解析完成: {len(text)} 字符, {len(tables)} 个表格, {len(images)} 张图片")
            
            return {
                "text": text,
                "images": images,
                "tables": tables,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"HTML 解析失败: {str(e)}")
            raise


class TXTParser(FileParser):
    """纯文本文件解析器"""
    
    async def parse(self, file_content: bytes, encoding: str = 'utf-8') -> Dict[str, Any]:
        """解析文本文件"""
        try:
            # 尝试多种编码
            encodings = [encoding, 'utf-8', 'gbk', 'gb2312', 'latin-1']
            text = None
            used_encoding = None
            
            for enc in encodings:
                try:
                    text = file_content.decode(enc)
                    used_encoding = enc
                    break
                except UnicodeDecodeError:
                    continue
            
            if text is None:
                raise ValueError("无法识别文件编码")
            
            logger.info(f"TXT 解析完成: {len(text)} 字符, 编码: {used_encoding}")
            
            return {
                "text": text,
                "images": [],
                "tables": [],
                "metadata": {"encoding": used_encoding}
            }
            
        except Exception as e:
            logger.error(f"TXT 解析失败: {str(e)}")
            raise


class ImageParser(FileParser):
    """图片文件解析器（OCR）"""
    
    def __init__(self):
        if not HAS_OCR:
            raise ImportError("图片 OCR 需要安装 pillow 和 pytesseract")
    
    async def parse(self, file_content: bytes, language: str = 'chi_sim+eng') -> Dict[str, Any]:
        """解析图片文件（OCR 识别）"""
        try:
            image = Image.open(io.BytesIO(file_content))
            
            # 提取图片元数据
            metadata = {
                "format": image.format,
                "mode": image.mode,
                "size": image.size,
                "width": image.width,
                "height": image.height
            }
            
            # OCR 识别
            try:
                text = pytesseract.image_to_string(image, lang=language)
                logger.info(f"图片 OCR 完成: {len(text)} 字符")
            except Exception as ocr_error:
                logger.warning(f"OCR 识别失败: {str(ocr_error)}, 返回空文本")
                text = ""
            
            return {
                "text": text,
                "images": [{
                    "format": image.format,
                    "size": image.size,
                    "mode": image.mode
                }],
                "tables": [],
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"图片解析失败: {str(e)}")
            raise


class FileParserFactory:
    """文件解析器工厂"""
    
    _parsers = {
        'pdf': PDFParser,
        'docx': DOCXParser,
        'doc': DOCXParser,
        'html': HTMLParser,
        'htm': HTMLParser,
        'txt': TXTParser,
        'md': TXTParser,
        'jpg': ImageParser,
        'jpeg': ImageParser,
        'png': ImageParser,
        'bmp': ImageParser,
        'gif': ImageParser,
    }
    
    @classmethod
    def get_parser(cls, file_extension: str) -> Optional[FileParser]:
        """
        根据文件扩展名获取解析器
        
        Args:
            file_extension: 文件扩展名（不带点）
        """
        ext = file_extension.lower().lstrip('.')
        parser_class = cls._parsers.get(ext)
        
        if parser_class is None:
            logger.warning(f"不支持的文件类型: {ext}")
            return None
        
        try:
            return parser_class()
        except ImportError as e:
            logger.error(f"解析器初始化失败: {str(e)}")
            return None
    
    @classmethod
    def supported_extensions(cls) -> List[str]:
        """返回支持的文件扩展名列表"""
        return list(cls._parsers.keys())
    
    @classmethod
    async def parse_file(
        cls,
        file_content: bytes,
        filename: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        解析文件
        
        Args:
            file_content: 文件内容
            filename: 文件名
            **kwargs: 传递给解析器的额外参数
        """
        # 获取文件扩展名
        ext = Path(filename).suffix.lstrip('.').lower()
        
        # 获取解析器
        parser = cls.get_parser(ext)
        if parser is None:
            raise ValueError(f"不支持的文件类型: {ext}")
        
        # 解析文件
        result = await parser.parse(file_content, **kwargs)
        
        # 添加文件名到元数据
        if "metadata" not in result:
            result["metadata"] = {}
        result["metadata"]["filename"] = filename
        result["metadata"]["file_extension"] = ext
        
        return result
