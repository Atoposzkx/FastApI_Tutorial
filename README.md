# FastAPI 图片与视频分享项目

一个用于学习 FastAPI 的全栈练习项目：使用 Streamlit 展示界面，FastAPI 提供接口，SQLite 保存用户和帖子信息，ImageKit 保存图片与视频。

## 已实现功能

- 用户注册、登录和 JWT 身份认证。
- 登录后上传图片或视频，并填写文字说明。
- 按发布时间倒序展示帖子和作者邮箱。
- 只向作者显示删除按钮，后端同时校验删除权限。
- 数据保存在本地 SQLite 数据库，重启后仍然存在。

## 技术与目录

Python 3.12+、FastAPI、FastAPI Users、异步 SQLAlchemy / aiosqlite、ImageKit Python SDK 5.x、Streamlit，以及 uv。

```text
frontend.py                 # Streamlit 界面，通过 HTTP 调用后端
src/fast_api/
    main.py                 # Uvicorn 启动入口
    app.py                  # 应用生命周期、认证路由和帖子接口
    db.py                   # 数据库模型、连接和 Session 依赖
    user.py                 # 用户管理器、JWT 策略和当前用户依赖
    schemas.py              # 请求、响应的数据模型
    images.py               # ImageKit 客户端配置
tests/test_auth_posts.py    # 认证、作者关联、帖子列表和删除权限测试
pyproject.toml              # 项目依赖
uv.lock                    # 锁定依赖版本
```

## 本地运行

先安装 [uv](https://docs.astral.sh/uv/getting-started/installation/)，然后在项目根目录运行：

```bash
uv sync
```

在项目根目录创建 `.env`，填写自己的配置：

```dotenv
AUTH_SECRET=替换为自己生成的随机密钥
IMAGEKIT_PRIVATE_KEY=替换为自己的ImageKit私钥
# 可选：ImageKit URL endpoint；上传接口直接使用 ImageKit 返回的 URL。
IMAGEKIT_URL_ENDPOINT=https://ik.imagekit.io/你的账号标识
```

使用 `openssl rand -hex 32` 生成 `AUTH_SECRET`，生成后保存，不要每次启动都更换。ImageKit 私钥从自己的 ImageKit 控制台获取。不要提交 `.env` 或分享密钥。

在两个终端分别启动后端和前端：

```bash
# 终端一：后端（开发模式，自动重载）
uv run python -m fast_api.main
```

```bash
# 终端二：前端
uv run streamlit run frontend.py
```

- 前端：http://localhost:8501
- 接口文档：http://localhost:8000/docs
- 前端默认请求 `http://localhost:8000`，更改后端地址时需同步修改前端。

首次启动会自动创建根目录下的 `.test.db`。`create_all()` 只创建缺失的表，不会迁移已有表结构；后续修改模型时需要数据库迁移。

## 验证流程

1. 在前端填写邮箱和密码，点击 **Sign Up** 注册，再点击 **Login** 登录。
2. 在 **Upload** 页面选择图片或视频，填写说明并点击 **Share**。
3. 切换到 **Feed**，检查媒体、作者和发布时间。
4. 使用第二个账号登录，确认能看到帖子，但没有删除按钮。
5. 切回作者账号，删除帖子并确认列表更新。

登录返回的 JWT 通过 `Authorization: Bearer <token>` 请求头发送。上传时作者 ID 来自当前登录用户；删除时后端比较作者 ID 与当前用户 ID，越权请求返回 `403`。

## 主要接口

| 方法与路径 | 用途 |
| --- | --- |
| `POST /auth/register` | 注册，提交 JSON 邮箱和密码 |
| `POST /auth/jwt/login` | 登录，提交表单 `username`（填写邮箱）和 `password` |
| `GET /users/me` | 获取当前登录用户 |
| `POST /upload` | 登录后提交 multipart 文件 `file` 和文字 `caption` |
| `GET /feed` | 登录后获取帖子列表，包含 `email` 和 `is_owner` |
| `DELETE /posts/{post_id}` | 作者删除自己的帖子 |

其余用户管理、密码重置和邮箱验证接口见 `/docs`。

## 自动测试

完成上述环境配置后执行：

```bash
uv run python -m unittest discover -s tests -v
```

测试使用独立内存数据库并模拟 ImageKit 上传，不修改本地数据或上传真实文件。覆盖注册登录、匿名请求拒绝、作者外键关联、列表所有权字段、越权删除和重复删除。测试加载应用时仍需要环境配置，请使用测试配置，不使用生产密钥。

## 当前限制

- 邮箱验证和密码重置接口已注册，但邮件发送尚未实现；当前不要求邮箱验证后才能发帖。
- JWT 有效期为一小时。前端退出会清除本地会话中的令牌，不会立即撤销已签发的 JWT。
- 删除帖子仅删除数据库记录，不会删除 ImageKit 中的文件。
- 文件分类依赖客户端 MIME 类型，尚未实现严格内容检测、应用层文件大小限制和上传失败补偿。
- 当前用于学习和本地演示，未配置生产部署、数据库迁移或完善的网络错误处理。

## 教程来源

参考 Tech With Tim 的 [Learn Fast API With This ONE Project](https://www.youtube.com/watch?v=SR5NYCdzKkc)。前端来自作者的 [FastAPIPhotoVideoSharing](https://github.com/techwithtim/FastAPIPhotoVideoSharing) 仓库，后端已适配当前项目结构和 ImageKit 5.x SDK。
