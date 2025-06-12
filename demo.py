#!/usr/bin/env python3
"""
演示脚本 - 展示视频字幕处理功能
"""

import sys
import os
from pathlib import Path
import tempfile
import shutil

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

def create_demo_video():
    """创建一个演示用的短视频"""
    print("创建演示视频...")
    
    # 创建一个简单的测试视频（5秒，纯色+音频）
    demo_video = Path("/tmp/demo_video.mp4")
    
    # 使用ffmpeg创建测试视频
    cmd = f"""ffmpeg -f lavfi -i "testsrc2=duration=5:size=640x480:rate=30" \
-f lavfi -i "sine=frequency=1000:duration=5" \
-c:v libx264 -c:a aac -shortest -y {demo_video}"""
    
    try:
        os.system(cmd)
        if demo_video.exists():
            print(f"✅ 演示视频已创建: {demo_video}")
            return demo_video
        else:
            print("❌ 演示视频创建失败")
            return None
    except Exception as e:
        print(f"❌ 创建演示视频时出错: {e}")
        return None

def create_demo_subtitle():
    """创建演示字幕文件"""
    demo_srt = Path("/tmp/demo_video.srt")
    
    subtitle_content = """1
00:00:00,000 --> 00:00:02,000
大家好，欢迎来到演示

2
00:00:02,000 --> 00:00:03,000
呃

3
00:00:03,000 --> 00:00:05,000
[DEL]这段要删除

4
00:00:05,000 --> 00:00:07,000
这是最后一段内容
"""
    
    with open(demo_srt, 'w', encoding='utf-8') as f:
        f.write(subtitle_content)
    
    print(f"✅ 演示字幕已创建: {demo_srt}")
    return demo_srt

def demo_basic_functions():
    """演示基本功能"""
    print("\n=== 演示基本功能 ===")
    
    try:
        import transcript
        
        # 1. 测试词典加载
        print("\n1. 测试自定义词典...")
        custom_map = transcript.init_jieba()
        print(f"✅ 加载了 {len(custom_map)} 个自定义词汇")
        
        # 2. 测试时间转换
        print("\n2. 测试时间转换...")
        test_times = [1000, 65000, 3661000]
        for ms in test_times:
            hms = transcript._ms_to_hms(ms)
            print(f"   {ms}ms -> {hms}")
        
        # 3. 测试字幕处理
        print("\n3. 测试字幕处理...")
        demo_srt = create_demo_subtitle()
        
        if demo_srt and demo_srt.exists():
            # 应用词典纠错
            transcript.sub(demo_srt)
            print("✅ 字幕纠错完成")
            
            # 显示处理后的内容
            with open(demo_srt, 'r', encoding='utf-8') as f:
                content = f.read()
                print("处理后的字幕内容:")
                print(content[:200] + "..." if len(content) > 200 else content)
        
        return True
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        return False

def demo_file_operations():
    """演示文件操作"""
    print("\n=== 演示文件操作 ===")
    
    try:
        # 创建临时工作目录
        temp_dir = Path(tempfile.mkdtemp(prefix="transcript_demo_"))
        print(f"临时工作目录: {temp_dir}")
        
        # 创建演示文件
        demo_files = {
            "video.mp4": "演示视频文件",
            "subtitle.srt": "演示字幕文件",
            "config.json": '{"name": "demo", "version": "1.0"}'
        }
        
        for filename, content in demo_files.items():
            file_path = temp_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 创建文件: {file_path}")
        
        # 列出文件
        print("\n工作目录内容:")
        for item in temp_dir.iterdir():
            print(f"   {item.name} ({item.stat().st_size} bytes)")
        
        # 清理
        shutil.rmtree(temp_dir)
        print(f"✅ 清理临时目录: {temp_dir}")
        
        return True
        
    except Exception as e:
        print(f"❌ 文件操作演示失败: {e}")
        return False

def demo_command_line():
    """演示命令行接口"""
    print("\n=== 演示命令行接口 ===")
    
    print("可用的命令:")
    commands = [
        ("process", "完整的视频处理流程"),
        ("transcript", "视频转字幕"),
        ("cut", "剪辑视频"),
        ("merge", "合并输出"),
        ("test", "测试模型"),
        ("align", "字幕对齐")
    ]
    
    for cmd, desc in commands:
        print(f"   python transcript.py {cmd} - {desc}")
    
    print("\n示例命令:")
    examples = [
        "python transcript.py process /path/to/video.mp4",
        "python transcript.py test",
        "python transcript.py transcript /path/to/video.mp4 --output_dir /tmp/work"
    ]
    
    for example in examples:
        print(f"   {example}")

def main():
    """主演示函数"""
    print("🎬 视频字幕处理工具演示")
    print("=" * 50)
    
    # 检查依赖
    print("检查依赖...")
    try:
        import transcript
        import fire
        import jieba
        import pysubs2
        print("✅ 所有依赖都已安装")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install fire jieba opencc pysubs2 whisperx")
        return 1
    
    # 运行演示
    demos = [
        ("基本功能", demo_basic_functions),
        ("文件操作", demo_file_operations),
        ("命令行接口", demo_command_line)
    ]
    
    passed = 0
    for name, demo_func in demos:
        print(f"\n{'='*20} {name} {'='*20}")
        try:
            if demo_func():
                passed += 1
                print(f"✅ {name} 演示成功")
            else:
                print(f"❌ {name} 演示失败")
        except Exception as e:
            print(f"❌ {name} 演示异常: {e}")
    
    print(f"\n{'='*50}")
    print(f"演示结果: {passed}/{len(demos)} 成功")
    
    if passed == len(demos):
        print("🎉 所有演示都成功完成！")
        print("\n下一步:")
        print("1. 准备您的视频文件")
        print("2. 运行: python transcript.py process /path/to/your/video.mp4")
        print("3. 查看生成的字幕和视频文件")
        return 0
    else:
        print("⚠️  部分演示失败，请检查配置")
        return 1

if __name__ == "__main__":
    sys.exit(main())
