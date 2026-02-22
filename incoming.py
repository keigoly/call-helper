"""機能A: 着信時ガイダンス制御。

【レイテンシー最適化済み】
事前準備フェーズ（音声読み込み・デバイス検索）を先に行い、
ミュート→再生の間のラグを最小化する。

処理順序:
1. 音声ファイルを事前にメモリへ読み込み（重いI/O）
2. VB-CABLE デバイスを事前検索（デバイス列挙）
3. 物理マイクをミュート + スピーカーをミュート
4. 即座に音声ガイダンスを再生開始
5. 録音サブプロセスを起動（再生と並行）
6. 再生完了を待機
7. マイク・スピーカーのミュート解除（通常通話に復帰）
"""

import logging
import os
import subprocess
import sys
import time

import sounddevice as sd
import soundfile as sf

from audio_devices import (
    find_virtual_cable_device,
    mute_physical_mic,
    unmute_physical_mic,
    mute_default_speaker,
    unmute_default_speaker,
)
from config_loader import load_config, _base_dir

logger = logging.getLogger(__name__)


def _launch_recording_subprocess(number: str | None = None) -> None:
    """録音サブプロセスをバックグラウンドで起動する。"""
    try:
        if getattr(sys, "frozen", False):
            record_cmd = [sys.executable, "--mode=record"]
        else:
            script_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "call_helper.py"
            )
            record_cmd = [sys.executable, script_path, "--mode=record"]

        if number:
            record_cmd.append(f"--number={number}")

        CREATE_NO_WINDOW = 0x08000000
        subprocess.Popen(record_cmd, creationflags=CREATE_NO_WINDOW)
        logger.info("録音サブプロセスを起動しました: %s", " ".join(record_cmd))
    except Exception:
        logger.exception("録音サブプロセスの起動に失敗しました（ガイダンス再生は続行します）")


def run(number: str | None = None) -> None:
    """着信時ガイダンス処理を実行する。

    Parameters
    ----------
    number : str | None
        着信番号（ログ記録用）。
    """
    if number:
        logger.info("着信番号: %s", number)

    t_start = time.perf_counter()
    config = load_config()

    # ============================================================
    # 事前準備フェーズ（時間のかかるI/O処理をミュート前に実行）
    # ============================================================

    # --- 音声ファイルの事前読み込み ---
    guidance_file = config.get("general", "guidance_file")
    if not os.path.isabs(guidance_file):
        guidance_file = os.path.join(_base_dir(), guidance_file)

    if not os.path.isfile(guidance_file):
        logger.warning("音声ファイルが見つかりません: %s", guidance_file)
        return

    t0 = time.perf_counter()
    data, samplerate = sf.read(guidance_file, dtype="float32")
    t1 = time.perf_counter()
    duration_sec = len(data) / samplerate
    logger.info(
        "音声ファイルを事前読み込み完了: %s (%.1f秒, %dHz, 読み込み %.0fms)",
        guidance_file, duration_sec, samplerate, (t1 - t0) * 1000,
    )

    # --- 仮想ケーブルデバイスの事前検索 ---
    cable_name = config.get("audio", "virtual_cable_name")
    device_index = find_virtual_cable_device(cable_name)
    if device_index is None:
        logger.error("仮想ケーブルデバイス '%s' が見つかりません", cable_name)
        return

    t_ready = time.perf_counter()
    logger.info("事前準備完了 (%.0fms)", (t_ready - t_start) * 1000)

    # ============================================================
    # 時間クリティカルフェーズ（ミュート→再生を最速で実行）
    # ============================================================

    # --- マイクミュート ---
    try:
        mute_physical_mic()
    except Exception:
        logger.error("マイクミュートに失敗しました。処理を中断します。")
        return

    # --- スピーカーミュート（ハウリング防止） ---
    speaker_muted = False
    try:
        mute_default_speaker()
        speaker_muted = True
    except Exception:
        logger.warning("スピーカーミュートに失敗しました（ガイダンス再生は続行します）")

    try:
        # --- 即座にガイダンス再生開始 ---
        t_play = time.perf_counter()
        logger.info(
            "音声ガイダンスを再生します (ミュート→再生: %.0fms)",
            (t_play - t_ready) * 1000,
        )
        sd.play(data, samplerate=samplerate, device=device_index)

        # --- 再生開始後に録音サブプロセスを起動（再生と並行） ---
        _launch_recording_subprocess(number)

        # --- 再生完了待機 ---
        sd.wait()
        logger.info("音声ガイダンスの再生が完了しました")

    except Exception:
        logger.exception("ガイダンス再生中にエラーが発生しました")
    finally:
        # --- 必ずミュート解除 ---
        try:
            unmute_physical_mic()
        except Exception:
            logger.exception("マイクミュート解除に失敗しました — 手動で解除してください")
        if speaker_muted:
            try:
                unmute_default_speaker()
            except Exception:
                logger.exception("スピーカーミュート解除に失敗しました — 手動で解除してください")
