"""config.ini の読み込みユーティリティ。

EXE化された場合でも、実行ファイルと同じディレクトリにある config.ini を自動検出する。
"""

import configparser
import os
import sys


def _base_dir() -> str:
    """実行ファイル（またはスクリプト）が置かれているディレクトリを返す。"""
    if getattr(sys, "frozen", False):
        # PyInstaller で EXE 化された場合
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def load_config() -> configparser.ConfigParser:
    """config.ini を読み込んで ConfigParser を返す。

    ファイルが存在しない場合は FileNotFoundError を送出する。
    """
    config_path = os.path.join(_base_dir(), "config.ini")
    if not os.path.isfile(config_path):
        raise FileNotFoundError(f"設定ファイルが見つかりません: {config_path}")

    config = configparser.ConfigParser()
    config.read(config_path, encoding="utf-8")
    return config
