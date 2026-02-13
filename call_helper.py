"""BlueBean 連携用 音声ガイダンス＆録音制御アプリ。

使い方:
    python call_helper.py --mode=incoming [--number=09012345678]
    python call_helper.py --mode=convert
"""

import argparse
import logging
import os
import sys


def _setup_logging() -> None:
    """ファイル＋コンソールの両方にログを出力する設定。"""
    if getattr(sys, "frozen", False):
        log_dir = os.path.dirname(sys.executable)
    else:
        log_dir = os.path.dirname(os.path.abspath(__file__))

    log_file = os.path.join(log_dir, "call_helper.log")

    handlers: list[logging.Handler] = [
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="BlueBean 連携用 音声ガイダンス＆録音制御アプリ"
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=["incoming", "convert"],
        help="実行モード: incoming=着信時ガイダンス, convert=WAV→MP3変換",
    )
    parser.add_argument(
        "--number",
        default=None,
        help="着信番号（ログ記録用、incoming モード時のみ使用）",
    )
    args = parser.parse_args()

    _setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("=== call_helper 起動 (mode=%s) ===", args.mode)

    try:
        if args.mode == "incoming":
            import incoming

            incoming.run(number=args.number)
        elif args.mode == "convert":
            import converter

            converter.run()
    except Exception:
        logger.exception("予期しないエラーが発生しました")
        sys.exit(1)

    logger.info("=== call_helper 終了 ===")


if __name__ == "__main__":
    main()
