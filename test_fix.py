#!/usr/bin/env python3
"""
测试音频转录修复
"""

import sys
import tempfile
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from transcript.transcript import transcript, is_audio_file


def create_test_audio():
    """创建一个测试用的音频文件"""
    test_file = Path("test_audio.wav")
    
    if test_file.exists():
        print(f"测试音频文件已存在: {test_file}")
        return test_file
    
    print("创建测试音频文件...")
    
    # 创建一个简单的WAV文件头
    with open(test_file, "wb") as f:
        # WAV文件头
        f.write(b"RIFF")
        f.write((36).to_bytes(4, 'little'))  # 文件大小
        f.write(b"WAVE")
        f.write(b"fmt ")
        f.write((16).to_bytes(4, 'little'))  # fmt chunk大小
        f.write((1).to_bytes(2, 'little'))   # 音频格式 (PCM)
        f.write((1).to_bytes(2, 'little'))   # 声道数
        f.write((16000).to_bytes(4, 'little'))  # 采样率
        f.write((32000).to_bytes(4, 'little'))  # 字节率
        f.write((2).to_bytes(2, 'little'))   # 块对齐
        f.write((16).to_bytes(2, 'little'))  # 位深度
        f.write(b"data")
        f.write((0).to_bytes(4, 'little'))   # 数据大小
    
    print(f"✅ 测试音频文件已创建: {test_file}")
    return test_file


def test_audio_transcription():
    """测试音频转录功能"""
    print("=" * 60)
    print("🧪 测试音频转录修复")
    print("=" * 60)
    
    # 创建测试音频文件
    audio_file = create_test_audio()
    
    # 验证文件类型检测
    print(f"\n🔍 文件类型检测:")
    print(f"   文件: {audio_file}")
    print(f"   是音频文件: {is_audio_file(audio_file)}")
    
    try:
        print(f"\n🚀 开始转录测试...")
        print(f"   注意: 这是一个空的音频文件，转录可能会失败，但应该能正确处理错误")
        
        # 尝试转录
        result = transcript(audio_file, dry_run=False)
        print(f"✅ 转录完成: {result}")
        
        # 检查生成的文件
        if result and Path(result).exists():
            print(f"✅ 字幕文件已生成: {result}")
            with open(result, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"   文件内容长度: {len(content)} 字符")
                if content.strip():
                    print(f"   内容预览: {content[:100]}...")
                else:
                    print(f"   文件为空（这是正常的，因为测试音频没有实际内容）")
        else:
            print(f"❌ 字幕文件未生成")
            
    except Exception as e:
        print(f"❌ 转录测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理测试文件
        if audio_file.exists():
            audio_file.unlink()
            print(f"🧹 已清理测试文件: {audio_file}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_audio_transcription()
