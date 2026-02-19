"""オーディオデバイス操作ユーティリティ。

- 物理マイクのミュート / ミュート解除 (pycaw)
- スピーカー（再生デバイス）のミュート / ミュート解除 (pycaw)
- VB-CABLE Input デバイスの検索 (sounddevice)
"""

import logging
from typing import Optional

import comtypes
import sounddevice as sd
from ctypes import POINTER, cast
from comtypes import CLSCTX_ALL
from pycaw.pycaw import IAudioEndpointVolume

logger = logging.getLogger(__name__)


# ---------- 物理マイクのミュート制御 ----------

def _get_mic_endpoint_volume() -> "IAudioEndpointVolume":
    """デフォルト録音デバイスの IAudioEndpointVolume を取得する。

    AudioUtilities.GetMicrophone() が一部環境で AudioDevice ラッパーを返し
    Activate() が使えないケースがあるため、COM を直接操作する。
    """
    comtypes.CoInitialize()
    from pycaw.pycaw import IMMDeviceEnumerator

    CLSID_MMDeviceEnumerator = comtypes.GUID(
        "{BCDE0395-E52F-467C-8E3D-C4579291692E}"
    )
    enumerator = comtypes.CoCreateInstance(
        CLSID_MMDeviceEnumerator,
        IMMDeviceEnumerator,
        comtypes.CLSCTX_INPROC_SERVER,
    )
    # eCapture=1, eMultimedia=1
    mic = enumerator.GetDefaultAudioEndpoint(1, 1)
    if mic is None:
        raise RuntimeError("デフォルトの録音デバイスが見つかりません")
    interface = mic.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
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


# ---------- スピーカー（再生デバイス）のミュート制御 ----------

def _get_speaker_endpoint_volume() -> "IAudioEndpointVolume":
    """デフォルト再生デバイスの IAudioEndpointVolume を取得する。

    AudioUtilities.GetSpeakers() が一部環境で AudioDevice ラッパーを返し
    Activate() が使えないケースがあるため、COM を直接操作する。
    """
    comtypes.CoInitialize()
    from pycaw.pycaw import IMMDeviceEnumerator

    CLSID_MMDeviceEnumerator = comtypes.GUID(
        "{BCDE0395-E52F-467C-8E3D-C4579291692E}"
    )
    enumerator = comtypes.CoCreateInstance(
        CLSID_MMDeviceEnumerator,
        IMMDeviceEnumerator,
        comtypes.CLSCTX_INPROC_SERVER,
    )
    # eRender=0, eMultimedia=1
    speakers = enumerator.GetDefaultAudioEndpoint(0, 1)
    if speakers is None:
        raise RuntimeError("デフォルトの再生デバイスが見つかりません")
    interface = speakers.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return cast(interface, POINTER(IAudioEndpointVolume))


def mute_speaker() -> None:
    """デフォルト再生デバイス（スピーカー）をミュートする。"""
    try:
        volume = _get_speaker_endpoint_volume()
        volume.SetMute(1, None)
        logger.info("スピーカーをミュートしました")
    except Exception:
        logger.exception("スピーカーのミュートに失敗しました")
        raise


def unmute_speaker() -> None:
    """デフォルト再生デバイス（スピーカー）のミュートを解除する。"""
    try:
        volume = _get_speaker_endpoint_volume()
        volume.SetMute(0, None)
        logger.info("スピーカーのミュートを解除しました")
    except Exception:
        logger.exception("スピーカーのミュート解除に失敗しました")
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
