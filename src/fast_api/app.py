from fastapi import FastAPI,HTTPException
from fast_api.schemas import PostCreate,PostResponse

app = FastAPI()

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
request(请求):Method(操作),Path(路径)，Body(真正内容)，Headers(身份认证)

response(响应):Status Code,Body,Headers

这里的「操作」指的是一种 HTTP「方法」
POST：创建数据。
GET：读取数据。
PUT：更新数据。
DELETE：删除数据。
'''


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

'''
果希望新增数据在重启后仍然存在，就需要使用 SQLite、MySQL 等数据库，而不能只使用 text_posts 这个内存字典。
'''
@app.post("/posts")
def create_post(post:PostCreate)->PostResponse:
    new_post = {"title":post.title,"content":post.content}
    text_posts[max(text_posts.keys())+1] = new_post
    #return不是再次添加数据，而是告诉客户端创建的结果
    return new_post
