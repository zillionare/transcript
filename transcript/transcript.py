#! /Users/aaronyang/miniforge3/envs/coursea/bin/python

"""
todo: 

1. 在进行第一轮transcript之前，就对输入视频进行切分(a)，使得每一段不长于15分钟。将分割的文件保存到 /tmp/$working_dir/cuts
2. 对cuts里的每一个文件，进行transcript，然后等待人工校对
3. 人工校正的srt可能包含编辑指令，比如[del],和自动删除单行的『呃、恩、对，好』等，这样会生成一些小的碎片，通过ffmpeg进行剪辑、合并。这一步的结果保存到/tmp/$working_dir/reviewed
4. 将reviewed的文件、加入片头片尾，合并、压缩和保存
5. 将reviewed中的文件，烧入字幕，加片头片尾，合并、压缩和保存


其它：
1. 对1中产生的cuts，每处理一个，都要显示 正在处理 i/total 及 已完成

参考：
a: 这个命令能按关键帧分割： ffmpeg -i raw.mp4 -c copy -map 0 -segment_time 00:15:00 -f segment -break_non_keyframes 0 output%03d.mp4

"""

import datetime
import json
import os
import shlex
import shutil
import subprocess
import sys
import warnings
from multiprocessing.util import is_exiting
from pathlib import Path
from subprocess import PIPE, STDOUT, Popen
from typing import Any, List, Tuple

# fire已移除，使用CLI接口
import jieba
import opencc
import pysubs2

# from pywhispercpp.model import Model


warnings.filterwarnings("ignore")

import whisperx


def detect_optimal_device_config():
    """检测并配置最优的设备和计算类型（专为M1/M4优化）"""
    import platform
    import subprocess

    # 首先检查是否有环境变量覆盖
    env_device = os.environ.get('WHISPERX_DEVICE')
    env_compute_type = os.environ.get('WHISPERX_COMPUTE_TYPE')

    if env_device and env_compute_type:
        print(f"🔧 使用环境变量配置: device={env_device}, compute_type={env_compute_type}")
        return env_device, env_compute_type

    # 检测系统信息
    system = platform.system()
    machine = platform.machine()

    if system == "Darwin" and machine == "arm64":
        # Apple Silicon Mac - 专为M1/M4优化
        try:
            result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'],
                                  capture_output=True, text=True)
            cpu_info = result.stdout.strip()

            if "M1" in cpu_info:
                print("⚡ M1芯片：使用CPU优化配置（经实测验证最优）")
                device = "cpu"
                compute_type = "int8"
                # M1专用优化
                os.environ.setdefault('BLAS_VENDOR', 'Apple')
                os.environ.setdefault('LAPACK_VENDOR', 'Apple')
                os.environ.setdefault('VECLIB_MAXIMUM_THREADS', '8')
                os.environ.setdefault('WHISPERX_BATCH_SIZE', '8')
                os.environ.setdefault('WHISPERX_CHUNK_SIZE', '10')

            elif "M4" in cpu_info:
                print("🚀 M4芯片：使用MPS优化配置")
                device = "mps"
                compute_type = "float16"
                # M4专用优化
                os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK', '1')
                os.environ.setdefault('PYTORCH_MPS_HIGH_WATERMARK_RATIO', '0.0')
                os.environ.setdefault('WHISPERX_BATCH_SIZE', '16')
                os.environ.setdefault('WHISPERX_CHUNK_SIZE', '15')

                # 检查MPS可用性
                try:
                    import torch
                    if not torch.backends.mps.is_available():
                        print("⚠️ MPS不可用，回退到CPU配置")
                        device = "cpu"
                        compute_type = "int8"
                        os.environ['WHISPERX_BATCH_SIZE'] = '8'
                        os.environ['WHISPERX_CHUNK_SIZE'] = '10'
                except ImportError:
                    print("⚠️ PyTorch未安装，使用CPU配置")
                    device = "cpu"
                    compute_type = "int8"
                    os.environ['WHISPERX_BATCH_SIZE'] = '8'
                    os.environ['WHISPERX_CHUNK_SIZE'] = '10'
            else:
                # 默认M1配置
                device = "cpu"
                compute_type = "int8"
                os.environ.setdefault('WHISPERX_BATCH_SIZE', '8')
                os.environ.setdefault('WHISPERX_CHUNK_SIZE', '10')

        except Exception:
            # 默认配置
            device = "cpu"
            compute_type = "int8"
            os.environ.setdefault('WHISPERX_BATCH_SIZE', '8')
            os.environ.setdefault('WHISPERX_CHUNK_SIZE', '10')

        # 通用Apple优化
        os.environ.setdefault('OMP_NUM_THREADS', '8')
        os.environ.setdefault('MKL_NUM_THREADS', '8')

    else:
        # 非Apple Silicon系统
        device = "cpu"
        compute_type = "int8"
        os.environ.setdefault('WHISPERX_BATCH_SIZE', '8')
        os.environ.setdefault('WHISPERX_CHUNK_SIZE', '10')

    return device, compute_type


# 在模块加载时检测最优配置
optimal_device, optimal_compute_type = detect_optimal_device_config()

prompt = ",".join(["大家好，我们开始上课了。请输出简体中文。"])

opening_video = Path("/Volumes/share/data/autobackup/ke/factor-ml/opening.mp4")
ending_video = Path("/Volumes/share/data/autobackup/ke/factor-ml/end.mp4")

cpp_path = Path("/Volumes/share/data/whisper.cpp")
cpp_model = Path("/Volumes/share/data/whisper.cpp/models/ggml-large-v2.bin")
# 设置本地模型目录，如果环境变量未设置则使用默认路径
model_dir = os.environ.get("hf_model_dir", "/Volumes/share/data/models/huggingface/hub")

# 设置whisperx模型名称
whisperx_model = "large-v2"  # 支持中文的whisper模型
w2v_model = "jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn"  # 中文对齐模型

def align_subtitles_with_audio(video: Path, original_srt: Path, aligned_srt: Path):
    """
    使用 whisperx 对齐字幕文件与音频。
    这是确保剪辑后视频与字幕同步的关键步骤。

    Args:
        video: 合并后的视频文件路径
        original_srt: 原始字幕文件路径
        aligned_srt: 对齐后的字幕文件路径
    """
    print(f"开始字幕对齐: {original_srt} -> {aligned_srt}")

    try:
        # 验证输入文件
        if not Path(video).exists():
            raise FileNotFoundError(f"视频文件不存在: {video}")
        if not Path(original_srt).exists():
            raise FileNotFoundError(f"字幕文件不存在: {original_srt}")

        # 提取音频
        audio_path = Path(video).with_suffix(".wav")
        if not audio_path.exists():
            print("提取音频文件...")
            extract_audio(video, audio_path)

        # 设置设备 - Mac ARM优化
        import platform
        if platform.system() == "Darwin" and platform.machine() == "arm64":
            # Mac ARM架构，使用CPU
            device = "cpu"
            print("检测到Mac ARM架构，使用CPU进行对齐")
        else:
            device = "cpu"  # 保持兼容性

        print("加载音频...")
        audio = whisperx.load_audio(str(audio_path))

        # 加载字幕文件
        print("加载字幕文件...")
        subs = pysubs2.load(str(original_srt))

        if not subs.events:
            print("警告: 字幕文件为空")
            shutil.copy2(original_srt, aligned_srt)
            return

        segments = []
        for i, event in enumerate(subs.events):
            if event.text.strip():  # 跳过空字幕
                segments.append({
                    "start": event.start / 1000,
                    "end": event.end / 1000,
                    "text": event.text.strip(),
                    "id": i
                })

        if not segments:
            print("警告: 没有有效的字幕段落")
            shutil.copy2(original_srt, aligned_srt)
            return

        # 设置离线模式环境变量
        import os
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HUB_OFFLINE"] = "1"

        # 加载对齐模型
        print("加载对齐模型...")
        model_name = None

        # 尝试使用本地路径
        local_model_path = Path(model_dir) / "models--jonatasgrosman--wav2vec2-large-xlsr-53-chinese-zh-cn"
        if local_model_path.exists():
            snapshots_dir = local_model_path / "snapshots"
            if snapshots_dir.exists():
                snapshot_dirs = [d for d in snapshots_dir.iterdir() if d.is_dir()]
                if snapshot_dirs:
                    latest_snapshot = max(snapshot_dirs, key=lambda x: x.stat().st_mtime)
                    print(f"使用本地模型: {latest_snapshot}")
                    model_name = str(latest_snapshot)

        if model_name is None:
            model_name = w2v_model
            print(f"使用默认模型名称: {model_name}")

        try:
            model_a, metadata = whisperx.load_align_model(
                language_code="zh",
                device=device,
                model_name=model_name,
                model_dir=model_dir
            )
            print("对齐模型加载成功，开始对齐...")
        except Exception as model_error:
            print(f"模型加载失败: {model_error}")
            raise

        # 执行对齐
        print(f"对齐 {len(segments)} 个字幕段落...")
        aligned_result = whisperx.align(segments, model_a, metadata, audio, device)

        if "segments" not in aligned_result or not aligned_result["segments"]:
            print("警告: 对齐结果为空")
            shutil.copy2(original_srt, aligned_srt)
            return

        # 创建对齐后的字幕
        aligned_subs = pysubs2.SSAFile()

        for i, segment in enumerate(aligned_result["segments"]):
            if "start" in segment and "end" in segment and "text" in segment:
                event = pysubs2.SSAEvent()
                event.start = int(segment["start"] * 1000)  # 转换为毫秒
                event.end = int(segment["end"] * 1000)
                event.text = segment["text"]

                # 确保时间戳合理
                if event.end <= event.start:
                    event.end = event.start + 1000  # 至少1秒

                # 避免重叠
                if i > 0 and event.start < aligned_subs.events[-1].end:
                    event.start = aligned_subs.events[-1].end + 100
                    if event.end <= event.start:
                        event.end = event.start + 1000

                aligned_subs.events.append(event)

        # 保存对齐后的字幕文件
        aligned_subs.save(str(aligned_srt))
        print(f"✅ 字幕对齐完成: {len(aligned_subs.events)} 个段落")
        print(f"对齐结果保存到: {aligned_srt}")

    except Exception as e:
        print(f"❌ 字幕对齐失败: {e}")
        print("使用原始字幕文件作为备选方案...")

        # 直接复制原始字幕文件
        shutil.copy2(original_srt, aligned_srt)
        print(f"已复制原始字幕到: {aligned_srt}")
        print("💡 提示: 要使用字幕对齐功能，请确保:")
        print("   1. 运行 'python download_models.py' 下载对齐模型")
        print("   2. 检查模型文件是否完整")
        print("   3. 确保网络连接正常（首次下载时）")


def execute(cmd, dry_run=False, supress_log=False, msg: str = ""):
    start = datetime.datetime.now()
    if not supress_log:
        print(f">>> {msg} {cmd}")

    if dry_run:
        return

    if isinstance(cmd, str):
        args = shlex.split(cmd)
    else:
        args = cmd
    with Popen(args, stdout=PIPE, stderr=STDOUT, text=True) as proc:
        for line in proc.stdout:  # type: ignore
            print(line)

    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg Error {proc.returncode}: {proc.stderr}")

    if not supress_log:
        cost(start, prefix=f"<<< {msg} Done ")


def _ms_to_hms(ms: int):
    ms_ = ms / 1000
    h = int(ms_ // 3600)
    m = int((ms_ - h * 3600) // 60)
    s = int((ms_ - h * 3600 - m * 60))

    return f"{h:02d}:{m:02d}:{s:02d}.{ms % 1000:03d}"


def transcript_cpp(input_audio: Path, output_srt: Path, prompt: str, dry_run=False, enable_diarization=False):
    """使用whisper.cpp进行音频转录，支持简单说话人分离

    Args:
        input_audio: 输入音频文件路径
        output_srt: 输出字幕文件路径
        prompt: 转录提示词
        dry_run: 是否为试运行模式
        enable_diarization: 是否启用说话人分离功能
    """
    print(f"使用whisper.cpp转录音频: {input_audio} -> {output_srt}")
    if enable_diarization:
        print("🎭 启用简单说话人分离功能")

    if dry_run:
        print("试运行模式，跳过实际转录")
        return

    whisper = os.path.join(cpp_path, "whisper-cli")
    cmd = f"{whisper} {input_audio} -l zh -sow -ml 30 -t 8 -m {cpp_model} -osrt -of {output_srt.with_suffix('')} --prompt '{prompt}'"

    try:
        execute(cmd)

        # 检查字幕文件是否生成成功
        if output_srt.exists():
            print(f"✅ 字幕文件生成成功: {output_srt}")

            # 如果启用说话人分离，处理字幕
            if enable_diarization:
                try:
                    print("🔄 添加说话人分离标签...")
                    add_speaker_labels_to_srt(output_srt)
                    print("✅ 说话人分离标签添加完成")
                except Exception as diarize_error:
                    print(f"⚠️ 说话人分离处理失败: {diarize_error}")
                    print("保留原始字幕文件")
        else:
            raise FileNotFoundError(f"whisper.cpp未生成字幕文件: {output_srt}")

    except Exception as e:
        print(f"❌ whisper.cpp转录失败: {e}")
        raise


def add_speaker_labels_to_srt(srt_file: Path):
    """为现有SRT文件添加简单的说话人标签"""
    subs = pysubs2.load(str(srt_file))

    if not subs.events:
        return

    # 简单的说话人分离策略
    current_speaker = "SPEAKER_A"
    speaker_count = 0
    last_end_time = 0

    # 说话人名称映射
    speaker_names = {
        "SPEAKER_A": "说话人A",
        "SPEAKER_B": "说话人B",
        "SPEAKER_C": "说话人C",
        "SPEAKER_D": "说话人D",
    }

    speaker_stats = {}

    for event in subs.events:
        start_time_sec = event.start / 1000.0

        # 如果间隔超过2秒，可能是说话人切换
        if start_time_sec - last_end_time > 2.0:
            speaker_count = (speaker_count + 1) % 2  # 在两个主要说话人之间切换
            current_speaker = f"SPEAKER_{chr(65 + speaker_count)}"  # A, B, C, D...

        # 统计说话人
        if current_speaker not in speaker_stats:
            speaker_stats[current_speaker] = 0
        speaker_stats[current_speaker] += 1

        # 添加说话人标签
        speaker_name = speaker_names.get(current_speaker, current_speaker)
        if not event.text.startswith('['):  # 避免重复添加标签
            event.text = f"[{speaker_name}] {event.text}"

        last_end_time = event.end / 1000.0

    # 保存修改后的字幕
    subs.save(str(srt_file))

    # 输出统计信息
    print(f"\n🎭 说话人分离统计:")
    for speaker, count in speaker_stats.items():
        speaker_name = speaker_names.get(speaker, speaker)
        print(f"   {speaker_name}: {count} 个片段")

    return subs


def init_jieba():
    """
    初始化jieba分词器并加载自定义词典

    Returns:
        tuple: (replace_map, warning_words) - 替换词典和警告词列表
    """
    import yaml

    replace_map = {}
    warning_words = []

    # 尝试加载YAML格式的字典文件
    dict_path = Path(__file__).parent.parent / "dict.yaml"

    if dict_path.exists():
        try:
            with open(dict_path, "r", encoding="utf-8") as f:
                dict_data = yaml.safe_load(f)

            # 加载替换词典
            if "replace" in dict_data and dict_data["replace"]:
                replace_map = dict_data["replace"]
                print(f"📚 加载替换词典: {len(replace_map)} 个词汇")

            # 加载警告词列表
            if "warning" in dict_data and dict_data["warning"]:
                warning_words = dict_data["warning"]
                print(f"⚠️  加载警告词列表: {len(warning_words)} 个词汇")

        except Exception as e:
            print(f"❌ 加载YAML字典失败: {e}")
            print("尝试加载旧格式字典...")

            # 回退到旧格式
            old_dict_path = Path(__file__).parent.parent / "words.md"
            if old_dict_path.exists():
                with open(old_dict_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("#") or len(line) == 0:
                            continue
                        parts = line.split(",")
                        if len(parts) >= 2:
                            wrong, right = parts[0], parts[1]
                            replace_map[wrong] = right
                print(f"📚 从旧格式加载: {len(replace_map)} 个词汇")
    else:
        print(f"⚠️  字典文件不存在: {dict_path}")

    # 将所有词汇添加到jieba词典
    for word in replace_map.keys():
        jieba.add_word(word)

    for word in warning_words:
        jieba.add_word(word)

    return replace_map, warning_words


def transcriptx(input_audio: Path, output_srt: Path, prompt: str):
    """使用whisperx进行音频转录，支持Apple Silicon优化"""
    print(f"使用whisperx转录音频: {input_audio} -> {output_srt}")

    # 使用检测到的最优配置
    device = optimal_device
    compute_type = optimal_compute_type

    print(f"🎯 使用设备配置: {device} (compute_type: {compute_type})")

    try:
        options = {"initial_prompt": prompt}
        print("加载whisperx模型...")
        try:
            # 使用环境变量设置的缓存目录
            download_root = os.environ.get('HF_HOME', None)
            local_files_only = os.environ.get('HF_HUB_OFFLINE', '0') == '1'

            print(f"🔧 模型缓存目录: {download_root}")
            print(f"🔧 离线模式: {local_files_only}")

            model = whisperx.load_model(
                whisperx_model,
                device=device,
                compute_type=compute_type,
                asr_options=options,
                language="zh",
                threads=8,
                download_root=download_root,
                local_files_only=local_files_only
            )
        except Exception as model_error:
            print(f"⚠️ 加载whisperx模型失败: {model_error}")
            print("尝试使用本地模型或降级模型...")
            # 尝试使用更简单的模型
            try:
                model = whisperx.load_model(
                    "base",  # 使用基础模型
                    device=device,
                    compute_type=compute_type,
                    asr_options=options,
                    language="zh",
                    threads=8,
                    local_files_only=False
                )
                print("✅ 成功加载基础模型")
            except Exception as fallback_error:
                print(f"❌ 基础模型也加载失败: {fallback_error}")
                raise model_error

        print("加载音频文件...")
        audio = whisperx.load_audio(str(input_audio))

        print("开始转录...")

        # 从环境变量获取批处理配置
        batch_size = int(os.environ.get('WHISPERX_BATCH_SIZE', '8'))
        chunk_size = int(os.environ.get('WHISPERX_CHUNK_SIZE', '10'))

        print(f"🔧 转录参数: batch_size={batch_size}, chunk_size={chunk_size}")

        result = model.transcribe(
            audio, language="zh", print_progress=True,
            batch_size=batch_size, chunk_size=chunk_size
        )

        if "segments" not in result or not result["segments"]:
            print("⚠️ 转录结果为空，创建空字幕文件")
            # 创建一个空的字幕文件
            empty_subs = pysubs2.SSAFile()
            empty_subs.save(str(output_srt))
        else:
            print(f"转录完成，共 {len(result['segments'])} 个片段")
            subs = pysubs2.load_from_whisper(result["segments"])
            subs.save(str(output_srt))
            print(f"字幕文件已保存: {output_srt}")

    except Exception as e:
        print(f"❌ whisperx转录失败: {e}")
        # 创建一个空的字幕文件以避免后续错误
        print("创建空字幕文件以避免后续错误...")
        empty_subs = pysubs2.SSAFile()
        empty_subs.save(str(output_srt))
        raise
    # 2. Align whisper output
    # model_a, metadata = whisperx.load_align_model(
    #     language_code=result["language"], device=device, model_name = w2v_model
    # )
    # result = whisperx.align(
    #     result["segments"],
    #     model_a,
    #     metadata,
    #     audio,
    #     device,
    #     return_char_alignments=False,
    # )

    # print(result["segments"])  # after alignment


def transcriptx_with_diarization(input_audio: Path, output_srt: Path, prompt: str):
    """使用whisperx进行音频转录，支持说话人分离和Apple Silicon优化"""
    print(f"使用whisperx转录音频（含说话人分离）: {input_audio} -> {output_srt}")
    print("🎭 启用说话人分离功能")

    # 使用检测到的最优配置
    device = optimal_device
    compute_type = optimal_compute_type

    print(f"🎯 使用设备配置: {device} (compute_type: {compute_type})")

    try:
        options = {"initial_prompt": prompt}
        print("加载whisperx模型...")
        try:
            # 使用环境变量设置的缓存目录
            download_root = os.environ.get('HF_HOME', None)
            local_files_only = os.environ.get('HF_HUB_OFFLINE', '0') == '1'

            print(f"🔧 模型缓存目录: {download_root}")
            print(f"🔧 离线模式: {local_files_only}")

            model = whisperx.load_model(
                whisperx_model,
                device=device,
                compute_type=compute_type,
                asr_options=options,
                language="zh",
                threads=8,
                download_root=download_root,
                local_files_only=local_files_only
            )
        except Exception as model_error:
            print(f"⚠️ 加载whisperx模型失败: {model_error}")
            print("尝试使用本地模型或降级模型...")
            # 尝试使用更简单的模型
            try:
                model = whisperx.load_model(
                    "base",  # 使用基础模型
                    device=device,
                    compute_type=compute_type,
                    asr_options=options,
                    language="zh",
                    threads=8,
                    local_files_only=False
                )
                print("✅ 成功加载基础模型")
            except Exception as fallback_error:
                print(f"❌ 基础模型也加载失败: {fallback_error}")
                raise model_error

        print("加载音频文件...")
        audio = whisperx.load_audio(str(input_audio))

        print("开始转录...")

        # 从环境变量获取批处理配置
        batch_size = int(os.environ.get('WHISPERX_BATCH_SIZE', '8'))
        chunk_size = int(os.environ.get('WHISPERX_CHUNK_SIZE', '10'))

        print(f"🔧 转录参数: batch_size={batch_size}, chunk_size={chunk_size}")

        result = model.transcribe(
            audio, language="zh", print_progress=True,
            batch_size=batch_size, chunk_size=chunk_size
        )

        if "segments" not in result or not result["segments"]:
            print("⚠️ 转录结果为空，创建空字幕文件")
            empty_subs = pysubs2.SSAFile()
            empty_subs.save(str(output_srt))
            return

        print(f"转录完成，共 {len(result['segments'])} 个片段")

        try:
            print("🔄 开始说话人分离...")

            # 2. 对齐模型（提高时间戳精度）
            print("加载对齐模型...")
            # 使用环境变量设置
            model_dir = os.environ.get('HF_HOME', None)

            model_a, metadata = whisperx.load_align_model(
                language_code=result["language"],
                device=device,
                model_dir=model_dir
            )

            print("对齐转录结果...")
            result = whisperx.align(
                result["segments"],
                model_a,
                metadata,
                audio,
                device,
                return_char_alignments=False,
            )

            # 3. 说话人分离
            print("加载说话人分离模型...")
            try:
                # 使用pyannote.audio进行说话人分离
                from pyannote.audio import Pipeline

                # 加载说话人分离模型
                diarize_model = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=None
                )

                print("执行说话人分离...")
                diarize_segments = diarize_model(str(input_audio))

                print("分配说话人标签...")
                result = whisperx.assign_word_speakers(diarize_segments, result)

                # 统计说话人数量
                speakers = set()
                for seg in result['segments']:
                    if 'speaker' in seg:
                        speakers.add(seg['speaker'])

                print(f"✅ 说话人分离完成，检测到 {len(speakers)} 个说话人: {', '.join(speakers)}")

            except ImportError as import_error:
                print(f"❌ 缺少pyannote.audio依赖: {import_error}")
                print("请安装说话人分离依赖:")
                print("pip install pyannote.audio")
                raise Exception("说话人分离需要安装pyannote.audio")

            except Exception as diarize_error:
                print(f"❌ 说话人分离失败: {diarize_error}")
                print("可能的原因:")
                print("1. 网络连接问题，无法下载模型")
                print("2. 音频文件格式不支持")
                print("3. 内存不足")
                raise

            print(f"✅ 说话人分离完成")

            # 生成带说话人标签的字幕
            subs = create_speaker_subtitles(result["segments"])

        except Exception as diarize_error:
            print(f"⚠️ 说话人分离失败: {diarize_error}")
            print("回退到普通转录模式...")
            subs = pysubs2.load_from_whisper(result["segments"])

        subs.save(str(output_srt))
        print(f"字幕文件已保存: {output_srt}")

    except Exception as e:
        print(f"❌ whisperx转录失败: {e}")
        # 创建一个空的字幕文件以避免后续错误
        print("创建空字幕文件以避免后续错误...")
        empty_subs = pysubs2.SSAFile()
        empty_subs.save(str(output_srt))
        raise


def simple_speaker_separation(segments):
    """简单的说话人分离，基于音频间隔和音量变化"""
    if not segments:
        return segments

    # 简单策略：根据时间间隔判断说话人切换
    current_speaker = "SPEAKER_00"
    speaker_count = 0
    last_end_time = 0

    for i, segment in enumerate(segments):
        start_time = segment["start"]

        # 如果间隔超过2秒，可能是说话人切换
        if start_time - last_end_time > 2.0:
            speaker_count = (speaker_count + 1) % 2  # 在两个说话人之间切换
            current_speaker = f"SPEAKER_0{speaker_count}"

        segment["speaker"] = current_speaker
        last_end_time = segment["end"]

    return segments


def create_speaker_subtitles(segments):
    """根据说话人分离结果创建带说话人标签的字幕"""
    subs = pysubs2.SSAFile()

    # 说话人颜色映射
    speaker_colors = {
        'SPEAKER_00': '&H00FF0000',  # 蓝色
        'SPEAKER_01': '&H0000FF00',  # 绿色
        'SPEAKER_02': '&H000000FF',  # 红色
        'SPEAKER_03': '&H00FF00FF',  # 紫色
        'SPEAKER_04': '&H0000FFFF',  # 黄色
        'SPEAKER_05': '&H00FFFF00',  # 青色
    }

    # 说话人中文名称映射
    speaker_names = {
        'SPEAKER_00': '说话人A',
        'SPEAKER_01': '说话人B',
        'SPEAKER_02': '说话人C',
        'SPEAKER_03': '说话人D',
        'SPEAKER_04': '说话人E',
        'SPEAKER_05': '说话人F',
    }

    # 统计说话人出现次数
    speaker_stats = {}

    for segment in segments:
        start_ms = int(segment["start"] * 1000)
        end_ms = int(segment["end"] * 1000)
        text = segment["text"].strip()

        # 获取说话人信息
        speaker = segment.get("speaker", "UNKNOWN")
        speaker_name = speaker_names.get(speaker, f"说话人{speaker}")

        # 统计说话人
        if speaker not in speaker_stats:
            speaker_stats[speaker] = 0
        speaker_stats[speaker] += 1

        # 创建字幕事件
        event = pysubs2.SSAEvent(
            start=start_ms,
            end=end_ms,
            text=f"[{speaker_name}] {text}"
        )

        # 设置说话人样式
        event.style = speaker if speaker in speaker_colors else "Default"

        subs.events.append(event)

    # 添加说话人样式定义
    for speaker, color in speaker_colors.items():
        if speaker in speaker_names:
            style = pysubs2.SSAStyle()
            style.fontsize = 20
            style.bold = True
            # 注意：pysubs2的颜色格式可能不同，这里简化处理
            subs.styles[speaker] = style

    # 输出说话人统计信息
    print(f"\n🎭 说话人分离统计:")
    for speaker, count in speaker_stats.items():
        speaker_name = speaker_names.get(speaker, f"说话人{speaker}")
        print(f"   {speaker_name}: {count} 个片段")

    return subs


def extract_audio(input_video: Path, output_wav: Path):
    cmd = (
        f"ffmpeg -i {input_video} -vn -acodec pcm_s16le -ar 16000 -ac 2 -y {output_wav} -v error"
    )
    execute(cmd)


def cost(start, cmd: str = "", prefix=""):
    end = datetime.datetime.now()
    elapsed = (end - start).total_seconds()
    mins = elapsed // 60
    seconds = elapsed % 60
    print(
        f"{prefix}{end.hour:02d}:{end.minute:02d}:{end.second:02d} {cmd}用时{mins}分{seconds:.0f}秒"
    )


def is_audio_file(file_path: Path) -> bool:
    """检测是否为音频文件"""
    audio_extensions = {'.wav', '.mp3', '.m4a', '.flac', '.aac', '.ogg', '.wma'}
    return file_path.suffix.lower() in audio_extensions


def is_video_file(file_path: Path) -> bool:
    """检测是否为视频文件"""
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'}
    return file_path.suffix.lower() in video_extensions


def transcript(input_file: Path, output_dir: Path = None, dry_run=False, enable_diarization=False):
    """
    将视频或音频文件转换为字幕文件

    Args:
        input_file: 输入视频或音频文件路径
        output_dir: 输出目录，如果为None则将srt文件保存到项目根目录
        dry_run: 是否为试运行模式
        enable_diarization: 是否启用说话人分离功能
    """
    input_file = Path(input_file)

    # 验证输入文件存在
    if not input_file.exists():
        raise FileNotFoundError(f"输入文件不存在: {input_file}")

    # 验证文件格式
    is_audio = is_audio_file(input_file)
    is_video = is_video_file(input_file)

    if not (is_audio or is_video):
        raise ValueError(f"不支持的文件格式: {input_file.suffix}。支持的格式：视频(.mp4, .avi, .mov, .mkv, .flv, .wmv)，音频(.wav, .mp3, .m4a, .flac, .aac, .ogg, .wma)")

    # 使用文件名（不含扩展名）作为项目名称
    name = input_file.stem

    # 设置工作目录（用于临时文件）
    working_dir = Path("/tmp/transcript") / name

    # 设置最终srt文件的输出目录
    if output_dir is None:
        # 获取项目根目录（transcript.py所在目录的上级目录）
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        final_output_dir = project_root
    else:
        final_output_dir = Path(output_dir)

    working_dir.mkdir(parents=True, exist_ok=True)

    # 保存工作日志
    log_file = "/tmp/transcript.log"
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump({
            "working_dir": str(working_dir),
            "name": name,
            "raw_file": str(input_file),
            "file_type": "audio" if is_audio else "video",
            "timestamp": datetime.datetime.now().isoformat()
            }, f, indent=2)

    # 复制文件到工作目录
    media_file = working_dir / input_file.name
    if not media_file.exists():
        print(f"复制{'音频' if is_audio else '视频'}文件到工作目录: {input_file} -> {media_file}")
        shutil.copy(input_file, media_file)

    # 设置临时srt文件路径（在工作目录中）
    temp_srt = working_dir / f"{name}.srt"

    # 设置最终srt文件路径（在项目根目录中）
    final_srt = final_output_dir / f"{name}.srt"

    print(f"开始转换{'音频' if is_audio else '视频'}为字幕: {input_file} -> {final_srt}")

    # 处理音频
    start = datetime.datetime.now()
    print(f"{start.hour:02d}:{start.minute:02d}:{start.second:02d}: 开始处理")

    if is_audio:
        # 对于音频文件，需要确保格式为16kHz WAV
        output_wav = media_file.with_suffix(".wav")
        if not output_wav.exists():
            print("转换音频格式为16kHz WAV...")
            # 强制转换为16kHz采样率，这是whisper.cpp的要求
            cmd = f"ffmpeg -i '{media_file}' -acodec pcm_s16le -ar 16000 -ac 1 -y '{output_wav}' -v error"
            execute(cmd)
        else:
            # 即使是WAV文件，也需要检查采样率
            print("检查并转换音频采样率为16kHz...")
            temp_wav = output_wav.parent / f"{output_wav.stem}_temp.wav"
            cmd = f"ffmpeg -i '{output_wav}' -acodec pcm_s16le -ar 16000 -ac 1 -y '{temp_wav}' -v error"
            execute(cmd)
            # 替换原文件
            import os
            os.replace(temp_wav, output_wav)
    else:
        # 对于视频文件，提取音频
        output_wav = media_file.with_suffix(".wav")
        if not output_wav.exists():
            print("提取音频...")
            extract_audio(media_file, output_wav)

    # 生成字幕到临时位置
    print("生成字幕...")

    # 检查whisper.cpp是否可用，如果不可用则使用whisperx
    whisper_cpp_available = cpp_path.exists() and cpp_model.exists()

    if enable_diarization:
        # 说话人分离必须使用whisperx，不使用whisper.cpp
        print("🎭 说话人分离功能需要使用whisperx...")
        transcriptx_with_diarization(output_wav, temp_srt, prompt)
    elif whisper_cpp_available and not dry_run:
        try:
            transcript_cpp(output_wav, temp_srt, prompt, dry_run)
        except Exception as e:
            print(f"⚠️ whisper.cpp转录失败: {e}")
            print("回退到whisperx转录...")
            transcriptx(output_wav, temp_srt, prompt)
    else:
        if not whisper_cpp_available:
            print("⚠️ whisper.cpp不可用，使用whisperx转录...")
        transcriptx(output_wav, temp_srt, prompt)

    # 检查字幕文件是否生成成功
    if not temp_srt.exists():
        raise FileNotFoundError(f"字幕生成失败，文件不存在: {temp_srt}")

    print(f"✅ 字幕文件生成成功: {temp_srt}")

    # 应用自定义词典纠错
    print("应用词典纠错...")
    sub(temp_srt)

    # 复制字幕文件到项目根目录
    print(f"复制字幕文件到项目根目录: {temp_srt} -> {final_srt}")
    shutil.copy2(temp_srt, final_srt)

    cost(start, prefix="字幕生成完成 ")
    print(f"字幕文件已保存到: {final_srt}")
    print(f"工作目录: {working_dir}")

    return final_srt


def probe_duration(video):
    """returns duration of a video in seconds"""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        video,
    ]
    duration = float(subprocess.check_output(cmd).strip())
    return duration


def cut_video(input_video: Path, to_del: List[Tuple[int, int, int]], out_dir: Path):
    """根据slices剪去视频片段

    ffmpeg -hide_banner -ss '60.08300' -i '/private/tmp/fa.mp4' -t '178.00000' -avoid_negative_ts make_zero -map '0:0' '-c:0' copy -map '0:1' '-c:1' copy -map_metadata 0 -movflags '+faststart' -default_mode infer_no_subs -ignore_unknown -f mp4 -y '/private/tmp/fa-00.01.00.083-00.03.58.083-seg2.mp4'
    """
    duration = probe_duration(input_video) * 1000

    edges = [item for sublist in to_del for item in sublist[1:]]
    edges.insert(0, 0)
    edges.append(int(duration))

    if edges[:2] == [0, 0]:
        edges = edges[2:]

    slices = [(edges[i], edges[i + 1]) for i in range(0, len(edges) - 1, 2)]

    tmp_files = []

    for i, (start, end) in enumerate(slices):
        start_time = _ms_to_hms(start)
        end_time = _ms_to_hms(end)
        start_secs = f"{start/1000:.3f}"
        dur = f"'{(end - start)/1000:.3f}'"

        tmp_file = os.path.join(out_dir, f"{i}-{start_time}-{end_time}.mp4")
        tmp_files.append(tmp_file)
        cmd = f"ffmpeg -hide_banner -ss '{start_secs}' -i '{input_video}' -t '{dur}' -c copy -map 0:v -map 0:a -map_metadata 0 -movflags '+faststart' -f mp4 -video_track_timescale 600 -y -v error '{tmp_file}'"

        execute(cmd, supress_log=True)

    list_file = os.path.join(out_dir, "list.text")
    with open(list_file, "w", encoding="utf-8") as f:
        for video in tmp_files:
            f.write(f"file '{video}'\n")

    return list_file


def cut_audio(input_audio: Path, to_del: List[Tuple[int, int, int]], out_dir: Path):
    """根据slices剪去音频片段

    类似cut_video但处理音频文件
    """
    duration = probe_duration(input_audio) * 1000

    edges = [item for sublist in to_del for item in sublist[1:]]
    edges.insert(0, 0)
    edges.append(int(duration))

    if edges[:2] == [0, 0]:
        edges = edges[2:]

    slices = [(edges[i], edges[i + 1]) for i in range(0, len(edges) - 1, 2)]

    tmp_files = []

    for i, (start, end) in enumerate(slices):
        start_time = _ms_to_hms(start)
        end_time = _ms_to_hms(end)
        start_secs = f"{start/1000:.3f}"
        dur = f"'{(end - start)/1000:.3f}'"

        # 保持原音频格式
        audio_ext = input_audio.suffix
        tmp_file = os.path.join(out_dir, f"{i}-{start_time}-{end_time}{audio_ext}")
        tmp_files.append(tmp_file)

        # 音频剪辑命令，不需要视频相关参数
        cmd = f"ffmpeg -hide_banner -ss '{start_secs}' -i '{input_audio}' -t '{dur}' -c copy -y -v error '{tmp_file}'"

        execute(cmd, supress_log=True)

    list_file = os.path.join(out_dir, "list.text")
    with open(list_file, "w", encoding="utf-8") as f:
        for audio in tmp_files:
            f.write(f"file '{audio}'\n")

    return list_file


def sub(srt_file: Path):
    """输入字幕文件，通过自定义词典，先粗筛一次。在transcript之后被自动调用。

    Args:
        srt_file (str): _description_
    """
    try:
        subs = pysubs2.load(str(srt_file))
    except Exception as e:
        print(f"⚠️ 加载字幕文件失败: {e}")
        # 检查文件是否为空或格式不正确
        if srt_file.exists():
            with open(srt_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            if not content:
                print("字幕文件为空，创建空的字幕对象")
                subs = pysubs2.SSAFile()
                # 保存空字幕文件以确保格式正确
                subs.save(str(srt_file))
                return  # 空文件无需进一步处理
            else:
                print(f"字幕文件内容: {content[:200]}...")
                raise
        else:
            print("字幕文件不存在，创建空的字幕对象")
            subs = pysubs2.SSAFile()
            subs.save(str(srt_file))
            return

    replace_map, warning_words = init_jieba()
    warnings_found = []

    for i, event in enumerate(subs.events):
        text = event.text

        # 先应用替换词典
        replaced = "".join([replace_map.get(x, x) for x in jieba.cut(text)])
        if event.text != replaced:
            print(f"🔄 词典替换: {event.text} -> {replaced}")
        event.text = replaced

        # 对替换后的内容检查警告词
        for word in warning_words:
            if word in event.text:
                warnings_found.append({
                    'word': word,
                    'text': event.text,
                    'index': i + 1
                })

    subs.save(str(srt_file))

    # 集中输出警告信息
    if warnings_found:
        print(f"\n{'='*60}")
        print(f"⚠️  发现 {len(warnings_found)} 个需要人工复检的字幕")
        print(f"{'='*60}")
        for warning in warnings_found:
            print(f"字幕 {warning['index']}: 发现词汇 '{warning['word']}'")
            print(f"内容: {warning['text']}")
            print("-" * 40)
        print(f"请检查以上字幕内容是否需要手动调整")
        print(f"{'='*60}\n")


def cut():
    """字幕编辑之后，进行视频切分、合并、压字幕、压缩及拷贝

    1. 剪掉语助（单行的好，呃等）
    2. 剪掉字幕中以[del]开头的event
    3. 根据自定义词典完成替换

    Args:
        working_dir: 工作目录，如果为None则从/tmp/transcript.log文件读取
    """
    # 读取工作日志
    log_file = Path("/tmp/transcript.log")
    if not log_file.exists():
        raise FileNotFoundError("找不到工作日志文件，请先运行transcript命令")

    with open(log_file, "r", encoding="utf-8") as f:
        log = json.load(f)
        name = log["name"]
        # 兼容旧版本日志格式
        if "raw_file" in log:
            media_file = Path(log["raw_file"])
            file_type = log.get("file_type", "video")  # 默认为视频
        else:
            # 兼容旧版本
            media_file = Path(log["raw_video"])
            file_type = "video"
        parent = Path(log["working_dir"])

    # 查找字幕文件 - 优先查找项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    srt_file = project_root / f"{name}.srt"

    if not srt_file.exists():
        # 尝试在工作目录查找
        srt_file = parent / f"{name}.srt"
        if not srt_file.exists():
            # 尝试在当前目录查找
            srt_file = Path(f"./{name}.srt").resolve()
            if not srt_file.exists():
                raise FileNotFoundError(f"找不到字幕文件: {srt_file}")

    if not media_file.exists():
        # 尝试在工作目录查找媒体文件
        media_in_workspace = parent / Path(media_file).name
        if media_in_workspace.exists():
            media_file = media_in_workspace
        else:
            raise FileNotFoundError(f"找不到{'音频' if file_type == 'audio' else '视频'}文件: {media_file}")

    print(f"处理字幕文件: {srt_file}")
    print(f"处理{'音频' if file_type == 'audio' else '视频'}文件: {media_file}")

    workspace = parent / "cut"
    workspace.mkdir(exist_ok=True)

    out_srt = parent / "cut.srt"

    replace_map, warning_words = init_jieba()
    markers = "好呃恩嗯"

    to_del = []

    subs = pysubs2.load(str(srt_file))
    keep_subs = pysubs2.SSAFile()
    cum_lag: int = 0

    def remove_event(to_del: list, i: int, event: Any) -> int:
        # 遇到连续删除，要进行合并
        if len(to_del) > 0 and to_del[-1][0] == i - 1:
            item = to_del[-1]
            item[0] = i
            lag = event.end - item[2]
            item[2] = event.end
            return lag
        else:
            to_del.append([i, event.start, event.end])
            return event.duration

    deleted_count = 0
    for i, event in enumerate(subs.events):
        text = event.text
        if len(text) == 1 and text in markers:
            cum_lag += remove_event(to_del, i, event)
            deleted_count += 1
            print(f"删除语助词: {event.text}")
            continue

        if text.startswith("[del]") or text.startswith("[DEL]"):
            cum_lag += remove_event(to_del, i, event)
            deleted_count += 1
            print(f"删除标记字幕: {event.text}")
            continue

        # 先应用替换词典
        replaced = "".join([replace_map.get(x, x) for x in jieba.cut(text)])
        if event.text != replaced:
            print(f"🔄 词典替换: {event.text} -> {replaced}")

        event.text = replaced

        # 对替换后的内容检查警告词（在cut阶段不集中输出，因为可能有删除）
        for word in warning_words:
            if word in event.text:
                print(f"⚠️  警告: 字幕中发现需要人工复检的词汇 '{word}': {event.text}")
        event.start -= cum_lag
        event.end -= cum_lag
        keep_subs.events.append(event)

    keep_subs.save(str(out_srt))
    print(f"删除了 {deleted_count} 个字幕片段")
    print(f"保留了 {len(keep_subs.events)} 个字幕片段")

    # 切分媒体文件
    if to_del:
        if file_type == "audio":
            print("开始切分音频...")
            cut_audio(media_file, to_del, workspace)
            print("音频切分完成，开始合并")
        else:
            print("开始切分视频...")
            cut_video(media_file, to_del, workspace)
            print("视频切分完成，开始合并和压缩")
    else:
        print("没有需要删除的片段，直接进行合并")
        # 创建一个包含完整媒体文件的列表文件
        list_file = workspace / "list.text"
        with open(list_file, "w", encoding="utf-8") as f:
            f.write(f"file '{media_file}'\n")

    return parent


def adjust_subtitles_offset(srt: Path, opening_video: Path, full_srt: Path):
    # dur_ms = int(round(probe_duration(opening_video) * 1000))
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        opening_video,
    ]
    dur_ms = int(round(float(subprocess.check_output(cmd).strip()) * 1000))

    subs = pysubs2.load(str(srt))
    for event in subs.events:
        event.start += dur_ms
        event.end += dur_ms

    subs.save(str(full_srt))


def optimize_subtitles_for_display(srt_file: Path, output_srt: Path = None):
    """
    优化字幕显示：自动换行和调整过长的字幕

    Args:
        srt_file: 输入字幕文件
        output_srt: 输出字幕文件，如果为None则覆盖原文件
    """
    if output_srt is None:
        output_srt = srt_file

    subs = pysubs2.load(str(srt_file))

    for event in subs.events:
        text = event.text.strip()
        if not text:
            continue

        # 计算字符长度（中文字符按2个字符计算）
        char_count = sum(2 if ord(c) > 127 else 1 for c in text)

        # 根据字符长度决定是否需要换行
        if char_count > 40:  # 超过40个字符宽度需要换行
            # 智能换行：优先在标点符号处换行
            punctuation = '，。！？；：、'
            words = []
            current_word = ""

            for char in text:
                current_word += char
                if char in punctuation:
                    words.append(current_word)
                    current_word = ""

            if current_word:
                words.append(current_word)

            # 重新组织成两行
            if len(words) > 1:
                mid_point = len(words) // 2
                line1 = ''.join(words[:mid_point]).strip()
                line2 = ''.join(words[mid_point:]).strip()

                # 确保两行长度相对均衡
                line1_len = sum(2 if ord(c) > 127 else 1 for c in line1)
                line2_len = sum(2 if ord(c) > 127 else 1 for c in line2)

                if abs(line1_len - line2_len) > 10 and len(words) > 2:
                    # 重新调整分割点
                    best_split = mid_point
                    best_diff = abs(line1_len - line2_len)

                    for i in range(1, len(words)):
                        test_line1 = ''.join(words[:i]).strip()
                        test_line2 = ''.join(words[i:]).strip()
                        test_len1 = sum(2 if ord(c) > 127 else 1 for c in test_line1)
                        test_len2 = sum(2 if ord(c) > 127 else 1 for c in test_line2)
                        test_diff = abs(test_len1 - test_len2)

                        if test_diff < best_diff:
                            best_diff = test_diff
                            best_split = i

                    line1 = ''.join(words[:best_split]).strip()
                    line2 = ''.join(words[best_split:]).strip()

                if line1 and line2:
                    event.text = f"{line1}\\N{line2}"
            else:
                # 如果没有标点符号，按字符数强制换行
                mid_char = len(text) // 2
                # 寻找最近的空格或合适的断点
                split_point = mid_char
                for i in range(max(0, mid_char - 5), min(len(text), mid_char + 5)):
                    if text[i] in ' \t':
                        split_point = i
                        break

                line1 = text[:split_point].strip()
                line2 = text[split_point:].strip()
                if line1 and line2:
                    event.text = f"{line1}\\N{line2}"

    subs.save(str(output_srt))
    print(f"字幕显示优化完成: {output_srt}")


def get_adaptive_subtitle_style(srt_file: Path):
    """
    根据字幕内容生成自适应的字幕样式

    Args:
        srt_file: 字幕文件路径

    Returns:
        str: FFmpeg字幕样式字符串
    """
    subs = pysubs2.load(str(srt_file))

    # 分析字幕特征
    max_char_count = 0
    avg_char_count = 0
    total_events = 0

    for event in subs.events:
        if event.text.strip():
            # 计算字符长度（中文字符按2个字符计算）
            char_count = sum(2 if ord(c) > 127 else 1 for c in event.text)
            max_char_count = max(max_char_count, char_count)
            avg_char_count += char_count
            total_events += 1

    if total_events > 0:
        avg_char_count /= total_events

    # 根据字幕长度动态调整字体大小
    if max_char_count > 60:
        font_size = 18  # 很长的字幕用小字体
    elif max_char_count > 40:
        font_size = 20  # 较长的字幕用中等字体
    elif avg_char_count > 30:
        font_size = 22  # 平均较长用稍小字体
    else:
        font_size = 24  # 短字幕用正常字体

    # 生成样式字符串 - 黑色字体白色边框方案
    style = (
        f"FontName=WenQuanYi Micro Hei Light,"
        f"FontSize={font_size},"
        f"PrimaryColour=&H00000000,"  # 黑色字体
        f"OutlineColour=&H00FFFFFF," # 白色描边
        f"Outline=10,"                # 10px白色描边
        f"Shadow=0,"                 # 不使用阴影
        f"MarginV=40,"               # 底部边距
        f"MarginL=60,"               # 左边距
        f"MarginR=60,"               # 右边距
        f"Alignment=2,"              # 底部居中对齐
        f"WrapStyle=2"               # 智能换行
    )

    print(f"自适应字幕样式: 字体大小={font_size}, 最长字幕={max_char_count}字符, 平均长度={avg_char_count:.1f}字符")
    return style

def merge(output_path: Path = None,
          opening_video_path: Path = None, ending_video_path: Path = None):
    """合并剪辑片段、片头、片尾以及压缩

    Args:
        working_dir: 工作目录，如果为None则从/tmp/transcript.log文件读取
        output_path: 输出路径，如果为None则使用原视频位置
        opening_video_path: 片头视频路径
        ending_video_path: 片尾视频路径

    这一步之后，所有的字幕及剪辑都应该正确完成了
    """
    # 读取工作日志
    log_file = Path("/tmp/transcript.log")
    if not log_file.exists():
        raise FileNotFoundError("找不到工作日志文件")


    log = json.load(open(log_file, "r", encoding="utf-8"))
    working_dir = Path(log["working_dir"])
    name = log["name"]

    # 兼容旧版本日志格式
    if "raw_file" in log:
        original_file = Path(log["raw_file"])
        file_type = log.get("file_type", "video")  # 默认为视频
    else:
        # 兼容旧版本
        original_file = Path(log["raw_video"])
        file_type = "video"

    cut_srt = working_dir / "cut.srt"
    if not cut_srt.exists():
        raise FileNotFoundError(f"找不到剪辑后的字幕文件: {cut_srt}")

    list_file = working_dir / "cut/list.text"

    if not list_file.exists():
        raise FileNotFoundError(f"找不到{'音频' if file_type == 'audio' else '视频'}片段列表文件: {list_file}")

    if file_type == "audio":
        # 音频处理
        main_audio = working_dir / f"main{original_file.suffix}"
        print("合并音频片段...")
        command = f"ffmpeg -hide_banner -f concat -safe 0 -i {list_file} -fflags +genpts -c copy -avoid_negative_ts make_zero -v error -y '{main_audio}'"
        execute(command, msg="合并主音频")
        merged_media = main_audio
    else:
        # 视频处理
        main_video = working_dir / "main.mp4"
        print("合并视频片段...")
        command = f"ffmpeg -hide_banner -f concat -safe 0 -i {list_file} -fflags +genpts -c copy -map 0:v -map 0:a -movflags +faststart -video_track_timescale 600 -f mp4 -avoid_negative_ts make_zero -v error -y '{main_video}'"
        execute(command, msg="合并主视频")
        merged_media = main_video

    if file_type == "video":
        # 视频处理：支持片头片尾
        video_files = []

        # 添加片头
        if opening_video_path and Path(opening_video_path).exists():
            video_files.append(Path(opening_video_path))
            print(f"添加片头视频: {opening_video_path}")

        # 添加主视频
        video_files.append(merged_media)

        # 添加片尾
        if ending_video_path and Path(ending_video_path).exists():
            video_files.append(Path(ending_video_path))
            print(f"添加片尾视频: {ending_video_path}")

        # 如果有片头或片尾，需要重新合并
        if len(video_files) > 1:
            merge_list = working_dir / "full.text"
            merged_video = working_dir / f"full.mp4"

            with open(merge_list, "w", encoding="utf-8") as f:
                for video_file in video_files:
                    f.write(f"file '{video_file}'\n")

            # 首先尝试使用copy模式合并，避免重新编码
            cmd_copy = f"ffmpeg -hide_banner -f concat -safe 0 -i {merge_list} -fflags +genpts -c copy -map 0:v -map 0:a -movflags +faststart -y -f mp4 -video_track_timescale 600 -v error {merged_video}"

            try:
                execute(cmd_copy, msg="合并完整视频(copy模式)")
            except RuntimeError:
                print("⚠️ copy模式失败，尝试重新编码...")
                # 如果copy模式失败，使用重新编码
                cmd_encode = f"ffmpeg -hide_banner -f concat -safe 0 -i {merge_list} -fflags +genpts -c:v libx264 -preset medium -crf 23 -c:a aac -b:a 128k -map 0:v -map 0:a -movflags +faststart -y -f mp4 -video_track_timescale 600 -v error {merged_video}"
                execute(cmd_encode, msg="合并完整视频(重新编码)")

            # 如果有片头，需要调整字幕时间偏移
            if opening_video_path:
                adjusted_srt = working_dir / "adjusted.srt"
                adjust_subtitles_offset(cut_srt, opening_video_path, adjusted_srt)
                cut_srt = adjusted_srt

            merged_media = merged_video
        # 如果没有片头片尾，merged_media 已经是正确的文件

    # 自动对齐字幕 - 这是关键步骤
    print("开始字幕对齐...")
    aligned_srt = working_dir / "aligned.srt"
    align_subtitles_with_audio(merged_media, cut_srt, aligned_srt)

    # 确定最终输出路径
    if output_path is None:
        # 使用原文件的目录，文件名加后缀
        output_dir = original_file.parent
        base_name = original_file.stem
    else:
        output_path = Path(output_path)
        if output_path.is_dir():
            output_dir = output_path
            base_name = name
        else:
            output_dir = output_path.parent
            base_name = output_path.stem

    # 生成最终文件路径
    if file_type == "audio":
        # 音频文件输出
        final_audio = output_dir / f"{base_name}-final{original_file.suffix}"
        final_srt = output_dir / f"{base_name}-final.srt"

        print(f"输出目录: {output_dir}")
        print(f"剪辑音频: {final_audio}")
        print(f"字幕文件: {final_srt}")

        # 复制剪辑后的音频文件
        print("复制剪辑后的音频...")
        shutil.copy2(merged_media, final_audio)

        # 复制字幕文件
        shutil.copy2(aligned_srt, final_srt)

        print("\n=== 音频处理完成 ===")
        print(f"✅ 剪辑音频: {final_audio}")
        print(f"✅ 字幕文件: {final_srt}")

        return final_audio, None, final_srt
    else:
        # 视频文件输出
        final_with_sub = output_dir / f"{base_name}-final-sub.mp4"
        final_no_sub = output_dir / f"{base_name}-final.mp4"
        final_srt = output_dir / f"{base_name}-final.srt"

        print(f"输出目录: {output_dir}")
        print(f"带字幕版本: {final_with_sub}")
        print(f"无字幕版本: {final_no_sub}")

        # 优化字幕显示
        print("优化字幕显示...")
        optimized_srt = working_dir / "optimized.srt"
        optimize_subtitles_for_display(aligned_srt, optimized_srt)

        # 压缩及烧字幕
        print("生成带字幕版本...")

        # 获取自适应字幕样式
        subtitle_style = get_adaptive_subtitle_style(optimized_srt)

        cmd = f"ffmpeg -hide_banner -i {merged_media} -vf \"subtitles={optimized_srt}:force_style='{subtitle_style}'\" -c:v libx264 -preset slow -crf 23 -c:a copy -v error -y '{final_with_sub}'"
        execute(cmd, msg="生成带字幕版本")

        # 压缩未加字幕的视频
        print("生成无字幕版本...")
        cmd = f"ffmpeg -hide_banner -i {merged_media} -c:v libx264 -preset slow -crf 23 -c:a copy -v error -y '{final_no_sub}'"
        execute(cmd, msg="生成无字幕版本")

        # 复制字幕文件
        shutil.copy2(aligned_srt, final_srt)

        print("\n=== 视频处理完成 ===")
        print(f"✅ 带字幕视频: {final_with_sub}")
        print(f"✅ 无字幕视频: {final_no_sub}")
        print(f"✅ 字幕文件: {final_srt}")

        return final_with_sub, final_no_sub, final_srt


def t2s(srt: str):
    """将繁中转换为简中"""
    srt_file = Path(srt)
    if not srt_file.exists():
        raise FileNotFoundError(f"字幕文件不存在: {srt_file}")

    subs = pysubs2.load(str(srt_file))

    converter = opencc.OpenCC("t2s.json")
    for event in subs.events:
        text = event.text

        replaced = converter.convert(text)
        if event.text != replaced:
            print(f"{event.text} -> {replaced}")
        event.text = replaced

    subs.save(str(srt_file))

def process_video(input_video: str, output_path: str = None,
                 opening_video: str = None, ending_video: str = None,
                 auto_process: bool = False):
    """
    完整的视频处理流程

    Args:
        input_video: 输入视频文件路径
        output_path: 输出路径（目录或文件路径）
        opening_video: 片头视频路径
        ending_video: 片尾视频路径
        auto_process: 是否自动处理（跳过手动编辑步骤）
    """
    try:
        print("=== 开始视频字幕处理流程 ===")

        # 步骤1: 生成字幕
        print("\n步骤1: 生成字幕")
        srt_file = transcript(Path(input_video))

        if not auto_process:
            print(f"\n请编辑字幕文件: {srt_file}")
            print("- 可以删除不需要的字幕行")
            print("- 在需要删除的字幕前添加 [DEL] 标记")
            print("- 编辑完成后按回车继续...")
            input("按回车键继续...")

        # 步骤2: 剪辑视频
        print("\n步骤2: 剪辑视频")
        cut()

        # 步骤3: 合并和输出
        print("\n步骤3: 合并和输出")
        final_with_sub, final_no_sub, final_srt = merge(
            output_path=Path(output_path) if output_path else None,
            opening_video_path=Path(opening_video) if opening_video else None,
            ending_video_path=Path(ending_video) if ending_video else None
        )

        print("\n=== 处理完成 ===")
        return final_with_sub, final_no_sub, final_srt

    except Exception as e:
        print(f"❌ 处理失败: {e}")
        raise


def resume(output_path: str = None, opening_video: str = None, ending_video: str = None):
    """
    编辑字幕后继续处理（自动调用align）

    Args:
        output_path: 输出路径（目录或文件路径）
        opening_video: 片头视频路径
        ending_video: 片尾视频路径
    """
    try:
        print("=== 继续处理已编辑的字幕 ===")
        print("将自动调用字幕对齐功能")

        # 步骤1: 剪辑视频
        print("\n步骤1: 剪辑视频")
        cut()

        # 步骤2: 合并和输出（merge函数内部会自动调用align）
        print("\n步骤2: 合并和输出")
        final_with_sub, final_no_sub, final_srt = merge(
            output_path=Path(output_path) if output_path else None,
            opening_video_path=Path(opening_video) if opening_video else None,
            ending_video_path=Path(ending_video) if ending_video else None
        )

        print("\n=== 处理完成 ===")
        print(f"✅ 带字幕视频: {final_with_sub}")
        print(f"✅ 无字幕视频: {final_no_sub}")
        print(f"✅ 字幕文件: {final_srt}")

        return final_with_sub, final_no_sub, final_srt

    except Exception as e:
        print(f"❌ 处理失败: {e}")
        raise


def auto(input_video: str, output_path: str = None,
         opening_video: str = None, ending_video: str = None):
    """
    自动处理流程（无需手动编辑字幕）

    Args:
        input_video: 输入视频文件路径
        output_path: 输出路径（目录或文件路径）
        opening_video: 片头视频路径
        ending_video: 片尾视频路径
    """
    return process_video(input_video, output_path, opening_video, ending_video, auto_process=True)


def test():
    """测试模型加载功能"""
    import os
    print("HF_ENDPOINT:", os.environ.get("HF_ENDPOINT"))
    print("Model directory:", model_dir)

    # 设置离线模式
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_HUB_OFFLINE"] = "1"

    device = "cpu"
    try:
        print("Loading align model...")

        # 尝试使用本地路径
        local_model_path = Path(model_dir) / "models--jonatasgrosman--wav2vec2-large-xlsr-53-chinese-zh-cn"
        if local_model_path.exists():
            # 查找最新的快照目录
            snapshots_dir = local_model_path / "snapshots"
            if snapshots_dir.exists():
                snapshot_dirs = [d for d in snapshots_dir.iterdir() if d.is_dir()]
                if snapshot_dirs:
                    latest_snapshot = max(snapshot_dirs, key=lambda x: x.stat().st_mtime)
                    print(f"Using local model from: {latest_snapshot}")
                    model_name = str(latest_snapshot)
                else:
                    model_name = "jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn"
            else:
                model_name = "jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn"
        else:
            model_name = "jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn"

        model_a, metadata = whisperx.load_align_model(
            language_code="zh",
            device=device,
            model_name=model_name,
            model_dir=model_dir
        )
        print("✅ Model loaded successfully!")
        print(f"Model type: {type(model_a)}")
        print(f"Metadata: {metadata}")
    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        print("Please check if the model files are properly downloaded.")

# CLI入口点已移至 transcript/cli.py
# 如需使用原版命令，请直接导入相应函数
