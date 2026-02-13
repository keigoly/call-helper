@echo off
chcp 65001 >nul
echo ============================================
echo  BlueBean Call Helper セットアップ
echo ============================================
echo.

:: Python確認
python --version >nul 2>&1
if errorlevel 1 (
    echo [エラー] Python が見つかりません。先に Python をインストールしてください。
    pause
    exit /b 1
)

:: FFmpeg確認
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [警告] FFmpeg が見つかりません。WAV→MP3変換を使う場合はインストールしてください。
    echo         https://ffmpeg.org/download.html
    echo.
)

:: パッケージインストール
echo 依存パッケージをインストールしています...
pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
    echo [エラー] パッケージのインストールに失敗しました。
    pause
    exit /b 1
)

echo.
echo ============================================
echo  セットアップ完了！
echo ============================================
echo.
echo 次のステップ:
echo   1. config.ini を環境に合わせて編集
echo   2. guidance.mp3 をこのフォルダに配置
echo   3. 実行例:
echo      python call_helper.py --mode=incoming --number=09012345678
echo      python call_helper.py --mode=convert
echo.
pause
