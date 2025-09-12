# FuyaoDownloadMusic

一个可以从主流音乐平台下载音乐的第三方库

# 下载

```cmd
pip install FuyaoDownloadMusic
```

# 使用

1.选择音乐源：目前支持网易云（netease）

2.音乐源对应的搜索、获取、下载的参数

```python
SEARCH_PARAMS = {
    "keyword": "知我",
    "limit": 30
}

SONG_URL_PARAMS = {
    "songId": 1394167216,
}

DOWNLOAD_SONG_PARAMS = {
    "songUrl": "",
    "songName": "知我",
    "songAuthors": "",
    "songSavePath": "",
}
```

3.代码样例

```python
from FuyaoDownloadMusic.download import DownloadMusic

COOKIE_STR = {
    "netease": "MUSIC_U",  # 获取网易的MUSIC_U
}

dm = DownloadMusic(
    musicSrcKey="netease",  # 音乐源
    cookieStr="...",  # 音乐平台的会员关键cookie
)

# search
dm.search({
    "keyword": "知我",
    "limit": 30
})
# return songId、songName、songAuthors
# [{"songId": xxx, "songName": "xxx", "songAuthors": ["xxx", "xxxx"]}]

# get song url
dm.getSongUrl({
    "songId": 1394167216,
})
# return songUrl


# download music
dm.downloadMusic({
    "songUrl": "https://....",
    "songName": "知我",
    "songAuthors": "...",
    "songSavePath": "E:/music",
})

```

# 注意

- 需要node环境,且在项目根目录安装 crypto-js 库
- 使用该包需要保证nodejs环境且在代码同层级目录使用 npm install crypto-js

# 更新日志

版本说明：

```text
0.0.1:
    0:发行版本
    0:开发版本
    1:测试版本
```

## v0.0.8
1.优化第三方库及项目结构

## v0.0.7
1.新增酷狗音乐源-vip

2.将各个音乐源的download函数提取放置在download模块中，减少重复代码

## v0.0.6

1.修改返回格式："xxx;xxx" => ["xxx", "xxx"]

## v0.0.5

1.修复包中没有js文件<br>
2.修复logger.info的报错问题

## v0.0.2

1.修复导包问题

## v0.0.1

1.音乐源: 网易(netease)<br>
2.对网易云的api做逆向,目前提供网易的vip的cookie,
但是不负责其稳定性,如需要稳定vip请自己获取





