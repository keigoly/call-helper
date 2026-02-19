"""機能A: 着信時ガイダンス制御。

1. 物理マイクを即座にミュート（オペレーターの声を遮断）
2. 録音サブプロセスを起動（通話録音）
3. guidance 音声ファイルの存在確認 → なければミュート解除して終了
4. VB-CABLE Input デバイスを検索 → なければエラーログ出力＆ミュート解除して終了
5. sounddevice + soundfile で音声を CABLE Input へ再生
   （オペレーター側は VoiceMeeter の A バス経由でスピーカーに届く）
6. 再生完了を待機（ピー音が鳴るまで）
7. 物理マイクのミュート解除（通常通話に復帰）
"""

import logging
import os
import subprocess
import sys

import sounddevice as sd
import soundfile as sf

from audio_devices import (
    find_virtual_cable_device,
    mute_physical_mic,
    unmute_physical_mic,
)
from config_loader import load_config, _base_dir

logger = logging.getLogger(__name__)


def run(number: str | None = None) -> None:
    """着信時ガイダンス処理を実行する。

    Parameters
    ----------
    number : str | None
        着信番号（ログ記録用）。
    """
    if number:
        logger.info("着信番号: %s", number)

    config = load_config()

    # --- 1. 物理マイクをミュート ---
    try:
        mute_physical_mic()
    except Exception:
        logger.error("マイクミュートに失敗しました。処理を中断します。")
        return

    # --- 録音サブプロセスの起動 ---
    try:
        if getattr(sys, "frozen", False):
            # EXE モード: call_helper.exe --mode=record
            record_cmd = [sys.executable, "--mode=record"]
        else:
            # スクリプトモード: python call_helper.py --mode=record
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

    try:
        # --- 2. 音声ファイルの存在確認 ---
        guidance_file = config.get("general", "guidance_file")
        # 相対パスの場合は config.ini と同じディレクトリを基準にする
        if not os.path.isabs(guidance_file):
            guidance_file = os.path.join(_base_dir(), guidance_file)

        if not os.path.isfile(guidance_file):
            logger.warning("音声ファイルが見つかりません: %s — ミュート解除して終了します", guidance_file)
            return

        # --- 3. 仮想ケーブルデバイスの検索 ---
        cable_name = config.get("audio", "virtual_cable_name")
        device_index = find_virtual_cable_device(cable_name)
        if device_index is None:
            logger.error(
                "仮想ケーブルデバイス '%s' が見つかりません — ミュート解除して終了します",
                cable_name,
            )
            return

        # --- 4 & 5. 音声再生 & 完了待機（ピー音まで再生） ---
        # VB-CABLE へ再生 → VoiceMeeter 経由で相手側 (B) + オペレーター側 (A) に届く
        logger.info("音声ガイダンスを再生します: %s", guidance_file)
        data, samplerate = sf.read(guidance_file, dtype="float32")
        sd.play(data, samplerate=samplerate, device=device_index)
        sd.wait()
        logger.info("音声ガイダンスの再生が完了しました")

    except Exception:
        logger.exception("ガイダンス再生中にエラーが発生しました")
    finally:
        # --- 6. 必ずマイクのミュート解除 ---
        try:
            unmute_physical_mic()
        except Exception:
            logger.exception("ミュート解除に失敗しました — 手動でミュート解除してください")
