#!/usr/bin/env python3
"""
测试音频文件支持功能
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from transcript.transcript import (cut_audio, is_audio_file, is_video_file,
                                   probe_duration, transcript)


class TestAudioSupport:
    """测试音频文件支持"""
    
    def test_is_audio_file(self):
        """测试音频文件检测"""
        # 测试音频文件
        assert is_audio_file(Path("test.wav"))
        assert is_audio_file(Path("test.mp3"))
        assert is_audio_file(Path("test.m4a"))
        assert is_audio_file(Path("test.flac"))
        assert is_audio_file(Path("test.aac"))
        assert is_audio_file(Path("test.ogg"))
        assert is_audio_file(Path("test.wma"))
        
        # 测试大小写不敏感
        assert is_audio_file(Path("test.WAV"))
        assert is_audio_file(Path("test.MP3"))
        
        # 测试非音频文件
        assert not is_audio_file(Path("test.mp4"))
        assert not is_audio_file(Path("test.txt"))
        assert not is_audio_file(Path("test.jpg"))
    
    def test_is_video_file(self):
        """测试视频文件检测"""
        # 测试视频文件
        assert is_video_file(Path("test.mp4"))
        assert is_video_file(Path("test.avi"))
        assert is_video_file(Path("test.mov"))
        assert is_video_file(Path("test.mkv"))
        assert is_video_file(Path("test.flv"))
        assert is_video_file(Path("test.wmv"))
        
        # 测试大小写不敏感
        assert is_video_file(Path("test.MP4"))
        assert is_video_file(Path("test.AVI"))
        
        # 测试非视频文件
        assert not is_video_file(Path("test.wav"))
        assert not is_video_file(Path("test.txt"))
        assert not is_video_file(Path("test.jpg"))
    
    def test_audio_file_validation(self):
        """测试音频文件验证逻辑"""
        # 创建临时音频文件用于测试
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
            
        try:
            # 创建一个简单的WAV文件头（用于测试）
            with open(tmp_path, "wb") as f:
                # 写入简单的WAV文件头
                f.write(b"RIFF")
                f.write((36).to_bytes(4, 'little'))  # 文件大小
                f.write(b"WAVE")
                f.write(b"fmt ")
                f.write((16).to_bytes(4, 'little'))  # fmt chunk大小
                f.write((1).to_bytes(2, 'little'))   # 音频格式
                f.write((1).to_bytes(2, 'little'))   # 声道数
                f.write((16000).to_bytes(4, 'little'))  # 采样率
                f.write((32000).to_bytes(4, 'little'))  # 字节率
                f.write((2).to_bytes(2, 'little'))   # 块对齐
                f.write((16).to_bytes(2, 'little'))  # 位深度
                f.write(b"data")
                f.write((0).to_bytes(4, 'little'))   # 数据大小
            
            # 验证文件被正确识别为音频文件
            assert is_audio_file(tmp_path)
            assert not is_video_file(tmp_path)
            
        finally:
            # 清理临时文件
            if tmp_path.exists():
                tmp_path.unlink()
    
    def test_file_type_detection_in_transcript(self):
        """测试transcript函数中的文件类型检测"""
        # 测试不存在的文件
        try:
            transcript(Path("nonexistent.wav"))
            assert False, "应该抛出FileNotFoundError"
        except FileNotFoundError:
            print("✅ 正确检测到文件不存在")

        # 测试不支持的文件格式
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            try:
                transcript(tmp_path)
                assert False, "应该抛出ValueError"
            except ValueError as e:
                if "不支持的文件格式" in str(e):
                    print("✅ 正确检测到不支持的文件格式")
                else:
                    raise
        finally:
            if tmp_path.exists():
                tmp_path.unlink()


def test_cut_audio_function():
    """测试音频剪辑函数的基本结构"""
    # 这个测试只验证函数存在且可以导入
    assert callable(cut_audio)
    print("✅ cut_audio函数可以正常导入")


def run_all_tests():
    """运行所有测试"""
    print("开始测试音频文件支持功能...")

    test_suite = TestAudioSupport()

    try:
        test_suite.test_is_audio_file()
        print("✅ 音频文件检测测试通过")
    except Exception as e:
        print(f"❌ 音频文件检测测试失败: {e}")

    try:
        test_suite.test_is_video_file()
        print("✅ 视频文件检测测试通过")
    except Exception as e:
        print(f"❌ 视频文件检测测试失败: {e}")

    try:
        test_suite.test_audio_file_validation()
        print("✅ 音频文件验证测试通过")
    except Exception as e:
        print(f"❌ 音频文件验证测试失败: {e}")

    try:
        test_suite.test_file_type_detection_in_transcript()
        print("✅ transcript函数文件类型检测测试通过")
    except Exception as e:
        print(f"❌ transcript函数文件类型检测测试失败: {e}")

    try:
        test_cut_audio_function()
        print("✅ cut_audio函数测试通过")
    except Exception as e:
        print(f"❌ cut_audio函数测试失败: {e}")

    print("\n测试完成!")


if __name__ == "__main__":
    run_all_tests()
