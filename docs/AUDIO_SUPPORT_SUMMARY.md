# 音频文件支持功能实现总结

## 概述

本次更新为transcript项目添加了完整的音频文件处理支持，使得项目不仅能处理视频文件，还能处理纯音频文件。用户现在可以：

1. 转录音频文件为字幕
2. 编辑字幕并使用[del]标记删除不需要的片段
3. 根据编辑后的字幕自动剪辑音频
4. 输出剪辑后的音频文件和同步的字幕文件

## 支持的文件格式

### 音频格式
- `.wav` - WAV音频文件
- `.mp3` - MP3音频文件
- `.m4a` - M4A音频文件
- `.flac` - FLAC无损音频文件
- `.aac` - AAC音频文件
- `.ogg` - OGG音频文件
- `.wma` - WMA音频文件

### 视频格式（原有支持）
- `.mp4`, `.avi`, `.mov`, `.mkv`, `.flv`, `.wmv`

## 主要功能变更

### 1. 文件类型检测
- 新增 `is_audio_file()` 函数：检测是否为音频文件
- 新增 `is_video_file()` 函数：检测是否为视频文件
- 修改 `transcript()` 函数：支持音频和视频文件的统一处理

### 2. 音频剪辑功能
- 新增 `cut_audio()` 函数：专门处理音频文件的剪辑
- 类似 `cut_video()` 但针对音频文件优化
- 保持原音频格式进行剪辑

### 3. 处理流程优化
- 修改 `cut()` 函数：根据文件类型自动选择音频或视频剪辑
- 修改 `merge()` 函数：支持音频文件的合并和输出
- 音频文件不支持片头片尾功能（因为这是视频特有的）

### 4. CLI接口更新
- 更新参数描述：支持"视频或音频文件"
- 优化输出信息：根据文件类型显示不同的结果
- 更新状态显示：兼容新的日志格式

## 使用方法

### 基本命令（与视频处理相同）

```bash
# 自动处理音频文件
transcript auto audio.wav

# 生成字幕
transcript gen audio.mp3

# 编辑字幕后继续处理
transcript resume

# 查看状态
transcript status
```

### 处理流程

1. **生成字幕**
   ```bash
   transcript gen my_audio.wav
   ```
   - 自动识别为音频文件
   - 直接转录音频（跳过视频提取步骤）
   - 生成 `my_audio.srt` 字幕文件

2. **编辑字幕**
   - 打开生成的 `.srt` 文件
   - 在不需要的字幕前添加 `[del]` 标记
   - 例如：`[del]这段话不需要`

3. **剪辑音频**
   ```bash
   transcript resume
   ```
   - 自动检测为音频处理
   - 根据[del]标记剪辑音频
   - 调整字幕时间戳

4. **输出结果**
   - `my_audio-final.wav` - 剪辑后的音频
   - `my_audio-final.srt` - 同步的字幕文件

## 技术实现细节

### 文件类型检测
```python
def is_audio_file(file_path: Path) -> bool:
    audio_extensions = {'.wav', '.mp3', '.m4a', '.flac', '.aac', '.ogg', '.wma'}
    return file_path.suffix.lower() in audio_extensions
```

### 音频剪辑
```python
def cut_audio(input_audio: Path, to_del: List[Tuple[int, int, int]], out_dir: Path):
    # 使用ffmpeg剪辑音频片段
    # 保持原音频格式
    # 生成片段列表文件
```

### 日志格式更新
```json
{
  "working_dir": "/tmp/transcript/audio_name",
  "name": "audio_name",
  "raw_file": "/path/to/audio.wav",
  "file_type": "audio",
  "timestamp": "2024-01-01T12:00:00"
}
```

## 与视频处理的区别

| 功能 | 视频文件 | 音频文件 |
|------|----------|----------|
| 转录 | 提取音频→转录 | 直接转录 |
| 剪辑 | 视频+音频剪辑 | 仅音频剪辑 |
| 片头片尾 | ✅ 支持 | ❌ 不支持 |
| 输出格式 | 带字幕视频+无字幕视频+字幕 | 剪辑音频+字幕 |
| 字幕烧录 | ✅ 支持 | ❌ 不适用 |

## 测试验证

创建了完整的测试套件：
- 文件类型检测测试
- 音频文件验证测试
- 函数导入测试
- 错误处理测试

所有测试均通过验证。

## 向后兼容性

- 完全兼容现有的视频处理功能
- CLI接口保持不变
- 日志格式向后兼容
- 现有脚本无需修改

## 示例演示

提供了 `demo_audio.py` 演示脚本，展示：
- 音频文件类型检测
- 处理流程说明
- 使用方法示例
- 输出文件说明

## 总结

本次更新成功实现了音频文件的完整支持，使transcript项目成为一个真正的多媒体字幕处理工具。用户现在可以处理纯音频内容，如播客、录音、音乐等，享受与视频处理相同的便利性和功能完整性。
