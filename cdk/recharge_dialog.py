# recharge_dialog.py
import logging

import pymysql
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QMessageBox, QLabel, QLineEdit, QPushButton, QHBoxLayout
from PyQt5.QtCore import pyqtSignal, QTimer, Qt, QMetaObject, Q_ARG
from PyQt5.QtGui import QPixmap

from config import anno_config
from config.db_config import db_config

class RechargeDialog(QDialog):
    recharge_success_signal = pyqtSignal()  # 充值成功信号

    def __init__(self, user_info, parent=None):
        super().__init__(parent)
        self.user_info = user_info
        self.setWindowTitle("充值")
        self.setFixedSize(300, 200)
        self.init_ui()

    def init_ui(self):
        # 设置整体样式
        self.setStyleSheet("""
            QDialog {
                background-color: #f7f7f7;
            }
            QLabel {
                font-size: 14px;
                color: #333333;
            }
            QLineEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 6px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #53B6D6; /* 浅蓝色 */
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #4398D4; /* 鼠标悬停时蓝色 */
            }
            QPushButton:pressed {
                background-color: #0056b3;
            }
        """)

        layout = QVBoxLayout(self)

        # 提示信息（点击链接打开微店）
        prompt_label = QLabel("请前往微店链接进行购买：<a href='https://weidian.com/?userid=1728312873&spider_token=b10a'>点击购买</a>")
        prompt_label.setOpenExternalLinks(True)
        layout.addWidget(prompt_label)

        # CDK输入框
        self.cdk_input = QLineEdit()
        self.cdk_input.setPlaceholderText("请输入CDK")
        layout.addWidget(self.cdk_input)

        # 兑换按钮
        self.exchange_button = QPushButton("兑换CDK")
        self.exchange_button.clicked.connect(self.exchange_cdk)
        layout.addWidget(self.exchange_button)

        # 状态信息显示
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

    def exchange_cdk(self):
        cdk_value = self.cdk_input.text().strip()
        if not cdk_value:
            self.status_label.setText("请输入CDK")
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
                get_vip_sql = "SELECT vip FROM user_info WHERE id = %s"
                cursor.execute(get_vip_sql, (self.user_info['id'],))
                current_vip_level = cursor.fetchone()[0]

                sql = "SELECT id, is_used, points FROM cdk WHERE cdk = %s"
                cursor.execute(sql, (cdk_value,))
                result = cursor.fetchone()

                if not result:
                    self.status_label.setText("无效的CDK")
                    return

                cdk_id, is_used, points = result
                if is_used == 1:
                    self.status_label.setText("该CDK已使用")
                    return

                update_cdk_sql = "UPDATE cdk SET is_used = 1 WHERE id = %s"
                cursor.execute(update_cdk_sql, (cdk_id,))

                # 更新用户积分和VIP等级
                update_user_sql = """
                    UPDATE user_info
                    SET current_points = current_points + %s,
                        total_points = total_points + %s
                    WHERE id = %s
                """
                cursor.execute(update_user_sql, (points, points, self.user_info['id']))

                # 获取更新后的用户信息
                get_user_sql = "SELECT total_points FROM user_info WHERE id = %s"
                cursor.execute(get_user_sql, (self.user_info['id'],))
                total_points = cursor.fetchone()[0]

                # 根据累积积分更新VIP等级
                if total_points >= 168888:
                    vip_level = 5
                elif total_points >= 88800:
                    vip_level = 4
                elif total_points >= 6800:
                    vip_level = 3
                elif total_points >= 1090:
                    vip_level = 2
                else:
                    vip_level = 1

                # 更新VIP等级
                update_vip_sql = "UPDATE user_info SET vip = %s WHERE id = %s"
                cursor.execute(update_vip_sql, (vip_level, self.user_info['id']))

                connection.commit()

                # -----------------------------
                # 充值金额为兑换积分除以100
                insert_record_sql = "INSERT INTO recharge_records (account, amount) VALUES (%s, %s)"
                cursor.execute(insert_record_sql, (self.user_info['account'], points / 100))
                connection.commit()
                # -----------------------------

                # 更新本地数据
                self.user_info['current_points'] += points
                self.user_info['total_points'] += points
                self.user_info['vip'] = vip_level

                if current_vip_level != vip_level:
                    if current_vip_level != vip_level:
                        # 创建自定义提示框
                        msg_box = QMessageBox(self)
                        msg_box.setWindowTitle("VIP等级提升")

                        # 设置样式和尺寸
                        msg_box.setStyleSheet("""
                                QMessageBox {
                                    background-color: #F7F7F7;
                                    min-width: 300px;
                                    min-height: 150px;
                                }
                                QLabel {
                                    color: #FFD700;  /* 金色字体 */
                                    font-size: 18px;
                                    font-weight: bold;
                                    qproperty-alignment: AlignCenter;
                                }
                                QPushButton {
                                    min-width: 80px;
                                    min-height: 30px;
                                    font-size: 14px;
                                }
                            """)

                        # 设置提示内容
                        msg_box.setText(f"恭喜！您的VIP等级已提升至\nVIP{vip_level}")

                        # 增大图标尺寸（可选）
                        msg_box.setIconPixmap(QPixmap("vip_icon.png").scaled(64, 64, Qt.KeepAspectRatio))

                        # 设置窗口尺寸
                        msg_box.setMinimumSize(350, 180)

                        # 添加确认按钮
                        msg_box.addButton("确定", QMessageBox.AcceptRole)

                        # 显示对话框
                        msg_box.exec_()
                self.status_label.setText("充值成功")
                self.recharge_success_signal.emit()
                QTimer.singleShot(150, self.close)
        except pymysql.Error as e:
            self.status_label.setText("数据库错误: " + str(e))
        finally:
            if 'connection' in locals() and connection.open:
                connection.close()

class ExchangeDialog(QDialog):
    def __init__(self, user_info, parent=None):
        super().__init__(parent)
        self.setStyleSheet(anno_config.exchange_dialog_style)
        self.user_info = user_info
        self.parent = parent  # 保存父窗口引用
        self.setWindowTitle("积分兑换")
        self.setFixedSize(400, 300)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # VIP等级显示
        self.vip_label = QLabel(f"当前VIP等级：VIP{self.user_info['vip']}")
        self.vip_label.setStyleSheet("font-size: 16px; color: #333;")
        layout.addWidget(self.vip_label)

        # 兑换比例说明
        rate_text = self.get_exchange_rate_text()
        self.rate_label = QLabel(rate_text)
        layout.addWidget(self.rate_label)

        # 输入框
        self.input_layout = QHBoxLayout()
        self.quantity_edit = QLineEdit()
        self.quantity_edit.setPlaceholderText("输入兑换数量")
        self.quantity_edit.textChanged.connect(self.calculate_points)
        self.input_layout.addWidget(QLabel("兑换数量："))
        self.input_layout.addWidget(self.quantity_edit)
        layout.addLayout(self.input_layout)

        # 积分显示
        self.points_label = QLabel("所需积分：0")
        layout.addWidget(self.points_label)

        # 确认按钮
        self.confirm_btn = QPushButton("确认兑换")
        self.confirm_btn.clicked.connect(self.confirm_exchange)
        layout.addWidget(self.confirm_btn)

    def get_exchange_rate_text(self):
        rates = {
            1: "您当前为青铜VIP1，兑换方式为5积分兑换1标注余额",
            2: "您当前为白银VIP2，兑换方式为4积分兑换1标注余额",
            3: "您当前为黄金VIP3，兑换方式为3积分兑换1标注余额",
            4: "您当前为钻石VIP4，兑换方式为2积分兑换1标注余额",
            5: "您当前为至尊VIP5，兑换方式为1积分兑换1标注余额"
        }
        return rates.get(self.user_info['vip'], "未知VIP等级")

    def calculate_points(self):
        try:
            quantity = int(self.quantity_edit.text())
            rate = self.get_exchange_rate()
            required = quantity * rate
            self.points_label.setText(f"所需积分：{required}")
        except ValueError:
            self.points_label.setText("所需积分：0")

    def get_exchange_rate(self):
        vip_rates = {1: 5, 2: 4, 3: 3, 4: 2, 5: 1}
        return vip_rates.get(self.user_info['vip'], 0)

    def confirm_exchange(self):
        try:
            input_text = self.quantity_edit.text().strip()
            if not input_text:
                raise ValueError("兑换数量不能为空")
            # 输入验证
            quantity = int(self.quantity_edit.text())
            if not (1 <= quantity <= 1000000):
                raise ValueError("兑换数量需在1-1000000之间")

            # 计算积分
            rate = self.get_exchange_rate()
            required_points = quantity * rate

            # 积分检查
            if self.user_info['current_points'] < required_points:
                raise ValueError("积分不足")

            # 数据库操作
            with self.create_db_connection() as connection:
                with connection.cursor() as cursor:
                    sql = """UPDATE user_info 
                             SET current_points = current_points - %s,
                                 rectangle_remaining = rectangle_remaining + %s 
                             WHERE id = %s"""
                    cursor.execute(sql, (required_points, quantity, self.user_info['id']))
                    connection.commit()

            # 更新本地数据
            self.user_info['current_points'] -= required_points
            self.user_info['rectangle_remaining'] += quantity

            # 线程安全更新UI
            QMetaObject.invokeMethod(
                self.parent,
                'update_ui_after_exchange',
                Qt.QueuedConnection,
                Q_ARG(int, self.user_info['current_points']),
                Q_ARG(int, self.user_info['rectangle_remaining'])
            )

            # 显示成功提示
            QMessageBox.information(self, "成功",
                f"成功兑换{quantity}标注余额，消耗{required_points}积分")
            self.close()

        except ValueError as e:
            error_msg = str(e)
            if "invalid literal for int()" in error_msg:
                QMessageBox.warning(self, "输入错误", "请输入有效的数字")
            else:
                QMessageBox.warning(self, "输入错误", error_msg)
        except pymysql.Error as e:
            QMessageBox.critical(self, "数据库错误", f"操作失败: {str(e)}")
            logging.error(f"数据库错误: {e}")
        except Exception as e:
            QMessageBox.critical(self, "系统错误", f"发生未预期的错误: {str(e)}")
            logging.exception("严重错误:")

    def create_db_connection(self):
        """创建可重用的数据库连接"""
        return pymysql.connect(
            host=db_config.HOST,
            port=db_config.PORT,
            user=db_config.USER,
            password=db_config.PASSWORD,
            database=db_config.DATABASE,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )