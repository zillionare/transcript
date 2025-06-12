# WhisperX 字幕对齐功能使用说明

## 问题解决

✅ **已解决**: WhisperX 对齐模型无法加载的问题

### 问题描述
之前遇到的错误：
```
ValueError: The chosen align_model "jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn" could not be found in huggingface
```

### 解决方案
1. **模型路径配置**: 已将模型目录设置为你现有的路径 `/Volumes/share/data/models/huggingface/hub`
2. **离线模式**: 配置了离线模式，避免网络连接问题
3. **本地模型加载**: 直接使用本地快照目录加载模型

## 当前配置

### 模型目录
```
/Volumes/share/data/models/huggingface/hub/models--jonatasgrosman--wav2vec2-large-xlsr-53-chinese-zh-cn/
```

### 环境变量
程序会自动设置以下环境变量以启用离线模式：
```bash
TRANSFORMERS_OFFLINE=1
HF_HUB_OFFLINE=1
```

## 使用方法

### 1. 测试模型加载
```bash
# 测试模型是否正确加载
python transcript.py test

# 或者使用简单测试脚本
python simple_test.py
```

### 2. 字幕对齐功能
```bash
# 方法1: 使用 merge 命令（推荐）
python transcript.py merge <工作目录> <目标名称>

# 方法2: 直接调用对齐函数
python -c "
from transcript import align_subtitles_with_audio
from pathlib import Path
align_subtitles_with_audio(
    Path('video.mp4'),      # 视频文件
    Path('original.srt'),   # 原始字幕
    Path('aligned.srt')     # 对齐后字幕
)
"
```

### 3. 完整工作流程
```bash
# 1. 视频转字幕
python transcript.py transcript /path/to/raw.mp4

# 2. 编辑字幕文件（手动）
# 编辑生成的 .srt 文件

# 3. 剪辑和对齐
python transcript.py cut
```

## 功能特性

### 自动降级
如果对齐模型加载失败，程序会自动：
1. 显示错误信息
2. 复制原始字幕文件作为对齐结果
3. 提示用户检查模型配置

### 离线工作
- ✅ 完全离线运行
- ✅ 不需要网络连接
- ✅ 使用本地模型文件

### 错误处理
- ✅ 优雅的错误处理
- ✅ 详细的错误信息
- ✅ 自动回退机制

## 测试结果

```
✅ WhisperX 导入成功
✅ 模型加载成功!
✅ 模型类型: Wav2Vec2ForCTC
✅ 语言: zh (中文)
✅ 字典大小: 3503 个字符
```

## 故障排除

### 如果模型加载失败
1. 检查模型文件是否完整：
   ```bash
   ls -la "/Volumes/share/data/models/huggingface/hub/models--jonatasgrosman--wav2vec2-large-xlsr-53-chinese-zh-cn/snapshots/"
   ```

2. 检查必要文件是否存在：
   - config.json
   - preprocessor_config.json
   - pytorch_model.bin
   - vocab.json

3. 重新运行测试：
   ```bash
   python simple_test.py
   ```

### 如果字幕对齐效果不好
1. 确保音频质量良好
2. 检查原始字幕的时间戳是否准确
3. 考虑调整音频采样率（当前为16kHz）

## 技术细节

### 模型信息
- **模型名称**: jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn
- **模型类型**: Wav2Vec2ForCTC
- **语言**: 中文 (zh)
- **用途**: 语音识别和字幕对齐

### 音频处理
- **采样率**: 16kHz
- **声道**: 2 (立体声)
- **格式**: PCM 16-bit

### 依赖项
- whisperx
- transformers
- torch
- pysubs2
- ffmpeg

## 更新日志

### 2024-12-20
- ✅ 解决模型加载问题
- ✅ 配置离线模式
- ✅ 添加错误处理和自动降级
- ✅ 创建测试脚本
- ✅ 完善文档
