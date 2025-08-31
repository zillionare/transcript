#!/usr/bin/env python3
"""
Transcript CLI - 简化的命令行接口

提供更友好的命令行体验，简化视频字幕处理操作。
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional


def setup_huggingface_env():
    """设置Hugging Face环境变量"""
    # 设置HF_HOME（缓存目录）
    # 优先使用环境变量，但如果指向原来的共享目录，则改用本地目录
    env_hf_home = os.environ.get('HF_HOME')
    if env_hf_home and not env_hf_home.startswith("/Volumes/share/data"):
        # 如果环境变量已设置且不是原来的共享目录，则使用环境变量
        default_hf_home = Path(env_hf_home)
    else:
        # 否则使用本地目录
        default_hf_home = Path.home() / ".cache" / "huggingface"
        # 更新环境变量
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


def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog='transcript',
        description='视频字幕处理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  transcript auto video.mp4                  # 自动处理（无需手动编辑）
  transcript gen video.mp4                   # 快速转录（优先使用whisper.cpp）
  transcript gen video.mp4 --speakers        # 说话人分离转录（使用whisperx）
  transcript gen video.mp4 --force-whisperx  # 强制使用whisperx引擎
  transcript gen video.mp4 --enable-diarization  # 启用说话人分离功能
  transcript resume                          # 编辑字幕后继续处理
  transcript status                          # 查看状态
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 1. auto - 自动处理流程
    auto_parser = subparsers.add_parser(
        'auto',
        help='自动处理流程（无需手动编辑字幕）'
    )
    auto_parser.add_argument('video', help='输入视频或音频文件路径')
    auto_parser.add_argument('-o', '--output', help='输出目录')
    auto_parser.add_argument('--opening', help='片头视频路径（仅视频文件支持）')
    auto_parser.add_argument('--ending', help='片尾视频路径（仅视频文件支持）')

    # 2. gen - 生成字幕
    gen_parser = subparsers.add_parser(
        'gen',
        help='生成字幕文件'
    )
    gen_parser.add_argument('video', help='输入视频或音频文件路径')
    gen_parser.add_argument('-o', '--output', help='输出目录（默认：项目根目录）')
    gen_parser.add_argument('--force-whisperx', action='store_true', 
                           help='强制使用whisperx而不是whisper.cpp')
    gen_parser.add_argument('--enable-diarization', action='store_true',
                           help='启用说话人分离功能（默认禁用，需要tinydiarize模型）')
    gen_parser.add_argument('--speakers', action='store_true',
                           help='启用说话人分离并强制使用whisperx（快速转录时不使用此参数）')

    # 3. resume - 编辑字幕后继续处理
    resume_parser = subparsers.add_parser(
        'resume',
        help='编辑字幕后继续处理（自动调用align）'
    )
    resume_parser.add_argument('-o', '--output', help='输出目录')
    resume_parser.add_argument('--opening', help='片头视频路径')
    resume_parser.add_argument('--ending', help='片尾视频路径')

    # 4. status - 查看状态
    status_parser = subparsers.add_parser(
        'status',
        help='查看当前处理状态'
    )

    return parser


def print_banner():
    """打印欢迎横幅"""
    print("=" * 60)
    print("🎬 Transcript - 视频字幕处理工具")
    print("=" * 60)


def print_success(message: str):
    """打印成功消息"""
    print(f"✅ {message}")


def print_error(message: str):
    """打印错误消息"""
    print(f"❌ {message}")


def print_info(message: str):
    """打印信息消息"""
    print(f"ℹ️  {message}")


def print_warning(message: str):
    """打印警告消息"""
    print(f"⚠️  {message}")


def validate_media_file(file_path: str) -> Path:
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


def validate_video_file(video_path: str) -> Path:
    """验证视频文件（保持向后兼容）"""
    return validate_media_file(video_path)


def validate_subtitle_file(subtitle_path: str) -> Path:
    """验证字幕文件"""
    subtitle = Path(subtitle_path)
    if not subtitle.exists():
        raise FileNotFoundError(f"字幕文件不存在: {subtitle_path}")
    
    if subtitle.suffix.lower() != '.srt':
        raise ValueError(f"不支持的字幕格式: {subtitle.suffix}")
    
    return subtitle


def cmd_auto(args):
    """自动处理流程命令"""
    try:
        # 延迟导入
        from .transcript import auto

        print_banner()
        print_info(f"开始自动处理流程: {args.video}")
        print_info("自动处理模式 - 将跳过手动编辑步骤")

        video = validate_video_file(args.video)

        final_with_sub, final_no_sub, final_srt = auto(
            str(video),
            output_path=args.output,
            opening_video=args.opening,
            ending_video=args.ending
        )

        print_success("处理完成!")
        if final_no_sub:  # 视频文件
            print_info(f"带字幕视频: {final_with_sub}")
            print_info(f"无字幕视频: {final_no_sub}")
        else:  # 音频文件
            print_info(f"剪辑音频: {final_with_sub}")
        print_info(f"字幕文件: {final_srt}")

    except Exception as e:
        print_error(f"处理失败: {e}")
        sys.exit(1)


def cmd_gen(args):
    """生成字幕命令"""
    try:
        # 延迟导入以避免启动时的依赖问题
        from .transcript import transcript

        print_banner()
        print_info(f"开始生成转录文件: {args.video}")
        
        # 处理--speakers参数：启用说话人分离并强制使用whisperx
        if hasattr(args, 'speakers') and args.speakers:
            enable_diarization = True
            force_whisperx = True
            print_info("🎭 启用说话人分离功能（--speakers）")
            print_info("🔧 强制使用whisperx引擎（说话人分离模式）")
        else:
            # 根据参数决定是否启用说话人分离
            enable_diarization = args.enable_diarization
            force_whisperx = args.force_whisperx
            
            if enable_diarization:
                print_info("🎭 启用说话人分离功能")
            else:
                print_info("📝 禁用说话人分离功能（快速转录模式）")
                
            # 根据参数决定是否强制使用whisperx
            if force_whisperx:
                print_info("🔧 强制使用whisperx引擎")
            else:
                print_info("🚀 优先使用whisper.cpp引擎（快速转录）")

        video = validate_video_file(args.video)
        output_dir = Path(args.output) if args.output else None

        # 现在transcript函数返回两个文件
        srt_file, speaker_txt = transcript(
            video, 
            output_dir, 
            enable_diarization=enable_diarization,
            force_whisperx=force_whisperx
        )

        print_success(f"转录文件生成完成!")
        print_info(f"SRT字幕文件（无说话人标识）: {srt_file}")
        if speaker_txt:
            print_info(f"文本文件（含说话人标识）: {speaker_txt}")
            print_info("✨ 已自动生成两个版本的转录文件")
        else:
            print_info("📝 已生成SRT字幕文件")
        print_info("下一步: 编辑SRT字幕文件，然后运行 'transcript resume' 继续处理")

    except Exception as e:
        print_error(f"生成转录文件失败: {e}")
        sys.exit(1)


def cmd_resume(args):
    """编辑后继续处理命令"""
    try:
        # 延迟导入
        from .transcript import resume

        print_banner()

        final_with_sub, final_no_sub, final_srt = resume(
            output_path=args.output,
            opening_video=args.opening,
            ending_video=args.ending
        )

        print_success("处理完成!")
        if final_no_sub:  # 视频文件
            print_info(f"带字幕视频: {final_with_sub}")
            print_info(f"无字幕视频: {final_no_sub}")
        else:  # 音频文件
            print_info(f"剪辑音频: {final_with_sub}")
        print_info(f"字幕文件: {final_srt}")

    except Exception as e:
        print_error(f"处理失败: {e}")
        sys.exit(1)


def cmd_status(args):
    """查看状态命令"""
    try:
        print_banner()
        print_info("查看处理状态...")
        
        # 查找最近的工作目录
        tmp_dir = Path("/tmp/transcript")
        if tmp_dir.exists():
            log_files = list(tmp_dir.glob("*/.log"))
            if log_files:
                latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
                print_info(f"最近的工作目录: {latest_log.parent}")
                
                import json
                with open(latest_log, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                    print_info(f"项目名称: {log_data.get('name', 'N/A')}")
                    # 兼容新旧日志格式
                    if 'raw_file' in log_data:
                        file_type = log_data.get('file_type', 'unknown')
                        print_info(f"原始文件: {log_data.get('raw_file', 'N/A')} ({file_type})")
                    else:
                        print_info(f"原始视频: {log_data.get('raw_video', 'N/A')}")
                    print_info(f"创建时间: {log_data.get('timestamp', 'N/A')}")
            else:
                print_info("没有找到活动的处理任务")
        else:
            print_info("没有找到工作目录")
            
    except Exception as e:
        print_error(f"查看状态失败: {e}")
        sys.exit(1)


def main():
    """主入口函数"""
    parser = create_parser()
    
    # 如果没有参数，显示帮助
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    
    args = parser.parse_args()
    
    # 根据命令调用相应函数
    command_map = {
        'auto': cmd_auto,
        'gen': cmd_gen,
        'resume': cmd_resume,
        'status': cmd_status,
    }
    
    if args.command in command_map:
        command_map[args.command](args)
    else:
        print_error(f"未知命令: {args.command}")
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
