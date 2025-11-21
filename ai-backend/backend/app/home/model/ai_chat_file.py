#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Optional

from sqlalchemy import JSON, Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base


class AIChatFile(Base):
    """AI Chat File model for storing file information in chat messages"""

    __tablename__ = "ai_chat_file"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    chat_message_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # ExportResult 主要字段
    filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_paths: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # 多文件路径
    export_directory: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    task_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    data_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    export_time: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 文件类型和状态
    file_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # csv, excel, pdf等
    status: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "chat_message_id": self.chat_message_id,
            "filename": self.filename,
            "file_path": self.file_path,
            "file_paths": self.file_paths,
            "export_directory": self.export_directory,
            "task_id": self.task_id,
            "data_source": self.data_source,
            "export_time": self.export_time,
            "url": self.url,
            "file_size": self.file_size,
            "error_message": self.error_message,
            "file_type": self.file_type,
            "status": self.status,
            "created_time": self.created_time.isoformat() if self.created_time else None,
            "updated_time": self.updated_time.isoformat() if self.updated_time else None,
        }
