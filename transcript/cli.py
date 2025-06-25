#!/usr/bin/env python3
"""
Transcript CLI - 使用Fire的简洁命令行接口

Fire让命令行接口变得非常直观和强大！
"""

import os
import sys
from pathlib import Path
from typing import Optional
import fire


def setup_huggingface_env():
    """设置Hugging Face环境变量"""
    # 设置HF_HOME（缓存目录）
    if 'HF_HOME' not in os.environ:
        default_hf_home = Path.home() / ".cache" / "huggingface"
        os.environ['HF_HOME'] = str(default_hf_home)

    # 设置HF_ENDPOINT（镜像端点）
    if 'HF_ENDPOINT' in os.environ:
        # 设置huggingface_hub使用的环境变量
        os.environ['HUGGINGFACE_HUB_DEFAULT_ENDPOINT'] = os.environ['HF_ENDPOINT']

    # 设置相关的缓存环境变量
    hf_home = Path(os.environ['HF_HOME'])
    os.environ['HUGGINGFACE_HUB_CACHE'] = str(hf_home / "hub")
    os.environ['TRANSFORMERS_CACHE'] = str(hf_home / "transformers")

    # 创建缓存目录
    hf_home.mkdir(parents=True, exist_ok=True)
    (hf_home / "hub").mkdir(parents=True, exist_ok=True)
    (hf_home / "transformers").mkdir(parents=True, exist_ok=True)


# 在模块加载时设置环境
setup_huggingface_env()


class TranscriptCLI:
    """
    Transcript 视频字幕处理工具

    使用Fire提供简洁直观的命令行接口。

    示例:
        transcript auto video.mp4                    # 自动处理（无需手动编辑）
        transcript gen video.mp4                     # 生成字幕
        transcript resume                            # 编辑字幕后继续处理
        transcript status                            # 查看状态

        # 带参数的例子
        transcript auto video.mp4 --output /path/to/output
        transcript gen video.mp4 --output /path/to/output
        transcript resume --opening opening.mp4 --ending ending.mp4
    """


    def _print_banner(self):
        """打印欢迎横幅"""
        print("=" * 60)
        print("🎬 Transcript - 视频字幕处理工具")
        print("=" * 60)

    def _validate_media_file(self, file_path: str) -> Path:
        """验证视频或音频文件"""
        media_file = Path(file_path)
        if not media_file.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'}
        audio_extensions = {'.wav', '.mp3', '.m4a', '.flac', '.aac', '.ogg', '.wma'}
        valid_extensions = video_extensions | audio_extensions

        if media_file.suffix.lower() not in valid_extensions:
            raise ValueError(f"不支持的文件格式: {media_file.suffix}。支持的格式：视频({', '.join(video_extensions)})，音频({', '.join(audio_extensions)})")

        return media_file


    def auto(self, video: str, output: Optional[str] = None, opening: Optional[str] = None, ending: Optional[str] = None):
        """
        自动处理流程（无需手动编辑字幕）

        Args:
            video: 输入视频或音频文件路径
            output: 输出目录
            opening: 片头视频路径（仅视频文件支持）
            ending: 片尾视频路径（仅视频文件支持）
        """
        try:
            # 延迟导入
            from .transcript import auto

            self._print_banner()
            print(f"ℹ️  开始自动处理流程: {video}")
            print("ℹ️  自动处理模式 - 将跳过手动编辑步骤")

            media_file = self._validate_media_file(video)

            final_with_sub, final_no_sub, final_srt = auto(
                str(media_file),
                output_path=output,
                opening_video=opening,
                ending_video=ending
            )

            print("✅ 处理完成!")
            if final_no_sub:  # 视频文件
                print(f"ℹ️  带字幕视频: {final_with_sub}")
                print(f"ℹ️  无字幕视频: {final_no_sub}")
            else:  # 音频文件
                print(f"ℹ️  剪辑音频: {final_with_sub}")
            print(f"ℹ️  字幕文件: {final_srt}")

        except Exception as e:
            print(f"❌ 处理失败: {e}")
            sys.exit(1)


    def gen(self, video: str, output: Optional[str] = None):
        """
        生成字幕文件

        Args:
            video: 输入视频或音频文件路径
            output: 输出目录（默认：项目根目录）
        """
        try:
            from .transcript import transcript

            self._print_banner()
            print(f"ℹ️  开始生成转录文件: {video}")
            print("ℹ️  🎭 自动启用说话人分离功能")

            media_file = self._validate_media_file(video)
            output_dir = Path(output) if output else None

            # 现在transcript函数返回两个文件，自动启用说话人分离
            srt_file, speaker_txt = transcript(media_file, output_dir, enable_diarization=True)

            print("✅ 转录文件生成完成!")
            print(f"ℹ️  SRT字幕文件（无说话人标识）: {srt_file}")
            print(f"ℹ️  文本文件（含说话人标识）: {speaker_txt}")
            print("ℹ️  ✨ 已自动生成两个版本的转录文件")
            print("ℹ️  下一步: 编辑SRT字幕文件，然后运行 'transcript resume' 继续处理")

        except Exception as e:
            print(f"❌ 生成转录文件失败: {e}")
            sys.exit(1)


    def resume(self, output: Optional[str] = None, opening: Optional[str] = None, ending: Optional[str] = None):
        """
        编辑字幕后继续处理（自动调用align）

        Args:
            output: 输出目录
            opening: 片头视频路径
            ending: 片尾视频路径
        """
        try:
            # 延迟导入
            from .transcript import resume

            self._print_banner()

            final_with_sub, final_no_sub, final_srt = resume(
                output_path=output,
                opening_video=opening,
                ending_video=ending
            )

            print("✅ 处理完成!")
            if final_no_sub:  # 视频文件
                print(f"ℹ️  带字幕视频: {final_with_sub}")
                print(f"ℹ️  无字幕视频: {final_no_sub}")
            else:  # 音频文件
                print(f"ℹ️  剪辑音频: {final_with_sub}")
            print(f"ℹ️  字幕文件: {final_srt}")

        except Exception as e:
            print(f"❌ 处理失败: {e}")
            sys.exit(1)


    def status(self):
        """查看当前处理状态"""
        try:
            self._print_banner()
            print("ℹ️  查看处理状态...")

            # 查找最近的工作目录
            tmp_dir = Path("/tmp/transcript")
            if tmp_dir.exists():
                log_files = list(tmp_dir.glob("*/.log"))
                if log_files:
                    latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
                    print(f"ℹ️  最近的工作目录: {latest_log.parent}")

                    import json
                    with open(latest_log, 'r', encoding='utf-8') as f:
                        log_data = json.load(f)
                        print(f"ℹ️  项目名称: {log_data.get('name', 'N/A')}")
                        # 兼容新旧日志格式
                        if 'raw_file' in log_data:
                            file_type = log_data.get('file_type', 'unknown')
                            print(f"ℹ️  原始文件: {log_data.get('raw_file', 'N/A')} ({file_type})")
                        else:
                            print(f"ℹ️  原始视频: {log_data.get('raw_video', 'N/A')}")
                        print(f"ℹ️  创建时间: {log_data.get('timestamp', 'N/A')}")
                else:
                    print("ℹ️  没有找到活动的处理任务")
            else:
                print("ℹ️  没有找到工作目录")

        except Exception as e:
            print(f"❌ 查看状态失败: {e}")
            sys.exit(1)


def main():
    """主入口函数 - 使用Fire启动CLI"""
    fire.Fire(TranscriptCLI)


if __name__ == '__main__':
    main()
