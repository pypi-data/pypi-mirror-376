"""
encoding:   -*- coding: utf-8 -*-
@Time           :  2025/9/11 15:09
@Project_Name   :  FuyaoDownloadMusic
@Author         :  lhw
@File_Name      :  getJSPath.py

功能描述

实现步骤

"""

from pathlib import Path

def getJsCodePath(currentPath, jsFileName):
    current_path = Path(currentPath).resolve().parent
    return current_path / 'js' / jsFileName