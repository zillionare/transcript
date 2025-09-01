#!/bin/bash

# whisper.cpp 设置脚本
# 该脚本会下载、编译 whisper.cpp，并将其安装到正确的位置

set -e  # 遇到错误时停止执行

echo "开始设置 whisper.cpp..."

# 创建必要的目录
mkdir -p ~/workspace

# 进入工作目录
cd ~/workspace

# 如果 whisper.cpp 目录已存在，则先删除
if [ -d "whisper.cpp" ]; then
    echo "删除现有的 whisper.cpp 目录..."
    rm -rf whisper.cpp
fi

# 克隆 whisper.cpp 仓库
echo "克隆 whisper.cpp 仓库..."
git clone https://github.com/ggerganov/whisper.cpp.git

# 进入 whisper.cpp 目录
cd whisper.cpp

# 编译 whisper.cpp
echo "编译 whisper.cpp..."
make

# 创建目标目录（如果不存在）
mkdir -p ~/workspace/whisper_cpp/models

# 复制可执行文件到目标位置
echo "复制 whisper-cli 到目标位置..."
cp main ~/workspace/whisper_cpp/whisper-cli

# 进入 models 目录
cd ~/workspace/whipser.cpp

# 下载 large-v2 模型
cp -r /Volumes/share/data/whisper.cpp/models ./

# 验证文件是否存在
echo "验证文件..."
if [ -f "~/workspace/whisper.cpp/whisper-cli" ]; then
    echo "✓ whisper-cli 存在"
else
    echo "✗ whisper-cli 不存在"
fi

if [ -f "~/workspace/whisper_cpp/models/ggml-large-v2.bin" ]; then
    echo "✓ ggml-large-v2.bin 存在"
else
    echo "✗ ggml-large-v2.bin 不存在"
fi
