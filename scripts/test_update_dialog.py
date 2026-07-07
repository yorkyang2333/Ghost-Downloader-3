import sys
import os
import importlib.util

# Ensure the root directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtCore import QTimer
from app.update import Release, ReleaseAsset
from app.signal_bus import signalBus
import app.startup

# Prevent actual GitHub update check during preview
app.startup.checkUpdateAtStartup = lambda: None

spec = importlib.util.spec_from_file_location("main_app", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Ghost-Downloader-3.py"))
main_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_app)


def main():
    from app.platform.application import SingletonApplication

    main_app.setupEnvironment()
    # Use a custom test key to prevent QSharedMemory collision with any existing instance
    app = SingletonApplication(sys.argv, "GhostDownloaderTestID_v350_Preview")
    main_app.startApp(app, isSilent=False)

    fake_release = Release(
        version="v3.5.0",
        publishedAt="2026-07-06T12:00:00Z",
        body="### 新版本功能特性\n\n- ✨ **自动适配当前操作系统**：系统会自动识别您当前运行的 macOS/Windows 系统与 CPU 架构，默认高亮选中列表里对应的更新包。\n- 🚀 **一键直达下载任务**：点击下方“下载”或提示条“立即下载”后，将立即自动平滑跳转至主界面的“下载任务”页面。\n- 🐛 **其他优化**：提升了客户端整体性能与稳定性。",
        pageUrl="https://github.com/XiaoYouChR/Ghost-Downloader-3/releases",
        prerelease=False,
        assets=[
            ReleaseAsset(
                name="Ghost-Downloader-3-v3.5.0-Windows-x86_64-Setup.exe",
                size=48123456,
                downloadCount=12050,
                downloadUrl="https://github.com/XiaoYouChR/Ghost-Downloader-3/releases/download/v3.5.0/win.exe",
            ),
            ReleaseAsset(
                name="Ghost-Downloader-3-v3.5.0-macOS-arm64.dmg",
                size=53345678,
                downloadCount=8900,
                downloadUrl="https://github.com/XiaoYouChR/Ghost-Downloader-3/releases/download/v3.5.0/mac-arm64.dmg",
            ),
            ReleaseAsset(
                name="Ghost-Downloader-3-v3.5.0-macOS-x86_64.dmg",
                size=55321098,
                downloadCount=4500,
                downloadUrl="https://github.com/XiaoYouChR/Ghost-Downloader-3/releases/download/v3.5.0/mac-x64.dmg",
            ),
            ReleaseAsset(
                name="Ghost-Downloader-3-v3.5.0-Linux-x86_64.AppImage",
                size=62234567,
                downloadCount=3100,
                downloadUrl="https://github.com/XiaoYouChR/Ghost-Downloader-3/releases/download/v3.5.0/linux.AppImage",
            ),
        ],
    )

    def trigger_popup():
        # Emit updateAvailable signal so the bottom-right notification banner appears
        signalBus.updateAvailable.emit(fake_release)
        # Open ReleaseInfoDialog on the real MainWindow
        from app.update import showReleaseDialog
        for w in app.topLevelWidgets():
            if w.inherits("MSFluentWindow") or w.__class__.__name__ == "MainWindow":
                showReleaseDialog(fake_release, w)
                break

    QTimer.singleShot(1500, trigger_popup)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
