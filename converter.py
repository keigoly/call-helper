"""機能B: WAV → MP3 変換。

1. watch_folder をスキャンして .wav ファイルを列挙
2. 各 WAV ファイルを pydub (FFmpeg) で MP3 に変換
3. MP3 を output_folder に保存
4. 元 WAV ファイルを backup_folder に移動
5. 処理結果をログ出力
"""

import logging
import os
import shutil

from pydub import AudioSegment

from config_loader import load_config

logger = logging.getLogger(__name__)


def run() -> None:
    """WAV → MP3 変換処理を実行する。"""
    config = load_config()

    watch_folder = config.get("convert", "watch_folder")
    output_folder = config.get("convert", "output_folder")
    backup_folder = config.get("convert", "backup_folder")

    # フォルダの存在確認・作成
    for folder, label in [
        (watch_folder, "監視フォルダ"),
        (output_folder, "出力フォルダ"),
        (backup_folder, "バックアップフォルダ"),
    ]:
        if not os.path.isdir(folder):
            logger.info("%sを作成します: %s", label, folder)
            os.makedirs(folder, exist_ok=True)

    # WAV ファイルの列挙
    wav_files = [f for f in os.listdir(watch_folder) if f.lower().endswith(".wav")]
    if not wav_files:
        logger.info("変換対象の WAV ファイルがありません: %s", watch_folder)
        return

    logger.info("%d 件の WAV ファイルを検出しました", len(wav_files))

    success_count = 0
    fail_count = 0

    for wav_name in wav_files:
        wav_path = os.path.join(watch_folder, wav_name)
        mp3_name = os.path.splitext(wav_name)[0] + ".mp3"
        mp3_path = os.path.join(output_folder, mp3_name)
        backup_path = os.path.join(backup_folder, wav_name)

        try:
            logger.info("変換中: %s", wav_name)
            audio = AudioSegment.from_wav(wav_path)
            audio.export(mp3_path, format="mp3")
            logger.info("変換完了: %s → %s", wav_name, mp3_path)

            # 元ファイルをバックアップに移動
            shutil.move(wav_path, backup_path)
            logger.info("バックアップ: %s → %s", wav_name, backup_path)

            success_count += 1
        except Exception:
            logger.exception("変換失敗: %s — スキップします", wav_name)
            fail_count += 1

    logger.info(
        "変換処理完了 — 成功: %d 件, 失敗: %d 件", success_count, fail_count
    )
