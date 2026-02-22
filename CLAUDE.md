# CLAUDE.md

このファイルは Claude Code (claude.ai/code) がこのリポジトリで作業する際のガイダンスです。

## プロジェクト概要

BlueBean Call Helper — BlueBeanコールセンターソフトと連携するWindows CLIツール。着信時に仮想オーディオルーティング経由で音声ガイダンスを自動再生し、オプションで通話をMP3録音する。PyInstallerで単体EXEとして配布。

**言語:** 日本語（UI、ドキュメント、コミットメッセージ）

## ビルド・実行コマンド

```bash
# 依存パッケージのインストール
pip install -r requirements.txt
# 注意: lameenc も必要だが requirements.txt に未記載
pip install lameenc

# 直接実行（開発時）
python call_helper.py --mode=incoming --number=09012345678
python call_helper.py --mode=record --number=09012345678
python call_helper.py --mode=stop-recording

# EXEビルド（本番用）
pyinstaller call_helper.spec
# 出力: dist/call_helper.exe
```

テストスイート・リンター設定は未導入。

## アーキテクチャ

### 実行モード

`call_helper.py` が唯一のエントリポイントで、3つのCLIモードを持つ:

1. **`incoming`** → `incoming.py`: 物理マイクをミュート → 録音サブプロセスを起動 → `guidance.mp3` をVB-CABLE経由で再生 → マイクミュート解除
2. **`record`** → `recorder.py`: VoiceMeeterからの音声をメモリバッファに蓄積 → 停止時にlameencでMP3変換
3. **`stop-recording`** → `recorder.py`: `.stop_recording` シグナルファイルを作成し、録音プロセスをグレースフルに停止

### オーディオルーティング（VoiceMeeter + VB-CABLE 必須）

```
ガイダンスMP3 → sounddevice → VB-CABLE Input → VoiceMeeter Input 2 → Output B → BlueBean マイク
物理マイク → VoiceMeeter Input 1 → Output A（オペレータースピーカー）+ Output B（BlueBean マイク）
VoiceMeeter Out B1 → recorder.py（オペレーター＋通話相手の両方の音声をキャプチャ）
```

### モジュール構成

| モジュール | 役割 |
|---|---|
| `call_helper.py` | CLI引数解析、ロギング設定、モードディスパッチ |
| `incoming.py` | ガイダンス再生の制御、マイクミュート/ミュート解除のライフサイクル管理 |
| `recorder.py` | 音声キャプチャ、メモリバッファリング、PCM→MP3変換（lameenc使用） |
| `audio_devices.py` | Windows COM API によるマイクミュート制御（pycaw）、WASAPI優先のデバイス列挙 |
| `config_loader.py` | INI設定ファイルの読み込み、frozen（EXE）/スクリプト実行時のベースパス解決 |

### プロセス間通信

録音はファイルベースのIPC（OSシグナル不使用）:
- `.recording.pid` — 録音プロセスがPIDを書き込み、プロセス追跡に使用
- `.stop_recording` — stop-recordingモードが作成、録音プロセスがポーリングしてグレースフル停止を実行

### 主要な技術的判断

- **WASAPI API 優先** — 録音デバイス選択時にMME/DirectSoundで発生する音声破損を防止
- **メモリバッファリング**（`list[np.ndarray]`）— 録音中はメモリに蓄積し、停止後にMP3エンコード。録音中のディスクI/Oを回避
- **lameenc** によるMP3エンコード — FFmpeg依存を排除、単体EXE配布に不可欠
- **pycaw COM API** によるマイクミュート — Windows音声エンドポイントの直接制御。comtypesのクリーンアップエラーは既知の問題として意図的に抑制
- **デバイス自動検出** — サンプルレート・チャンネル数はデバイスから取得（ハードコーディングしない）

## 設定ファイル

`config.ini`（EXE/スクリプトと同じディレクトリに配置）:

```ini
[general]
guidance_file = guidance.mp3        # 通話相手に再生する音声ファイル

[audio]
virtual_cable_name = CABLE Input (VB-Audio Virtual Cable)  # 再生先デバイス

[recording]
output_folder = D:\CallRecordings   # MP3出力ディレクトリ
recording_device = Voicemeeter Out B1  # WASAPIキャプチャソース
max_duration_minutes = 120          # 安全上限（分）
```

## ロギング

全モジュールが `call_helper.log`（＋コンソール）に出力。フォーマット: `YYYY-MM-DD HH:MM:SS [LEVEL] module: message`。対象オーディオデバイスが見つからない場合、デバッグ用に利用可能な全デバイスがログに出力される。
