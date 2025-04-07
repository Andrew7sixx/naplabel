import os
import sys
import winreg
import json
import requests
import zipfile
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import QProgressDialog, QMessageBox, QDialog, QVBoxLayout, QLabel

SERVER_URL = "http://39.108.104.215"  # 替换为实际服务器地址
CURRENT_VERSION = "1.0"

def get_desktop_path() -> str:
    """
    获取桌面路径（跨平台优化版）
    返回值：桌面绝对路径字符串
    """
    if sys.platform != "win32":
        # 非Windows系统直接返回标准路径
        return os.path.join(os.path.expanduser("~"), "Desktop")

    try:
        # 更现代的注册表路径（推荐）
        with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
        ) as key:
            # 读取注册表值（DESKTOP的REG_EXPAND_SZ类型需要展开环境变量）
            path, reg_type = winreg.QueryValueEx(key, "Desktop")
            if reg_type == winreg.REG_EXPAND_SZ:
                return os.path.expandvars(path)
            return path
    except Exception as e:
        print(f"注册表读取失败，使用备用方案: {str(e)}")
        # 备用方案1：使用Shell API
        try:
            from ctypes import windll, create_unicode_buffer
            buf = create_unicode_buffer(260)
            windll.shell32.SHGetFolderPathW(0, 0x0010, 0, 0, buf)  # 0x0010对应CSIDL_DESKTOP
            return buf.value
        except:
            # 备用方案2：系统默认路径
            return os.path.join(os.path.expanduser("~"), "Desktop")

DESKTOP_PATH = get_desktop_path()


class UpdateDownloader(QThread):
    download_progress = pyqtSignal(int)
    extract_progress = pyqtSignal(int)
    finished = pyqtSignal(bool)
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url
        self._is_running = True

    def run(self):
        try:
            # 下载更新包
            zip_path = os.path.join(DESKTOP_PATH, "update.zip")
            self.download_file(zip_path)
            if not self._is_running: return

            # 解压到桌面
            self.extract_file(zip_path)
            os.remove(zip_path)  # 清理压缩包

            self.finished.emit(True)
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit(False)

    def download_file(self, save_path):
        response = requests.get(self.url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0

        with open(save_path, 'wb') as f:
            for data in response.iter_content(1024):
                if not self._is_running:
                    os.remove(save_path)
                    return
                f.write(data)
                downloaded += len(data)
                progress = int((downloaded / total_size) * 100) if total_size > 0 else 0
                self.download_progress.emit(progress)

    def extract_file(self, zip_path):
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            total = len(zip_ref.infolist())
            for idx, file in enumerate(zip_ref.infolist()):
                if not self._is_running: return
                zip_ref.extract(file, DESKTOP_PATH)
                self.extract_progress.emit(int((idx + 1) / total * 100))

    def stop(self):
        self._is_running = False
        if self.isRunning():
            self.terminate()  # 确保线程终止


class UpdateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle("软件更新")
        self.setFixedSize(400, 200)
        self.setWindowModality(Qt.WindowModal)

        layout = QVBoxLayout()
        self.status_label = QLabel("准备下载更新...")
        self.progress = QProgressDialog("下载进度", "取消", 0, 100, self)
        self.progress.setWindowTitle("更新进度")
        self.progress.canceled.connect(self.cancel_update)

        layout.addWidget(self.status_label)
        layout.addWidget(self.progress)
        self.setLayout(layout)

    def cancel_update(self):
        self.progress.setLabelText("正在取消更新...")
        if hasattr(self.parent(), 'update_thread') and self.parent().update_thread:
            self.parent().update_thread.stop()


class UpdateManager:
    def __init__(self, parent):
        self.parent = parent
        self.update_dialog = None  # 改为延迟初始化
        self.update_thread = None

    def check_update(self):
        try:
            response = requests.get(f"{SERVER_URL}/version.json", timeout=5)
            version_info = json.loads(response.text)
            if version_info["version"] != CURRENT_VERSION:
                self.ask_for_download(version_info)
        except Exception as e:
            QMessageBox.critical(self.parent, "错误", f"检查更新失败: {str(e)}")

    def ask_for_download(self, version_info):
        reply = QMessageBox.question(
            self.parent, "发现新版本",
            f"发现新版本 {version_info['version']}，是否立即下载？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.start_download(version_info["url"])

    def start_download(self, url):
        # 创建新的对话框实例
        self.update_dialog = UpdateDialog(self.parent)

        # 连接信号
        self.update_thread = UpdateDownloader(url)
        self.update_thread.download_progress.connect(self.update_dialog.progress.setValue)
        self.update_thread.finished.connect(self.on_update_finished)
        self.update_thread.error.connect(self.show_error)

        # 初始化进度条并显示
        self.update_dialog.progress.reset()
        self.update_dialog.show()  # 只有点击Yes后才显示

        self.update_thread.start()

    def on_update_finished(self, success):
        self.update_dialog.close()
        if success:
            QMessageBox.information(
                self.parent, "完成",
                "更新文件已下载到桌面！\n请手动替换文件后重启程序。"
            )

    def show_error(self, msg):
        QMessageBox.critical(self.parent, "错误", f"更新失败: {msg}")
        self.update_dialog.close()