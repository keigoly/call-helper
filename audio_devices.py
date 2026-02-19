"""オーディオデバイス操作ユーティリティ。

- 物理マイクのミュート / ミュート解除 (pycaw)
- VB-CABLE Input デバイスの検索 (sounddevice)
"""

import logging
import sys
from typing import Optional

import comtypes
import sounddevice as sd
from ctypes import POINTER, cast
from comtypes import CLSCTX_ALL
from pycaw.pycaw import IAudioEndpointVolume

logger = logging.getLogger(__name__)

# COM DeviceEnumerator の CLSID（Windows 標準、不変）
_CLSID_MMDeviceEnumerator = comtypes.GUID(
    "{BCDE0395-E52F-467C-8E3D-C4579291692E}"
)


# ---------- comtypes COM 解放エラーの抑制 ----------
# comtypes の COM ポインタが GC で回収される際に Release() が失敗し
# "Exception ignored in: <function _compointer_base.__del__>" が
# stderr に表示される。これは comtypes 内部の既知の問題であり、
# アプリの動作には影響しないため、このエラーのみ抑制する。

_original_unraisablehook = sys.unraisablehook


def _suppress_com_cleanup_error(unraisable):
    if "_compointer_base.__del__" in repr(unraisable.object):
        return
    _original_unraisablehook(unraisable)


sys.unraisablehook = _suppress_com_cleanup_error


# ---------- 物理マイクのミュート制御 ----------

def _set_mic_mute(mute: bool) -> None:
    """デフォルト録音デバイスのミュート状態を設定する。"""
    comtypes.CoInitialize()
    from pycaw.pycaw import IMMDeviceEnumerator

    enumerator = comtypes.CoCreateInstance(
        _CLSID_MMDeviceEnumerator,
        IMMDeviceEnumerator,
        comtypes.CLSCTX_INPROC_SERVER,
    )
    # eCapture=1, eMultimedia=1
    mic = enumerator.GetDefaultAudioEndpoint(1, 1)
    if mic is None:
        raise RuntimeError("デフォルトの録音デバイスが見つかりません")
    interface = mic.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    volume.SetMute(1 if mute else 0, None)


def mute_physical_mic() -> None:
    """デフォルト物理マイクをミュートする。"""
    try:
        _set_mic_mute(True)
        logger.info("物理マイクをミュートしました")
    except Exception:
        logger.exception("物理マイクのミュートに失敗しました")
        raise


def unmute_physical_mic() -> None:
    """デフォルト物理マイクのミュートを解除する。"""
    try:
        _set_mic_mute(False)
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
    search = device_name.lower()
    for idx, dev in enumerate(devices):
        if search in dev["name"].lower() and dev["max_output_channels"] > 0:
            logger.info("仮想ケーブルデバイスを検出: [%d] %s", idx, dev["name"])
            return idx

    logger.warning("仮想ケーブルデバイス '%s' が見つかりません", device_name)
    return None


# ---------- 入力デバイスの検索 ----------

def find_input_device(device_name: str) -> Optional[int]:
    """sounddevice のデバイスリストから *device_name* を含む入力デバイスを検索する。

    見つかった場合はデバイスインデックスを、見つからなければ None を返す。
    """
    devices = sd.query_devices()
    search = device_name.lower()
    for idx, dev in enumerate(devices):
        if search in dev["name"].lower() and dev["max_input_channels"] > 0:
            logger.info("入力デバイスを検出: [%d] %s", idx, dev["name"])
            return idx

    logger.warning("入力デバイス '%s' が見つかりません", device_name)
    return None
