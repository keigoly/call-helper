"""オーディオデバイス操作ユーティリティ。

- 物理マイクのミュート / ミュート解除 (pycaw)
- VB-CABLE Input デバイスの検索 (sounddevice)
"""

import gc
import logging
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


def _set_mic_mute(mute: bool) -> None:
    """デフォルト録音デバイスのミュート状態を設定する。

    COM オブジェクトを関数内で生成・操作・解放まで完結させ、
    ガベージコレクション時の COM ポインタ解放エラーを防ぐ。
    """
    comtypes.CoInitialize()
    from pycaw.pycaw import IMMDeviceEnumerator

    enumerator = None
    mic = None
    interface = None
    volume = None
    try:
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
    finally:
        # COM オブジェクトを明示的に解放してから GC で回収
        del volume, interface, mic, enumerator
        gc.collect()


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
    for idx, dev in enumerate(devices):
        if device_name in dev["name"] and dev["max_output_channels"] > 0:
            logger.info("仮想ケーブルデバイスを検出: [%d] %s", idx, dev["name"])
            return idx

    logger.warning("仮想ケーブルデバイス '%s' が見つかりません", device_name)
    return None
