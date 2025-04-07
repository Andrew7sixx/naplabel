import sys
import json
import pymysql
import secrets
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QMessageBox, \
    QApplication, QSizePolicy
from PyQt5.QtCore import pyqtSignal, QTimer
from config import password_config
from config.db_config import db_config
from aliyunsdkcore.client import AcsClient
from aliyunsdkdysmsapi.request.v20170525 import SendSmsRequest


class PasswordWidget(QWidget):
    switch_back = pyqtSignal()

    def __init__(self):
        super().__init__()
        # 窗口基础设置
        self.setWindowTitle("Nap-Label修改密码")
        self.setFixedSize(400, 550)  # 设置窗口大小为400x550

        # 倒计时定时器
        self.countdown = 60
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_countdown)

        self.init_ui()

    def init_ui(self):
        # 主布局容器（保持原有样式）
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 20)
        main_layout.setSpacing(2)

        # ==================== 标题区块 ====================
        title_container = QWidget()
        title_container.setObjectName("TitleContainer")
        title_container.setStyleSheet(password_config.title_container_style)
        title_container.setFixedHeight(80)

        title_label = QLabel("Naptec")
        title_label.setObjectName("MainTitle")
        title_label.setStyleSheet(password_config.main_title_style)

        title_layout = QVBoxLayout(title_container)
        title_layout.addWidget(title_label)
        main_layout.addWidget(title_container)

        # ==================== 副标题 ====================
        subtitle_label = QLabel("修改密码", self)
        subtitle_label.setObjectName("SubTitle")
        subtitle_label.setStyleSheet(password_config.password_sub_title_style)
        main_layout.addWidget(subtitle_label)

        # ==================== 表单区域 ====================
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(50, 0, 50, 0)
        form_layout.setSpacing(15)

        # 手机号码输入
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("请输入手机号码")
        self.phone_edit.setStyleSheet(password_config.account_edit_style)
        form_layout.addWidget(self.phone_edit)

        # 验证码输入及发送按钮
        verification_code_layout = QHBoxLayout()
        self.verification_code_edit = QLineEdit()
        self.verification_code_edit.setPlaceholderText("请输入验证码")
        self.verification_code_edit.setStyleSheet(password_config.verification_code_edit_style)
        verification_code_layout.addWidget(self.verification_code_edit)

        self.send_verification_code_button = QPushButton("发送验证码")
        self.send_verification_code_button.setStyleSheet(password_config.send_verification_code_button_style)
        self.send_verification_code_button.clicked.connect(self.send_verification_code)
        verification_code_layout.addWidget(self.send_verification_code_button)
        form_layout.addLayout(verification_code_layout)

        # 新密码输入
        self.new_password_edit = QLineEdit()
        self.new_password_edit.setPlaceholderText("请输入新密码")
        self.new_password_edit.setEchoMode(QLineEdit.Password)
        self.new_password_edit.setStyleSheet(password_config.password_edit_style)
        form_layout.addWidget(self.new_password_edit)

        # 确认密码
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setPlaceholderText("请确认密码")
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)
        self.confirm_password_edit.setStyleSheet(password_config.password_edit_style)
        form_layout.addWidget(self.confirm_password_edit)

        # 修改密码按钮
        self.change_password_button = QPushButton("修改密码")
        self.change_password_button.setStyleSheet(password_config.button_style)
        self.change_password_button.clicked.connect(self.change_password)
        form_layout.addWidget(self.change_password_button)

        # 返回按钮
        back_button = QPushButton("返回登录")
        back_button.setStyleSheet(password_config.back_button_style)
        back_button.clicked.connect(self.switch_back.emit)
        form_layout.addWidget(back_button)

        main_layout.addWidget(form_container)

    def generate_code(self, length=6):
        """生成指定位数的随机数字验证码"""
        return ''.join(str(secrets.randbelow(10)) for _ in range(length))

    def store_verification_code(self, phone, code, expire_seconds=300):
        """存储验证码到数据库"""
        expire_time = datetime.now() + timedelta(seconds=expire_seconds)
        conn = None
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
            sql = """INSERT INTO sms_verification 
                     (phone_number, code, expire_at) 
                     VALUES (%s, %s, %s)"""
            cursor.execute(sql, (phone, code, expire_time))
            conn.commit()
        except Exception as e:
            raise Exception(f"验证码存储失败: {str(e)}")
        finally:
            if conn:
                conn.close()

    def send_sms(self, phone, code):
        """调用阿里云短信服务发送验证码"""
        client = AcsClient(db_config.SMS_ACCESS_KEY_ID,
                           db_config.SMS_ACCESS_KEY_SECRET,
                           "cn-hangzhou")
        request = SendSmsRequest.SendSmsRequest()
        request.set_TemplateCode('SMS_480620092')  # 使用验证码模板
        request.set_SignName('Naptec数据标注业务')
        request.set_PhoneNumbers(phone)
        request.set_TemplateParam(json.dumps({"code": code}))
        return client.do_action_with_exception(request)

    def send_verification_code(self):
        """发送验证码按钮点击事件"""
        phone = self.phone_edit.text().strip()
        if not phone:
            QMessageBox.warning(self, "提示", "请输入手机号码")
            return

        # 验证手机号是否已注册
        conn = None
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
            cursor.execute("SELECT * FROM user_info WHERE account=%s", (phone,))
            if not cursor.fetchone():
                QMessageBox.warning(self, "提示", "该手机号未注册")
                return
        except Exception as e:
            QMessageBox.critical(self, "错误", f"查询失败: {str(e)}")
            return
        finally:
            if conn:
                conn.close()

        # 生成并发送验证码
        try:
            code = self.generate_code()
            self.send_sms(phone, code)
            self.store_verification_code(phone, code)

            # 启动倒计时
            self.send_verification_code_button.setEnabled(False)
            self.countdown = 60
            self.timer.start()
            self.send_verification_code_button.setText(f"{self.countdown}s")
            QMessageBox.information(self, "提示", "验证码已发送")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"验证码发送失败: {str(e)}")

    def update_countdown(self):
        """更新倒计时显示"""
        self.countdown -= 1
        if self.countdown <= 0:
            self.timer.stop()
            self.send_verification_code_button.setEnabled(True)
            self.send_verification_code_button.setText("发送验证码")
        else:
            self.send_verification_code_button.setText(f"{self.countdown}s")

    def change_password(self):
        """修改密码核心逻辑"""
        phone = self.phone_edit.text().strip()
        code = self.verification_code_edit.text().strip()
        new_password = self.new_password_edit.text().strip()
        confirm_password = self.confirm_password_edit.text().strip()

        # 基础验证
        if not all([phone, code, new_password, confirm_password]):
            QMessageBox.warning(self, "提示", "请填写所有字段")
            return
        if new_password != confirm_password:
            QMessageBox.warning(self, "错误", "两次密码输入不一致")
            return

        # 验证码校验
        conn = None
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
            cursor.execute("""SELECT code, expire_at 
                            FROM sms_verification 
                            WHERE phone_number=%s 
                            ORDER BY created_at DESC LIMIT 1""", (phone,))
            result = cursor.fetchone()

            if not result:
                QMessageBox.warning(self, "错误", "请先获取验证码")
                return
            stored_code, expire_time = result
            if datetime.now() > expire_time:
                QMessageBox.warning(self, "错误", "验证码已过期")
                return
            if code != stored_code:
                QMessageBox.warning(self, "错误", "验证码不正确")
                return
        except Exception as e:
            QMessageBox.critical(self, "错误", f"验证码验证失败: {str(e)}")
            return
        finally:
            if conn:
                conn.close()

        # 更新密码
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
            cursor.execute("UPDATE user_info SET password=%s WHERE account=%s",
                           (new_password, phone))
            conn.commit()
            QMessageBox.information(self, "成功", "密码修改成功，请返回登录")
            self.switch_back.emit()  # 自动跳转回登录界面
        except Exception as e:
            QMessageBox.critical(self, "错误", f"密码更新失败: {str(e)}")
        finally:
            if conn:
                conn.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PasswordWidget()
    window.show()
    sys.exit(app.exec_())