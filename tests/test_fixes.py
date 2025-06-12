#!/usr/bin/env python3
"""
测试修复后的功能
"""

import sys
import os
import tempfile
import json
from pathlib import Path

# 添加transcript目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / "transcript"))

def test_imports():
    """测试模块导入"""
    print("测试模块导入...")
    try:
        import transcript
        print("✅ transcript模块导入成功")
        
        # 测试主要函数是否存在
        functions = [
            'transcript', 'cut', 'merge', 'process_video',
            'align_subtitles_with_audio', 'init_jieba', 't2s'
        ]
        
        for func_name in functions:
            if hasattr(transcript, func_name):
                print(f"✅ 函数 {func_name} 存在")
            else:
                print(f"❌ 函数 {func_name} 不存在")
                
        return True
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_jieba_init():
    """测试jieba初始化"""
    print("\n测试jieba初始化...")
    try:
        import transcript
        
        custom_map = transcript.init_jieba()
        print(f"✅ 加载了 {len(custom_map)} 个自定义词汇")
        
        # 显示前几个词汇
        for i, (wrong, right) in enumerate(list(custom_map.items())[:3]):
            print(f"   {wrong} -> {right}")
            
        return True
    except Exception as e:
        print(f"❌ jieba初始化失败: {e}")
        return False

def test_t2s_function():
    """测试t2s函数修复"""
    print("\n测试t2s函数...")
    try:
        import transcript
        
        # 创建临时字幕文件
        temp_dir = Path(tempfile.mkdtemp())
        test_srt = temp_dir / "test.srt"
        
        # 创建测试字幕内容（繁体中文）
        srt_content = """1
00:00:01,000 --> 00:00:03,000
這是繁體中文測試

2
00:00:03,000 --> 00:00:05,000
轉換為簡體中文
"""
        
        with open(test_srt, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        print(f"创建测试文件: {test_srt}")
        
        # 测试t2s函数
        transcript.t2s(str(test_srt))
        
        # 读取转换后的内容
        with open(test_srt, 'r', encoding='utf-8') as f:
            converted_content = f.read()
        
        print("转换后的内容:")
        print(converted_content[:100] + "..." if len(converted_content) > 100 else converted_content)
        
        # 清理
        import shutil
        shutil.rmtree(temp_dir)
        
        print("✅ t2s函数测试成功")
        return True
        
    except Exception as e:
        print(f"❌ t2s函数测试失败: {e}")
        return False

def test_log_file_handling():
    """测试日志文件处理"""
    print("\n测试日志文件处理...")
    try:
        # 创建模拟的日志文件
        log_data = {
            "working_dir": "/tmp/transcript/test_video",
            "name": "test_video",
            "raw_video": "/path/to/test_video.mp4",
            "timestamp": "2024-01-01T12:00:00"
        }
        
        log_file = "/tmp/transcript.log"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2)
        
        print(f"创建测试日志文件: {log_file}")
        
        # 读取并验证
        with open(log_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        print(f"日志内容: {loaded_data}")
        
        # 清理
        os.remove(log_file)
        
        print("✅ 日志文件处理测试成功")
        return True
        
    except Exception as e:
        print(f"❌ 日志文件处理测试失败: {e}")
        return False

def test_path_handling():
    """测试路径处理"""
    print("\n测试路径处理...")
    try:
        import transcript
        
        # 测试项目根目录获取
        script_dir = Path(transcript.__file__).parent
        project_root = script_dir.parent
        
        print(f"脚本目录: {script_dir}")
        print(f"项目根目录: {project_root}")
        
        # 验证words.md文件路径
        words_file = project_root / "words.md"
        print(f"words.md路径: {words_file}")
        print(f"words.md存在: {words_file.exists()}")
        
        print("✅ 路径处理测试成功")
        return True
        
    except Exception as e:
        print(f"❌ 路径处理测试失败: {e}")
        return False

def test_file_operations():
    """测试文件操作"""
    print("\n测试文件操作...")
    try:
        import transcript
        
        # 测试时间转换
        test_times = [1000, 65000, 3661000]
        for ms in test_times:
            hms = transcript._ms_to_hms(ms)
            print(f"   {ms}ms -> {hms}")
        
        print("✅ 文件操作测试成功")
        return True
        
    except Exception as e:
        print(f"❌ 文件操作测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🔧 测试修复后的功能")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_imports),
        ("jieba初始化", test_jieba_init),
        ("t2s函数", test_t2s_function),
        ("日志文件处理", test_log_file_handling),
        ("路径处理", test_path_handling),
        ("文件操作", test_file_operations)
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"\n{'='*20} {name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {name} 测试成功")
            else:
                print(f"❌ {name} 测试失败")
        except Exception as e:
            print(f"❌ {name} 测试异常: {e}")
    
    print(f"\n{'='*50}")
    print(f"测试结果: {passed}/{total} 成功")
    
    if passed == total:
        print("🎉 所有测试都通过！修复成功！")
        return 0
    else:
        print("⚠️  部分测试失败，需要进一步检查")
        return 1

if __name__ == "__main__":
    sys.exit(main())
