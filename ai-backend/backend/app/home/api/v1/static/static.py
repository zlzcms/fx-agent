# -*- coding: utf-8 -*-
# @Author: AI Assistant
# @Date: 2025-01-XX
# @Description: 静态文件API服务

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from backend.app.admin.model import User
from backend.app.home.api.deps import get_current_home_user

router = APIRouter()
# 静态文件基础路径
STATIC_BASE_PATH = Path(__file__).parent.parent.parent.parent.parent.parent / "agents" / "static"


@router.get("/files/{data_source}/{date}/{task_id}/{filename}")
async def get_static_file(
    data_source: str, date: str, task_id: str, filename: str, current_user: User = Depends(get_current_home_user)
):
    """获取指定的静态文件"""
    # 构建文件路径
    file_path = STATIC_BASE_PATH / data_source / date / task_id / filename
    print(file_path)
    # 检查文件是否存在
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="文件未找到")

    # 检查文件路径安全性（防止路径遍历攻击）
    try:
        file_path.resolve().relative_to(STATIC_BASE_PATH.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="访问被拒绝")

    # 根据文件扩展名设置媒体类型
    media_type_map = {
        ".csv": "text/csv",
        ".json": "application/json",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls": "application/vnd.ms-excel",
        ".md": "text/markdown",
        ".txt": "text/plain",
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
        ".html": "text/html",
        ".xml": "application/xml",
        ".zip": "application/zip",
    }

    file_extension = file_path.suffix.lower()
    media_type = media_type_map.get(file_extension, "application/octet-stream")

    return FileResponse(path=str(file_path), media_type=media_type, filename=filename)


@router.get("/list/{data_source}/{date}/{task_id}")
async def list_task_files(
    data_source: str, date: str, task_id: str, current_user: User = Depends(get_current_home_user)
):
    """列出指定任务的所有文件"""
    # 构建目录路径
    dir_path = STATIC_BASE_PATH / data_source / date / task_id

    # 检查目录是否存在
    if not dir_path.exists() or not dir_path.is_dir():
        raise HTTPException(status_code=404, detail="目录未找到")

    # 检查路径安全性
    try:
        dir_path.resolve().relative_to(STATIC_BASE_PATH.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="访问被拒绝")

    # 获取文件列表
    files = []
    try:
        for item in dir_path.iterdir():
            if item.is_file():
                file_info = {
                    "filename": item.name,
                    "size": item.stat().st_size,
                    "modified_time": item.stat().st_mtime,
                    "extension": item.suffix.lower(),
                    "download_url": f"/api/v1/static/files/{data_source}/{date}/{task_id}/{item.name}",
                }
                files.append(file_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取目录失败: {str(e)}")

    return {"data_source": data_source, "date": date, "task_id": task_id, "files": files, "total_files": len(files)}
