# 视频字幕自动生成和编辑工具

这是一个功能完整的视频字幕处理工具，支持自动生成字幕、智能纠错、视频剪辑、字幕对齐和最终输出。

## 主要功能

1. **自动字幕生成**: 使用Whisper模型将视频转换为中文字幕
2. **智能纠错**: 基于自定义词典(words.md)进行错误纠正
3. **视频剪辑**: 支持通过[DEL]标记删除视频片段
4. **字幕对齐**: 使用语音对齐模型确保剪辑后字幕与语音同步
5. **片头片尾**: 支持添加自定义片头和片尾视频
6. **双版本输出**: 生成带字幕和不带字幕两个版本

## 系统要求

- Python 3.10+
- FFmpeg
- 支持 macOS ARM64 和 Linux x86_64

## 安装

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 下载对齐模型：
```bash
python download_models.py
```

## 使用方法

### 方法1: 完整自动流程

```bash
# 基本用法
python transcript.py process /path/to/video.mp4

# 指定输出路径
python transcript.py process /path/to/video.mp4 --output_path /path/to/output/

# 添加片头片尾
python transcript.py process /path/to/video.mp4 \
    --opening_video /path/to/opening.mp4 \
    --ending_video /path/to/ending.mp4 \
    --output_path /path/to/output/

# 自动处理（跳过手动编辑）
python transcript.py process /path/to/video.mp4 --auto_process True
```

### 方法2: 分步执行

```bash
# 步骤1: 生成字幕
python transcript.py transcript /path/to/video.mp4

# 步骤2: 手动编辑字幕文件
# 编辑生成的.srt文件，在需要删除的字幕前添加[DEL]标记

# 步骤3: 剪辑视频
python transcript.py cut

# 步骤4: 合并输出
python transcript.py merge
```

## 输出文件

处理完成后会生成以下文件：

- `{name}-final.mp4`: 无字幕版本
- `{name}-final-sub.mp4`: 带字幕版本  
- `{name}-final.srt`: 对齐后的字幕文件

## 字幕编辑说明

在生成的字幕文件中，您可以：

1. **删除字幕**: 在字幕行前添加`[DEL]`标记
2. **修改文本**: 直接编辑字幕内容
3. **调整时间**: 修改时间戳（不推荐，会被对齐功能覆盖）

示例：
```srt
1
00:00:01,000 --> 00:00:03,000
大家好，欢迎来到我的频道

2
00:00:03,000 --> 00:00:05,000
[DEL]这段话我想删除

3
00:00:05,000 --> 00:00:07,000
今天我们来学习新的内容
```

## 自定义词典

编辑`words.md`文件来添加自定义纠错规则：

```
错误词,正确词
宽体,匡醍
延报,研报
浮现,复现
```

## 高级功能

### 字幕对齐

系统会自动使用语音对齐模型确保剪辑后的字幕与语音同步。这是通过以下步骤实现的：

1. 提取视频音频
2. 加载中文语音对齐模型
3. 将字幕文本与音频进行对齐
4. 生成精确的时间戳

### 片头片尾处理

- 支持自定义片头片尾视频
- 自动调整字幕时间偏移
- 保持视频质量和格式一致性

### 错误处理

- 如果对齐模型加载失败，会自动使用原始字幕
- 提供详细的错误信息和解决建议
- 支持离线运行

## 故障排除

### 模型加载失败

```bash
# 测试模型加载
python transcript.py test

# 重新下载模型
python download_models.py
```

### 视频格式不支持

支持的格式：`.mp4`, `.avi`, `.mov`, `.mkv`, `.flv`, `.wmv`

### 字幕对齐效果不佳

1. 确保音频质量良好
2. 检查字幕文本准确性
3. 验证模型文件完整性

## 配置

### 环境变量

- `hf_model_dir`: Hugging Face模型目录路径
- `TRANSFORMERS_OFFLINE`: 设置为"1"启用离线模式
- `HF_HUB_OFFLINE`: 设置为"1"启用离线模式

### 默认路径

- 工作目录: `/tmp/transcript/`
- 模型目录: `/Volumes/share/data/models/huggingface/hub`
- 片头视频: `/Volumes/share/data/autobackup/ke/factor-ml/opening.mp4`
- 片尾视频: `/Volumes/share/data/autobackup/ke/factor-ml/end.mp4`

## 技术细节

### 使用的模型

- **语音识别**: Whisper large-v2 (支持中文)
- **字幕对齐**: wav2vec2-large-xlsr-53-chinese-zh-cn

### 视频处理

- 使用FFmpeg进行视频处理
- 支持硬件加速 (macOS VideoToolbox)
- 保持原始视频质量

### 字幕格式

- 输入/输出: SRT格式
- 编码: UTF-8
- 时间精度: 毫秒级

## 许可证

本项目采用开源许可证，详见LICENSE文件。
