"""文件处理服务"""
import hashlib
import mimetypes
from typing import Dict, Any, List, Optional
from pathlib import Path
import io
from loguru import logger

# PDF处理
try:
    import PyPDF2
    import pdfplumber
    HAS_PDF = True
except ImportError:
    HAS_PDF = False
    logger.warning("未安装PDF处理库，将无法处理PDF文件。请安装: pip install PyPDF2 pdfplumber")

# Word处理
try:
    from docx import Document as DocxDocument
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False
    logger.warning("未安装Word处理库，将无法处理DOCX文件。请安装: pip install python-docx")

# HTML处理
try:
    from bs4 import BeautifulSoup
    HAS_HTML = True
except ImportError:
    HAS_HTML = False
    logger.warning("未安装HTML处理库，将无法处理HTML文件。请安装: pip install beautifulsoup4")

# 图片OCR处理
try:
    from PIL import Image
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    logger.warning("未安装OCR处理库，将无法从图片提取文字。请安装: pip install Pillow pytesseract")


class FileService:
    """文件处理服务"""
    
    SUPPORTED_EXTENSIONS = {
        # 文档
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'doc': 'application/msword',
        'txt': 'text/plain',
        'md': 'text/markdown',
        # Web
        'html': 'text/html',
        'htm': 'text/html',
        # 图片
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'bmp': 'image/bmp',
        'gif': 'image/gif',
    }
    
    def __init__(self):
        self.max_file_size = 50 * 1024 * 1024  # 50MB
    
    def is_supported(self, filename: str) -> bool:
        """检查文件是否支持"""
        ext = Path(filename).suffix.lower().lstrip('.')
        return ext in self.SUPPORTED_EXTENSIONS
    
    def get_supported_extensions(self) -> List[str]:
        """获取支持的文件扩展名列表"""
        return list(self.SUPPORTED_EXTENSIONS.keys())
    
    def get_file_hash(self, content: bytes) -> str:
        """计算文件哈希"""
        return hashlib.sha256(content).hexdigest()
    
    async def process_upload(
        self,
        file_content: bytes,
        filename: str,
        extract_images: bool = True,
        extract_tables: bool = True,
        table_format: str = "markdown"
    ) -> Dict[str, Any]:
        """
        处理上传的文件
        
        Returns:
            {
                "content": str,  # 提取的文本内容
                "images": List[Dict],  # 提取的图片信息
                "tables": List[Dict],  # 提取的表格信息
                "metadata": Dict,  # 文件元数据
                "file_size": int,
                "file_hash": str
            }
        """
        try:
            # 检查文件大小
            if len(file_content) > self.max_file_size:
                raise ValueError(f"文件大小超过限制 ({self.max_file_size / 1024 / 1024}MB)")
            
            ext = Path(filename).suffix.lower().lstrip('.')
            
            # 计算文件哈希
            file_hash = self.get_file_hash(file_content)
            
            # 根据文件类型处理
            if ext == 'pdf':
                result = await self._process_pdf(
                    file_content,
                    extract_images=extract_images,
                    extract_tables=extract_tables,
                    table_format=table_format
                )
            elif ext in ['docx', 'doc']:
                result = await self._process_docx(file_content)
            elif ext in ['html', 'htm']:
                result = await self._process_html(file_content)
            elif ext in ['txt', 'md']:
                result = await self._process_text(file_content)
            elif ext in ['jpg', 'jpeg', 'png', 'bmp', 'gif']:
                result = await self._process_image(file_content)
            else:
                raise ValueError(f"不支持的文件类型: {ext}")
            
            # 添加通用元数据
            result["file_size"] = len(file_content)
            result["file_hash"] = file_hash
            result["filename"] = filename
            result["file_type"] = ext
            
            return result
            
        except Exception as e:
            logger.error(f"处理文件失败: {str(e)}")
            raise
    
    async def _process_pdf(
        self,
        content: bytes,
        extract_images: bool = True,
        extract_tables: bool = True,
        table_format: str = "markdown"
    ) -> Dict[str, Any]:
        """处理PDF文件"""
        if not HAS_PDF:
            raise RuntimeError("未安装PDF处理库")
        
        text_content = ""
        images = []
        tables = []
        metadata = {}
        
        try:
            # 使用pdfplumber提取文本和表格
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                metadata = {
                    "page_count": len(pdf.pages),
                    "metadata": pdf.metadata or {}
                }
                
                for i, page in enumerate(pdf.pages):
                    # 提取文本
                    page_text = page.extract_text() or ""
                    text_content += f"\n--- 第 {i+1} 页 ---\n{page_text}\n"
                    
                    # 提取表格
                    if extract_tables:
                        page_tables = page.extract_tables()
                        for j, table in enumerate(page_tables or []):
                            tables.append({
                                "page": i + 1,
                                "table_index": j + 1,
                                "data": table,
                                "markdown": self._table_to_markdown(table) if table_format == "markdown" else None
                            })
            
            return {
                "content": text_content.strip(),
                "images": images,
                "tables": tables,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"处理PDF失败: {str(e)}")
            # 降级使用PyPDF2
            try:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
                text_content = ""
                for page in pdf_reader.pages:
                    text_content += page.extract_text() + "\n"
                
                return {
                    "content": text_content.strip(),
                    "images": [],
                    "tables": [],
                    "metadata": {"page_count": len(pdf_reader.pages)}
                }
            except Exception as e2:
                logger.error(f"PDF降级处理也失败: {str(e2)}")
                raise
    
    async def _process_docx(self, content: bytes) -> Dict[str, Any]:
        """处理Word文档"""
        if not HAS_DOCX:
            raise RuntimeError("未安装Word处理库")
        
        try:
            doc = DocxDocument(io.BytesIO(content))
            
            # 提取文本
            text_content = "\n".join([para.text for para in doc.paragraphs])
            
            # 提取表格
            tables = []
            for i, table in enumerate(doc.tables):
                table_data = []
                for row in table.rows:
                    table_data.append([cell.text for cell in row.cells])
                
                tables.append({
                    "table_index": i + 1,
                    "data": table_data,
                    "markdown": self._table_to_markdown(table_data)
                })
            
            metadata = {
                "paragraph_count": len(doc.paragraphs),
                "table_count": len(tables)
            }
            
            return {
                "content": text_content,
                "images": [],
                "tables": tables,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"处理DOCX失败: {str(e)}")
            raise
    
    async def _process_html(self, content: bytes) -> Dict[str, Any]:
        """处理HTML文件"""
        if not HAS_HTML:
            raise RuntimeError("未安装HTML处理库")
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # 移除script和style标签
            for script in soup(["script", "style"]):
                script.decompose()
            
            # 提取文本
            text_content = soup.get_text(separator='\n', strip=True)
            
            # 提取表格
            tables = []
            for i, table in enumerate(soup.find_all('table')):
                table_data = []
                for row in table.find_all('tr'):
                    cells = row.find_all(['td', 'th'])
                    table_data.append([cell.get_text(strip=True) for cell in cells])
                
                if table_data:
                    tables.append({
                        "table_index": i + 1,
                        "data": table_data,
                        "markdown": self._table_to_markdown(table_data)
                    })
            
            metadata = {
                "title": soup.title.string if soup.title else None,
                "table_count": len(tables)
            }
            
            return {
                "content": text_content,
                "images": [],
                "tables": tables,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"处理HTML失败: {str(e)}")
            raise
    
    async def _process_text(self, content: bytes) -> Dict[str, Any]:
        """处理纯文本文件"""
        try:
            # 尝试不同编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
            text_content = None
            
            for encoding in encodings:
                try:
                    text_content = content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if text_content is None:
                text_content = content.decode('utf-8', errors='ignore')
            
            return {
                "content": text_content,
                "images": [],
                "tables": [],
                "metadata": {
                    "line_count": len(text_content.split('\n')),
                    "char_count": len(text_content)
                }
            }
            
        except Exception as e:
            logger.error(f"处理文本文件失败: {str(e)}")
            raise
    
    async def _process_image(self, content: bytes) -> Dict[str, Any]:
        """处理图片文件（使用OCR提取文字）"""
        if not HAS_OCR:
            return {
                "content": "[图片文件，OCR功能未启用]",
                "images": [],
                "tables": [],
                "metadata": {"has_ocr": False}
            }
        
        try:
            image = Image.open(io.BytesIO(content))
            
            # OCR提取文字
            text_content = pytesseract.image_to_string(image, lang='chi_sim+eng')
            
            metadata = {
                "width": image.width,
                "height": image.height,
                "format": image.format,
                "mode": image.mode,
                "has_ocr": True
            }
            
            return {
                "content": text_content,
                "images": [],
                "tables": [],
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"处理图片失败: {str(e)}")
            raise
    
    def _table_to_markdown(self, table_data: List[List[str]]) -> str:
        """将表格数据转换为Markdown格式"""
        if not table_data:
            return ""
        
        try:
            # 表头
            header = "| " + " | ".join(str(cell) for cell in table_data[0]) + " |"
            separator = "|" + "|".join(["---" for _ in table_data[0]]) + "|"
            
            # 表体
            rows = []
            for row in table_data[1:]:
                rows.append("| " + " | ".join(str(cell) for cell in row) + " |")
            
            return "\n".join([header, separator] + rows)
            
        except Exception as e:
            logger.error(f"表格转换失败: {str(e)}")
            return ""


# 单例
_file_service = None


def get_file_service() -> FileService:
    """获取文件服务实例"""
    global _file_service
    if _file_service is None:
        _file_service = FileService()
    return _file_service
