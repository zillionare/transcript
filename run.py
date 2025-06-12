#!/usr/bin/env python3
"""
便捷运行脚本 - 简化transcript工具的使用
"""

import sys
import os
from pathlib import Path

# 添加transcript目录到Python路径
transcript_dir = Path(__file__).parent / "transcript"
sys.path.insert(0, str(transcript_dir))

def main():
    """主函数 - 直接调用transcript模块"""
    try:
        # 导入transcript模块
        import transcript
        
        # 直接使用fire来处理命令行参数
        import fire
        fire.Fire({
            "process": transcript.process_video,    # 完整处理流程
            "transcript": transcript.transcript,    # 1. 视频转字幕
            "cut": transcript.cut,                 # 2. 剪辑视频
            "merge": transcript.merge,             # 3. 合并输出
            "sub": transcript.sub,                 # 字幕纠错
            "t2s": transcript.t2s,                 # 繁简转换
            "test": transcript.test,               # 测试模型
            "align": transcript.align_subtitles_with_audio  # 字幕对齐
        })
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("请确保已安装所有依赖:")
        print("pip install fire jieba opencc pysubs2 whisperx")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 运行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
