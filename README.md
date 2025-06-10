## 字幕处理流程
首先，使用剪映对影片进行粗剪，去掉片头等待、片尾空白及中间有剪辑标记的区域，导出为 h264编码，2k分辨率的视频。

### 生成原始字幕
1. 切换为course环境
2. 调用 python transcript.py transcript /path/to/*/parent/*.mp4

在转换过程中，会自动引用words.md作为字典，进行错误纠正。转换的结果会保存在/tmp/parent目录中。parent为包含视频文章的父级目录。

### 编辑字幕

手工，可以vscode中完成。生成的字幕需要进一步编辑，比如，发现其中未被纠正的错误，删除个别表达不通顺的地方。删除的方法是在该行字幕前加上 [del] 标记。这样再调用cut方法，这些部分就会被删除。

### 应用字幕

调用以下命令：

python transcript.py cut /path/to/parent

在生成原始字幕阶段，如果没有指定保存目录的话，此时的目录就是默认的/tmp/parent

### 合并剪辑

<!-- 合并cut的结果，传入工作目录，比如/tmp/14 和保存名字 -->
3. python transcript.py merge
