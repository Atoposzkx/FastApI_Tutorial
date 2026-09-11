'''
你当前项目实际发生的事情
运行：
uv run python -m fast_api.main
或者通过 Uvicorn 启动时：
1. Python 导入 fast_api.app。
2. 导入 db.py，创建 engine 和 Session 工厂。
3. 创建 FastAPI 对象。
4. Uvicorn 调用 lifespan。
5. create_db_and_tables() 根据 Base.metadata 创建 posts 表。
6. 执行到 yield，FastAPI 开始接收请求。
7. 接口通过数据库 Session 操作帖子，上传和删除需要登录。
8. 关闭服务器时，从 yield 后面继续执行。
'''
from fastapi import FastAPI,HTTPException,File,UploadFile,Form,Depends
from fast_api.schemas import UserCreate,UserRead,UserUpdate
from fast_api.db import User,Post,create_db_and_tables,get_async_session,engine
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from sqlalchemy import select
from uuid import UUID
from fast_api.images import imagekit

from fast_api.user import auth_backend,current_active_user,fastapi_users
'''
我们希望：

FastAPI 启动
     ↓
自动创建数据库表
     ↓
服务器开始接收请求

'''

#lifespan 管理整个 FastAPI 应用从启动到关闭的生命周期
@asynccontextmanager
async def lifespan(app:FastAPI):
    #启动阶段,await:等待数据库建表完成；等待期间允许事件循环处理其他异步任务。
    await create_db_and_tables()
    #启动阶段已经完成，现在把控制权交给 FastAPI；函数暂时不结束，等应用关闭后再回来。
    #它只是起一个作用：把“启动阶段”和“关闭阶段”分开
    yield
    #关闭阶段,dispose用于应用关闭时释放数据库连接资源。
    await imagekit.close()
    await engine.dispose()

#创建 FastAPI 应用，并告诉它：“这个应用的生命周期由 lifespan 函数负责。”
app = FastAPI(lifespan=lifespan)

#这几组自动生成路由挂到 app 上

#Fastapi Users自动生成的登录/登出接口(根据 auth_backend 生成认证相关接口)
app.include_router(fastapi_users.get_auth_router(auth_backend),prefix='/auth/jwt',tags=["auth"])
#自动生成注册接口,注册接口需要知道输入 Schema 和输出 Schema。
app.include_router(fastapi_users.get_register_router(UserRead,UserCreate),prefix="/auth",tags=["auth"])
#自动生成忘记密码 / 重置密码相关接口
app.include_router(fastapi_users.get_reset_password_router(),prefix="/auth",tags=["auth"])
#邮箱/账户验证相关接口。验证完成后要返回用户信息，
app.include_router(fastapi_users.get_verify_router(UserRead),prefix="/auth",tags=["auth"])
#这个负责：用户自己的资料接口。因此需要读取用户
#→ UserRead
#修改用户
#→ UserUpdate
app.include_router(fastapi_users.get_users_router(UserRead,UserUpdate),prefix="/users",tags=["users"])
'''
Request body：网页发送给 FastAPI 的数据。
Response body：FastAPI 通过 return 发送给网页的数据。(在下面的体现就是函数upload_life的返回值)
'''
@app.post("/upload")
async def upload_life(
    #...表示必填
    file:UploadFile=File(...),
    caption: str = Form(""),
    session:AsyncSession= Depends(get_async_session),
    # FastAPI 验证令牌后，将当前登录的用户对象传入这里。
    current_user: User = Depends(current_active_user),

):
    # content_type 是上传文件的 MIME 类型，例如：
    # image/jpeg、image/png、video/mp4

    content_type = file.content_type or ""
     ## 把各种具体格式统一分类成 image 或 video
    if content_type.startswith("video/"):
        file_type = "video"
    elif content_type.startswith("image/"):
        file_type = "image"
    else:
        raise HTTPException(
            status_code=400,
            detail="Only image and video files are allowed",
        )

    file_bytes = await file.read()
    upload_result = await imagekit.files.upload(
        file=file_bytes,
        file_name=file.filename or "upload",
    )

    if not upload_result.url: 
        raise HTTPException(status_code=502, detail="ImageKit upload failed")

    post = Post(
        # 作者必须来自登录身份，不能由客户端随意指定。
        user_id=current_user.id,
        caption = caption,
        url = upload_result.url,
        file_type=file_type,
        file_name=upload_result.name or file.filename or "upload",
    )
    session.add(post)
    await session.commit()
    # commit 负责把新增记录提交到数据库；refresh 会再按主键从数据库读取这条记录，
    # 确保 post 拿到数据库中的最终值（例如自动生成的 id 和 created_at），方便完整返回。refresh 并非每次都绝对必要，但当你需要立即返回数据库生成或处理后的完整数据时，显式刷新更稳妥。
    await session.refresh(post)
    return post


@app.get("/feed")
async def get_feed(
    session:AsyncSession=Depends(get_async_session)
):
    #按照时间倒序排列，SQLAlchemy 的查询结果对象。
    #图书管理员帮你把符合条件的书都找出来，放到推车里。
    result = await session.execute(select(Post).order_by(Post.created_at.desc()))
    #scalars() 会直接从查询结果中提取 Post 对象
    #你把推车里的书一本一本取出来，放进自己的书单列表。
    #scalars = 取对象，all = 全部拿出来
    posts = result.scalars().all()
    #posts = [row[0] for row in result.all()]
    posts_data = []

    for post in posts:
        posts_data.append(
            {
                "id":str(post.id),
                "caption":post.caption,
                "url":post.url,
                "file_type":post.file_type,
                "file_name":post.file_name,
                "created_at":post.created_at.isoformat()

            }
        )

    return {"posts":posts_data}




@app.delete("/posts/{post_id}")
async def delete_post(
    post_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    # id 是主键，所以直接使用 session.get() 查询；找不到时返回 None。
    post = await session.get(Post, post_id)

    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    # 登录只证明“你是谁”；这里继续检查“你是否有权删除”。
    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own posts")

    await session.delete(post)
    await session.commit()

    return {"success": True, "message": "Post deleted successfully"}
















'''
text_posts = {
    1: {"title": "New Post", "content": "Cool test post"},
    2: {"title": "Python Tip", "content": "Use list comprehensions for cleaner loops."},
    3: {"title": "Daily Motivation", "content": "Consistency beats intensity every time."},
    4: {"title": "Fun Fact", "content": "The first computer bug was an actual moth found in a Harvard Mark II."},
    5: {"title": "Update", "content": "Just launched my new project! Excited to share more soon."},
    6: {"title": "Tech Insight", "content": "Async IO in Python can massively speed up I/O-bound tasks."},
    7: {"title": "Quote", "content": "Programs must be written for people to read, and only incidentally for machines to execute."},
    8: {"title": "Weekend Plans", "content": "Might finally clean up my GitHub repos... or just play some Minecraft."},
    9: {"title": "Question", "content": "What's the most underrated Python library you've ever used?"},
    10: {"title": "Mini Announcement", "content": "New video drops tomorrow—covering the weirdest Python features!"},
}
'''

'''
request(请求):Method(操作),Path(路径)，Body(真正内容)，Headers(身份认证)

response(响应):Status Code,Body,Headers

这里的「操作」指的是一种 HTTP「方法」
POST：创建数据。
GET：读取数据。
PUT：更新数据。
DELETE：删除数据。
'''

''''
@app.get("/posts")
def get_all_posts(limit:int | None = None):
    if limit:
        return list(text_posts.values())[:limit]
    return text_posts


@app.get("/posts/{id}")
def get_post(id:int)->PostResponse:
    if id not in text_posts:
        raise HTTPException(status_code=404,detail="Post not found")

    return text_posts.get(id)


如果希望新增数据在重启后仍然存在，就需要使用 SQLite、MySQL 等数据库，而不能只使用 text_posts 这个内存字典。

@app.post("/posts")
def create_post(post:PostCreate)->PostResponse:
    new_post = {"title":post.title,"content":post.content}
    text_posts[max(text_posts.keys())+1] = new_post
    #return不是再次添加数据，而是告诉客户端创建的结果
    return new_post

'''
