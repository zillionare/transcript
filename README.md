# Transcript - 视频字幕处理工具

一个用于自动生成、编辑和处理视频字幕的Python工具包，提供简洁的CLI接口。

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

