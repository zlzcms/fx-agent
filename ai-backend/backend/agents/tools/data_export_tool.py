#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import json
import os

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from backend.common.log import logger


@dataclass
class ExportResult:
    """统一的导出结果结构"""

    success: bool
    file_path: str = None
    file_paths: Dict[str, str] = None  # 用于多文件导出
    filename: str = None
    export_directory: str = None
    task_id: str = None
    data_source: str = None
    export_time: str = None
    file_size: int = None
    error_message: str = None
    url: str = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "success": self.success,
            "file_path": self.file_path,
            "file_paths": self.file_paths,
            "filename": self.filename,
            "export_directory": self.export_directory,
            "task_id": self.task_id,
            "data_source": self.data_source,
            "export_time": self.export_time,
            "file_size": self.file_size,
            "error_message": self.error_message,
            "url": self.url,
        }


class DataExportTool:
    """数据导出工具类"""

    def __init__(self, data_source: str, base_path: str = ""):
        """初始化数据导出工具

        Args:
            base_path: 基础路径，默认为agents/static
        """
        self.data_source = data_source
        self.base_url = "/api/v1/home/static/files"
        if base_path == "admin":
            self.base_url = "/api/v1/static/files"
        current_dir = Path(__file__).parent.parent
        self.base_path = current_dir / "static"
        # 确保基础目录存在
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_file_size(self, file_path: str | Path) -> int:
        """获取文件大小"""
        try:
            return os.path.getsize(file_path)
        except (OSError, FileNotFoundError):
            return 0

    def _count_records(self, data: Dict[str, Any]) -> int:
        """统计记录总数"""
        total_records = 0
        for table_data in data.values():
            if isinstance(table_data, dict) and "rows" in table_data:
                total_records += len(table_data["rows"])
        return total_records

    def export_mcp_data_to_csv(self, table_name: str, table_data: Dict[str, Any], task_id: str) -> dict:
        """将MCP数据导出为CSV文件
        Args:
            data: MCP数据，格式如 {'columns': [...], 'rows': [...]}
            task_id: 任务ID
        """
        try:
            # 创建日期目录
            date_str = datetime.now().strftime("%Y-%m-%d")
            export_dir = self.base_path / self.data_source / date_str / task_id
            url = self.base_url + f"/{self.data_source}/{date_str}/{task_id}"
            export_dir.mkdir(parents=True, exist_ok=True)

            exported_files = {}
            total_size = 0

            # 遍历每个表的数据
            if not isinstance(table_data, dict) or "columns" not in table_data or "rows" not in table_data:
                logger.error(f"数据导出失败: 表 {table_name} 数据格式无效")
                return ExportResult(
                    success=False, task_id=task_id, error_message=f"表 {table_name} 数据格式无效"
                ).to_dict()

            # 生成CSV文件路径
            csv_filename = f"{table_name}.csv"
            csv_path = export_dir / csv_filename
            url = url + f"/{csv_filename}"

            # 写入CSV文件
            with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                # 写入列头
                writer.writerow(table_data["columns"])
                # 写入数据行
                writer.writerows(table_data["rows"])
            exported_files[table_name] = str(csv_path)
            total_size += self._get_file_size(csv_path)

            logger.info(f"数据导出完成，共导出 {len(exported_files)} 个表")
            export_time = datetime.now().isoformat()
            return ExportResult(
                success=True,
                filename=csv_filename,
                file_paths=exported_files,
                export_directory=str(export_dir),
                task_id=task_id,
                data_source=self.data_source,
                export_time=export_time,
                url=url,
                file_size=total_size,
            ).to_dict()

        except Exception as e:
            logger.error(f"数据导出失败: {e}")
            return ExportResult(success=False, task_id=task_id, error_message=str(e)).to_dict()

    def export_mcp_data_to_single_csv(self, data: Dict[str, Any], task_id: str, filename: str = None) -> dict:
        """将MCP数据导出为单个CSV文件
        Args:
            data: MCP数据，格式如 {'table_name': {'columns': [...], 'rows': [...]}}
            task_id: 任务ID
            filename: 自定义文件名（不包含扩展名），如果为None则使用默认命名
        """
        try:
            # 创建日期目录
            date_str = datetime.now().strftime("%Y-%m-%d")
            export_dir = self.base_path / self.data_source / date_str / task_id
            url = self.base_url + f"/{self.data_source}/{date_str}/{task_id}"
            export_dir.mkdir(parents=True, exist_ok=True)

            # 生成文件名
            if filename is None:
                filename = self.generate_filename_from_data(data)

            csv_filename = f"{filename}.csv"
            csv_path = export_dir / csv_filename
            url = url + f"/{csv_filename}"
            # 写入合并的CSV文件
            with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)

                # 遍历每个表的数据
                for table_name, table_data in data.items():
                    if not isinstance(table_data, dict) or "columns" not in table_data or "rows" not in table_data:
                        logger.warning(f"跳过无效的表数据: {table_name}")
                        continue
                    # 写入表名作为分隔
                    writer.writerow([f"=== {table_name} ==="])
                    # 写入列头
                    writer.writerow(table_data["columns"])
                    # 写入数据行
                    writer.writerows(table_data["rows"])
                    # 添加空行分隔
                    writer.writerow([])

            export_time = datetime.now().isoformat()
            file_size = self._get_file_size(csv_path)

            logger.info(f"成功导出合并数据到 {csv_path}")

            return ExportResult(
                success=True,
                file_path=str(csv_path),
                filename=csv_filename,
                export_directory=str(export_dir),
                task_id=task_id,
                data_source=self.data_source,
                export_time=export_time,
                file_size=file_size,
                url=url,
            ).to_dict()

        except Exception as e:
            logger.error(f"合并数据导出失败: {e}")
            return ExportResult(
                success=False, task_id=task_id, data_source=self.data_source, error_message=str(e)
            ).to_dict()

    def export_mcp_data_to_excel(self, data: Dict[str, Any], task_id: str, filename: str = None) -> dict:
        """将MCP数据导出为Excel文件（每个表作为一个工作表）

        Args:
            data: MCP数据，格式如 {'table_name': {'columns': [...], 'rows': [...]}}
            task_id: 任务ID
            filename: 自定义文件名（不包含扩展名），如果为None则使用默认命名
        Returns:
            dict: 统一的导出结果
        """
        try:
            import pandas as pd

            # 创建日期目录
            date_str = datetime.now().strftime("%Y-%m-%d")
            export_dir = self.base_path / self.data_source / date_str / task_id
            url = self.base_url + f"/{self.data_source}/{date_str}/{task_id}"
            export_dir.mkdir(parents=True, exist_ok=True)

            # 生成文件名
            if filename is None:
                filename = self.generate_filename_from_data(data)

            excel_filename = f"{filename}.xlsx"
            excel_path = export_dir / excel_filename
            url = url + f"/{excel_filename}"
            # 创建Excel写入器
            with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
                for table_name, table_data in data.items():
                    if not isinstance(table_data, dict) or "columns" not in table_data or "rows" not in table_data:
                        logger.warning(f"跳过无效的表数据: {table_name}")
                        continue

                    # 创建DataFrame
                    df = pd.DataFrame(table_data["rows"], columns=table_data["columns"])

                    # 写入工作表（限制工作表名称长度）
                    sheet_name = table_name[:31] if len(table_name) > 31 else table_name
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

            export_time = datetime.now().isoformat()
            file_size = self._get_file_size(excel_path)

            logger.info(f"成功导出Excel文件到 {excel_path}")

            return ExportResult(
                success=True,
                file_path=str(excel_path),
                filename=excel_filename,
                export_directory=str(export_dir),
                task_id=task_id,
                url=url,
                data_source=self.data_source,
                export_time=export_time,
                file_size=file_size,
            ).to_dict()

        except ImportError:
            error_msg = "导出Excel需要安装pandas和openpyxl: pip install pandas openpyxl"
            logger.error(error_msg)
            return ExportResult(
                success=False, task_id=task_id, data_source=self.data_source, error_message=error_msg
            ).to_dict()
        except Exception as e:
            logger.error(f"Excel导出失败: {e}")
            return ExportResult(
                success=False, task_id=task_id, data_source=self.data_source, error_message=str(e)
            ).to_dict()

    def export_to_json(self, data: Dict[str, Any], task_id: str, filename: str = None) -> dict:
        """将数据导出为JSON文件
        Args:
            data: 要导出的数据
            task_id: 任务ID
            filename: 自定义文件名
        Returns:
            dict: 统一的导出结果
        """
        try:
            # 创建日期目录
            date_str = datetime.now().strftime("%Y-%m-%d")
            export_dir = self.base_path / self.data_source / date_str / task_id
            url = self.base_url + f"/{self.data_source}/{date_str}/{task_id}"
            export_dir.mkdir(parents=True, exist_ok=True)

            # 生成JSON文件路径
            if filename is None:
                filename = f"data_{datetime.now().strftime('%H%M%S')}"
            json_filename = f"{filename}.json"
            json_path = export_dir / json_filename
            url = url + f"/{json_filename}"
            # 写入JSON文件
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            export_time = datetime.now().isoformat()
            file_size = self._get_file_size(json_path)

            logger.info(f"成功导出JSON文件到 {json_path}")

            return ExportResult(
                success=True,
                file_path=str(json_path),
                filename=json_filename,
                export_directory=str(export_dir),
                task_id=task_id,
                data_source=self.data_source,
                export_time=export_time,
                file_size=file_size,
                url=url,
            ).to_dict()

        except Exception as e:
            logger.error(f"JSON导出失败: {e}")
            return ExportResult(
                success=False, task_id=task_id, data_source=self.data_source, error_message=str(e)
            ).to_dict()

    def get_export_directory(self, task_id: str) -> Path:
        """获取导出目录路径

        Args:
            task_id: 任务ID
            data_source: 数据源名称

        Returns:
            Path: 导出目录路径
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        return self.base_path / self.data_source / date_str / task_id

    def list_exported_files(self, task_id: str) -> List[str]:
        """列出指定任务的所有导出文件

        Args:
            task_id: 任务ID
            data_source: 数据源名称

        Returns:
            List[str]: 文件路径列表
        """
        export_dir = self.get_export_directory(task_id)

        if not export_dir.exists():
            return []

        files = []
        for file_path in export_dir.rglob("*"):
            if file_path.is_file():
                files.append(str(file_path))

        return files

    def cleanup_old_exports(self, days_to_keep: int = 7) -> int:
        """清理旧的导出文件

        Args:
            days_to_keep: 保留天数

        Returns:
            int: 删除的文件数量
        """
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        deleted_count = 0

        try:
            for date_dir in self.base_path.rglob("*"):
                if date_dir.is_dir() and len(date_dir.name) == 10:  # YYYY-MM-DD格式
                    try:
                        dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d")
                        if dir_date < cutoff_date:
                            import shutil

                            shutil.rmtree(date_dir)
                            deleted_count += 1
                            logger.info(f"删除过期目录: {date_dir}")
                    except ValueError:
                        continue  # 跳过非日期格式的目录
        except Exception as e:
            logger.error(f"清理过期文件失败: {e}")

        return deleted_count

    def export_terminal_to_markdown(self, s_content: str | dict, task_id: str, filename: str = None) -> dict:
        """将终端输出内容导出为Markdown文件

        Args:
            content: 终端输出内容，可以是字符串或字典
            task_id: 任务ID
            filename: 自定义文件名（不包含扩展名），如果为None则使用默认命名

        Returns:
            dict: 统一的导出结果
        """
        try:
            content = "# 终端输出记录\n\n"
            content += f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            content += f"**任务ID**: {task_id}\n\n"
            content += "---\n\n"
            content += "## 输出内容\n\n"
            content += "```\n"

            # 处理不同类型的内容
            if isinstance(s_content, (dict, list, tuple)):
                content += json.dumps(s_content, ensure_ascii=False, indent=2)
            else:
                content += str(s_content)

            content += "\n```\n"
            return self.export_to_markdown(content, task_id, filename)

        except Exception as e:
            logger.error(f"终端内容导出失败: {e}")
            return ExportResult(
                success=False, task_id=task_id, data_source=self.data_source, error_message=str(e)
            ).to_dict()

    def export_to_html(self, content: str, task_id: str, filename: str = None) -> dict:
        """将内容导出为HTML文件"""
        try:
            date_str = datetime.now().strftime("%Y-%m-%d")
            export_dir = self.base_path / self.data_source / date_str / task_id
            url = self.base_url + f"/{self.data_source}/{date_str}/{task_id}"
            export_dir.mkdir(parents=True, exist_ok=True)

            if not filename:
                filename = f"web_{datetime.now().strftime('%H%M%S')}"

            html_filename = f"{filename}.html"
            html_path = export_dir / html_filename
            url = url + f"/{html_filename}"

            with open(html_path, "w", encoding="utf-8") as f:
                f.write(content)

            export_time = datetime.now().isoformat()
            file_size = self._get_file_size(html_path)

            logger.info(f"成功导出HTML文件到 {html_path}")

            return ExportResult(
                success=True,
                file_path=str(html_path),
                filename=html_filename,
                export_directory=str(export_dir),
                task_id=task_id,
                data_source=self.data_source,
                export_time=export_time,
                file_size=file_size,
                url=url,
            ).to_dict()

        except Exception as e:
            logger.error(f"HTML导出失败: {e}")
            return ExportResult(
                success=False, task_id=task_id, data_source=self.data_source, error_message=str(e)
            ).to_dict()

    def export_to_markdown(self, content: str | dict, task_id: str, filename: str = None) -> dict:
        """将内容导出为Markdown文件

        Args:
            content: 输出内容，可以是字符串或字典
            task_id: 任务ID
            filename: 自定义文件名（不包含扩展名），如果为None则使用默认命名
            data_source: 数据源名称，默认为"terminal"

        Returns:
            dict: 统一的导出结果
        """
        try:
            # 创建日期目录
            date_str = datetime.now().strftime("%Y-%m-%d")
            export_dir = self.base_path / self.data_source / date_str / task_id
            url = self.base_url + f"/{self.data_source}/{date_str}/{task_id}"
            export_dir.mkdir(parents=True, exist_ok=True)

            # 生成文件名
            if not filename:
                filename = f"data_{datetime.now().strftime('%H%M%S')}"

            md_filename = f"{filename}.md"
            md_path = export_dir / md_filename
            url = url + f"/{md_filename}"

            # 处理不同类型的内容
            if isinstance(content, (dict, list, tuple)):
                content_str = json.dumps(content, ensure_ascii=False, indent=2)
            else:
                content_str = str(content)

            # 写入Markdown文件
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(content_str)

            export_time = datetime.now().isoformat()
            file_size = self._get_file_size(md_path)

            logger.info(f"成功导出内容到 {md_path}")

            return ExportResult(
                success=True,
                file_path=str(md_path),
                filename=md_filename,
                export_directory=str(export_dir),
                task_id=task_id,
                data_source=self.data_source,
                export_time=export_time,
                file_size=file_size,
                url=url,
            ).to_dict()

        except Exception as e:
            logger.error(f"内容导出失败: {e}")
            return ExportResult(
                success=False, task_id=task_id, data_source=self.data_source, error_message=str(e)
            ).to_dict()

    def export_markdown_to_pdf(self, markdown_content: str, task_id: str, filename: str = None) -> dict:
        """将 Markdown 内容转换为 PDF 文件

        Args:
            markdown_content: Markdown 格式的内容
            task_id: 任务ID
            filename: 自定义文件名（不包含扩展名），如果为None则使用默认命名

        Returns:
            dict: 统一的导出结果
        """
        try:
            # 创建日期目录
            date_str = datetime.now().strftime("%Y-%m-%d")
            export_dir = self.base_path / self.data_source / date_str / task_id
            url = self.base_url + f"/{self.data_source}/{date_str}/{task_id}"
            export_dir.mkdir(parents=True, exist_ok=True)

            # 生成文件名
            if not filename:
                filename = f"report_{datetime.now().strftime('%H%M%S')}"

            pdf_filename = f"{filename}.pdf"
            pdf_path = export_dir / pdf_filename
            url = url + f"/{pdf_filename}"

            # 步骤 1: 将 Markdown 转换为 HTML
            try:
                from markdown_it import MarkdownIt

                # 使用 "default" 预设以支持更多 markdown 特性（表格、代码块等）
                md = MarkdownIt("default")
                html_content = md.render(markdown_content)
            except ImportError:
                # 如果 markdown-it-py 不存在，尝试使用标准的 markdown 库
                try:
                    import markdown as md

                    md_converter = md.Markdown(extensions=["extra", "tables", "fenced_code", "codehilite"])
                    html_content = md_converter.convert(markdown_content)
                except ImportError:
                    error_msg = "未找到 markdown 转换库，请安装 markdown-it-py 或 markdown"
                    logger.error(error_msg)
                    return ExportResult(
                        success=False, task_id=task_id, data_source=self.data_source, error_message=error_msg
                    ).to_dict()

            # 添加基本的 CSS 样式（包含中文字体支持）
            html_template = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{
                        font-family: "Noto Sans CJK SC", "WenQuanYi Zen Hei", "Microsoft YaHei", "SimHei", Arial, sans-serif;
                        line-height: 1.6;
                        margin: 40px;
                        color: #333;
                    }}
                    h1, h2, h3, h4, h5, h6 {{
                        color: #2c3e50;
                        margin-top: 20px;
                        margin-bottom: 10px;
                    }}
                    table {{
                        border-collapse: collapse;
                        width: 100%;
                        margin: 20px 0;
                    }}
                    th, td {{
                        border: 1px solid #ddd;
                        padding: 12px;
                        text-align: left;
                    }}
                    th {{
                        background-color: #f2f2f2;
                        font-weight: bold;
                    }}
                    code {{
                        background-color: #f4f4f4;
                        padding: 2px 6px;
                        border-radius: 3px;
                        font-family: "Noto Sans Mono CJK SC", "WenQuanYi Zen Hei Mono", 'Courier New', monospace;
                    }}
                    pre {{
                        background-color: #f4f4f4;
                        padding: 15px;
                        border-radius: 5px;
                        overflow-x: auto;
                        font-family: "Noto Sans Mono CJK SC", "WenQuanYi Zen Hei Mono", 'Courier New', monospace;
                    }}
                    blockquote {{
                        border-left: 4px solid #ddd;
                        margin: 20px 0;
                        padding-left: 20px;
                        color: #666;
                    }}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """

            # 步骤 2: 使用 weasyprint 将 HTML 转换为 PDF
            try:
                from weasyprint import HTML
                from weasyprint.text.fonts import FontConfiguration

                font_config = FontConfiguration()
                HTML(string=html_template).write_pdf(pdf_path, font_config=font_config)

                export_time = datetime.now().isoformat()
                file_size = self._get_file_size(pdf_path)

                logger.info(f"成功导出PDF文件到 {pdf_path}")

                return ExportResult(
                    success=True,
                    file_path=str(pdf_path),
                    filename=pdf_filename,
                    export_directory=str(export_dir),
                    task_id=task_id,
                    data_source=self.data_source,
                    export_time=export_time,
                    file_size=file_size,
                    url=url,
                ).to_dict()

            except ImportError:
                # 如果 weasyprint 不可用，尝试使用 pdfkit (需要系统安装 wkhtmltopdf)
                try:
                    import pdfkit

                    pdfkit.from_string(html_template, str(pdf_path))

                    export_time = datetime.now().isoformat()
                    file_size = self._get_file_size(pdf_path)

                    logger.info(f"成功使用pdfkit导出PDF文件到 {pdf_path}")

                    return ExportResult(
                        success=True,
                        file_path=str(pdf_path),
                        filename=pdf_filename,
                        export_directory=str(export_dir),
                        task_id=task_id,
                        data_source=self.data_source,
                        export_time=export_time,
                        file_size=file_size,
                        url=url,
                    ).to_dict()

                except ImportError:
                    # 如果都不可用，尝试使用 xhtml2pdf
                    try:
                        from xhtml2pdf import pisa

                        with open(pdf_path, "wb") as pdf_file:
                            pisa_status = pisa.CreatePDF(html_template, dest=pdf_file)

                            if pisa_status.err == 0:
                                export_time = datetime.now().isoformat()
                                file_size = self._get_file_size(pdf_path)

                                logger.info(f"成功使用xhtml2pdf导出PDF文件到 {pdf_path}")

                                return ExportResult(
                                    success=True,
                                    file_path=str(pdf_path),
                                    filename=pdf_filename,
                                    export_directory=str(export_dir),
                                    task_id=task_id,
                                    data_source=self.data_source,
                                    export_time=export_time,
                                    file_size=file_size,
                                    url=url,
                                ).to_dict()
                            else:
                                error_msg = "xhtml2pdf转换失败"
                                logger.error(error_msg)
                                return ExportResult(
                                    success=False,
                                    task_id=task_id,
                                    data_source=self.data_source,
                                    error_message=error_msg,
                                ).to_dict()

                    except ImportError:
                        error_msg = "PDF生成库未安装，请安装 weasyprint, pdfkit 或 xhtml2pdf"
                        logger.error(error_msg)
                        return ExportResult(
                            success=False, task_id=task_id, data_source=self.data_source, error_message=error_msg
                        ).to_dict()

        except Exception as e:
            logger.error(f"Markdown转PDF失败: {e}")
            return ExportResult(
                success=False, task_id=task_id, data_source=self.data_source, error_message=str(e)
            ).to_dict()

    # 生成自定义文件名的函数
    def generate_filename_from_data(self, data):
        """根据数据生成文件名"""
        if not isinstance(data, dict) or not data:
            return f"data_{datetime.now().strftime('%H%M%S')}"

        # 获取第一个属性的键和值
        first_key = list(data.keys())[0]
        first_value = data[first_key]

        # 如果第一个值是字典，取其第一个键作为标识
        if isinstance(first_value, dict):
            first_identifier = first_key
        else:
            first_identifier = str(first_value)[:20]  # 限制长度

        # 获取属性个数
        property_count = len(data)

        # 生成文件名（清理特殊字符）
        clean_identifier = "".join(c for c in first_identifier if c.isalnum() or c in "_-")
        filename = f"{clean_identifier}_{property_count}tables"

        return filename
