from collections.abc import AsyncGenerator
from datetime import datetime
import uuid

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Uuid,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase


# 使用 SQLite 数据库和 aiosqlite 异步驱动。
# .test.db 是保存数据的本地数据库文件。
DATABASE_URL = "sqlite+aiosqlite:///.test.db"


# 所有数据库模型都继承这个基础类。
# Base.metadata 会收集这些模型对应的数据表信息。
class Base(DeclarativeBase):
    pass


# Post 对应数据库中的 posts 表，用来保存文件或媒体帖子的信息。
class Post(Base):
    __tablename__ = "posts"

    # UUID 是全局唯一 ID，由 uuid.uuid4 自动生成。primary_key是表示主键，表示唯一；default=uuid.uuid4,表示创建数据时自动生成UUID
    id = Column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )

    # 帖子的文字说明，可以为空。
    caption = Column(Text)

    # 文件访问地址、类型和文件名是必填字段。
    url = Column(
        String,
        nullable=False,
    )

    file_type = Column(
        String,
        nullable=False,
    )

    file_name = Column(
        String,
        nullable=False,
    )

    # 创建对象时自动记录当前 UTC 时间。
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )


# engine 负责建立和管理异步数据库连接。
engine = create_async_engine(DATABASE_URL)


# Session 工厂：每次调用都会创建一个新的异步数据库会话。
# expire_on_commit=False 让对象提交后仍能直接读取已有属性。
async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


# 创建 Base 收集到的所有数据表；已经存在的表不会重复创建。
async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all
        )


# 作为 FastAPI 依赖提供 Session，请求结束后会自动关闭会话。
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
