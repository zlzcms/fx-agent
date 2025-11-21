# -*- coding: utf-8 -*-
# MCP Service Database Package
from .admin import admin_db
from .warehouse import warehouse_db

__all__ = ["warehouse_db", "admin_db"]
