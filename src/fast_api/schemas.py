from pydantic import BaseModel
#专门放 Pydantic 数据模型 的文件
'''
客户端传来的 JSON
        ↓
Pydantic Schema
        ↓
类型校验 / 字段校验
        ↓
Python 对象
        ↓
业务逻辑

如果没有这个schemas.py,自己手动拿json数据,然后自己判断字段对不对

Request Schema
定义客户端 → 后端的数据格式

Response Schema
定义后端 → 客户端的数据格式
'''

#以下就是约束数据，当发现类型不对，并直接返回校验错误
class PostCreate(BaseModel):
    title:str
    content:str

class PostResponse(BaseModel):
    title:str
    content:str