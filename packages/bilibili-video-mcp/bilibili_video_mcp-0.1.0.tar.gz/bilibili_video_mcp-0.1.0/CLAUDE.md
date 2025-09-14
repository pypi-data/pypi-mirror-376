制作一个 bilibili-video-mcp

我的 github 账号 yzfly， 邮箱 yz.liu.me@gmail.com

上下文文件：.context/fastmcp.txt


调用 python 的 youget 库支持下载 bilibili 的视频，提取字幕功能，调用 ASR api 提取视频文案。


src/server.py 是对抖音视频的处理，调用 ASR api 提取视频文案的代码供你参考

请你根据 src/server.py 中的代码，实现对 bilibili 视频的处理，调用 ASR api 提取视频文案。
其中，你需要实现以下功能：
1. 下载 bilibili 视频
2. 提取视频字幕 
3. 调用 ASR api 提取视频文案

使用OpenAI 接口调用大模型即可：

这是 request 代码，实际调用时候请使用 openai 的库调用吧，api key 是 AI_API_KEY,从这里获取 https://cloud.siliconflow.cn/i/TxUlXG3u ：
'''
 import requests

url = "https://api.siliconflow.cn/v1/chat/completions"

payload = {
    "model": "Qwen/QwQ-32B",
    "messages": [
        {
            "role": "user",
            "content": "What opportunities and challenges will the Chinese large model industry face in 2025?"
        }
    ]
}
headers = {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
'''

youget 命令行下载b站的视频有可能会带字幕文件 .cmt.xml ，可以直接调用  Qwen/Qwen3-8B  免费模型做处理和字幕翻译


冷白皮攻占娱乐圈，我很怀念黄种人的真实脸.mp4  冷白皮攻占娱乐圈，我很怀念黄种人的真实脸.cmt.xml

ASR的使用参考src/server.py 的 extract_text_from_audio 函数,教我怎么上传 pypi

默认使用Qwen/Qwen3-8B模型, 输入token 设置为最大16k, 同时帮我完成整个 mcp 项目的配置,实现完整的mcp server, mcp 的上下文在 .context/mcp.txt ,完成后协助我上传到 pypi