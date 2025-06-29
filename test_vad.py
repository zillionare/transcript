#!/usr/bin/env python3
import subprocess
import os

# 直接定义cpp_path和检查函数
cpp_path = "/Volumes/share/data/whisper.cpp"

def check_whisper_cpp_vad_support():
    """检查whisper.cpp是否支持VAD功能
    
    通过运行whisper-cli --help检查是否支持-vm和--vad参数
    
    Returns:
        bool: 如果支持VAD返回True，否则返回False
    """
    try:
        whisper = os.path.join(cpp_path, "whisper-cli")
        if not os.path.exists(whisper):
            print(f"❌ whisper-cli不存在: {whisper}")
            return False
            
        # 检查help输出中是否包含VAD相关参数
        result = subprocess.run([whisper, "--help"], 
                              capture_output=True, text=True, timeout=5)
        help_text = result.stdout + result.stderr
        
        print(f"whisper-cli路径: {whisper}")
        print(f"help命令返回码: {result.returncode}")
        print(f"help输出长度: {len(help_text)}")
        
        # 检查是否支持VAD参数
        vad_supported = "-vm" in help_text or "--vad" in help_text
        
        if vad_supported:
            print("✅ whisper.cpp支持VAD功能")
        else:
            print("⚠️ 当前whisper.cpp版本不支持VAD功能")
            print("   请使用支持VAD的whisper.cpp版本或重新编译")
            
        return vad_supported
        
    except Exception as e:
        print(f"⚠️ 检查whisper.cpp VAD支持时出错: {e}")
        return False

if __name__ == "__main__":
    print('测试VAD支持检查功能...')
    result = check_whisper_cpp_vad_support()
    print(f'VAD支持检查结果: {result}')