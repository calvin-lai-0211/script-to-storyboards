"""
API 通用辅助函数和依赖注入
"""
from utils.database import Database
from utils.config import DB_CONFIG, R2_CONFIG


def get_db():
    """
    数据库依赖（用于 FastAPI Depends）

    使用方法:
        @router.get("/endpoint")
        async def my_endpoint(db: Database = Depends(get_db)):
            ...

    注意:
        - 每个请求创建新的 Database 实例
        - 不使用 auto_init（性能优化）
    """
    db = Database(DB_CONFIG)
    try:
        yield db
    finally:
        pass


def to_cdn_url(image_url: str) -> str:
    """
    将图片 URL 转换为 CDN URL

    Args:
        image_url: 可以是以下格式之一:
            - R2 key: "tiangui/1/characters/李明.jpg"
            - 完整 URL: "https://cdn.example.com/xxx.jpg"
            - None/空字符串

    Returns:
        CDN URL 或 None
    """
    if not image_url:
        return None

    # 如果已经是完整 URL，直接返回
    if image_url.startswith("http://") or image_url.startswith("https://"):
        return image_url

    # 否则视为 R2 key，拼接 CDN 基础 URL
    return f"{R2_CONFIG['cdn_base_url']}/{image_url}"
