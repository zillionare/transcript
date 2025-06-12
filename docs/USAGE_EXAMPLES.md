# 使用示例

## 快速开始

### 1. 完整自动流程（推荐）

```bash
# 基本用法 - 处理单个视频文件
python transcript.py process /path/to/your/video.mp4

# 指定输出目录
python transcript.py process /path/to/your/video.mp4 --output_path /path/to/output/

# 添加片头片尾
python transcript.py process /path/to/your/video.mp4 \
    --opening_video /path/to/opening.mp4 \
    --ending_video /path/to/ending.mp4 \
    --output_path /path/to/output/

# 自动处理（跳过手动编辑步骤）
python transcript.py process /path/to/your/video.mp4 --auto_process True
```

### 2. 分步执行（高级用户）

```bash
# 步骤1: 生成字幕
python transcript.py transcript /path/to/your/video.mp4

# 步骤2: 手动编辑字幕文件
# 编辑生成的 .srt 文件，在需要删除的字幕前添加 [DEL] 标记

# 步骤3: 剪辑视频
python transcript.py cut

# 步骤4: 合并输出
python transcript.py merge
```

## 详细示例

### 示例1: 处理教学视频

```bash
# 处理一个教学视频，添加标准片头片尾
python transcript.py process /Users/teacher/videos/lesson01.mp4 \
    --opening_video /Users/teacher/assets/intro.mp4 \
    --ending_video /Users/teacher/assets/outro.mp4 \
    --output_path /Users/teacher/final_videos/
```

输出文件：
- `/Users/teacher/final_videos/lesson01-final.mp4` (无字幕版本)
- `/Users/teacher/final_videos/lesson01-final-sub.mp4` (带字幕版本)
- `/Users/teacher/final_videos/lesson01-final.srt` (字幕文件)

### 示例2: 批量处理多个视频

```bash
# 创建批处理脚本
#!/bin/bash
for video in /path/to/videos/*.mp4; do
    echo "处理: $video"
    python transcript.py process "$video" \
        --output_path /path/to/output/ \
        --auto_process True
done
```

### 示例3: 手动编辑字幕

```bash
# 1. 生成初始字幕
python transcript.py transcript /path/to/video.mp4

# 2. 编辑字幕文件 (例如: video.srt)
# 原始字幕内容:
```
1
00:00:01,000 --> 00:00:03,000
大家好，欢迎来到我的频道

2
00:00:03,000 --> 00:00:05,000
呃，今天我们来学习

3
00:00:05,000 --> 00:00:07,000
[DEL]这段话我想删除

4
00:00:07,000 --> 00:00:09,000
新的内容
```

```bash
# 3. 应用编辑
python transcript.py cut

# 4. 生成最终视频
python transcript.py merge --output_path /path/to/final/
```

### 示例4: 测试和调试

```bash
# 测试模型加载
python transcript.py test

# 测试字幕对齐功能
python transcript.py align /path/to/video.mp4 /path/to/original.srt /path/to/aligned.srt

# 仅进行字幕纠错
python transcript.py sub /path/to/subtitle.srt
```

## 字幕编辑技巧

### 删除标记

在字幕行前添加 `[DEL]` 或 `[del]` 标记：

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

### 自动删除的语助词

系统会自动删除单字的语助词：`好`、`呃`、`恩`、`嗯`

### 自定义词典

编辑 `words.md` 文件添加纠错规则：

```
错误词,正确词
宽体,匡醍
延报,研报
浮现,复现
量化24克,量化24课
2share,tushare
因子科,因子课
Pentas,pandas
```

## 输出文件说明

处理完成后会生成以下文件：

1. **{name}-final.mp4**: 无字幕的最终视频
2. **{name}-final-sub.mp4**: 带字幕的最终视频
3. **{name}-final.srt**: 对齐后的字幕文件

## 常见问题解决

### 1. 模型加载失败

```bash
# 下载对齐模型
python download_models.py

# 测试模型
python transcript.py test
```

### 2. 视频格式不支持

支持的格式：`.mp4`, `.avi`, `.mov`, `.mkv`, `.flv`, `.wmv`

转换不支持的格式：
```bash
ffmpeg -i input.webm -c:v libx264 -c:a aac output.mp4
```

### 3. 字幕对齐效果不佳

- 确保音频质量良好
- 检查字幕文本准确性
- 手动调整明显错误的字幕

### 4. 内存不足

对于大文件，可以先用视频编辑软件分割：

```bash
# 使用ffmpeg分割大文件
ffmpeg -i large_video.mp4 -c copy -map 0 -segment_time 00:30:00 -f segment part_%03d.mp4
```

## 性能优化

### Mac ARM优化

代码已针对Mac ARM架构优化：
- 自动检测ARM架构
- 使用CPU进行推理（避免GPU兼容性问题）
- 优化内存使用

### 批处理优化

```bash
# 并行处理多个文件
parallel -j 2 python transcript.py process {} --auto_process True ::: *.mp4
```

## 高级配置

### 环境变量

```bash
# 设置模型目录
export hf_model_dir="/custom/model/path"

# 启用离线模式
export TRANSFORMERS_OFFLINE=1
export HF_HUB_OFFLINE=1
```

### 自定义片头片尾

修改 `transcript.py` 中的默认路径：

```python
opening_video = Path("/your/custom/opening.mp4")
ending_video = Path("/your/custom/ending.mp4")
```

## 故障排除

### 日志查看

工作目录中的 `.log` 文件包含详细信息：

```bash
# 查看最近的工作日志
find /tmp/transcript -name ".log" -exec cat {} \;
```

### 清理临时文件

```bash
# 清理工作目录
rm -rf /tmp/transcript/*
```

### 重置环境

```bash
# 重新安装依赖
pip uninstall whisperx -y
pip install whisperx

# 重新下载模型
python download_models.py
```
