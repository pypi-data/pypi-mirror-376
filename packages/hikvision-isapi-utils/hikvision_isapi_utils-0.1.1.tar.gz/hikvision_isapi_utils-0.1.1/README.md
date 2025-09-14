# hikvision-isapi-utils

一个用于与海康威视 (Hikvision) 设备进行通信的 Python 库，支持同步和异步操作。

## 重要提示 (Important Notice)

**本项目仅为技术交流与学习目的而创建。**

*   **API 文档来源**: 海康威视 ISAPI 协议文档是海康威视公司的专有财产。**所有开发者必须通过官方渠道 [海康开放平台](https://open.hikvision.com) 申请并获取正式的 API 文档。**
*   **法律风险**: 任何通过非官方渠道（例如网络搜索到的直接链接）获取和使用 ISAPI 文档的行为，均可能构成对海康威视知识产权的侵犯。使用此类非官方文档所产生的一切风险和责任，由使用者自行承担。
*   **项目免责**: 本项目作者及贡献者不提供任何官方支持，也不对因使用本库或非官方文档而导致的任何设备故障、数据丢失或法律纠纷负责。

## 安装

```bash
pip install hikvision-isapi-utils
```

## 快速开始

### 同步客户端

```python
from hikvision_isapi_utils import Client

# 创建客户端
client = Client(
    ip="192.168.1.64",
    username="admin",
    password="your_password",
    protocol="http"
)

# 发送请求
response = client._request("GET", "/ISAPI/System/capabilities")
print(response.text)

# 关闭客户端
client.close()
```

### 异步客户端

```python
import asyncio
from hikvision_isapi_utils import AsyncClient

async def main():
    async with AsyncClient(
        ip="192.168.1.64",
        username="admin",
        password="your_password",
        protocol="http"
    ) as client:
        response = await client._request("GET", "/ISAPI/System/capabilities")
        print(response.text)

# 运行异步函数
asyncio.run(main())
```

## 依赖

*   Python >= 3.8
*   `requests`
*   `httpx`

## 许可证

本项目采用 MIT 许可证。详情请见 `LICENSE` 文件。
