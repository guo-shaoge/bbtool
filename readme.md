# 下载特定视频
 ./BBDown --show-all https://www.bilibili.com/video/BV1pXcgzQE8b --skip-cover

# 下载合集视频 
想根据一个视频链接下载该视频所在的合集里面的所有视频

1. 将单个视频链接放入 seeds.txt
2. 运行脚本 `./all_collections_v1.py --seeds ./downloads/eng/seeds.txt  --bbdown-args --work-dir ./downloads/eng --skip-cover --show-all`
   只下载音频: `./all_collections_v1.py --seeds ./downloads/eng/seeds.txt  --bbdown-args --work-dir ./downloads/eng --skip-cover --show-all --audio-only`

v2 版本示例:
```
./bbdown_all_collections.py \
  --bbdown ./BBDown \
  --seeds ./downloads/eng/seeds.txt \
  --after 2026-01-01 \
  --dry-run \
  --bbdown-args --work-dir ./downloads/eng --skip-cover --show-all

./bbdown_all_collections.py \
  --bbdown ./BBDown \
  --seeds ./downloads/eng/seeds.txt \
  --after 2026-01-01 \
  --bbdown-args --work-dir ./downloads/eng --skip-cover --show-all
```

# reference
reference: https://github.com/nilaoda/BBDown

# 音频转文字
需要在 mac 环境跑
```
brew install ffmpeg
# 装 3.11, 3.14 报错 wheel 可能包安装有问题
brew install python@3.11
/opt/homebrew/bin/python3.11 -m venv whisper-env311
source whisper-env311/bin/activate
python --version
pip install faster-whisper

python -m pip install "httpx[socks]"

vpn_on
python audio_to_text.py ./downloads/eng_only_audio/【New\ Scientist】新年最好的健康投资：不是盲目买补剂，而是学会“平衡”免疫力/\[P1\]中英字幕.m4a
python ./batch_audio_to_text.py
```
