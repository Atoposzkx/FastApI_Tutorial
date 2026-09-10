import os

from dotenv import load_dotenv
from imagekitio import AsyncImageKit


load_dotenv()


# ImageKit 5.x 的服务端客户端只需要私钥。
# 第二个变量名用于兼容当前 .env 中原来的 IMAGEKI_PRIVATE_KEY 写法。
imagekit = AsyncImageKit(
    private_key=(
        os.getenv("IMAGEKIT_PRIVATE_KEY")
    ),
)
URL_ENDPOINT = (
    os.getenv("IMAGEKIT_URL_ENDPOINT")
    or os.getenv("IMAGEKIT_URL")
)
