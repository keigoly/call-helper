"""オーディオデバイス操作ユーティリティ。

- 物理マイクのミュート / ミュート解除 (pycaw)
- VB-CABLE Input デバイスの検索 (sounddevice)
"""

import logging
from typing import Optional

import comtypes
import sounddevice as sd
from ctypes import POINTER, cast
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

logger = logging.getLogger(__name__)


# ---------- 物理マイクのミュート制御 ----------

def _get_mic_endpoint_volume() -> "IAudioEndpointVolume":
    """デフォルト録音デバイスの IAudioEndpointVolume を取得する。"""
    comtypes.CoInitialize()
    devices = AudioUtilities.GetMicrophone()
    if devices is None:
        raise RuntimeError("デフォルトの録音デバイスが見つかりません")
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return cast(interface, POINTER(IAudioEndpointVolume))


def mute_physical_mic() -> None:
    """デフォルト物理マイクをミュートする。"""
    try:
        volume = _get_mic_endpoint_volume()
        volume.SetMute(1, None)
        logger.info("物理マイクをミュートしました")
    except Exception:
        logger.exception("物理マイクのミュートに失敗しました")
        raise


def unmute_physical_mic() -> None:
    """デフォルト物理マイクのミュートを解除する。"""
    try:
        volume = _get_mic_endpoint_volume()
        volume.SetMute(0, None)
        logger.info("物理マイクのミュートを解除しました")
    except Exception:
        logger.exception("物理マイクのミュート解除に失敗しました")
        raise


# ---------- 仮想オーディオデバイスの検索 ----------

def find_virtual_cable_device(device_name: str) -> Optional[int]:
    """sounddevice のデバイスリストから *device_name* を含む出力デバイスを検索する。

    見つかった場合はデバイスインデックスを、見つからなければ None を返す。
    """
    devices = sd.query_devices()
    for idx, dev in enumerate(devices):
        if device_name in dev["name"] and dev["max_output_channels"] > 0:
            logger.info("仮想ケーブルデバイスを検出: [%d] %s", idx, dev["name"])
            return idx

    logger.warning("仮想ケーブルデバイス '%s' が見つかりません", device_name)
    return None
