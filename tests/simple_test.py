#!/usr/bin/env python3
"""
简单测试字幕对齐功能
"""

import os

# 设置离线模式
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

def test_model_loading():
    """测试模型加载"""
    try:
        import whisperx
        print("✅ WhisperX 导入成功")
        
        model_dir = "/Volumes/share/data/models/huggingface/hub"
        device = "cpu"
        
        print("正在加载对齐模型...")
        
        # 尝试使用本地路径
        from pathlib import Path
        local_model_path = Path(model_dir) / "models--jonatasgrosman--wav2vec2-large-xlsr-53-chinese-zh-cn"
        if local_model_path.exists():
            # 查找最新的快照目录
            snapshots_dir = local_model_path / "snapshots"
            if snapshots_dir.exists():
                snapshot_dirs = [d for d in snapshots_dir.iterdir() if d.is_dir()]
                if snapshot_dirs:
                    latest_snapshot = max(snapshot_dirs, key=lambda x: x.stat().st_mtime)
                    print(f"使用本地模型: {latest_snapshot}")
                    model_name = str(latest_snapshot)
                else:
                    model_name = "jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn"
            else:
                model_name = "jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn"
        else:
            model_name = "jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn"
        
        model_a, metadata = whisperx.load_align_model(
            language_code="zh", 
            device=device, 
            model_name=model_name, 
            model_dir=model_dir
        )
        
        print("✅ 模型加载成功!")
        print(f"模型类型: {type(model_a)}")
        print(f"语言: {metadata['language']}")
        print(f"字典大小: {len(metadata['dictionary'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        return False

if __name__ == "__main__":
    print("=== 简单模型加载测试 ===\n")
    
    if test_model_loading():
        print("\n🎉 测试成功! 字幕对齐功能已准备就绪")
        print("\n现在你可以使用以下方式进行字幕对齐:")
        print("1. 使用 transcript.py 的 merge 命令")
        print("2. 直接调用 align_subtitles_with_audio 函数")
        print("\n模型已正确配置，可以离线使用!")
    else:
        print("\n❌ 测试失败，请检查模型文件")
