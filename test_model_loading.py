#!/usr/bin/env python3
"""
测试 WhisperX 对齐模型加载
"""

import os
import sys
from pathlib import Path

# 设置模型目录
model_dir = "/Volumes/share/data/models/huggingface/hub"

def test_model_loading():
    """测试模型加载"""
    try:
        import whisperx
        print("WhisperX 导入成功")
        
        print(f"使用模型目录: {model_dir}")
        
        # 测试加载对齐模型
        print("尝试加载中文对齐模型...")
        device = "cpu"
        
        model_a, metadata = whisperx.load_align_model(
            language_code="zh", 
            device=device, 
            model_name="jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn", 
            model_dir=model_dir
        )
        
        print("✅ 模型加载成功!")
        print(f"模型类型: {type(model_a)}")
        print(f"元数据: {metadata}")
        
        return True
        
    except ImportError as e:
        print(f"❌ WhisperX 导入失败: {e}")
        return False
        
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        print("\n可能的解决方案:")
        print("1. 检查模型文件是否完整")
        print("2. 检查网络连接")
        print("3. 尝试重新下载模型")
        return False

def check_model_files():
    """检查模型文件是否存在"""
    model_path = Path(model_dir) / "models--jonatasgrosman--wav2vec2-large-xlsr-53-chinese-zh-cn"
    
    print(f"检查模型路径: {model_path}")
    
    if not model_path.exists():
        print(f"❌ 模型目录不存在: {model_path}")
        return False
    
    # 查找 snapshots 目录
    snapshots_dir = model_path / "snapshots"
    if not snapshots_dir.exists():
        print(f"❌ snapshots 目录不存在: {snapshots_dir}")
        return False
    
    # 查找最新的快照
    snapshot_dirs = [d for d in snapshots_dir.iterdir() if d.is_dir()]
    if not snapshot_dirs:
        print(f"❌ 没有找到快照目录")
        return False
    
    # 使用最新的快照
    latest_snapshot = max(snapshot_dirs, key=lambda x: x.stat().st_mtime)
    print(f"使用快照: {latest_snapshot.name}")
    
    # 检查必要文件
    required_files = [
        "config.json",
        "preprocessor_config.json", 
        "pytorch_model.bin",
        "vocab.json"
    ]
    
    missing_files = []
    for file_name in required_files:
        file_path = latest_snapshot / file_name
        if not file_path.exists():
            missing_files.append(file_name)
        else:
            print(f"✅ {file_name}")
    
    if missing_files:
        print(f"❌ 缺少文件: {missing_files}")
        return False
    
    print("✅ 所有必要文件都存在")
    return True

def main():
    print("=== WhisperX 模型加载测试 ===\n")
    
    print("1. 检查模型文件...")
    if not check_model_files():
        print("模型文件检查失败")
        sys.exit(1)
    
    print("\n2. 测试模型加载...")
    if test_model_loading():
        print("\n🎉 测试成功! 模型可以正常加载")
    else:
        print("\n❌ 测试失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
