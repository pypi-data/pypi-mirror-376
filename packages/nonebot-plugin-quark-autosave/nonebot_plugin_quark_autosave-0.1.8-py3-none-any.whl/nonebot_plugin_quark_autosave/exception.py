from collections.abc import Callable
from functools import wraps

import httpx
from nonebot.matcher import current_matcher


class QASException(Exception):
    def __init__(self, message: str):
        super().__init__(f"QAS: {message}")


def handle_exception():
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except QASException as e:
                matcher = current_matcher.get()
                await matcher.finish(str(e))
            except httpx.HTTPError:
                matcher = current_matcher.get()
                await matcher.send("请求失败, 详见后台输出")
                raise

        return wrapper

    return decorator
