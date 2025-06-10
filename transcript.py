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
from multiprocessing.util import is_exiting
import sys
import os
import shlex
import shutil
import subprocess
import warnings
from subprocess import PIPE, STDOUT, Popen
from typing import Any, List, Tuple
import json


import fire
import jieba
import opencc
import pysubs2
from pathlib import Path

# from pywhispercpp.model import Model


warnings.filterwarnings("ignore")

import whisperx

prompt = ",".join(["大家好，我们开始上课了。请输出简体中文。"])

opening_video = Path("/Volumes/share/data/autobackup/ke/factor-ml/opening.mp4")
ending_video = Path("/Volumes/share/data/autobackup/ke/factor-ml/end.mp4")

cpp_path = Path("/Volumes/share/data/whisper.cpp")
cpp_model = Path("/Volumes/share/data/whisper.cpp/models/ggml-large-v2.bin")
# 设置本地模型目录，如果环境变量未设置则使用默认路径
model_dir = os.environ.get("hf_model_dir", "/Volumes/share/data/models/huggingface/hub")

def align_subtitles_with_audio(video: Path, original_srt: Path, aligned_srt: Path):
    """
    使用 whisperx 对齐字幕文件与音频。
    如果对齐模型不可用，则直接复制原始字幕文件。

    Args:
        video (str): 合并后的视频文件路径。
        original_srt (str): 原始字幕文件路径。
        aligned_srt (str): 对齐后的字幕文件路径。
    """
    try:
        # 提取音频
        audio_path = Path(video).with_suffix(".wav")
        extract_audio(video, audio_path)

        device = "cpu"

        audio = whisperx.load_audio(str(audio_path))
        # 加载字幕文件
        subs = pysubs2.load(str(original_srt))
        segments = [
            {
                "start": event.start / 1000,
                "end": event.end / 1000,
                "text": event.text,
                "id": i
             }
               for i, event in enumerate(subs.events)]

        # 加载对齐模型
        print("Loading align model...")

        # 设置离线模式环境变量
        import os
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HUB_OFFLINE"] = "1"

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
        print("Align model loaded. Alignment in progress...")

        # 对齐字幕
        aligned_result = whisperx.align(segments, model_a, metadata, audio, device)

        # 更新字幕时间戳
        aligned_subs = pysubs2.SSAFile()
        for i, segment in enumerate(aligned_result["segments"]):
            event = pysubs2.SSAEvent()
            event.start = int(segment["start"] * 1000)  # 转换为毫秒
            end = int(segment["end"] * 1000)
            if i < len(aligned_result["segments"]) - 1:
                 next_start = int(aligned_result["segments"][i + 1]["start"] * 1000)
                 event.end = max(next_start - 500, end)
            else:
                event.end = end
            event.text = segment["text"]
            aligned_subs.events.append(event)

        # 保存对齐后的字幕文件
        aligned_subs.save(str(aligned_srt))
        print(f"字幕已对齐并保存到 {aligned_srt}")

    except Exception as e:
        print(f"对齐模型加载失败: {e}")
        print("使用原始字幕文件作为对齐结果...")

        # 直接复制原始字幕文件
        import shutil
        shutil.copy2(original_srt, aligned_srt)
        print(f"已复制原始字幕到 {aligned_srt}")
        print("提示: 要使用字幕对齐功能，请运行 'python download_models.py' 下载对齐模型")


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


def transcript_cpp(input_audio: Path, output_srt: Path, prompt: str, dry_run=False):
    """
    Args:
        input_audio (str): _description_
        output_srt (str): _description_
        prompt (str): _description_
    """
    whisper = os.path.join(cpp_path, "whisper-cli")

    cmd = f"{whisper} {input_audio} -l zh -sow -ml 30 -t 8 -m {cpp_model} -osrt -of {output_srt.with_suffix('')} --prompt '{prompt}'"
    execute(cmd)


def init_jieba():
    custom_map = {}
    dict_path = os.path.join(os.path.dirname(__file__), "words.md")
    with open(dict_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or len(line) == 0:
                continue
            wrong, right = line.split(",")
            custom_map[wrong] = right

    for word in custom_map.keys():
        jieba.add_word(word)

    return custom_map


def transcriptx(input_audio: Path, output_srt: Path, prompt: str):
    compute_type = "default"
    device = "cpu"

    options = {"initial_prompt": prompt}
    model = whisperx.load_model(
        whisperx_model,
        device=device,
        compute_type=compute_type,
        asr_options=options,
        language="zh",
        threads=8,
    )

    audio = whisperx.load_audio(input_audio)
    result = model.transcribe(
        audio, language="zh", print_progress=True, batch_size=8, chunk_size=10
    )

    subs = pysubs2.load_from_whisper(result["segments"])
    subs.save(output_srt)
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


def transcript(input_video: Path, dry_run=False):
    input_video = Path(input_video)
    assert input_video.name == "raw.mp4"

    name = input_video.parent.name
    output_dir = Path("/tmp/transcript") / name 
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(".log", "w", encoding="utf-8") as f:
        json.dump({
            "working_dir": str(output_dir), 
            "name": name,
            "raw_video": str(input_video)
            }, f)

    video = output_dir / input_video.name
    shutil.copy(input_video, video)

    output_srt = (Path(".") / input_video.parent.name).with_suffix(".srt").resolve()
    output_wav = video.with_suffix(".wav")
    print(f"convert video to subtitles: {input_video} > {output_srt}")

    # convert video to wav
    start = datetime.datetime.now()
    print(f"{start.hour}:{start.minute}:{start.second}: started")
    extract_audio(input_video, output_wav)

    transcript_cpp(output_wav, output_srt, prompt, dry_run)
    sub(output_srt)


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
        cmd = f"ffmpeg -hide_banner -ss '{start_secs}' -i '{input_video}' -t '{dur}' -map '0:0' '-c:0' copy -map '0:1' '-c:1' copy -map_metadata 0 -movflags '+faststart' -default_mode infer_no_subs -ignore_unknown -f mp4 -video_track_timescale 600 -y -v error '{tmp_file}'"

        execute(cmd, supress_log=True)

    list_file = os.path.join(out_dir, "list.text")
    with open(list_file, "w", encoding="utf-8") as f:
        for video in tmp_files:
            f.write(f"file '{video}'\n")

    return list_file


def sub(srt_file: Path):
    """输入字幕文件，通过自定义词典，先粗筛一次。在transcript之后被自动调用。

    Args:
        srt_file (str): _description_
    """
    subs = pysubs2.load(str(srt_file))

    custom_map = init_jieba()
    for event in subs.events:
        text = event.text

        replaced = "".join([custom_map.get(x, x) for x in jieba.cut(text)])
        if event.text != replaced:
            print(f"{event.text} -> {replaced}")
        event.text = replaced

    subs.save(str(srt_file))


def cut():
    """字幕编辑之后，进行视频切分、合并、压字幕、压缩及拷贝

    1. 剪掉语助（单行的好，呃等）
    2. 剪掉字幕中以[del]开头的event
    3. 根据自定义词典完成替换
    """
    with open (".log", "r", encoding="utf-8") as f:
        log = json.load(f)
        name = log["name"]
        video = Path(log["raw_video"])
        parent = Path(log["working_dir"])

    srt_file = Path(f"./{name}.srt").resolve()

    if not video.exists():
        print(f"{video} does not exist")
        return

    workspace = parent / "cut"
    workspace.mkdir(exist_ok=True)

    out_srt = parent / "cut.srt"

    custom_map = init_jieba()
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
        
    for i, event in enumerate(subs.events):
        text = event.text
        if len(text) == 1 and text in markers:
            cum_lag += remove_event(to_del, i, event)
            # print(f"del: {event.text}")
            continue

        if text.startswith("[del]"):
            cum_lag += remove_event(to_del, i, event)
            # print(f"del: {event.text}")
            continue

        replaced = "".join([custom_map.get(x, x) for x in jieba.cut(text)])
        if event.text != replaced:
            print(f"{event.text} -> {replaced}")

        event.text = replaced
        event.start -= cum_lag
        event.end -= cum_lag
        keep_subs.events.append(event)

    keep_subs.save(str(out_srt))

    # 切分视频
    cut_video(video, to_del, workspace)
    print("字幕切分完成，开始合并和压缩")

    merge(workspace, parent.name)


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

def merge(dst: str=None, opening: bool = False, ending: bool = False):
    """合并剪辑片段、片头、片尾以及压缩

    file 'file:/private/tmp/loseless/fa-00.30.58.083-00.45.58.083-seg4.mp4'" | ffmpeg -hide_banner -f concat -safe 0 -protocol_whitelist 'file,pipe,fd' -i - -map '0:0' '-c:0' copy '-disposition:0' default -map '0:1' '-c:1' copy '-disposition:1' default -movflags '+faststart' -default_mode infer_no_subs -ignore_unknown -f mp4 -y '/private/tmp/loseless/fa-merged.mp4'

    这一步之后，所有的字幕及剪辑都应该正确完成了
    """
    log = json.load(open(".log", "r", encoding="utf-8"))
    working_dir = Path(log["working_dir"])
    name = log["name"]

    if dst is None:
        dst = working_dir / f"{name}.mp4"

    cut_srt = working_dir / "cut.srt"

    main_video = working_dir / "main.mp4"
    list_file = working_dir / "cut/list.text"

    command = f"ffmpeg -hide_banner -f concat -safe 0 -i {list_file} -fflags +genpts -fps_mode vfr -c copy -map 0:v -map 0:a -disposition:s:0 default -movflags +faststart -video_track_timescale 600 -f mp4 -avoid_negative_ts make_zero -v error -y '{main_video}'"

    # merge main video
    execute(command)

    # 加片头、片尾
    video_files = [main_video]
    if opening:
        video_files.insert(0, opening_video)
    if ending:
        video_files.append(ending_video)

    if opening or ending:
        merge_list = working_dir / "full.text"
        merged_video = working_dir / f"full.mp4"

        with open(merge_list, "w", encoding="utf-8") as f:
            for video_file in video_files:
                f.write(f"file '{video_file}'\n")

        cmd = f"ffmpeg -hide_banner -f concat -safe 0 -i {merge_list} -fflags +genpts -fps_mode vfr -c:v libx264 -preset slow -crf 23 -c:a copy -map 0:v -map 0:a -movflags +faststart -y -f mp4 -video_track_timescale 600 -avoid_negative_ts make_zero -v error {merged_video}"
        execute(cmd, msg="加片头")
    else:
        merged_video = working_dir / "main.mp4"

    # 自动对齐字幕
    aligned_srt = working_dir.parent / f"{name}/aligned.srt"
    align_subtitles_with_audio(merged_video, cut_srt, aligned_srt)

    # 压缩及烧字幕
    with_sub = os.path.join(working_dir, f"{name}.sub.mp4")
    cmd = f"ffmpeg -hide_banner -hwaccel videotoolbox -i {merged_video} -vf \"subtitles={aligned_srt}:force_style='FontName='WenQuanYi Micro Hei Light',FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=1'\" -c:v libx264 -preset slow -crf 23 -c:a copy -c:s copy -v error {with_sub}"
    execute(cmd, msg="压缩、烧字幕")

    # 压缩未加字幕的视频
    no_sub = os.path.join(working_dir, f"{name}.mp4")
    cmd = f"ffmpeg -hide_banner -hwaccel videotoolbox -i {merged_video} -c:v libx264 -preset slow -crf 23 -c:a copy -c:s copy -v error {no_sub}"
    execute(cmd, msg="压缩")

    # 拷贝到目标目录
    # dst = Path("/Volumes/share/data/autobackup/ke/factor-ml/", dst)
    # print(f"copy to {dst}")
    # shutil.copy(with_sub, dst / f"{course}.sub.mp4")
    # shutil.copy(no_sub, dst / f"{course}.mp4")
    # shutil.copy(aligned_srt, dst / f"{course}.srt")
    # shutil.copy(cut_srt, dst / f"{course}.cut.srt")


def t2s(srt: str):
    """将繁中转换为简中"""
    srt_file = convert_path(srt)
    subs = pysubs2.load(srt_file)

    converter = opencc.OpenCC("t2s.json")
    for event in subs.events:
        text = event.text

        replaced = converter.convert(text)
        if event.text != replaced:
            print(f"{event.text} -> {replaced}")
        event.text = replaced

    subs.save(srt_file)

def test():
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

fire.Fire(
    {
        "transcript": transcript,  # 1 视频转字幕
        "sub": sub,
        "cut": cut,  # 2. 将字幕人工编辑后，对视频进行剪辑，输入工作目录
        "t2s": t2s,
        "merge": merge
    }
)
