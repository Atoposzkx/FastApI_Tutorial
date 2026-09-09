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
7. 当前接口仍然在操作 text_posts 内存字典，还没有真正使用数据库。
8. 关闭服务器时，从 yield 后面继续执行。
'''
from fastapi import FastAPI,HTTPException,File,UploadFile,Form,Depends
from fast_api.schemas import PostCreate,PostResponse
from fast_api.db import Post,create_db_and_tables,get_async_session,engine
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
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
    await engine.dispose()

#创建 FastAPI 应用，并告诉它：“这个应用的生命周期由 lifespan 函数负责。”
app = FastAPI(lifespan=lifespan)

@app.post("/upload")
async def upload_life(
    file:UploadFile=File(...),
    caption: str = Form(""),
    session:AsyncSession= Depends(get_async_session)

):
    pass

















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