#!/usr/bin/env python3
"""
Transcript CLI - 简化的命令行接口

提供更友好的命令行体验，简化视频字幕处理操作。
"""

import argparse
import sys
from pathlib import Path
from typing import Optional


def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog='transcript',
        description='视频字幕处理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  transcript auto video.mp4                  # 自动处理（无需手动编辑）
  transcript gen video.mp4                   # 生成字幕
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
    auto_parser.add_argument('video', help='输入视频文件路径')
    auto_parser.add_argument('-o', '--output', help='输出目录')
    auto_parser.add_argument('--opening', help='片头视频路径')
    auto_parser.add_argument('--ending', help='片尾视频路径')

    # 2. gen - 生成字幕
    gen_parser = subparsers.add_parser(
        'gen',
        help='生成字幕文件'
    )
    gen_parser.add_argument('video', help='输入视频文件路径')
    gen_parser.add_argument('-o', '--output', help='输出目录（默认：项目根目录）')

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


def validate_video_file(video_path: str) -> Path:
    """验证视频文件"""
    video = Path(video_path)
    if not video.exists():
        raise FileNotFoundError(f"视频文件不存在: {video_path}")
    
    valid_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'}
    if video.suffix.lower() not in valid_extensions:
        raise ValueError(f"不支持的视频格式: {video.suffix}")
    
    return video


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
        print_info(f"带字幕视频: {final_with_sub}")
        print_info(f"无字幕视频: {final_no_sub}")
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
        print_info(f"开始生成字幕: {args.video}")

        video = validate_video_file(args.video)
        output_dir = Path(args.output) if args.output else None

        srt_file = transcript(video, output_dir)

        print_success(f"字幕生成完成!")
        print_info(f"字幕文件: {srt_file}")
        print_info("下一步: 编辑字幕文件，然后运行 'transcript resume' 继续处理")

    except Exception as e:
        print_error(f"生成字幕失败: {e}")
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
        print_info(f"带字幕视频: {final_with_sub}")
        print_info(f"无字幕视频: {final_no_sub}")
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
