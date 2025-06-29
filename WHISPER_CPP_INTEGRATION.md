# Whisper.cpp 集成说明

本项目已成功集成 `whisper.cpp`，提供更快、更高效的音频转录功能。

## 🚀 主要优势

### whisper.cpp 相比 whisperx 的优势：
- ✅ **更快的转录速度**（特别是在 Apple Silicon 上）
- ✅ **更低的内存占用**
- ✅ **更好的 Apple Silicon 优化**
- ✅ **无需 Python 依赖，更稳定**
- ✅ **支持 GPU 加速（Metal）**

### 当前版本限制：
- ⚠️ **不支持 VAD（语音活动检测）功能**
- ⚠️ **说话人分离功能需要 tinydiarize 模型**
- 📝 **说话人分离功能默认关闭以提升转录速度**

## 📋 功能特性

### 1. 自动优化配置
- **Apple Silicon 优化**：根据 M1/M2/M3/M4 芯片自动调整线程数
- **GPU 加速**：自动检测并启用 Metal GPU 加速
- **Flash Attention**：支持更快的注意力计算

### 2. 智能回退机制
- 优先使用 `whisper.cpp` 进行基础转录
- 如果 `whisper.cpp` 不可用或转录失败，自动回退到 `whisperx`
- 如果启用说话人分离功能且有 tinydiarize 模型，使用 `whisper.cpp`
- 如果启用说话人分离功能但无 tinydiarize 模型，自动回退到 `whisperx`
- 保证转录任务的可靠性

### 3. 功能分工
- **whisper.cpp**：负责快速转录，支持 tinydiarize 模型的说话人分离
- **whisperx**：作为说话人分离的备选方案（速度较慢）
- 根据需求自动选择最适合的引擎

## 🛠️ 使用方法

### 基本使用
```bash
# 使用默认设置（优先使用 whisper.cpp）
transcript gen video.mp4

# 强制使用 whisperx
transcript gen video.mp4 --force-whisperx

# 启用说话人分离
transcript gen video.mp4 --enable-diarization
```

### 配置要求

确保以下路径和文件存在：
- `whisper.cpp` 可执行文件路径：`/Volumes/share/data/whisper.cpp/whisper-cli`
- 模型文件路径：`/Volumes/share/data/whisper.cpp/models/ggml-large-v3.bin`

### 支持的参数

#### whisper.cpp 支持的参数：
- `-l zh`：设置语言为中文
- `-sow`：按词分割
- `-ml 30`：最大行长度
- `-t N`：线程数（自动优化）
- `-osrt`：输出 SRT 格式
- `-ngl N`：GPU 层数设置（如果支持）
- `--flash-attn`：启用 Flash Attention（如果支持）
- `--prompt`：提示词设置

#### 说话人分离支持：
- `--tdrz`：说话人分离（需要 tinydiarize 模型，默认关闭）
- `--vad-*`：VAD 相关参数（当前版本不支持，已禁用）

## VAD (Voice Activity Detection) 支持

**当前状态**: whisper.cpp项目包含VAD功能代码和模型，但当前编译的whisper-cli版本不支持VAD参数。

### VAD功能说明
根据whisper.cpp官方文档，VAD功能可以：
- 检测语音活动段落，过滤静音部分
- 显著提升转录速度
- 使用Silero VAD模型进行语音检测

### 解决方案
1. **重新编译whisper.cpp**: 确保编译时启用VAD支持
2. **使用VAD示例程序**: whisper.cpp提供了`vad-speech-segments`示例
3. **外部VAD预处理**: 使用其他VAD工具预处理音频

### 当前实现
代码已实现VAD参数的自动检测和回退机制：
- 如果VAD参数不被支持，自动移除VAD参数重试
- 提供详细的错误信息和解决建议

## 🔧 技术实现

### 核心函数

1. **`get_whisper_cpp_optimal_config()`**
   - 检测 Apple Silicon 芯片型号
   - 自动优化线程数配置
   - 检测 GPU 和 Flash Attention 支持

2. **`check_whisper_cpp_diarization_support()`**
   - 检测 whisper.cpp 是否支持说话人分离
   - 动态调整功能可用性

3. **`transcript_cpp()`**
   - whisper.cpp 转录核心函数
   - 支持说话人分离和 VAD
   - 智能参数配置

### 自动回退逻辑

```python
if whisper_cpp_available and not force_whisperx:
    try:
        # 尝试使用 whisper.cpp
        transcript_cpp(...)
        if 转录成功:
            使用 whisper.cpp 结果
        else:
            回退到 whisperx
    except Exception:
        回退到 whisperx
else:
    # 直接使用 whisperx
    use_whisperx(...)
```

## 📊 性能对比

| 特性 | whisper.cpp | whisperx |
|------|-------------|----------|
| 转录速度 | ⚡ 更快 | 🐌 较慢 |
| 内存占用 | 💾 更低 | 📈 较高 |
| Apple Silicon 优化 | ✅ 原生支持 | ⚠️ 有限支持 |
| GPU 加速 | ✅ Metal | ✅ CUDA/Metal |
| 说话人分离 | ✅ 支持（需 tinydiarize 模型） | ✅ 完整支持 |
| VAD 功能 | ❌ 不支持 | ✅ 支持 |
| 词级时间戳 | ✅ 支持 | ✅ 支持 |
| Python 依赖 | ❌ 无需 | ✅ 需要 |

## 🐛 故障排除

### 常见问题

1. **whisper.cpp 不可用**
   - 检查 `/Volumes/share/data/whisper.cpp/whisper-cli` 是否存在
   - 检查模型文件是否存在
   - 系统会自动回退到 whisperx

2. **说话人分离失败**
- 缺少 tinydiarize 模型或模型不兼容
- 系统会自动回退到 whisperx 进行说话人分离

3. **转录速度慢**
   - 检查是否启用了 GPU 加速
   - 确认 Apple Silicon 优化是否生效
   - 考虑使用更小的模型

### 调试信息

运行时会显示详细的状态信息：
```
🚀 whisper.cpp优势:
   ✅ 更快的转录速度（特别是在Apple Silicon上）
   ✅ 更低的内存占用
   ...

🚀 使用GPU加速
⚡ 启用Flash Attention
🎭 启用说话人分离功能
```

## 🔄 版本兼容性

- **whisper.cpp**：支持最新版本
- **模型**：支持 ggml 格式模型
- **系统**：优化支持 macOS（Apple Silicon）
- **回退**：完全兼容原有 whisperx 功能

## 📝 更新日志

### v1.0.0
- ✅ 集成 whisper.cpp 支持
- ✅ 添加 Apple Silicon 优化
- ✅ 实现智能回退机制
- ✅ 支持说话人分离检测
- ✅ 添加 VAD 功能
- ✅ 新增命令行选项
- ✅ 完善错误处理

---

通过这次集成，项目现在可以充分利用 `whisper.cpp` 的性能优势，同时保持与原有 `whisperx` 功能的完全兼容性。用户可以根据需要选择最适合的转录引擎。