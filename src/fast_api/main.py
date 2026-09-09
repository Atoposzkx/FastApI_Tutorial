import uvicorn

#Uvicorn 是一个基于 ASGI（异步服务器网关接口）标准的、极速的 Python 异步 Web 服务器
if __name__ == "__main__":
    uvicorn.run("fast_api.app:app",host="0.0.0.0",port=8000,reload=True)

