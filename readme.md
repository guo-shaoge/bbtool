# 下载特定视频
 ./BBDown --show-all https://www.bilibili.com/video/BV1pXcgzQE8b --skip-cover

# 下载合集视频 
想根据一个视频链接下载该视频所在的合集里面的所有视频

1. 将单个视频链接放入 seeds.txt
2. 运行脚本 `./all_collections_v1.py --seeds ./downloads/eng/seeds.txt  --bbdown-args --work-dir ./downloads/eng`

v2 版本示例:
```
./bbdown_all_collections.py \
  --bbdown ./BBDown \
  --seeds ./downloads/eng/seeds.txt \
  --after 2026-01-01 \
  --dry-run \
  --bbdown-args --work-dir ./downloads/eng

./bbdown_all_collections.py \
  --bbdown ./BBDown \
  --seeds ./downloads/eng/seeds.txt \
  --after 2026-01-01 \
  --bbdown-args --work-dir ./downloads/eng
```

# BBDown
reference: https://github.com/nilaoda/BBDown
