# Transcript - 视频字幕处理工具

一个用于自动生成、编辑和处理视频字幕的Python工具包，提供简洁的CLI接口。

## 功能特性

- 🎯 **智能转录**: 支持多种音视频格式的自动转录
- 🎭 **说话人分离**: 自动识别不同说话人并标记
- 📝 **字幕生成**: 生成标准SRT格式字幕文件
- 🔧 **词典纠错**: 内置中文词典，自动纠正转录错误
- ⚡ **高性能**: 优先使用whisper.cpp，性能优异
- 🔄 **智能回退**: whisper.cpp失败时自动回退到whisperx
- 🎨 **字幕优化**: 自动调整字幕显示效果和时长
- 🎤 **VAD预处理**: 集成Silero VAD，自动移除静音片段，提高转录效率

## 🚀 快速开始

```bash
# 最简单的使用方式 - 一键处理视频
transcript auto video.mp4

# 或者先生成字幕，编辑后继续处理
transcript gen video.mp4
# 编辑生成的srt文件
transcript resume
```

## 📋 主要命令

| 命令     | 说明                                | 示例                        |
| -------- | ----------------------------------- | --------------------------- |
| `auto`   | 自动处理流程（无需手动编辑）        | `transcript auto video.mp4` |
| `gen`    | 生成字幕文件                        | `transcript gen video.mp4`  |
| `resume` | 编辑字幕后继续处理（自动调用align） | `transcript resume`         |
| `status` | 查看当前处理状态                    | `transcript status`         |

## 🎯 使用场景

### 场景1: 自动处理（极罕见）
```bash
transcript auto video.mp4
```
适用于不需要手动编辑字幕的情况。

### 场景2: 标准流程（推荐）
```bash
# 1. 生成字幕
transcript gen video.mp4

# 2. 手动编辑生成的 video.srt 文件
# 在需要删除的字幕前添加 [DEL] 标记

# 3. 继续处理（自动调用align）
transcript resume
```

### 场景3: 带片头片尾
```bash
transcript auto video.mp4 --opening intro.mp4 --ending outro.mp4
# 或
transcript resume --opening intro.mp4 --ending outro.mp4
```

### 场景4: 指定输出目录
```bash
transcript auto video.mp4 -o /path/to/output/
transcript resume -o /path/to/output/
```

## 🛠️ 安装和设置

```bash
# 安装依赖
pip install -e .

# 测试安装
transcript status
```

## 🎬 输出文件

处理完成后会生成：

- `{name}-final.mp4` - 无字幕的最终视频
- `{name}-final-sub.mp4` - 带字幕的最终视频
- `{name}-final.srt` - 对齐后的字幕文件

## 📝 字幕编辑技巧

### 删除标记
在字幕行前添加 `[DEL]` 或 `[del]` 标记：

```srt
1
00:00:01,000 --> 00:00:03,000
这段保留

2
00:00:03,000 --> 00:00:05,000
[DEL]这段删除
```

### 自动删除
系统会自动删除单字的语助词：`好`、`呃`、`恩`、`嗯`

### 自定义词典
编辑 `dict.yaml` 文件配置词典规则：

```yaml
replace:
  宽体: 匡醍
  延报: 研报
  2share: tushare

warning:
  - 24克
  - 其他需要复检的词
```

**两类设置说明：**
- **replace**: 强制替换词，自动应用于所有字幕
- **warning**: 警告词，不替换但会在控制台提示人工复检

**处理逻辑：**
1. 先执行替换词典
2. 对替换后的内容检查警告词
3. 集中输出警告信息，便于一次性处理



## 🎤 VAD预处理功能

### 什么是VAD？
VAD (Voice Activity Detection) 是语音活动检测技术，能够自动识别音频中的语音片段和静音片段。

### VAD预处理的优势
- **提高转录效率**: 自动移除静音片段，减少处理时间
- **提升转录准确性**: 减少噪音和静音对转录的干扰
- **节省计算资源**: 只处理包含语音的音频片段
- **自动优化**: 无需手动配置，自动检测最佳参数

### VAD处理流程
1. **音频预处理**: 将输入音频转换为16kHz单声道格式
2. **语音检测**: 使用Silero VAD模型检测语音片段
3. **片段提取**: 提取所有检测到的语音片段
4. **音频拼接**: 将语音片段拼接成连续音频
5. **转录处理**: 使用处理后的音频进行转录

### VAD参数配置
- **最小语音片段长度**: 250ms（过短的语音片段会被忽略）
- **最小静音片段长度**: 100ms（过短的静音不会被移除）
- **语音片段填充**: 30ms（在语音片段前后添加少量填充）

### 使用示例
```python
# VAD预处理会自动应用于所有转录任务
from transcript.transcript import transcript

# 处理音频文件（自动启用VAD预处理）
result = transcript(
    input_file="audio.wav",
    output_dir="./output"
)
```

### VAD处理统计
处理过程中会显示详细的统计信息：
```
🎯 开始VAD预处理，移除静音片段...
📥 加载Silero VAD模型...
📖 读取音频文件...
🔍 检测语音片段...
✅ 检测到 15 个语音片段
💾 保存VAD处理后的音频
📊 VAD处理统计:
   原始时长: 120.50秒
   处理后时长: 95.30秒
   压缩比例: 20.9%
```

## 🔧 常见问题

### Q: 如何查看帮助？
```bash
transcript --help
transcript auto --help  # 查看特定命令的帮助
```

### Q: 如何查看处理状态？
```bash
transcript status
```

### Q: VAD预处理失败怎么办？
VAD预处理失败时，系统会自动回退到使用原始音频文件，不会影响转录流程。

### Q: 如何禁用VAD预处理？
目前VAD预处理是自动启用的。如果需要禁用，可以修改代码中的VAD调用部分。

