#!/bin/bash

# WhisperX 模型设置脚本

# 设置模型目录
MODEL_DIR="/Volumes/share/data/hf_models"
export hf_model_dir="$MODEL_DIR"

echo "设置模型目录: $MODEL_DIR"

# 创建模型目录
mkdir -p "$MODEL_DIR"

# 检查网络连接
echo "检查网络连接..."
if ping -c 1 huggingface.co >/dev/null 2>&1; then
    echo "网络连接正常，尝试自动下载模型..."
    
    # 激活 conda 环境并下载模型
    source ~/miniconda3/etc/profile.d/conda.sh
    conda activate transcript
    
    python download_models.py
    
    if [ $? -eq 0 ]; then
        echo "模型下载成功!"
    else
        echo "自动下载失败，请手动下载模型"
        echo "手动下载步骤:"
        echo "1. 访问: https://huggingface.co/jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn"
        echo "2. 下载所有文件到: $MODEL_DIR/models--jonatasgrosman--wav2vec2-large-xlsr-53-chinese-zh-cn/"
    fi
else
    echo "无法连接到 huggingface.co"
    echo "请检查网络连接或手动下载模型"
    echo ""
    echo "手动下载步骤:"
    echo "1. 在有网络的环境中访问: https://huggingface.co/jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn"
    echo "2. 下载以下文件:"
    echo "   - config.json"
    echo "   - preprocessor_config.json"
    echo "   - pytorch_model.bin"
    echo "   - special_tokens_map.json"
    echo "   - tokenizer_config.json"
    echo "   - vocab.json"
    echo "3. 创建目录结构:"
    echo "   $MODEL_DIR/models--jonatasgrosman--wav2vec2-large-xlsr-53-chinese-zh-cn/snapshots/[commit_hash]/"
    echo "4. 将下载的文件放入 snapshots/[commit_hash]/ 目录中"
    echo ""
    echo "或者，你可以将整个模型目录从其他机器复制过来"
fi

echo ""
echo "设置环境变量:"
echo "export hf_model_dir=\"$MODEL_DIR\""
echo ""
echo "建议将上述环境变量添加到你的 ~/.bashrc 或 ~/.zshrc 文件中"
