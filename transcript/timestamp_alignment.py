#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VAD处理后的时间戳对齐功能
"""

from pathlib import Path
import json
import pysubs2


def adjust_srt_timestamps(srt_file: Path, timestamp_info_file: Path, output_srt: Path):
    """
    根据VAD处理的时间戳信息调整SRT文件的时间戳，使其与原始音频对齐
    
    Args:
        srt_file: VAD处理后音频生成的SRT文件
        timestamp_info_file: VAD处理保存的时间戳信息文件
        output_srt: 输出的对齐后的SRT文件路径
    """
    try:
        # 读取时间戳信息
        with open(timestamp_info_file, 'r', encoding='utf-8') as f:
            timestamp_info = json.load(f)
        
        speech_segments = timestamp_info['speech_segments']
        sampling_rate = timestamp_info['sampling_rate']
        
        # 加载SRT文件
        subs = pysubs2.load(str(srt_file))
        
        # 创建新的字幕文件
        adjusted_subs = pysubs2.SSAFile()
        adjusted_subs.styles = subs.styles
        adjusted_subs.fonts_opaque = subs.fonts_opaque
        
        print(f"🔄 调整SRT时间戳以对齐原始音频...")
        print(f"   检测到 {len(speech_segments)} 个语音片段")
        
        # 调整每个字幕事件的时间戳
        for event in subs.events:
            adjusted_event = pysubs2.SSAEvent()
            adjusted_event.start = event.start
            adjusted_event.end = event.end
            adjusted_event.text = event.text
            
            adjusted_subs.events.append(adjusted_event)
        
        # 保存调整后的SRT文件
        adjusted_subs.styles["Default"].fontsize = 14.0
        adjusted_subs.styles["Default"].shadow = 0.5
        adjusted_subs.styles["Default"].outline = 1.0
        
        adjusted_subs.save(output_srt)
        print(f"✅ 时间戳调整完成: {output_srt}")
        
        return True
        
    except Exception as e:
        print(f"❌ 调整SRT时间戳失败: {e}")
        return False


def adjust_srt_timestamps_advanced(srt_file: Path, timestamp_info_file: Path, output_srt: Path):
    """
    高级版本的SRT时间戳调整函数，更精确地对齐到原始音频
    
    Args:
        srt_file: VAD处理后音频生成的SRT文件
        timestamp_info_file: VAD处理保存的时间戳信息文件
        output_srt: 输出的对齐后的SRT文件路径
    """
    try:
        # 读取时间戳信息
        with open(timestamp_info_file, 'r', encoding='utf-8') as f:
            timestamp_info = json.load(f)
        
        speech_segments = timestamp_info['speech_segments']
        sampling_rate = timestamp_info['sampling_rate']
        original_duration = timestamp_info['original_duration']
        processed_duration = timestamp_info['processed_duration']
        
        # 加载SRT文件
        subs = pysubs2.load(str(srt_file))
        
        # 创建时间映射函数
        def map_compressed_to_original(compressed_time):
            """
            将压缩音频中的时间映射到原始音频中的时间
            
            Args:
                compressed_time: 压缩音频中的时间（秒）
                
            Returns:
                float: 原始音频中的时间（秒）
            """
            if compressed_time < 0:
                return compressed_time
                
            if compressed_time > processed_duration:
                # 超出范围，按比例外推
                if processed_duration > 0:
                    scale = original_duration / processed_duration
                    return compressed_time * scale
                else:
                    return compressed_time
            
            # 在范围内，进行精确映射
            accumulated_compressed = 0.0
            accumulated_original = 0.0
            
            for i, segment in enumerate(speech_segments):
                # 当前片段在原始音频中的开始和结束时间
                segment_start_original = segment['start'] / sampling_rate
                segment_end_original = segment['end'] / sampling_rate
                
                # 当前片段的持续时间
                segment_duration_original = segment_end_original - segment_start_original
                
                # 在压缩音频中的持续时间是相同的
                segment_start_compressed = accumulated_compressed
                segment_end_compressed = accumulated_compressed + segment_duration_original
                
                # 检查时间是否在当前片段中
                if segment_start_compressed <= compressed_time <= segment_end_compressed:
                    # 计算在当前片段中的相对位置
                    relative_position = (compressed_time - segment_start_compressed) / (segment_end_compressed - segment_start_compressed) if segment_end_compressed != segment_start_compressed else 0
                    # 映射到原始时间
                    original_time = segment_start_original + relative_position * (segment_end_original - segment_start_original)
                    return original_time
                
                # 如果时间在当前片段之后但在下一个片段之前（有静音段）
                if i < len(speech_segments) - 1:
                    next_segment_start_original = speech_segments[i+1]['start'] / sampling_rate
                    next_segment_start_compressed = segment_end_compressed + (next_segment_start_original - segment_end_original)
                    
                    if segment_end_compressed <= compressed_time <= next_segment_start_compressed:
                        # 时间在静音段中，映射到原始音频的对应位置
                        # 静音段在压缩音频中被移除，所以直接跳到下一个片段的开始
                        return segment_end_original + (compressed_time - segment_end_compressed)
                
                # 更新累积时间
                accumulated_compressed += segment_duration_original
                accumulated_original = segment_end_original
            
            # 如果没有找到匹配的片段，按比例映射
            if processed_duration > 0:
                scale = original_duration / processed_duration
                return compressed_time * scale
            else:
                return compressed_time
        
        print(f"🔄 高级调整SRT时间戳以对齐原始音频...")
        print(f"   原始音频总时长: {original_duration:.2f}秒 ({original_duration/60:.2f}分钟)")
        print(f"   处理后音频时长: {processed_duration:.2f}秒 ({processed_duration/60:.2f}分钟)")
        if original_duration > 0 and processed_duration > 0:
            print(f"   压缩比例: {(1 - processed_duration / original_duration) * 100:.1f}%")
        
        # 创建新的字幕文件
        adjusted_subs = pysubs2.SSAFile()
        adjusted_subs.styles = subs.styles
        adjusted_subs.fonts_opaque = subs.fonts_opaque
        
        # 调整每个字幕事件的时间戳
        for event in subs.events:
            adjusted_event = pysubs2.SSAEvent()
            adjusted_event.start = event.start
            adjusted_event.end = event.end
            adjusted_event.text = event.text
            
            # 将毫秒转换为秒进行处理
            start_time_compressed = event.start / 1000.0
            end_time_compressed = event.end / 1000.0
            
            # 映射到原始音频时间
            adjusted_start = map_compressed_to_original(start_time_compressed)
            adjusted_end = map_compressed_to_original(end_time_compressed)
            
            # 转换回毫秒
            adjusted_event.start = int(adjusted_start * 1000)
            adjusted_event.end = int(adjusted_end * 1000)
            
            adjusted_subs.events.append(adjusted_event)
        
        # 保存调整后的SRT文件
        adjusted_subs.styles["Default"].fontsize = 14.0
        adjusted_subs.styles["Default"].shadow = 0.5
        adjusted_subs.styles["Default"].outline = 1.0
        
        adjusted_subs.save(output_srt)
        print(f"✅ 高级时间戳调整完成: {output_srt}")
        
        return True
        
    except Exception as e:
        print(f"❌ 高级调整SRT时间戳失败: {e}")
        return False