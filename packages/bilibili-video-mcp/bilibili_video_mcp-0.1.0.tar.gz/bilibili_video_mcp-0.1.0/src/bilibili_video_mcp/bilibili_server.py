#!/usr/bin/env python3
"""
Bilibili 视频下载并提取文本的 MCP 服务器

该服务器提供以下功能：
1. 使用 you-get 下载 bilibili 视频
2. 提取视频字幕（.cmt.xml 文件）
3. 调用 ASR API 提取视频文案
4. 使用大模型处理和翻译字幕
"""

import os
import re
import json
import requests
import tempfile
import asyncio
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import ffmpeg
from tqdm.asyncio import tqdm
import openai

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp import Context


# 创建 MCP 服务器实例
mcp = FastMCP("Bilibili MCP Server", 
              dependencies=["you-get", "requests", "ffmpeg-python", "tqdm", "openai"])

# 默认 API 配置
DEFAULT_ASR_API_BASE_URL = "https://api.siliconflow.cn/v1/audio/transcriptions"
DEFAULT_ASR_MODEL = "FunAudioLLM/SenseVoiceSmall"
DEFAULT_LLM_API_BASE_URL = "https://api.siliconflow.cn/v1"
DEFAULT_LLM_MODEL = "Qwen/Qwen3-8B"


class BilibiliProcessor:
    """Bilibili 视频处理器"""
    
    def __init__(self, ai_api_key: str, asr_api_base_url: Optional[str] = None, 
                 asr_model: Optional[str] = None, llm_api_base_url: Optional[str] = None,
                 llm_model: Optional[str] = None):
        self.ai_api_key = ai_api_key
        self.asr_api_base_url = asr_api_base_url or DEFAULT_ASR_API_BASE_URL
        self.asr_model = asr_model or DEFAULT_ASR_MODEL
        self.llm_api_base_url = llm_api_base_url or DEFAULT_LLM_API_BASE_URL
        self.llm_model = llm_model or DEFAULT_LLM_MODEL
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # 初始化 OpenAI 客户端
        self.openai_client = openai.OpenAI(
            api_key=self.ai_api_key,
            base_url=self.llm_api_base_url
        )
    
    def __del__(self):
        """清理临时目录"""
        import shutil
        if hasattr(self, 'temp_dir') and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    async def download_bilibili_video(self, video_url: str, ctx: Context) -> Dict[str, Path]:
        """使用 you-get 下载 bilibili 视频"""
        ctx.info(f"正在下载 bilibili 视频: {video_url}")
        
        # 构建 you-get 命令
        cmd = [
            "you-get",
            "--output-dir", str(self.temp_dir),
            "--output-filename", "video",
            video_url
        ]
        
        try:
            # 执行下载命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.temp_dir)
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"you-get 下载失败: {stderr.decode('utf-8')}")
            
            ctx.info("视频下载完成")
            
            # 查找下载的文件
            downloaded_files = {}
            for file_path in self.temp_dir.glob("*"):
                if file_path.is_file():
                    if file_path.suffix == '.mp4':
                        downloaded_files['video'] = file_path
                    elif file_path.suffix == '.xml' and '.cmt.' in file_path.name:
                        downloaded_files['subtitle'] = file_path
            
            if 'video' not in downloaded_files:
                raise Exception("未找到下载的视频文件")
            
            return downloaded_files
            
        except Exception as e:
            raise Exception(f"下载 bilibili 视频失败: {str(e)}")
    
    def extract_subtitles_from_xml(self, xml_path: Path) -> str:
        """从 .cmt.xml 文件中提取字幕内容"""
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # 提取所有弹幕内容
            comments = []
            for d in root.findall('d'):
                if d.text:
                    comments.append(d.text.strip())
            
            # 去重并合并
            unique_comments = list(dict.fromkeys(comments))  # 保持顺序去重
            return '\n'.join(unique_comments)
            
        except Exception as e:
            raise Exception(f"解析字幕文件失败: {str(e)}")
    
    async def process_subtitles_with_llm(self, subtitle_text: str, ctx: Context) -> str:
        """使用大模型处理和翻译字幕"""
        if not subtitle_text.strip():
            return "未找到字幕内容"
        
        ctx.info("正在使用大模型处理字幕内容...")
        
        prompt = f"""请对以下弹幕内容进行处理和总结：

弹幕内容：
{subtitle_text}

请完成以下任务：
1. 过滤掉无意义的弹幕（如单纯的表情符号、重复内容等）
2. 总结视频的主要内容和观众的反应
3. 如果有英文内容，请翻译成中文
4. 整理成结构化的文本

请用中文回答，格式要清晰易读。"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=16000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"大模型处理字幕失败: {str(e)}")
    
    def extract_audio(self, video_path: Path) -> Path:
        """从视频文件中提取音频"""
        audio_path = video_path.with_suffix('.mp3')
        
        try:
            (
                ffmpeg
                .input(str(video_path))
                .output(str(audio_path), acodec='libmp3lame', q=0)
                .run(capture_stdout=True, capture_stderr=True, overwrite_output=True)
            )
            return audio_path
        except Exception as e:
            raise Exception(f"提取音频时出错: {str(e)}")
    
    def extract_text_from_audio(self, audio_path: Path) -> str:
        """从音频文件中提取文字"""
        files = {
            'file': (audio_path.name, open(audio_path, 'rb'), 'audio/mpeg'),
            'model': (None, self.asr_model)
        }
        
        headers = {
            "Authorization": f"Bearer {self.ai_api_key}"
        }
        
        try:
            response = requests.post(self.asr_api_base_url, files=files, headers=headers)
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            if 'text' in result:
                return result['text']
            else:
                return response.text
                
        except Exception as e:
            raise Exception(f"提取文字时出错: {str(e)}")
        finally:
            files['file'][1].close()
    
    def cleanup_files(self, *file_paths: Path):
        """清理指定的文件"""
        for file_path in file_paths:
            if file_path.exists():
                file_path.unlink()


@mcp.tool()
async def download_bilibili_video_info(video_url: str, ctx: Context = None) -> str:
    """
    下载 bilibili 视频并获取基本信息
    
    参数:
    - video_url: bilibili 视频链接
    
    返回:
    - 包含下载信息的JSON字符串
    """
    try:
        # 从环境变量获取API密钥
        ai_api_key = os.getenv('AI_API_KEY')
        if not ai_api_key:
            raise ValueError("未设置环境变量 AI_API_KEY，请在配置中添加 API 密钥")
        
        processor = BilibiliProcessor(ai_api_key)
        
        # 下载视频
        ctx.info("正在下载 bilibili 视频...")
        downloaded_files = await processor.download_bilibili_video(video_url, ctx)
        
        result = {
            "status": "success",
            "video_path": str(downloaded_files['video']),
            "has_subtitles": 'subtitle' in downloaded_files,
            "subtitle_path": str(downloaded_files.get('subtitle', '')),
            "message": "视频下载完成"
        }
        
        if 'subtitle' in downloaded_files:
            result["message"] += "，包含字幕文件"
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": f"下载视频失败: {str(e)}"
        }, ensure_ascii=False, indent=2)


@mcp.tool()
async def extract_bilibili_subtitles(video_url: str, ctx: Context = None) -> str:
    """
    提取 bilibili 视频的字幕内容并进行智能处理
    
    参数:
    - video_url: bilibili 视频链接
    
    返回:
    - 处理后的字幕内容
    """
    try:
        # 从环境变量获取API密钥
        ai_api_key = os.getenv('AI_API_KEY')
        if not ai_api_key:
            raise ValueError("未设置环境变量 AI_API_KEY，请在配置中添加 API 密钥")
        
        processor = BilibiliProcessor(ai_api_key)
        
        # 下载视频
        ctx.info("正在下载 bilibili 视频...")
        downloaded_files = await processor.download_bilibili_video(video_url, ctx)
        
        if 'subtitle' not in downloaded_files:
            return json.dumps({
                "status": "no_subtitles",
                "message": "该视频没有字幕文件，建议使用 ASR 功能提取音频文案"
            }, ensure_ascii=False, indent=2)
        
        # 提取字幕
        ctx.info("正在提取字幕内容...")
        subtitle_text = processor.extract_subtitles_from_xml(downloaded_files['subtitle'])
        
        # 使用大模型处理字幕
        processed_text = await processor.process_subtitles_with_llm(subtitle_text, ctx)
        
        # 清理文件
        processor.cleanup_files(*downloaded_files.values())
        
        return json.dumps({
            "status": "success",
            "processed_subtitles": processed_text,
            "raw_subtitles_count": len(subtitle_text.split('\n')),
            "message": "字幕提取和处理完成"
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": f"提取字幕失败: {str(e)}"
        }, ensure_ascii=False, indent=2)


@mcp.tool()
async def extract_bilibili_audio_text(
    video_url: str,
    asr_api_base_url: Optional[str] = None,
    asr_model: Optional[str] = None,
    ctx: Context = None
) -> str:
    """
    从 bilibili 视频中提取音频并转换为文本
    
    参数:
    - video_url: bilibili 视频链接
    - asr_api_base_url: ASR API基础URL（可选）
    - asr_model: ASR模型（可选）
    
    返回:
    - 音频转文本的结果
    """
    try:
        # 从环境变量获取API密钥
        ai_api_key = os.getenv('AI_API_KEY')
        if not ai_api_key:
            raise ValueError("未设置环境变量 AI_API_KEY，请在配置中添加 API 密钥")
        
        processor = BilibiliProcessor(ai_api_key, asr_api_base_url, asr_model)
        
        # 下载视频
        ctx.info("正在下载 bilibili 视频...")
        downloaded_files = await processor.download_bilibili_video(video_url, ctx)
        
        # 提取音频
        ctx.info("正在提取音频...")
        audio_path = processor.extract_audio(downloaded_files['video'])
        
        # ASR 转文本
        ctx.info("正在从音频中提取文本...")
        text_content = processor.extract_text_from_audio(audio_path)
        
        # 清理临时文件
        ctx.info("正在清理临时文件...")
        processor.cleanup_files(*downloaded_files.values(), audio_path)
        
        ctx.info("音频文本提取完成!")
        return json.dumps({
            "status": "success",
            "audio_text": text_content,
            "message": "音频文本提取完成"
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": f"音频文本提取失败: {str(e)}"
        }, ensure_ascii=False, indent=2)


@mcp.tool()
async def extract_bilibili_complete_content(
    video_url: str,
    asr_api_base_url: Optional[str] = None,
    asr_model: Optional[str] = None,
    llm_model: Optional[str] = None,
    ctx: Context = None
) -> str:
    """
    完整提取 bilibili 视频内容（字幕 + 音频文案）
    
    参数:
    - video_url: bilibili 视频链接
    - asr_api_base_url: ASR API基础URL（可选）
    - asr_model: ASR模型（可选）
    - llm_model: 大模型名称（可选）
    
    返回:
    - 完整的视频内容分析
    """
    try:
        # 从环境变量获取API密钥
        ai_api_key = os.getenv('AI_API_KEY')
        if not ai_api_key:
            raise ValueError("未设置环境变量 AI_API_KEY，请在配置中添加 API 密钥")
        
        processor = BilibiliProcessor(ai_api_key, asr_api_base_url, asr_model, 
                                    llm_model=llm_model)
        
        # 下载视频
        ctx.info("正在下载 bilibili 视频...")
        downloaded_files = await processor.download_bilibili_video(video_url, ctx)
        
        result = {
            "status": "success",
            "video_url": video_url,
            "subtitles": None,
            "audio_text": None,
            "combined_analysis": None
        }
        
        # 尝试提取字幕
        if 'subtitle' in downloaded_files:
            ctx.info("正在处理字幕内容...")
            try:
                subtitle_text = processor.extract_subtitles_from_xml(downloaded_files['subtitle'])
                processed_subtitles = await processor.process_subtitles_with_llm(subtitle_text, ctx)
                result["subtitles"] = processed_subtitles
            except Exception as e:
                ctx.error(f"字幕处理失败: {str(e)}")
        
        # 提取音频文案
        ctx.info("正在提取音频文案...")
        try:
            audio_path = processor.extract_audio(downloaded_files['video'])
            audio_text = processor.extract_text_from_audio(audio_path)
            result["audio_text"] = audio_text
        except Exception as e:
            ctx.error(f"音频文案提取失败: {str(e)}")
        
        # 综合分析
        if result["subtitles"] or result["audio_text"]:
            ctx.info("正在进行综合内容分析...")
            analysis_content = ""
            if result["subtitles"]:
                analysis_content += f"字幕内容分析：\n{result['subtitles']}\n\n"
            if result["audio_text"]:
                analysis_content += f"音频文案：\n{result['audio_text']}"
            
            # 使用大模型进行综合分析
            combined_prompt = f"""请对以下bilibili视频内容进行综合分析和总结：

{analysis_content}

请提供：
1. 视频主要内容概述
2. 关键信息提取
3. 内容特点分析
4. 如果内容涉及教程或知识分享，请总结要点

请用中文回答，格式清晰。"""
            
            try:
                response = processor.openai_client.chat.completions.create(
                    model=processor.llm_model,
                    messages=[
                        {"role": "user", "content": combined_prompt}
                    ],
                    max_tokens=16000
                )
                result["combined_analysis"] = response.choices[0].message.content
            except Exception as e:
                ctx.error(f"综合分析失败: {str(e)}")
        
        # 清理临时文件
        ctx.info("正在清理临时文件...")
        processor.cleanup_files(*downloaded_files.values())
        if 'audio_path' in locals():
            processor.cleanup_files(audio_path)
        
        ctx.info("bilibili 视频内容提取完成!")
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": f"完整内容提取失败: {str(e)}"
        }, ensure_ascii=False, indent=2)


@mcp.resource("bilibili://video/{video_url}")
def get_bilibili_video_resource(video_url: str) -> str:
    """
    获取指定 bilibili 视频的资源信息
    
    参数:
    - video_url: bilibili 视频链接
    
    返回:
    - 视频资源信息
    """
    return f"""# Bilibili 视频资源

视频链接: {video_url}

可用操作：
- 下载视频和字幕文件
- 提取并处理字幕内容  
- 从音频提取文案
- 综合内容分析

使用工具进行具体操作。"""


@mcp.prompt()
def bilibili_video_extraction_guide() -> str:
    """bilibili 视频内容提取使用指南"""
    return """
# Bilibili 视频内容提取使用指南

## 功能说明
这个MCP服务器可以从 bilibili 视频中提取多种内容：
1. 使用 you-get 下载视频和字幕文件
2. 智能处理和分析字幕内容（弹幕）
3. 从音频提取文案（ASR）
4. 综合内容分析和总结

## 环境变量配置
请确保设置了以下环境变量：
- `AI_API_KEY`: SiliconFlow API密钥（用于ASR和大模型调用）

## 工具说明
- `download_bilibili_video_info`: 下载视频并获取基本信息
- `extract_bilibili_subtitles`: 提取并智能处理字幕内容
- `extract_bilibili_audio_text`: 从音频提取文案
- `extract_bilibili_complete_content`: 完整内容提取和分析
- `bilibili://video/{video_url}`: 获取视频资源信息

## Claude Desktop 配置示例
```json
{
  "mcpServers": {
    "bilibili-mcp": {
      "command": "uvx",
      "args": ["bilibili-video-mcp-server"],
      "env": {
        "AI_API_KEY": "your-siliconflow-api-key-here"
      }
    }
  }
}
```

## 使用示例
1. 完整内容提取：`extract_bilibili_complete_content("https://www.bilibili.com/video/BV1xx411c7mu")`
2. 仅提取字幕：`extract_bilibili_subtitles("https://www.bilibili.com/video/BV1xx411c7mu")`
3. 仅提取音频文案：`extract_bilibili_audio_text("https://www.bilibili.com/video/BV1xx411c7mu")`

## 注意事项
- 需要安装 you-get: `pip install you-get`
- 需要 ffmpeg 用于音频处理
- 字幕文件(.cmt.xml)不是所有视频都有
- 音频转文本需要消耗 API 配额
- 中间文件会自动清理
"""


def main():
    """启动MCP服务器"""
    mcp.run()


if __name__ == "__main__":
    main()