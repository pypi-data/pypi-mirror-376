"""
encoding:   -*- coding: utf-8 -*-
@Time           :  2025/9/11 14:33
@Project_Name   :  FuyaoDownloadMusic
@Author         :  lhw
@File_Name      :  kugou.py

功能描述

实现步骤

"""
import json
import time
import logging
import requests
from FuyaoDownloadMusic.utils.execJsUtil import execJsCode
from FuyaoDownloadMusic.utils.getJSPath import getJsCodePath

APIS = {
    "search": "https://complexsearch.kugou.com/v2/search/song",
    "songInfo": "https://wwwapi.kugou.com/play/songinfo",
}

KUGOU_ENCRYPT_JS_PATH = getJsCodePath(__file__, "KugouEncrypt.js")


def kuwoEncrypt(logger: logging.Logger, data: list):
    logger.info("===Kuwo加密开始===")

    # data = [
    #     "NVPh5oo715z5DIWAeQlhMDsWXXQV4hwt",
    #     "appid=1014",
    #     "bitrate=0",
    #     "callback=callback123",
    #     "clienttime=" + str(clientTime),
    #     "clientver=1000",
    #     "dfid=1bq3hS0l3VXG3BD65H3ey1iP",
    #     "filter=10",
    #     "inputtype=0",
    #     "iscorrection=1",
    #     "isfuzzy=0",
    #     "keyword=" + keyword,
    #     "mid=c225a1e5d5acd9c6d0ba1255f58ddaf5",
    #     "page=1",
    #     "pagesize=30",
    #     "platform=WebFilter",
    #     "privilege_filter=0",
    #     "srcappid=2919",
    #     "token=",
    #     "userid=0",
    #     "uuid=c225a1e5d5acd9c6d0ba1255f58ddaf5",
    #     "NVPh5oo715z5DIWAeQlhMDsWXXQV4hwt"
    # ]

    data = "".join(data)

    logger.info(f"加密前: {data}")

    encrypted = execJsCode(KUGOU_ENCRYPT_JS_PATH, data)

    logger.info(f"加密后: {encrypted}")

    return encrypted


class KuGou:
    def __init__(
            self,
            logger: logging.Logger = logging.getLogger(),
    ):
        self.session = requests.Session()

        self.logger = logger

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0",
            "Referer": "https://www.kugou.com/",
            # "Cookie": "kg_mid=c225a1e5d5acd9c6d0ba1255f58ddaf5; kg_dfid=1bq3hS0l3VXG3BD65H3ey1iP; kg_dfid_collect=d41d8cd98f00b204e9800998ecf8427e; Hm_lvt_aedee6983d4cfc62f509129360d6bb3d=1757572305; HMACCOUNT=75ED759C6432177E; Hm_lpvt_aedee6983d4cfc62f509129360d6bb3d=1757572313",

        }

    def search(self, searchParams):
        url = APIS["search"]

        clientTime = int(time.time() * 1000)

        keyword = searchParams["keyword"]

        data = [
            "NVPh5oo715z5DIWAeQlhMDsWXXQV4hwt",
            "appid=1014",
            "bitrate=0",
            "callback=callback123",
            "clienttime=" + str(clientTime),
            "clientver=1000",
            "dfid=1bq3hS0l3VXG3BD65H3ey1iP",
            "filter=10",
            "inputtype=0",
            "iscorrection=1",
            "isfuzzy=0",
            "keyword=" + keyword,
            "mid=c225a1e5d5acd9c6d0ba1255f58ddaf5",
            "page=1",
            "pagesize=30",
            "platform=WebFilter",
            "privilege_filter=0",
            "srcappid=2919",
            "token=",
            "userid=0",
            "uuid=c225a1e5d5acd9c6d0ba1255f58ddaf5",
            "NVPh5oo715z5DIWAeQlhMDsWXXQV4hwt"
        ]

        params = {
            "callback": "callback123",
            "srcappid": "2919",
            "clientver": "1000",
            "clienttime": clientTime,  #
            "mid": "c225a1e5d5acd9c6d0ba1255f58ddaf5",
            "uuid": "c225a1e5d5acd9c6d0ba1255f58ddaf5",
            "dfid": "1bq3hS0l3VXG3BD65H3ey1iP",
            "keyword": keyword,  # keyword
            "page": "1",
            "pagesize": searchParams["limit"],
            "bitrate": "0",
            "isfuzzy": "0",
            "inputtype": "0",
            "platform": "WebFilter",
            "userid": "0",
            "iscorrection": "1",
            "privilege_filter": "0",
            "filter": "10",
            "token": "",
            "appid": "1014",
            "signature": kuwoEncrypt(self.logger, data)  #
        }

        response = self.session.get(url=url, headers=self.headers, params=params)

        result = response.text

        result = result[len('callback123('):-2]

        result = json.loads(result)

        print(result)

        songInfoList = []
        for song in result["data"]["lists"]:
            songInfoList.append({
                "songName": song["SongName"],
                "songAuthors": [i['name'] for i in song["Singers"]],
                "songId": song["EMixSongID"]
            })

        print(songInfoList)

        return songInfoList

    def getSongUrl(self, songUrlParams):
        url = APIS["songInfo"]

        clientTime = round(time.time() * 1000)
        # clientTime = 1757579237

        data = [
            "NVPh5oo715z5DIWAeQlhMDsWXXQV4hwt",
            "appid=1014",
            f"clienttime={round(clientTime)}",
            "clientver=20000",
            "dfid=1bq3hS0l3VXG3BD65H3ey1iP",
            f"encode_album_audio_id={songUrlParams['songId']}",
            "mid=c225a1e5d5acd9c6d0ba1255f58ddaf5",
            "platid=4",
            "srcappid=2919",
            "token=02d54da9b86156c330645c140955716624e3ea787811c0adeab445e8ff5d6ccf",
            "userid=2402675940",
            "uuid=c225a1e5d5acd9c6d0ba1255f58ddaf5",
            "NVPh5oo715z5DIWAeQlhMDsWXXQV4hwt"
        ]

        params = {
            "srcappid": "2919",
            "clientver": "20000",
            "clienttime": clientTime,
            "mid": "c225a1e5d5acd9c6d0ba1255f58ddaf5",
            "uuid": "c225a1e5d5acd9c6d0ba1255f58ddaf5",
            "dfid": "1bq3hS0l3VXG3BD65H3ey1iP",
            "appid": "1014",
            "platid": "4",
            "encode_album_audio_id": songUrlParams["songId"],
            "token": "02d54da9b86156c330645c140955716624e3ea787811c0adeab445e8ff5d6ccf",
            "userid": "2402675940",
            "signature": kuwoEncrypt(self.logger, data)
        }

        response = self.session.get(url=url, headers=self.headers, params=params)

        result = response.json()

        print(result)

        songUrl = result["data"]["play_url"]

        return songUrl

    def download(self, downloadMusicParams):
        """
        下载
        :param downloadMusicParams:
        :return:
        """
        # self.logger.info("===下载歌曲===")
        #
        # self.logger.info(f"歌曲名: {downloadMusicParams['songName']}; 歌曲源地址: {downloadMusicParams['songUrl']}")
        #
        # filePath = f"{downloadMusicParams['songSavePath']}/{downloadMusicParams['songName']}_{downloadMusicParams['songAuthors']}.mp3"
        # with open(filePath, "wb") as f:
        #     f.write(self.session.get(url=downloadMusicParams['songUrl'], headers=self.headers).content)
        #
        # self.logger.info(
        #     f"{downloadMusicParams['songName']} 已经保存到 {filePath}")


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',  # 时间格式
    )
    logger = logging.getLogger()
    kg = KuGou(logger)
    # kg.search({
    #     "keyword": "Always Online",
    #     "limit": 30,
    # })

    print(kg.getSongUrl({
        "songId": "j3bxf28",
    }))

    # kuwoEncrypt(logger, "知我", int(time.time() * 1000))
