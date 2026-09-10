import uuid
from typing import Optional
#是一个专门为 FastAPI 框架设计的用户身份验证和管理库。
from fastapi import Depends,Request
from fastapi_users import BaseUserManager,FastAPIUsers,UUIDIDMixin,models
from fastapi_users.authentication import(
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy
)

from fastapi_users.db import SQLAlchemyUserDatabase
from fast_api.db import User,get_user_db