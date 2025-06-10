#!/usr/bin/env python3
"""
下载 WhisperX 对齐模型的脚本

使用方法：
1. 确保网络连接正常
2. 运行: python download_models.py
3. 或者手动下载模型文件到指定目录

模型下载地址：
https://huggingface.co/jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn
"""

import os
import sys
from pathlib import Path
from huggingface_hub import snapshot_download
import shutil

def download_align_model():
    """下载中文对齐模型"""
    model_name = "jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn"
    
    # 使用与 transcript.py 相同的模型目录
    model_dir = os.environ.get("hf_model_dir", "/Volumes/share/data/hf_models")
    model_dir = Path(model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"下载模型到: {model_dir}")
    print(f"模型名称: {model_name}")
    
    try:
        # 下载模型
        local_dir = snapshot_download(
            repo_id=model_name,
            cache_dir=model_dir,
            local_files_only=False,
            resume_download=True
        )
        print(f"模型下载成功: {local_dir}")
        return True
        
    except Exception as e:
        print(f"下载失败: {e}")
        print("\n手动下载说明:")
        print("1. 访问: https://huggingface.co/jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn")
        print("2. 下载以下文件:")
        print("   - config.json")
        print("   - preprocessor_config.json") 
        print("   - pytorch_model.bin")
        print("   - special_tokens_map.json")
        print("   - tokenizer_config.json")
        print("   - vocab.json")
        print(f"3. 将文件放在目录: {model_dir}/models--jonatasgrosman--wav2vec2-large-xlsr-53-chinese-zh-cn/")
        return False

def check_model_exists():
    """检查模型是否已存在"""
    model_dir = os.environ.get("hf_model_dir", "/Volumes/share/data/hf_models")
    model_path = Path(model_dir) / "models--jonatasgrosman--wav2vec2-large-xlsr-53-chinese-zh-cn"
    
    if model_path.exists():
        print(f"模型目录已存在: {model_path}")
        # 检查必要文件
        required_files = [
            "snapshots/*/config.json",
            "snapshots/*/preprocessor_config.json", 
            "snapshots/*/pytorch_model.bin",
            "snapshots/*/vocab.json"
        ]
        
        import glob
        missing_files = []
        for pattern in required_files:
            if not glob.glob(str(model_path / pattern)):
                missing_files.append(pattern)
        
        if missing_files:
            print("缺少以下文件:")
            for f in missing_files:
                print(f"  - {f}")
            return False
        else:
            print("模型文件完整")
            return True
    else:
        print(f"模型目录不存在: {model_path}")
        return False

def main():
    print("检查 WhisperX 中文对齐模型...")
    
    if check_model_exists():
        print("模型已存在，无需下载")
        return
    
    print("开始下载模型...")
    if download_align_model():
        print("下载完成!")
    else:
        print("下载失败，请手动下载")
        sys.exit(1)

if __name__ == "__main__":
    main()
