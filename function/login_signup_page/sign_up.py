import sys
import json
import pymysql
import secrets
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QMessageBox, \
    QApplication, QSizePolicy
from PyQt5.QtCore import pyqtSignal, QTimer
from config.signup_config import (
    title_container_style,
    main_title_style,
    signup_sub_title_style,
    account_edit_style,
    verification_code_edit_style,
    password_edit_style,
    button_style,
    send_verification_code_button_style,
    back_button_style
)
from config.db_config import db_config
from aliyunsdkcore.client import AcsClient
from aliyunsdkdysmsapi.request.v20170525 import SendSmsRequest


class SignUpWidget(QWidget):
    switch_back = pyqtSignal()

    def __init__(self):
        super().__init__()
        # 窗口基础设置
        self.setWindowTitle("Nap-Label注册")
        self.setFixedSize(400, 550)  # 设置窗口大小为400x550

        # 倒计时定时器
        self.countdown = 60
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_countdown)

        self.init_ui()

    def init_ui(self):
        # 主布局容器
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 20)  # 下边距留20px
        main_layout.setSpacing(2)

        # ==================== 标题区块 ====================
        title_container = QWidget()
        title_container.setObjectName("TitleContainer")
        title_container.setStyleSheet(title_container_style)
        tittle_height = 80  # 假设原来的高度是80px
        title_container.setFixedHeight(tittle_height)

        title_label = QLabel("Naptec", self)
        title_label.setObjectName("MainTitle")
        title_label.setStyleSheet(main_title_style)
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.addWidget(title_label)
        main_layout.addWidget(title_container)

        # ==================== 副标题 ====================
        subtitle_label = QLabel("注册Nap-Label账号", self)
        subtitle_label.setObjectName("SubTitle")
        subtitle_label.setStyleSheet(signup_sub_title_style)
        main_layout.addWidget(subtitle_label)

        # ==================== 表单区域 ====================
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(50, 0, 50, 0)  # 左右留50px边距
        form_layout.setSpacing(15)

        # 输入用户名
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("请输入用户名")
        self.username_edit.setStyleSheet(account_edit_style)
        form_layout.addWidget(self.username_edit)

        # 输入手机号码
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("请输入手机号码")
        self.phone_edit.setStyleSheet(account_edit_style)
        form_layout.addWidget(self.phone_edit)

        # 输入验证码及发送验证码按钮
        verification_code_layout = QHBoxLayout()
        self.verification_code_edit = QLineEdit()
        self.verification_code_edit.setPlaceholderText("请输入验证码")
        self.verification_code_edit.setStyleSheet(verification_code_edit_style)
        self.verification_code_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        verification_code_layout.addWidget(self.verification_code_edit)

        self.send_verification_code_button = QPushButton("发送验证码")
        self.send_verification_code_button.setStyleSheet(send_verification_code_button_style)
        self.send_verification_code_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        verification_code_layout.addWidget(self.send_verification_code_button)
        form_layout.addLayout(verification_code_layout)

        # 绑定发送验证码逻辑
        self.send_verification_code_button.clicked.connect(self.send_verification_code)

        # 设置密码
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("请设置密码")
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setStyleSheet(password_edit_style)
        form_layout.addWidget(self.password_edit)

        # 确认密码
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setPlaceholderText("请确认密码")
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)
        self.confirm_password_edit.setStyleSheet(password_edit_style)
        form_layout.addWidget(self.confirm_password_edit)

        # 注册按钮
        self.sign_up_button = QPushButton("注册")
        self.sign_up_button.setStyleSheet(button_style)
        self.sign_up_button.clicked.connect(self.sign_up)
        form_layout.addWidget(self.sign_up_button)

        # 返回登录按钮
        back_button = QPushButton("返回登录")
        back_button.setStyleSheet(back_button_style)
        back_button.clicked.connect(self.switch_back.emit)
        form_layout.addWidget(back_button)

        main_layout.addWidget(form_container)

    def generate_code(self, length=6):
        # 使用 secrets 生成指定长度的数字验证码
        return ''.join(str(secrets.randbelow(10)) for _ in range(length))

    def store_verification_code(self, phone, code, expire_seconds=300):
        """将验证码存入数据库 sms_verification 表，设置5分钟后过期"""
        expire_time = datetime.now() + timedelta(seconds=expire_seconds)
        try:
            conn = pymysql.connect(
                host=db_config.HOST,
                port=db_config.PORT,
                user=db_config.USER,
                password=db_config.PASSWORD,
                database=db_config.DATABASE,
                charset="utf8"
            )
            cursor = conn.cursor()
            sql = "INSERT INTO sms_verification (phone_number, code, expire_at) VALUES (%s, %s, %s)"
            cursor.execute(sql, (phone, code, expire_time))
            conn.commit()
        except Exception as e:
            raise Exception(f"验证码存储失败: {str(e)}")
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    def send_verification_code(self):
        phone = self.phone_edit.text().strip()
        if not phone:
            QMessageBox.warning(self, "提示", "请输入手机号码")
            return

        # 使用 secrets 生成6位随机验证码
        code = self.generate_code(6)

        # 调用阿里云短信服务发送验证码（请根据实际情况修改AccessKey、模板CODE和签名）
        try:
            response = self.send_sms(phone, code)
            response_dict = json.loads(response.decode())
            if response_dict.get("Code") == "OK":
                # 验证码存储到数据库
                self.store_verification_code(phone, code)
                QMessageBox.information(self, "提示", "验证码发送成功")
                # 成功发送后禁用按钮，并启动60秒倒计时
                self.send_verification_code_button.setEnabled(False)
                self.countdown = 60
                self.send_verification_code_button.setText(f"{self.countdown}s")
                self.timer.start()
            else:
                QMessageBox.warning(self, "提示", "验证码发送失败：" + response_dict.get("Message", "未知错误"))
        except Exception as e:
            QMessageBox.warning(self, "提示", f"发送验证码异常: {str(e)}")

    def send_sms(self, phone, code):
        # 初始化AcsClient，注意区域要与短信服务所在区域一致
        client = AcsClient(db_config.SMS_ACCESS_KEY_ID,
                           db_config.SMS_ACCESS_KEY_SECRET,
                           "cn-hangzhou")
        request = SendSmsRequest.SendSmsRequest()
        # 请根据你在阿里云申请的短信模板和签名修改以下内容
        request.set_TemplateCode('SMS_480605081')  # 短信模板CODE
        request.set_SignName('Naptec数据标注业务')  # 签名名称
        request.set_PhoneNumbers(phone)
        request.set_TemplateParam(json.dumps({"code": code}))
        # 发起请求
        response = client.do_action_with_exception(request)
        return response

    def update_countdown(self):
        self.countdown -= 1
        if self.countdown <= 0:
            self.timer.stop()
            self.send_verification_code_button.setEnabled(True)
            self.send_verification_code_button.setText("发送验证码")
        else:
            self.send_verification_code_button.setText(f"{self.countdown}s")

    def sign_up(self):
        username = self.username_edit.text().strip()
        phone = self.phone_edit.text().strip()
        input_code = self.verification_code_edit.text().strip()
        password = self.password_edit.text()
        confirm_password = self.confirm_password_edit.text()

        if not username or not phone or not password or not confirm_password or not input_code:
            QMessageBox.warning(self, "提示", "请输入完整信息")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "提示", "两次输入的密码不一致")
            return

        # 从数据库查询该手机最近的一条验证码记录，并判断是否在有效期内
        try:
            conn = pymysql.connect(
                host=db_config.HOST,
                port=db_config.PORT,
                user=db_config.USER,
                password=db_config.PASSWORD,
                database=db_config.DATABASE,
                charset="utf8"
            )
            cursor = conn.cursor()
            sql = "SELECT code, expire_at FROM sms_verification WHERE phone_number=%s ORDER BY created_at DESC LIMIT 1"
            cursor.execute(sql, (phone,))
            result = cursor.fetchone()
            if not result:
                QMessageBox.warning(self, "提示", "请先获取验证码")
                return

            stored_code, expire_at = result
            # 检查验证码是否过期
            if datetime.now() > expire_at:
                QMessageBox.warning(self, "提示", "验证码已过期，请重新获取")
                return

            if input_code != stored_code:
                QMessageBox.warning(self, "提示", "验证码错误")
                return
        except Exception as e:
            QMessageBox.warning(self, "提示", f"验证码验证失败: {str(e)}")
            return
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

        # 连接数据库，检查该手机号码是否已经注册
        try:
            conn = pymysql.connect(
                host=db_config.HOST,
                port=db_config.PORT,
                user=db_config.USER,
                password=db_config.PASSWORD,
                database=db_config.DATABASE,
                charset="utf8"
            )
            cursor = conn.cursor()
            sql = "SELECT * FROM user_info WHERE account=%s"
            cursor.execute(sql, (phone,))
            result = cursor.fetchone()
            if result:
                QMessageBox.warning(self, "提示", "该账号已注册")
                return

            # 将用户信息写入数据库
            sql_insert = "INSERT INTO user_info (name, account, password) VALUES (%s, %s, %s)"
            cursor.execute(sql_insert, (username, phone, password))
            conn.commit()
            QMessageBox.information(self, "提示", "注册成功，请返回登录")
            self.switch_back.emit()
        except Exception as e:
            QMessageBox.warning(self, "提示", f"注册失败: {str(e)}")
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    sign_up_widget = SignUpWidget()
    sign_up_widget.show()
    sys.exit(app.exec_())
