"""使用内存数据库和模拟上传；不修改本地数据库、不上传真实文件。"""
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from fast_api.app import app, imagekit
from fast_api.db import Base, Post, User, get_async_session


class AuthPostTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")

        @event.listens_for(self.engine.sync_engine, "connect")
        def enable_foreign_keys(connection, record):
            connection.execute("PRAGMA foreign_keys=ON")

        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

        async def test_session():
            async with self.sessions() as session:
                yield session

        app.dependency_overrides[get_async_session] = test_session
        self.client = AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        )

    async def asyncTearDown(self):
        await self.client.aclose()
        app.dependency_overrides.clear()
        await self.engine.dispose()

    async def register_and_login(self, email):
        response = await self.client.post(
            "/auth/register", json={"email": email, "password": "test-password-123"}
        )
        self.assertEqual(response.status_code, 201, response.text)
        self.assertNotIn("hashed_password", response.json())
        response = await self.client.post(
            "/auth/jwt/login", data={"username": email, "password": "test-password-123"}
        )
        self.assertEqual(response.status_code, 200, response.text)
        return {"Authorization": "Bearer " + response.json()["access_token"]}

    async def test_anonymous_requests_are_rejected(self):
        with patch.object(imagekit.files, "upload", new_callable=AsyncMock) as upload:
            response = await self.client.post(
                "/upload", files={"file": ("test.png", b"test", "image/png")}
            )
            self.assertEqual(response.status_code, 401)
            upload.assert_not_awaited()
        response = await self.client.delete(f"/posts/{uuid4()}")
        self.assertEqual(response.status_code, 401)

    async def test_author_assignment_and_delete_permissions(self):
        owner = await self.register_and_login("owner@example.com")
        other = await self.register_and_login("other@example.com")
        with patch.object(
            imagekit.files, "upload", new_callable=AsyncMock,
            return_value=SimpleNamespace(url="https://example.com/test.png", name="test.png"),
        ):
            response = await self.client.post(
                "/upload", headers=owner,
                files={"file": ("test.png", b"test", "image/png")},
            )
        self.assertEqual(response.status_code, 200, response.text)
        post_id = response.json()["id"]
        async with self.sessions() as session:
            # 实际执行关联查询，检查作者外键的存储格式与用户主键一致。
            row = (await session.execute(select(Post, User).join(Post.user))).one()
            self.assertEqual(row.User.email, "owner@example.com")
        response = await self.client.delete(f"/posts/{post_id}", headers=other)
        self.assertEqual(response.status_code, 403)
        response = await self.client.delete(f"/posts/{post_id}", headers=owner)
        self.assertEqual(response.status_code, 200)
        response = await self.client.delete(f"/posts/{post_id}", headers=owner)
        self.assertEqual(response.status_code, 404)
