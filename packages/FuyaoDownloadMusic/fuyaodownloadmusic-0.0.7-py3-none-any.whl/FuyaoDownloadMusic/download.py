"""
encoding:   -*- coding: utf-8 -*-
@Time           :  2025/9/5 17:47
@Project_Name   :  FuyaoDownloadMusic
@Author         :  lhw
@File_Name      :  download.py

功能描述

实现步骤

"""
import logging
from FuyaoDownloadMusic.netease import Netease
import requests

MUSIC_SRC = {
    "netease": Netease,
}

SEARCH_PARAMS = {
    "netease": {
        "keyword": "知我",
        "limit": 30
    }
}


class DownloadMusic:

    def __init__(self, musicSrcKey: str, logger: logging.Logger = logging.getLogger(), cookieStr=None):

        self.logger = logger

        self.session = requests.Session()

        if not cookieStr:
            self.musicSrc = MUSIC_SRC[musicSrcKey](logger)
        else:
            self.musicSrc = MUSIC_SRC[musicSrcKey](logger, cookieStr)

    def search(self, searchParams):
        return self.musicSrc.search(searchParams)

    def getSongUrl(self, songUrlParams):
        return self.musicSrc.getSongUrl(songUrlParams)

    def downloadMusic(self, downloadMusicParams):
        """
        下载歌曲
        :param downloadMusicParams:
        :return:
        """

        self.logger.info("===下载歌曲===")

        self.logger.info(f"歌曲名: {downloadMusicParams['songName']}; 歌曲源地址: {downloadMusicParams['songUrl']}")

        filePath = f"{downloadMusicParams['songSavePath']}/{downloadMusicParams['songName']}_{downloadMusicParams['songAuthors']}.mp3"
        with open(filePath, "wb") as f:
            f.write(self.session.get(url=downloadMusicParams['songUrl'], headers=self.headers).content)

        self.logger.info(
            f"{downloadMusicParams['songName']} 已经保存到 {filePath}")

        self.musicSrc.download(downloadMusicParams)


if __name__ == '__main__':
    dm = DownloadMusic("netease")
    # dm.search({
    #     "keyword": "此生不换",
    #     "limit": 50,
    # })

    songUrl = dm.getSongUrl({
        "songId": 1934168650,
    })
    print(songUrl)
