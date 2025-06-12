# Transcript CLI 使用指南

## 简介

Transcript CLI 是一个简化的命令行接口，让视频字幕处理变得更加简单直观。

## 安装和设置

```bash
# 安装项目依赖
pip install -e .

# 或者直接使用脚本
python transcript_cli.py --help
```

## 快速开始

### 1. 最简单的使用方式

```bash
# 完整处理一个视频（推荐）
transcript process video.mp4

# 或者使用脚本
python transcript_cli.py process video.mp4
```

这个命令会：
1. 自动生成字幕
2. 提示你编辑字幕（可选）
3. 剪辑视频
4. 生成最终的视频文件

### 2. 自动处理（无需手动编辑）

```bash
# 完全自动化处理
transcript process video.mp4 --auto
```

### 3. 交互式配置

```bash
# 交互式配置各种选项
transcript process video.mp4 --interactive
```

## 命令详解

### 🎬 process - 完整处理流程（推荐）

最常用的命令，一次性完成所有处理步骤。

```bash
# 基本用法
transcript process video.mp4

# 指定输出目录
transcript process video.mp4 -o /path/to/output/

# 添加片头片尾
transcript process video.mp4 --opening intro.mp4 --ending outro.mp4

# 自动处理（跳过手动编辑）
transcript process video.mp4 --auto

# 交互式配置
transcript process video.mp4 --interactive
```

**别名**: `proc`, `auto`

### 📝 generate - 生成字幕

只生成字幕文件，不进行后续处理。

```bash
# 生成字幕到项目根目录
transcript generate video.mp4

# 指定输出目录
transcript generate video.mp4 -o /path/to/output/

# 试运行模式
transcript generate video.mp4 --dry-run
```

**别名**: `gen`, `transcript`

### ✏️ edit - 编辑后继续处理

当你手动编辑了字幕文件后，继续完成剩余的处理步骤。

```bash
# 使用默认工作目录
transcript edit

# 指定工作目录
transcript edit -w /tmp/transcript/my_video/

# 指定输出目录和片头片尾
transcript edit -o /path/to/output/ --opening intro.mp4 --ending outro.mp4
```

**别名**: `continue`, `resume`

### 🎯 align - 字幕对齐

将字幕与音频进行精确对齐。

```bash
# 基本对齐
transcript align video.mp4 subtitle.srt

# 指定输出文件
transcript align video.mp4 subtitle.srt -o aligned.srt
```

### 🔧 fix - 字幕纠错

使用自定义词典对字幕进行纠错。

```bash
transcript fix subtitle.srt
```

**别名**: `correct`, `sub`

### 🔄 convert - 格式转换

繁体中文转简体中文。

```bash
transcript convert subtitle.srt
```

**别名**: `t2s`

### 🧪 test - 测试模型

测试模型是否正确加载。

```bash
transcript test
```

### 📊 status - 查看状态

查看当前处理状态和最近的工作目录。

```bash
transcript status
```

## 使用场景

### 场景1: 新手用户 - 一键处理

```bash
# 最简单的方式，适合新手
transcript process my_video.mp4 --auto
```

### 场景2: 需要编辑字幕

```bash
# 1. 生成字幕
transcript generate my_video.mp4

# 2. 手动编辑生成的 my_video.srt 文件
# 在需要删除的字幕前添加 [DEL] 标记

# 3. 继续处理
transcript edit
```

### 场景3: 批量处理

```bash
# 创建批处理脚本
#!/bin/bash
for video in *.mp4; do
    echo "处理: $video"
    transcript process "$video" --auto -o output/
done
```

### 场景4: 高级配置

```bash
# 交互式配置所有选项
transcript process my_video.mp4 --interactive
```

### 场景5: 只需要字幕对齐

```bash
# 如果你已经有字幕文件，只需要对齐
transcript align video.mp4 existing_subtitle.srt
```

## 输出文件

处理完成后会生成：

- `{name}-final.mp4` - 无字幕的最终视频
- `{name}-final-sub.mp4` - 带字幕的最终视频  
- `{name}-final.srt` - 对齐后的字幕文件

## 字幕编辑技巧

### 删除标记

在字幕行前添加 `[DEL]` 或 `[del]` 标记来删除该段：

```srt
1
00:00:01,000 --> 00:00:03,000
这段保留

2
00:00:03,000 --> 00:00:05,000
[DEL]这段删除

3
00:00:05,000 --> 00:00:07,000
这段也保留
```

### 自动删除

系统会自动删除单字的语助词：`好`、`呃`、`恩`、`嗯`

### 自定义词典

编辑项目根目录的 `words.md` 文件添加纠错规则：

```
错误词,正确词
宽体,匡醍
延报,研报
浮现,复现
```

## 常见问题

### Q: 如何查看帮助？

```bash
transcript --help
transcript process --help  # 查看特定命令的帮助
```

### Q: 如何指定输出目录？

```bash
transcript process video.mp4 -o /path/to/output/
```

### Q: 如何跳过手动编辑？

```bash
transcript process video.mp4 --auto
```

### Q: 如何添加片头片尾？

```bash
transcript process video.mp4 --opening intro.mp4 --ending outro.mp4
```

### Q: 如何查看当前处理状态？

```bash
transcript status
```

### Q: 模型加载失败怎么办？

```bash
# 测试模型
transcript test

# 如果失败，重新下载模型
python transcript/download_models.py
```

## 与原版对比

| 功能 | 原版命令 | 新CLI命令 |
|------|----------|-----------|
| 完整处理 | `python transcript.py process video.mp4` | `transcript process video.mp4` |
| 生成字幕 | `python transcript.py transcript video.mp4` | `transcript generate video.mp4` |
| 字幕对齐 | `python transcript.py align video.mp4 sub.srt out.srt` | `transcript align video.mp4 sub.srt -o out.srt` |
| 测试模型 | `python transcript.py test` | `transcript test` |

新CLI的优势：
- ✅ 更简洁的命令
- ✅ 更友好的错误信息
- ✅ 交互式配置选项
- ✅ 智能默认值
- ✅ 进度提示和状态查看
- ✅ 命令别名支持
