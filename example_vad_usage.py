#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Silero VAD预处理功能使用示例

这个脚本演示了如何使用新增的VAD预处理功能来处理音频文件。
VAD (Voice Activity Detection) 可以自动检测并移除音频中的静音片段，
从而提高转录效率和准确性。
"""

from pathlib import Path
from transcript.transcript import transcript

def main():
    print("🎯 Silero VAD预处理功能使用示例")
    print("=" * 50)
    
    # 示例：处理音频文件
    # 请将下面的路径替换为您的实际音频文件路径
    audio_file = "path/to/your/audio.wav"  # 替换为实际路径
    output_dir = "./output"  # 输出目录
    
    print(f"输入文件: {audio_file}")
    print(f"输出目录: {output_dir}")
    print()
    
    print("📋 VAD预处理功能说明:")
    print("1. 自动检测语音片段")
    print("2. 移除静音和噪音片段")
    print("3. 拼接有效语音内容")
    print("4. 提高转录效率和准确性")
    print()
    
    print("🔧 VAD参数配置:")
    print("- 最小语音片段长度: 250ms")
    print("- 最小静音片段长度: 100ms")
    print("- 语音片段前后填充: 30ms")
    print()
    
    # 注意：这里只是示例，实际使用时需要提供真实的音频文件
    if Path(audio_file).exists():
        try:
            print("🚀 开始处理...")
            result = transcript(
                input_file=audio_file,
                output_dir=output_dir,
                enable_diarization=False,  # 可选：启用说话人分离
                force_whisperx=False       # 可选：强制使用whisperx
            )
            print(f"✅ 处理完成: {result}")
        except Exception as e:
            print(f"❌ 处理失败: {e}")
    else:
        print("⚠️ 请将audio_file变量设置为实际的音频文件路径")
        print("   支持的格式: .wav, .mp3, .m4a, .flac, .aac, .ogg, .wma")
    
    print()
    print("📊 VAD预处理的优势:")
    print("- 减少转录时间（移除静音片段）")
    print("- 提高转录准确性（减少噪音干扰）")
    print("- 节省计算资源")
    print("- 自动优化音频质量")

if __name__ == "__main__":
    main()