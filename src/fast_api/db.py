'''
整体思路：
FastAPI 接口
   ↓
Session
   ↓
SQLAlchemy ORM
   ↓
Engine
   ↓
SQLite / PostgreSQL
核心代码：
1. 定义数据库地址
2. 定义表长什么样
3. 创建数据库连接工具
4. 给每个请求提供 Session

'''

'''
JWT代码验证
注册用户
  ↓
登录
  ↓
FastAPI Users 校验邮箱/密码
  ↓
生成 JWT
  ↓
客户端以后请求时带上：
Authorization: Bearer <token>
  ↓
current_active_user 验证 JWT
  ↓
拿到当前登录的 User
  ↓
接口才允许继续执行

user.py 定义 JWT 认证后端，app.py 把登录、注册、用户管理路由挂载进 FastAPI，并且 /upload、删除帖子这些接口开始依赖当前登录用户。
'''


from collections.abc import AsyncGenerator
from datetime import datetime
import uuid

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Uuid,
    ForeignKey
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase,relationship
from fastapi_users.db import SQLAlchemyUserDatabase,SQLAlchemyBaseUserTableUUID
from fastapi_users_db_sqlalchemy.generics import GUID
from fastapi import Depends
# 使用 SQLite 数据库和 aiosqlite 异步驱动。
# .test.db 是保存数据的本地数据库文件。
#SQLite 可以理解成：一个不需要额外启动数据库服务器的轻量数据库。
DATABASE_URL = "sqlite+aiosqlite:///.test.db"


# 所有数据库模型都继承这个基础类。这个 Base 是所有 ORM 模型的父类。
# Base.metadata 会收集这些模型对应的数据表信息。
class Base(DeclarativeBase):
    pass

#SQLAlchemyBaseUserTableUUID:FastAPI Users 已经替你定义了很多用户表字段
#我要创建一个使用 UUID 主键的 FastAPI Users 用户表，同时它也是我项目 SQLAlchemy Base 下的模型。
class User(SQLAlchemyBaseUserTableUUID,Base):
    #一个 User 可以通过 .posts 访问属于自己的 Post。
    ## back_populates 用于双向绑定对方的属性名称
    posts = relationship("Post",back_populates="user")

'''
relationship：建立 ORM 对象之间的访问关系，不是数据库真正存的一列，双方都写表明这条关系可以双向访问。(用上back_populates两个对象里都得体现，但是在这里只有Post对象里设置对User的外键,所以是一对多，这个通过外键约束)
ForeignKey：建立数据库层面的关联。

 一对多判断：
 多条 Post 都可以保存同一个 user_id，
 但每条 Post 只有一个 user_id。
 所以：一个 User -> 多个 Post，一篇 Post -> 一个 User。

 双向 relationship 不等于多对多。
 User.posts 和 Post.user 只是同一条一对多关系的两个访问方向。

 多对多判断：
 两边都可以对应多个对象，通常需要第三张中间表保存双方 id。

'''





# Post 对应数据库中的 posts 表，用来保存文件或媒体帖子的信息。
#Post 不是普通 Python 类，它是数据库模型 ，继承这个Base
#当 Post 继承 Base 后，SQLAlchemy 会把 Post 这张表的信息记录到：Base.metadata
class Post(Base):
    __tablename__ = "posts"

    # UUID 是全局唯一 ID，由 uuid.uuid4 自动生成。primary_key是表示主键，表示唯一；default=uuid.uuid4,表示创建数据时自动生成UUID
    id = Column(
        #个列 (id) 应该存储 UUID（通用唯一识别码） 数据
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    #user_id 保存帖子作者的 UUID，外键指向用户表的 id
    #ForeignKey("user.id")意思：posts.user_id 必须指向 user 表里的 id。GUID:user_id 保存 UUID 类型。
    user_id = Column(GUID,ForeignKey("user.id"),nullable=False)
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

    '''
    post.user_id
→ 作者 ID

post.user
→ 作者这个完整 User 对象
    '''
    user = relationship("User",back_populates="posts")
'''
最终表的样子
| id   | caption | url    | file_type | file_name | created_at |
| ---- | ------- | ------ | --------- | --------- | ---------- |
| UUID | text    | string | string    | string    | datetime   |
本质就是：

用 Python 类描述数据库表结构。

这就是 ORM 的核心思想之一。
ORM：
Object Relational Mapping
对象关系映射
用了 SQLAlchemy ORM 以后，你可以操作 Python 对象：
'''

# engine 负责建立和管理异步数据库连接。应用程序与数据库之间的连接基础设施
engine = create_async_engine(DATABASE_URL)


# Session 工厂：每次调用都会创建一个新的异步数据库会话。
# expire_on_commit=False 让对象提交后仍能直接读取已有属性。

#Session 是你真正写 CRUD 时用的东西。CRUD就是创建，插入，删除，查询，修改数据库基本操作



#复制创建Session工厂
async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
)

#Base.metadata.create_all才相当于：根据图纸开始施工。
# 创建 Base 收集到的所有数据表；已经存在的表不会重复创建。
#定义一个异步的建表函数。
async def create_db_and_tables():
    '''
    with
= 管理普通资源

async with
= 管理异步资源

示例：
with open('example.txt', 'r') as file:
    content = file.read()
    print(content)
# 文件已自动关闭
    
    
    engine：

    数据库连接基础设施。

    begin()：

    开始一个数据库连接/事务上下文。

    as conn：

    把这个连接对象叫做 conn。

  所以相当于：

engine
↓
获得连接
↓
conn
↓
使用
↓
自动结束
    '''

    #获取一个数据库连接，并保证用完自动处理。
    async with engine.begin() as conn:
        #等待数据库执行建表操作。
        await conn.run_sync(
            Base.metadata.create_all #根据所有 Model 建表。
        )





# 作为 FastAPI 依赖提供 Session，请求结束后会自动关闭会话。

#Session 可以理解成：一次数据库操作上下文
'''
以后 CRUD 都会围绕它：

session.add(...)
await session.execute(...)
await session.commit()
await session.rollback()
Session
├─ 添加数据
├─ 查询数据
├─ 修改数据
├─ 删除数据
├─ commit
└─ rollback
'''
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


#获取数据库中的数据
async def get_user_db(session:AsyncSession=Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session,User)

#异步函数与普通函数最大区别是，异步中可以用await


'''

await。

比如以后调用数据库：

async def get_user():
    result = await database.query(...)
await:这件事需要等待结果，但等待期间不要傻站着，把 CPU 让给其他任务；结果回来了以后我再从这里继续。

yield = 给出去，但函数暂时不结束。这正适合数据库 Session。
'''



'''
| 函数 | 管理的对象 | 执行频率 |
|---|---|---|
| `lifespan()` | 整个 FastAPI 应用 | 每次应用启动、关闭 |
| `get_async_session()` | 某一次请求的数据库 Session | 每个使用该依赖的请求 |



async def
= 定义一个异步函数

await
= 等一个异步操作完成，等待时可以让出执行权

async with
= 异步地管理资源的进入和退出

yield
= 暂时把值/控制权交出去，函数以后还能继续
'''
