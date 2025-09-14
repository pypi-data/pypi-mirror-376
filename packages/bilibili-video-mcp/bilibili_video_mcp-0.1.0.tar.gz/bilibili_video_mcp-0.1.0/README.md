# Bilibili Video MCP Server

一个用于从 Bilibili 视频中提取内容的 MCP (Model Context Protocol) 服务器。

## 功能特性

- 🎬 **视频下载**: 使用 you-get 下载 Bilibili 视频
- 📝 **字幕提取**: 智能提取和处理视频弹幕字幕
- 🎙️ **音频转文本**: 使用 ASR API 从音频中提取文案
- 🤖 **智能分析**: 使用大模型进行内容分析和总结
- 🔄 **自动清理**: 自动清理临时文件

## 安装

### 从 PyPI 安装

```bash
pip install bilibili-video-mcp
```

### 从源代码安装

```bash
git clone https://github.com/yzfly/bilibili-video-mcp.git
cd bilibili-video-mcp
pip install -e .
```

## 系统依赖

确保系统已安装以下依赖：

1. **FFmpeg**: 用于音频处理
   ```bash
   # macOS
   brew install ffmpeg
   
   # Ubuntu/Debian
   sudo apt update && sudo apt install ffmpeg
   
   # Windows
   # 下载 FFmpeg 并添加到 PATH
   ```

2. **you-get**: 用于下载 Bilibili 视频
   ```bash
   pip install you-get
   ```

## 配置

### 环境变量

设置以下环境变量：

- `AI_API_KEY`: SiliconFlow API 密钥（用于 ASR 和大模型调用）

### Claude Desktop 配置

在 Claude Desktop 的配置文件中添加：

```json
{
  "mcpServers": {
    "bilibili-video-mcp": {
      "command": "bilibili-video-mcp-server",
      "env": {
        "AI_API_KEY": "your-siliconflow-api-key-here"
      }
    }
  }
}
```

或者使用 uvx：

```json
{
  "mcpServers": {
    "bilibili-video-mcp": {
      "command": "uvx",
      "args": ["bilibili-video-mcp"],
      "env": {
        "AI_API_KEY": "your-siliconflow-api-key-here"
      }
    }
  }
}
```

## 获取 API 密钥

1. 访问 [SiliconFlow](https://cloud.siliconflow.cn/i/TxUlXG3u)
2. 注册账号并获取 API 密钥
3. 将密钥设置为环境变量 `AI_API_KEY`

## 使用方法

### 可用工具

1. **download_bilibili_video_info**
   - 下载视频并获取基本信息
   - 参数：`video_url` (Bilibili 视频链接)

2. **extract_bilibili_subtitles**
   - 提取并智能处理字幕内容
   - 参数：`video_url` (Bilibili 视频链接)

3. **extract_bilibili_audio_text**
   - 从音频提取文案
   - 参数：`video_url`，可选参数：`asr_api_base_url`，`asr_model`

4. **extract_bilibili_complete_content**
   - 完整内容提取和分析（推荐）
   - 参数：`video_url`，可选参数：`asr_api_base_url`，`asr_model`，`llm_model`

### 使用示例

```python
# 完整内容提取
result = extract_bilibili_complete_content("https://www.bilibili.com/video/BV1xx411c7mu")

# 仅提取字幕
subtitles = extract_bilibili_subtitles("https://www.bilibili.com/video/BV1xx411c7mu")

# 仅提取音频文案
audio_text = extract_bilibili_audio_text("https://www.bilibili.com/video/BV1xx411c7mu")
```

## 技术架构

- **FastMCP**: 基于 FastMCP 框架构建 MCP 服务器
- **you-get**: 下载 Bilibili 视频和字幕文件
- **FFmpeg**: 音频处理和格式转换
- **SiliconFlow API**: ASR 语音识别和大模型调用
- **OpenAI SDK**: 统一的大模型调用接口

## 支持的模型

### ASR 模型
- `FunAudioLLM/SenseVoiceSmall` (默认)

### 大语言模型
- `Qwen/Qwen3-8B` (默认，免费)
- `Qwen/QwQ-32B`
- 其他 SiliconFlow 支持的模型

## 开发

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 代码格式化

```bash
black src/
isort src/
```

### 运行测试

```bash
pytest
```

## 注意事项

1. **网络要求**: 需要能够访问 Bilibili 和 SiliconFlow API
2. **存储空间**: 下载视频需要临时存储空间，文件会自动清理
3. **API 配额**: ASR 和大模型调用会消耗 API 配额
4. **视频格式**: 支持大部分 Bilibili 视频格式
5. **字幕可用性**: 并非所有视频都有字幕文件

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 贡献

欢迎提交 Issue 和 Pull Request！

## 作者

- **yzfly** - [GitHub](https://github.com/yzfly)
- 邮箱: yz.liu.me@gmail.com