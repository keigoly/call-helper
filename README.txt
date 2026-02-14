==============================================================
BlueBean 連携用 音声ガイダンス＆録音制御アプリ
==============================================================

■ 概要
  コールセンターシステム「BlueBean」と連携し、以下の機能を提供します。
  - 機能A (incoming): 応答時に自動音声ガイダンスを再生し、物理マイクをミュート制御
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

     【重要】config.ini の値にダブルクォート（"）を付けないでください。
       正しい例: guidance_file = guidance.mp3
       誤った例: guidance_file = "guidance.mp3"

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

■ BlueBean との連携設定
  BlueBean の設定画面から「コマンド連携設定」タブを開き、
  用途に合わせて以下のいずれかの欄にコマンドを登録してください。

  ● 応答時アクセス（推奨）
    着信ボタンを押して通話を開始したタイミングでガイダンスを再生します。

  ● 着信時アクセス
    電話が鳴った瞬間（応答前）にガイダンスを再生します。

  登録するコマンド:
    （フォルダのパス）\call_helper.exe --mode=incoming --number=（相手番号パラメータ）

  ※ パスは call_helper.exe を配置した場所に合わせてください
  ※ --number= の後にカーソルを置き、BlueBean の「相手番号」ボタンを
    クリックすると着信番号のパラメータが自動挿入されます
  ※ --number パラメータはログ記録用です。省略しても動作に影響はありません

■ ログ
  実行ログは call_helper.log に出力されます（EXE と同じフォルダ）。

■ トラブルシューティング
  - 「仮想ケーブルデバイスが見つかりません」
    → VB-Audio Virtual Cable がインストールされているか確認してください。
    → config.ini の virtual_cable_name がデバイス名と一致しているか確認してください。

  - 「音声ファイルが見つかりません」
    → guidance.mp3 が call_helper.exe と同じフォルダにあるか確認してください。
    → config.ini の guidance_file の値にダブルクォート（"）が
      付いていないか確認してください。
      誤: guidance_file = "guidance.mp3"
      正: guidance_file = guidance.mp3

  - 「変換失敗」
    → FFmpeg がインストールされ PATH が通っているか確認してください。
    → コマンドプロンプトで ffmpeg -version が実行できるか確認してください。

  - ミュートが解除されない場合
    → Windows の音量ミキサーから手動でミュート解除してください。
