import sys
import os
import pymysql
from docx import Document  # 添加导入
from function.login_signup_page.update_checker import UpdateManager
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QCheckBox, QPushButton, QHBoxLayout, QMessageBox, \
    QDialog, QApplication,QTextEdit
from PyQt5.QtCore import pyqtSignal, Qt, QUrl
from PyQt5.QtGui import QPixmap, QDesktopServices
from config import login_config
from function.Annotation_page.auto_annotation_main import AutoAnnotationSystem
from function.login_signup_page.sign_up import SignUpWidget
from function.login_signup_page.password import PasswordWidget
from config.db_config import db_config


# 在LoginWidget类中添加以下新类
class DocumentViewer(QDialog):
    def __init__(self, doc_path, title="文档查看", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(600, 800)

        # 主布局
        layout = QVBoxLayout(self)

        # 文本显示区域
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)

        # 加载文档内容
        self.load_document(doc_path)

    def load_document(self, path):
        try:
            doc = Document(path)
            full_text = []
            for para in doc.paragraphs:
                # 保留换行和基本格式
                text = para.text.replace('\n', '<br>')
                if para.style.name.startswith('Heading'):
                    text = f"<b>{text}</b>"
                full_text.append(text)
            self.text_edit.setHtml('<br>'.join(full_text))
        except Exception as e:
            self.text_edit.setText(f"无法加载文档：{str(e)}")

class LoginWidget(QWidget):
    switch_window = pyqtSignal()
    switch_to_annotation_signal = pyqtSignal(dict)  # 添加dict类型参数

    switch_to_personal_center_signal = pyqtSignal()  # 定义切换到个人中心页面的信号

    def __init__(self):
        super().__init__()
        # self.switch_to_annotation_signal.connect(self.show_annotation)
        # 窗口基础设置
        self.setWindowTitle("Nap-Label登录")
        self.setFixedSize(400, 550)  # 设置窗口大小为400x550
        self.init_ui()
        self.sign_up_window = None
        self.password_window = None
        self.update_manager = UpdateManager(self)
        self.check_update()

    def check_update(self):
        # 延迟1秒检查，避免界面卡顿
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(1000, self.update_manager.check_update)

    def init_ui(self):
        # 主布局容器
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 20)  # 下边距留20px
        main_layout.setSpacing(2)

        # ==================== 标题区块 ====================
        title_container = QWidget()
        title_container.setObjectName("TitleContainer")
        title_container.setStyleSheet(login_config.title_container_style)

        # 设置标题容器的高度为原来的一半
        tittle_height = 80
        title_container.setFixedHeight(tittle_height)

        # 标题文字
        title_label = QLabel("Naptec", self)
        title_label.setObjectName("MainTitle")
        title_label.setStyleSheet(login_config.main_title_style)

        # 标题布局
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.addWidget(title_label)
        main_layout.addWidget(title_container)

        # ==================== 副标题 ====================
        subtitle_label = QLabel("Nap-Label", self)
        subtitle_label.setObjectName("SubTitle")
        subtitle_label.setStyleSheet(login_config.sub_title_style)
        main_layout.addWidget(subtitle_label)

        # ==================== 表单区域 ====================
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(50, 0, 50, 0)  # 左右留50px边距
        form_layout.setSpacing(15)

        # 描述文字
        desc_label = QLabel("方便快捷的数据标注工具")
        desc_label.setStyleSheet(login_config.desc_label_style)
        form_layout.addWidget(desc_label)

        # 账号输入
        self.account_edit = QLineEdit()
        self.account_edit.setPlaceholderText("请输入账号/邮箱")
        self.account_edit.setStyleSheet(login_config.account_edit_style)
        form_layout.addWidget(self.account_edit)

        # 密码输入
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("请输入密码")
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setStyleSheet(login_config.password_edit_style)
        form_layout.addWidget(self.password_edit)

        # 协议勾选容器
        agreement_container = QWidget()
        agreement_layout = QHBoxLayout(agreement_container)
        agreement_layout.setContentsMargins(0, 0, 0, 0)
        agreement_layout.setSpacing(5)

        # 勾选框
        self.agreement_check = QCheckBox()
        self.agreement_check.setFixedSize(20, 20)
        agreement_layout.addWidget(self.agreement_check)

        # 修改协议链接点击处理（替换原来的agreement_text设置部分）
        agreement_text = QLabel(
            '已阅读并同意 <a href="service" style="text-decoration: none; color: #007BFF;">服务协议</a> 和 <a href="privacy" style="text-decoration: none; color: #007BFF;">隐私保护指引</a>')
        agreement_text.setOpenExternalLinks(False)  # 重要：禁用自动打开

        def handle_link_click(link):
            base_dir = os.path.abspath(os.path.dirname(__file__))
            if link == "service":
                doc_path = os.path.join(base_dir, "服务条款.docx")
                viewer = DocumentViewer(doc_path, "服务协议", self)
            elif link == "privacy":
                doc_path = os.path.join(base_dir, "隐私协议.docx")
                viewer = DocumentViewer(doc_path, "隐私协议", self)
            else:
                return
            viewer.exec_()

        agreement_text.linkActivated.connect(handle_link_click)
        agreement_layout.addWidget(agreement_text)  # 确保此行存在
        form_layout.addWidget(agreement_container, alignment=Qt.AlignCenter)  # 确保此行存在

        # 登录按钮
        self.login_button = QPushButton("登录")
        self.login_button.setStyleSheet(login_config.login_button_style)
        self.login_button.clicked.connect(self.login)
        form_layout.addWidget(self.login_button)

        # 底部选项
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()

        # 注册账号按钮
        reg = QLabel("注册账号")
        reg.setStyleSheet(login_config.extra_options_label_style)
        reg.mousePressEvent = lambda e: self.show_sign_up()
        bottom_layout.addWidget(reg)

        # 找回密码按钮
        pwd = QLabel("找回密码")
        pwd.setStyleSheet(login_config.extra_options_label_style)
        pwd.mousePressEvent = lambda e: self.show_password_widget()
        bottom_layout.addWidget(pwd)

        bottom_layout.addStretch()

        form_layout.addLayout(bottom_layout)
        main_layout.addWidget(form_container)

    # ==================== 功能方法 ====================
    def show_annotation(self, user_info):
        self.annotation_window = AutoAnnotationSystem(user_info=user_info)
        self.annotation_window.show()
        self.hide()

    def login(self):
        # 基础校验逻辑
        if not self.agreement_check.isChecked():
            QMessageBox.warning(self, "提示", "请先同意服务协议")
            return
        account = self.account_edit.text()
        password = self.password_edit.text()
        if not account or not password:
            QMessageBox.warning(self, "提示", "请输入账号密码")
            return
        try:
            connection = pymysql.connect(
                host=db_config.HOST,
                port=db_config.PORT,
                user=db_config.USER,
                password=db_config.PASSWORD,
                database=db_config.DATABASE,
                charset='utf8mb4'
            )
            with connection.cursor() as cursor:
                sql = "SELECT id, name, vip, current_points, total_points, rectangle_remaining, account FROM user_info WHERE account = %s AND password = %s"
                # sql = "SELECT id, name, vip, current_points, rectangle_remaining FROM user_info WHERE account = %s AND password = %s"
                cursor.execute(sql, (account, password))
                result = cursor.fetchone()

                if result:
                    self.logged_in_user = {
                        "id": result[0],
                        "name": result[1],
                        "vip": result[2],
                        "current_points": result[3],
                        "total_points": result[4],
                        "rectangle_remaining": result[5],
                        "account": result[6]  # 注意这里传递账号
                    }
                    ### 改：4.2
                    # 直接实例化并显示主界面，不传入父窗口
                    self.annotation_window = AutoAnnotationSystem(user_info=self.logged_in_user)
                    self.annotation_window.show()  # 显示为独立的顶级窗口
                    self.close()  # 关闭或隐藏登录窗口
                    ############
                else:
                    QMessageBox.warning(self, "登录失败", "账号或密码错误")
        except pymysql.Error as e:
            QMessageBox.critical(self, "数据库错误", f"数据库连接异常: {str(e)}")
        finally:
            # 确保关闭连接
            if 'connection' in locals() and connection.open:
                connection.close()
    def show_qr_code(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("扫码登录")
        dialog.setFixedSize(160, 160)
        label = QLabel(dialog)
        label.setPixmap(QPixmap("../../Image/erweima.png").scaled(160, 160))  # 准备二维码图片
        dialog.exec_()

    def handle_registration(self):
        QMessageBox.information(self, "提示", "注册功能开发中")

    def handle_password_retrieval(self):
        QMessageBox.information(self, "提示", "密码找回开发中")

    def show_sign_up(self):
        if self.sign_up_window is None:
            self.sign_up_window = SignUpWidget()
            self.sign_up_window.switch_back.connect(self.show_login_and_close_signup)
        self.sign_up_window.show()
        self.hide()

    def show_password_widget(self):
        if self.password_window is None:
            self.password_window = PasswordWidget()
            self.password_window.switch_back.connect(self.show_login_and_close_password)
        self.password_window.show()
        self.hide()

    def show_login_and_close_signup(self):
        self.show()
        if self.sign_up_window:
            self.sign_up_window.close()
            self.sign_up_window = None

    def show_login_and_close_password(self):
        self.show()
        if self.password_window:
            self.password_window.close()
            self.password_window = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWidget()
    window.show()
    sys.exit(app.exec_())
