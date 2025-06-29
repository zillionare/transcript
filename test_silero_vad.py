#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Silero VAD功能
"""

try:
    from silero_vad import load_silero_vad, read_audio, get_speech_timestamps
    import torch
    import torchaudio
    print("✅ Silero VAD导入成功")
    
    # 加载模型
    model = load_silero_vad()
    print("✅ Silero VAD模型加载成功")
    
    print("🎯 VAD功能测试完成，所有依赖都正常工作")
    
except ImportError as e:
    print(f"❌ 导入错误: {e}")
except Exception as e:
    print(f"❌ 其他错误: {e}")