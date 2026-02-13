==============================================================
BlueBean 連携用 音声ガイダンス＆録音制御アプリ
==============================================================

■ 概要
  コールセンターシステム「BlueBean」と連携し、以下の機能を提供します。
  - 機能A (incoming): 着信時に自動音声ガイダンスを再生し、物理マイクをミュート制御
  - 機能B (convert):  通話録音 WAV ファイルを MP3 に変換

■ 前提条件
  - Python 3.10 以上
  - VB-Audio Virtual Cable がインストール済み
    https://vb-audio.com/Cable/
  - FFmpeg がインストール済み（WAV→MP3 変換に必要）
    https://ffmpeg.org/download.html
    ※ ffmpeg.exe に PATH が通っていること

■ セットアップ
  1. 依存パッケージをインストール:
       pip install -r requirements.txt

  2. config.ini を編集:
     - guidance_file : 再生する音声ガイダンスファイルのパス
     - virtual_cable_name : VB-CABLE デバイス名（通常は変更不要）
     - watch_folder  : WAV ファイルの監視先フォルダ
     - output_folder : MP3 ファイルの出力先フォルダ
     - backup_folder : 変換済み WAV ファイルの退避先フォルダ

  3. 音声ガイダンスファイル (guidance.mp3) をこのフォルダに配置

■ 使い方
  【機能A】着信時ガイダンス:
    python call_helper.py --mode=incoming --number=09012345678

  【機能B】WAV→MP3 変換:
    python call_helper.py --mode=convert

■ EXE 化（オプション）
  PyInstaller でスタンドアロン EXE を作成できます:
    pip install pyinstaller
    pyinstaller --onefile call_helper.py

  生成された dist\call_helper.exe と同じフォルダに config.ini と
  guidance.mp3 を配置して使用してください。

■ ログ
  実行ログは call_helper.log に出力されます（EXE と同じフォルダ）。

■ トラブルシューティング
  - 「仮想ケーブルデバイスが見つかりません」
    → VB-Audio Virtual Cable がインストールされているか確認してください。
    → config.ini の virtual_cable_name がデバイス名と一致しているか確認してください。

  - 「変換失敗」
    → FFmpeg がインストールされ PATH が通っているか確認してください。
    → コマンドプロンプトで ffmpeg -version が実行できるか確認してください。

  - ミュートが解除されない場合
    → Windows の音量ミキサーから手動でミュート解除してください。
