#!/usr/bin/env python3
"""
基本功能测试脚本
"""

import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """测试模块导入"""
    print("测试模块导入...")
    try:
        import transcript.transcript as transcript
        print("✅ transcript模块导入成功")
        
        # 测试主要函数是否存在
        functions = [
            'transcript', 'cut', 'merge', 'process_video',
            'align_subtitles_with_audio', 'init_jieba'
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

def test_dependencies():
    """测试依赖包"""
    print("\n测试依赖包...")
    dependencies = [
        'fire', 'jieba', 'opencc', 'pysubs2', 'whisperx'
    ]
    
    all_ok = True
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep} 可用")
        except ImportError:
            print(f"❌ {dep} 不可用")
            all_ok = False
    
    return all_ok

def test_model_config():
    """测试模型配置"""
    print("\n测试模型配置...")
    try:
        import transcript.transcript as transcript
        
        print(f"模型目录: {transcript.model_dir}")
        print(f"Whisper模型: {transcript.whisperx_model}")
        print(f"对齐模型: {transcript.w2v_model}")
        
        # 检查模型目录是否存在
        model_path = Path(transcript.model_dir)
        if model_path.exists():
            print(f"✅ 模型目录存在: {model_path}")
        else:
            print(f"⚠️  模型目录不存在: {model_path}")
            
        return True
    except Exception as e:
        print(f"❌ 模型配置测试失败: {e}")
        return False

def test_words_dict():
    """测试自定义词典"""
    print("\n测试自定义词典...")
    try:
        import transcript.transcript as transcript
        
        words_file = Path("words.md")
        if words_file.exists():
            print(f"✅ 词典文件存在: {words_file}")
            
            # 测试词典加载
            custom_map = transcript.init_jieba()
            print(f"✅ 加载了 {len(custom_map)} 个自定义词汇")
            
            # 显示前几个词汇
            for i, (wrong, right) in enumerate(list(custom_map.items())[:3]):
                print(f"   {wrong} -> {right}")
                
        else:
            print(f"❌ 词典文件不存在: {words_file}")
            
        return True
    except Exception as e:
        print(f"❌ 词典测试失败: {e}")
        return False

def test_file_operations():
    """测试文件操作功能"""
    print("\n测试文件操作...")
    try:
        from transcript.transcript import _ms_to_hms, probe_duration
        
        # 测试时间转换
        test_ms = 65000  # 1分5秒
        hms = _ms_to_hms(test_ms)
        print(f"✅ 时间转换: {test_ms}ms -> {hms}")
        
        return True
    except Exception as e:
        print(f"❌ 文件操作测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=== 基本功能测试 ===\n")
    
    tests = [
        test_imports,
        test_dependencies,
        test_model_config,
        test_words_dict,
        test_file_operations
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ 测试异常: {e}")
    
    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("🎉 所有测试通过！")
        return 0
    else:
        print("⚠️  部分测试失败，请检查配置")
        return 1

if __name__ == "__main__":
    sys.exit(main())
