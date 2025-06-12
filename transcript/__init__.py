"""
Transcript - 视频字幕处理工具

一个用于自动生成、编辑和处理视频字幕的Python工具包。
"""

__version__ = "0.1.0"
__author__ = "Flora-cj"
__email__ = "1625864556@qq.com"

# 延迟导入以避免启动时的依赖问题
def get_transcript_functions():
    """延迟导入transcript模块的函数"""
    from .transcript import (align_subtitles_with_audio, cut, merge,
                             process_video, sub, t2s, test, transcript)
    return {
        'transcript': transcript,
        'cut': cut,
        'merge': merge,
        'process_video': process_video,
        'align_subtitles_with_audio': align_subtitles_with_audio,
        'sub': sub,
        't2s': t2s,
        'test': test
    }

from .cli import main as cli_main

__all__ = [
    'get_transcript_functions',
    'cli_main'
]
