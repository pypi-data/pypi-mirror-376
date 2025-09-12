"""
encoding:   -*- coding: utf-8 -*-
@Time           :  2025/9/11 15:17
@Project_Name   :  FuyaoDownloadMusic
@Author         :  lhw
@File_Name      :  execJsUtil.py

功能描述

实现步骤

"""
import execjs


def execJsCode(jsFilePath, *args):
    with open(jsFilePath, "r", encoding="utf-8") as f:
        js_code = f.read()

    js_compile = execjs.compile(js_code)
    encrypted = js_compile.call("main", *args)

    return encrypted
