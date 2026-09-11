'''
注册
↓
User 写入数据库
↓
登录
↓
认证后生成 JWT
↓
客户端后续请求携带 Bearer Token
↓
current_active_user 验证 Token
↓
得到 current_user
↓
接口继续执行

'''
import uuid
from typing import Optional
#是一个专门为 FastAPI 框架设计的用户身份验证和管理库。
from fastapi import Depends,Request
from fastapi_users import BaseUserManager,FastAPIUsers,UUIDIDMixin
from fastapi_users.authentication import(
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy
)

from fastapi_users.db import SQLAlchemyUserDatabase
from fast_api.db import User,get_user_db

import os
from dotenv import load_dotenv


#创建 JWT 的规则：用 SECRET 签名，并让 Token 1 小时后失效。可以将jwt想象为一个服务器签发的登录凭证
#从 .env 文件中加载环境变量到当前的 Python 运行环境中
load_dotenv()

#假如JWT=用户身份信息+过期时间+签名  那么签名需要SECRET，粗略理解为服务器专用的“防伪印章”

SECRET= os.getenv("AUTH_SECRET")
if not SECRET:
    raise RuntimeError("请在 .env 中配置 AUTH_SECRET")

class UserManager(UUIDIDMixin,BaseUserManager[User,uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user:User, request:Optional[Request] = None):
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(self, user:User, token:str, request:Optional[Request] = None):
        # 后续在这里发送包含 token 的重置邮件；不要把 token 写入日志。
        print(f"Password reset requested for user {user.id}.")

    async def on_after_request_verify(self, user:User, token:str, request:Optional[Request] = None):
        # 后续在这里发送验证邮件；当前仅记录请求，尚未发送邮件。
        print(f"Verification requested for user {user.id}.")


async def get_user_manager(user_db:SQLAlchemyUserDatabase=Depends(get_user_db)):
    yield UserManager(user_db)

#这个BearerTransport规定JWT从请求Header的Bearer位置传来
#Bearer 指的是 HTTP Header 的这种格式：Authorization: Bearer eyJhbGciOi...
#tokenUrl 则告诉 FastAPI/OpenAPI：登录拿 Token 的接口在哪里。
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

def get_jwt_strategy():
    return JWTStrategy(secret=SECRET,lifetime_seconds=3600)

#这个的作用是：Token 怎么传？BearerTransport+Token 怎么生成/验证？->JWTStrategy
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

#FastAPI Users的总控制器，它知道用户 Model 是谁，用户 ID 是 UUID，怎么找 UserManager，用什么认证方式
'''
后面才能自动帮你生成
注册
登录
登出
重置密码
验证用户
用户 CRUD
'''

#创建 FastAPI Users 的用户系统对象。User 是用户模型，UUID 是 ID 类型，get_user_manager 提供用户管理器，auth_backend 是认证方式。
'''本质是：对象 = 类(
    参数1,
    参数2
)'''
fastapi_users = FastAPIUsers[User,uuid.UUID](get_user_manager,[auth_backend])
#检查请求里的 JWT，并返回当前已经登录且处于 active 状态的用户
current_active_user = fastapi_users.current_user(active=True)

'''
SQLAlchemyBaseUserTableUUID
        ↓
定义 User 数据库基础字段
        ↓
class User(...)
        ↓
数据库拥有 user 表

UserCreate
UserRead
UserUpdate
        ↓
定义 API 输入输出格式

FastAPIUsers(...)
        ↓
把用户数据库 + UserManager + JWT 认证组织起来

get_register_router(...)
        ↓
生成注册接口

get_auth_router(...)
        ↓
生成登录接口

get_users_router(...)
        ↓
生成用户资料接口

然后post
User
 id
 │
 │ ForeignKey
 ▼
Post.user_id
得到
User.posts
Post.user


必须知道的表格
| 代码 | 你至少要知道 |
|---|---|
| `User` | 数据库用户 Model |
| `UserCreate` | 注册请求 Schema |
| `UserRead` | 用户响应 Schema |
| `UserUpdate` | 修改用户 Schema |
| `SQLAlchemyBaseUserTableUUID` | FastAPI Users 提供的 UUID 用户表基础类 |
| `ForeignKey("user.id")` | Post.user_id 指向 User.id |
| `relationship("Post")` | Python 层访问关联 Post |
| `back_populates` | 声明双向 ORM 关系 |
| `get_auth_router()` | 生成登录/登出接口 |
| `get_register_router()` | 生成注册接口 |
| `get_users_router()` | 生成用户管理接口 |
| `include_router()` | 把一组接口挂到 FastAPI |
| `prefix` | 给接口统一加 URL 前缀 |
| `tags` | Swagger 文档分类 |
'''