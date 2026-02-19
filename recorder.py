"""通話録音モジュール。

VoiceMeeter Output からオペレーター＋相手の両方の音声をキャプチャし、
MP3 形式で保存する。

- run(number): 録音を開始し、停止シグナルファイルまたは安全上限まで録音を継続
- stop(): 停止シグナルファイルを作成して録音プロセスを終了させる
"""

import logging
import os
import sys
import time
import wave
from datetime import datetime

import lameenc
import sounddevice as sd

from audio_devices import find_input_device
from config_loader import load_config, _base_dir

logger = logging.getLogger(__name__)

# シグナルファイル名（EXE ディレクトリに作成）
_PID_FILE = ".recording.pid"
_STOP_FILE = ".stop_recording"

# 録音パラメータ
_SAMPLE_RATE = 44100
_CHANNELS = 2  # ステレオ（デバイスが対応しない場合は自動調整）
_DTYPE = "int16"


def _wav_to_mp3(wav_path: str, mp3_path: str, sample_rate: int, channels: int) -> None:
    """lameenc を使って WAV → MP3 変換する（ffmpeg 不要）。"""
    with wave.open(wav_path, "rb") as wf:
        pcm_data = wf.readframes(wf.getnframes())

    encoder = lameenc.Encoder()
    encoder.set_bit_rate(128)
    encoder.set_in_sample_rate(sample_rate)
    encoder.set_channels(channels)
    encoder.set_quality(2)  # 0=best, 9=fastest

    mp3_data = encoder.encode(pcm_data)
    mp3_data += encoder.flush()

    with open(mp3_path, "wb") as f:
        f.write(mp3_data)
    logger.info("MP3 ファイルを保存しました: %s", mp3_path)


def _signal_path(filename: str) -> str:
    """EXE（またはスクリプト）ディレクトリ内のシグナルファイルパスを返す。"""
    return os.path.join(_base_dir(), filename)


def run(number: str | None = None) -> None:
    """録音メイン処理。

    VoiceMeeter Output から音声をキャプチャし、WAV → MP3 変換して保存する。

    Parameters
    ----------
    number : str | None
        電話番号（ファイル名に使用）。
    """
    config = load_config()

    # --- 設定読み込み ---
    output_folder = config.get("recording", "output_folder", fallback="D:\\CallRecordings")
    device_name = config.get("recording", "recording_device", fallback="VoiceMeeter Output")
    max_duration_min = config.getint("recording", "max_duration_minutes", fallback=120)
    max_duration_sec = max_duration_min * 60

    # --- 出力フォルダの作成 ---
    os.makedirs(output_folder, exist_ok=True)

    # --- 録音デバイスの検索 ---
    device_index = find_input_device(device_name)
    if device_index is None:
        logger.error("録音デバイス '%s' が見つかりません。録音を中止します。", device_name)
        return

    # --- デバイス情報の自動検出 ---
    dev_info = sd.query_devices(device_index)
    max_ch = dev_info["max_input_channels"]
    channels = min(_CHANNELS, max_ch) if max_ch > 0 else _CHANNELS
    sample_rate = int(dev_info["default_samplerate"])
    logger.info("録音チャンネル数: %d (デバイス最大: %d)", channels, max_ch)
    logger.info("録音サンプルレート: %d Hz (デバイスデフォルト)", sample_rate)

    # --- ファイル名の決定 ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    number_part = f"_{number}" if number else ""
    base_name = f"recording_{timestamp}{number_part}"
    wav_path = os.path.join(output_folder, f"{base_name}.wav")
    mp3_path = os.path.join(output_folder, f"{base_name}.mp3")

    # --- PID ファイルの作成 ---
    pid_path = _signal_path(_PID_FILE)
    stop_path = _signal_path(_STOP_FILE)

    # 前回の残留シグナルファイルをクリーンアップ
    for path in (pid_path, stop_path):
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass

    try:
        with open(pid_path, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
        logger.info("PID ファイルを作成しました: %s (PID=%d)", pid_path, os.getpid())
    except OSError:
        logger.exception("PID ファイルの作成に失敗しました")
        return

    # --- WAV ファイルを開いて録音開始 ---
    logger.info("録音を開始します: デバイス=[%d] %s", device_index, device_name)
    logger.info("出力先: %s", mp3_path)
    logger.info("安全上限: %d 分", max_duration_min)

    wf = wave.open(wav_path, "wb")
    wf.setnchannels(channels)
    wf.setsampwidth(2)  # int16 = 2 bytes
    wf.setframerate(sample_rate)

    def _audio_callback(indata, frames, time_info, status):
        if status:
            logger.warning("録音コールバック status: %s", status)
        wf.writeframes(indata.copy().tobytes())

    try:
        with sd.InputStream(
            samplerate=sample_rate,
            channels=channels,
            dtype=_DTYPE,
            device=device_index,
            callback=_audio_callback,
        ):
            start_time = time.time()
            logger.info("録音中... (停止シグナル待機)")

            while True:
                time.sleep(0.5)

                # 停止シグナルの検出
                if os.path.exists(stop_path):
                    logger.info("停止シグナルを検出しました")
                    break

                # 安全上限チェック
                elapsed = time.time() - start_time
                if elapsed >= max_duration_sec:
                    logger.warning("安全上限 (%d 分) に達したため録音を停止します", max_duration_min)
                    break

        wf.close()
        elapsed_total = time.time() - start_time
        logger.info("録音を停止しました (録音時間: %.1f 秒)", elapsed_total)

        # --- WAV → MP3 変換（lameenc 使用、ffmpeg 不要） ---
        logger.info("WAV → MP3 変換中: %s", wav_path)
        try:
            _wav_to_mp3(wav_path, mp3_path, sample_rate, channels)

            # WAV ファイルを削除
            os.remove(wav_path)
            logger.info("WAV ファイルを削除しました: %s", wav_path)
        except Exception:
            logger.exception("MP3 変換に失敗しました。WAV ファイルはそのまま残ります: %s", wav_path)

    except Exception:
        logger.exception("録音中にエラーが発生しました")
        try:
            wf.close()
        except Exception:
            pass
    finally:
        # --- クリーンアップ ---
        for path in (pid_path, stop_path):
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
        logger.info("録音プロセスを終了します")


def stop() -> None:
    """録音停止シグナルを送信し、録音プロセスの終了を待機する。"""
    pid_path = _signal_path(_PID_FILE)
    stop_path = _signal_path(_STOP_FILE)

    # --- PID ファイルの確認 ---
    if not os.path.exists(pid_path):
        logger.warning("PID ファイルが見つかりません。録音プロセスが起動していない可能性があります。")
        return

    try:
        with open(pid_path, "r", encoding="utf-8") as f:
            pid = int(f.read().strip())
        logger.info("録音プロセス PID: %d", pid)
    except (OSError, ValueError):
        logger.exception("PID ファイルの読み取りに失敗しました")
        return

    # --- 停止シグナルファイルの作成 ---
    try:
        with open(stop_path, "w", encoding="utf-8") as f:
            f.write("stop")
        logger.info("停止シグナルファイルを作成しました: %s", stop_path)
    except OSError:
        logger.exception("停止シグナルファイルの作成に失敗しました")
        return

    # --- 録音プロセスの終了を待機（PID ファイル消滅を監視） ---
    logger.info("録音プロセスの終了を待機しています...")
    max_wait = 30
    start = time.time()
    while time.time() - start < max_wait:
        if not os.path.exists(pid_path):
            logger.info("録音プロセスが正常に終了しました")
            return
        time.sleep(0.5)

    logger.warning("録音プロセスが %d 秒以内に終了しませんでした", max_wait)

    # 残留シグナルファイルのクリーンアップ
    for path in (stop_path,):
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass
