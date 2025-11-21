import json

from typing import Any, Dict, Optional

from backend.agents.config.setting import settings
from backend.common.log import logger
from backend.database.redis import redis_client


async def check_cache(cache_hash: str) -> Optional[Dict[str, Any]]:
    """检查是否存在重复请求，如果存在则返回缓存的结果"""
    try:
        if not settings.is_cache_request:
            return None
        cache_key = f"agent_cache:{cache_hash}"
        cached_result = await redis_client.get(cache_key)
        if cached_result:
            return json.loads(cached_result)
        return None
    except Exception as e:
        logger.warning(f"Failed to check duplicate request: {e}")
        return None


async def set_cache(cache_hash: str, result: Dict[str, Any]) -> None:
    """缓存请求结果"""
    try:
        cache_key = f"agent_cache:{cache_hash}"
        await redis_client.setex(cache_key, settings.cache_ttl, json.dumps(result, ensure_ascii=False))
    except Exception as e:
        logger.warning(f"Failed to cache request result: {e}")
