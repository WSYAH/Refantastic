from typing import List, Dict, Any
from loguru import logger


class TableProcessor:
    """表格数据处理器"""
    
    @staticmethod
    def table_to_markdown(table_data: List[List[str]]) -> str:
        """
        将表格转换为 Markdown 格式
        
        Args:
            table_data: 二维列表表示的表格数据
        """
        if not table_data:
            return ""
        
        lines = []
        
        # 表头
        header = table_data[0]
        lines.append("| " + " | ".join(header) + " |")
        
        # 分隔线
        lines.append("| " + " | ".join(["---"] * len(header)) + " |")
        
        # 数据行
        for row in table_data[1:]:
            # 确保行长度与表头一致
            padded_row = row + [""] * (len(header) - len(row))
            lines.append("| " + " | ".join(padded_row[:len(header)]) + " |")
        
        return "\n".join(lines)
    
    @staticmethod
    def table_to_text(table_data: List[List[str]], delimiter: str = "\t") -> str:
        """
        将表格转换为纯文本格式
        
        Args:
            table_data: 二维列表表示的表格数据
            delimiter: 列分隔符
        """
        if not table_data:
            return ""
        
        return "\n".join([delimiter.join(row) for row in table_data])
    
    @staticmethod
    def table_to_dict(table_data: List[List[str]]) -> List[Dict[str, Any]]:
        """
        将表格转换为字典列表（表头作为键）
        
        Args:
            table_data: 二维列表表示的表格数据
        """
        if not table_data or len(table_data) < 2:
            return []
        
        headers = table_data[0]
        result = []
        
        for row in table_data[1:]:
            row_dict = {}
            for i, header in enumerate(headers):
                value = row[i] if i < len(row) else ""
                row_dict[header] = value
            result.append(row_dict)
        
        return result
    
    @staticmethod
    def merge_tables(tables: List[Dict[str, Any]], format: str = "markdown") -> str:
        """
        合并多个表格为文本
        
        Args:
            tables: 表格列表
            format: 输出格式 (markdown, text)
        """
        parts = []
        
        for idx, table_info in enumerate(tables, 1):
            table_data = table_info.get("data", [])
            if not table_data:
                continue
            
            parts.append(f"\n[表格 {idx}]")
            
            if table_info.get("page"):
                parts.append(f"(第 {table_info['page']} 页)")
            
            if format == "markdown":
                parts.append(TableProcessor.table_to_markdown(table_data))
            else:
                parts.append(TableProcessor.table_to_text(table_data))
            
            parts.append("")  # 空行分隔
        
        return "\n".join(parts)
    
    @staticmethod
    def clean_table(table_data: List[List[str]]) -> List[List[str]]:
        """
        清理表格数据
        
        - 移除空行
        - 去除单元格首尾空白
        - 统一列数
        """
        if not table_data:
            return []
        
        # 去除空白并过滤空行
        cleaned = []
        for row in table_data:
            cleaned_row = [cell.strip() if isinstance(cell, str) else str(cell) for cell in row]
            if any(cleaned_row):  # 不是全空行
                cleaned.append(cleaned_row)
        
        if not cleaned:
            return []
        
        # 统一列数（以第一行为准）
        max_cols = max(len(row) for row in cleaned)
        
        normalized = []
        for row in cleaned:
            if len(row) < max_cols:
                row = row + [""] * (max_cols - len(row))
            normalized.append(row[:max_cols])
        
        return normalized
