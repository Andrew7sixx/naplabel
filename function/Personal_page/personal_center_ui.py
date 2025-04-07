import sys
import sqlite3

import pymysql
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
                             QTableWidgetItem, QApplication, QStackedWidget, QSizePolicy, QHeaderView, QMessageBox,
                             QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from config import personal_config
from config.db_config import db_config

# 客服反馈页面类（可简化，因弹窗替代原页面功能）
class CustomerFeedbackPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

# 历史标注记录页面类
class AnnotationRecordPage(QWidget):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data  # 保存当前登录用户数据
        layout = QVBoxLayout()

        # 添加“标注记录”标题
        title_label = QLabel("标注记录")
        # 假设 personal_config 模块存在，引用配置文件样式
        title_label.setStyleSheet(personal_config.title_label_style)
        layout.addWidget(title_label)

        # 添加搜索框
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("按标注类型搜索")
        # 可以根据需要取消注释下面这行来设置搜索框样式
        # self.search_edit.setStyleSheet(personal_config.search_box_style)
        self.search_edit.textChanged.connect(self.filter_annotation_data)
        layout.addWidget(self.search_edit)

        self.annotation_table = QTableWidget()
        self.annotation_table.setColumnCount(3)
        self.annotation_table.setHorizontalHeaderLabels(["标注类型", "完成时间", "使用框数"])

        # 设置表格尺寸策略，允许扩展
        self.annotation_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 设置列宽自动拉伸占满表格宽度
        header = self.annotation_table.horizontalHeader()
        for i in range(self.annotation_table.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.Stretch)

        # 设置表头字体
        font = QFont()
        font.setPointSize(14)
        font.setFamily('Arial')
        font.setBold(False)
        header.setFont(font)

        # 新增表格数据样式设置
        self.annotation_table.setStyleSheet("""
            QTableWidget {
                font-size: 14px;         /* 字体大小 */
                color: #333333;          /* 文字颜色 */
                background-color: #F9F9F9;/* 表格背景色 */
                border: 1px solid #DDDDDD;/* 表格边框 */
            }
            QTableWidget::item {
                padding: 8px;            /* 单元格内边距 */
                border-bottom: 1px solid #E5E5E5; /* 单元格底部边框 */
            }
            QTableWidget::item:selected {
                background-color: #3883EF;/* 选中单元格背景色 */
                color: white;             /* 选中文字颜色 */
                border: none;
            }
            QTableWidget::item:focus {  /* 新增：处理焦点状态下的边框 */
                outline: none;  /* 清除焦点虚线框，部分场景需同时处理 outline */
                border: none;   /* 确保边框无绘制 */
            }
        """)

        layout.addWidget(self.annotation_table)

        # 新增提示标签
        self.no_data_label = QLabel("暂未连接数据库，无内容")
        self.no_data_label.setAlignment(Qt.AlignCenter)
        self.no_data_label.setVisible(False)
        layout.addWidget(self.no_data_label)

        self.setLayout(layout)
        # 设置页面自身尺寸策略，允许水平垂直扩展
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.load_annotation_data()
        self.raw_data = []  # 存储原始数据用于搜索过滤

    def filter_annotation_data(self):
        search_text = self.search_edit.text()
        self.load_annotation_data(search_text)


    def load_annotation_data(self, search_text=""):
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
                if search_text:
                    sql = ("SELECT annotation_type, create_time, used_count FROM annotation_history "
                           "WHERE account = %s AND LOWER(annotation_type) LIKE %s")
                    cursor.execute(sql, (self.user_data["account"], '%' + search_text.lower() + '%'))
                else:
                    sql = "SELECT annotation_type, create_time, used_count FROM annotation_history WHERE account = %s"
                    cursor.execute(sql, (self.user_data["account"],))
                data = cursor.fetchall()
            connection.close()

            # 清空并更新表格数据
            self.raw_data = data
            self.annotation_table.setRowCount(0)
            if data:
                self.no_data_label.setVisible(False)
                self.annotation_table.setRowCount(len(data))
                for row, record in enumerate(data):
                    for col, item in enumerate(record):
                        table_item = QTableWidgetItem(str(item))
                        self.annotation_table.setItem(row, col, table_item)
            else:
                self.no_data_label.setVisible(True)
        except pymysql.Error as e:
            print(f"数据库错误: {e}")
            self.no_data_label.setVisible(True)


# 充值记录页面类
class RechargeRecordPage(QWidget):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data  # 保存当前登录用户数据
        layout = QVBoxLayout()

        # 添加“充值记录”标题
        title_label = QLabel("充值记录")
        title_label.setStyleSheet(personal_config.title_label_style)
        layout.addWidget(title_label)

        # 添加搜索框
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("按充值时间搜索")
        # 可以根据需要取消注释下面这行来设置搜索框样式
        # self.search_edit.setStyleSheet(personal_config.search_box_style)
        self.search_edit.textChanged.connect(self.filter_recharge_data)
        layout.addWidget(self.search_edit)

        self.recharge_table = QTableWidget()
        self.recharge_table.setColumnCount(3)
        self.recharge_table.setHorizontalHeaderLabels(["充值账号", "充值时间", "充值金额"])

        # 设置表格尺寸策略，允许扩展
        self.recharge_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 设置列宽自动拉伸占满表格宽度
        header = self.recharge_table.horizontalHeader()
        for i in range(self.recharge_table.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.Stretch)

        # 设置表头字体
        font = QFont()
        font.setPointSize(14)
        font.setFamily('Arial')
        font.setBold(False)
        header.setFont(font)

        # 新增表格数据样式设置
        self.recharge_table.setStyleSheet("""
            QTableWidget {
                font-size: 14px;         /* 字体大小 */
                color: #333333;          /* 文字颜色 */
                background-color: #F9F9F9;/* 表格背景色 */
                border: 1px solid #DDDDDD;/* 表格边框 */
            }
            QTableWidget::item {
                padding: 8px;            /* 单元格内边距 */
                border-bottom: 1px solid #E5E5E5; /* 单元格底部边框 */
            }
            QTableWidget::item:selected {
                background-color: #3883EF;/* 选中单元格背景色 */
                color: white;             /* 选中文字颜色 */
                border: none;
            }
            QTableWidget::item:focus {  /* 处理焦点状态下的边框 */
                outline: none;  /* 清除焦点虚线框，部分场景需同时处理 outline */
                border: none;   /* 确保边框无绘制 */
            }
        """)

        layout.addWidget(self.recharge_table)

        # 新增提示标签
        self.no_data_label = QLabel("暂未连接数据库，无内容")
        self.no_data_label.setAlignment(Qt.AlignCenter)
        self.no_data_label.setVisible(False)
        layout.addWidget(self.no_data_label)

        self.setLayout(layout)
        # 设置页面自身尺寸策略，允许水平垂直扩展
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.load_recharge_data()
        self.raw_data = []  # 存储原始数据用于搜索过滤

    def filter_recharge_data(self):
        search_text = self.search_edit.text()
        self.load_recharge_data(search_text)


    def load_recharge_data(self, search_text=""):
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
                if search_text:
                    sql = ("SELECT account, create_time, amount FROM recharge_records "
                           "WHERE account = %s AND LOWER(create_time) LIKE %s")
                    cursor.execute(sql, (self.user_data["account"], '%' + search_text.lower() + '%'))
                else:
                    sql = "SELECT account, create_time, amount FROM recharge_records WHERE account = %s"
                    cursor.execute(sql, (self.user_data["account"],))
                data = cursor.fetchall()
            connection.close()

            self.raw_data = data
            self.recharge_table.setRowCount(0)
            if data:
                self.no_data_label.setVisible(False)
                self.recharge_table.setRowCount(len(data))
                for row, record in enumerate(data):
                    for col, item in enumerate(record):
                        table_item = QTableWidgetItem(str(item))
                        self.recharge_table.setItem(row, col, table_item)
            else:
                self.no_data_label.setVisible(True)
        except pymysql.Error as e:
            print(f"数据库错误: {e}")
            self.no_data_label.setVisible(True)


class PersonalCenter(QWidget):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data  # 存储当前登录用户信息
        # 后续初始化中就可以使用 self.user_data["account"] 来过滤查询
        self.setWindowTitle("个人中心")
        self.resize(1000, 600)
        self.setStyleSheet("QWidget { background-color: #F0F8FF; font-family: 'Roboto', sans-serif; color: #333; }")
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)  # 去除主布局边距

        # 顶部信息栏
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)  # 去除布局边距
        info_widget = QWidget()
        info_widget.setObjectName("InfoWidget")
        info_widget.setFixedHeight(int(self.height() * 0.08))
        info_widget.setStyleSheet(personal_config.info_widget_style)

        # 添加“个人中心”标题，并设置对齐方式为左上角
        center_title = QLabel("个人中心")
        center_title.setStyleSheet(personal_config.center_title_style)
        info_layout.addWidget(center_title, Qt.AlignLeft)  # 指定对齐方式

        # 显示剩余积分
        remain_score = self.get_remain_score()
        self.score_label = QLabel(f"当前剩余积分：{remain_score}")
        self.score_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #000;
                background-color: #F0F8FF;
                padding: 8px 15px;
                border: 1px solid #ccc;
                border-radius: 10px;
            }
        """)
        info_layout.addWidget(self.score_label)

        # 从数据库中获取用户账号
        account = self.get_user_account()
        account_info_text = QLabel(f"当前账号：{account}")
        account_info_text.setStyleSheet(personal_config.account_info_text_style)
        account_info_text.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        info_layout.addWidget(account_info_text)

        info_widget.setLayout(info_layout)
        main_layout.addWidget(info_widget)

        # 主体内容布局（后续代码保持不变）
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)  # 去除内容布局边距

        # 左侧菜单栏
        menu_layout = QVBoxLayout()
        menu_layout.setSpacing(10)
        menu_layout.setAlignment(Qt.AlignTop)
        menu_widget = QWidget()
        menu_widget.setObjectName("MenuWidget")
        menu_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)  # 固定水平，垂直扩展
        menu_widget.setFixedWidth(int(self.width() * 0.24))
        menu_widget.setStyleSheet(personal_config.menu_widget_style)

        annotation_record_button = QPushButton("历史标注")
        annotation_record_button.setStyleSheet(personal_config.menu_widget_button_style)

        recharge_record_button = QPushButton("充值记录")
        recharge_record_button.setStyleSheet(personal_config.menu_widget_button_style)

        customer_feedback_button = QPushButton("客服反馈")
        customer_feedback_button.setStyleSheet(personal_config.customer_feedback_button_style)

        menu_layout.addWidget(annotation_record_button)
        menu_layout.addWidget(recharge_record_button)
        menu_layout.addWidget(customer_feedback_button)
        menu_layout.addStretch(1)  # 调整拉伸，确保按钮布局合理

        menu_widget.setLayout(menu_layout)
        content_layout.addWidget(menu_widget)

        # 右侧页面容器
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_layout.addWidget(self.stacked_widget)
        content_layout.setStretchFactor(self.stacked_widget, 1)  # 右侧拉伸权重

        main_layout.addLayout(content_layout)

        # 页面添加
        self.annotation_record_page = AnnotationRecordPage(self.user_data)
        self.recharge_record_page = RechargeRecordPage(self.user_data)
        self.customer_feedback_page = CustomerFeedbackPage()  # 如果无需user_data可保持不变

        self.stacked_widget.addWidget(self.annotation_record_page)
        self.stacked_widget.addWidget(self.recharge_record_page)
        self.stacked_widget.addWidget(self.customer_feedback_page)

        # 信号连接
        annotation_record_button.clicked.connect(self.show_annotation_record_page)
        recharge_record_button.clicked.connect(self.show_recharge_record_page)
        customer_feedback_button.clicked.connect(self.show_feedback_dialog)

        self.setLayout(main_layout)

    def get_user_account(self):
        try:
            # 连接到云数据库MySQL
            connection = pymysql.connect(
                host=db_config.HOST,
                port=db_config.PORT,
                user=db_config.USER,
                password=db_config.PASSWORD,
                database=db_config.DATABASE,
                charset='utf8mb4'
            )

            with connection.cursor() as cursor:
                # 查询当前登录用户的用户名
                sql = "SELECT name FROM user_info WHERE account = %s"
                cursor.execute(sql, (self.user_data["account"],))
                result = cursor.fetchone()

            connection.close()

            if result:
                return result[0]  # 返回用户名
            else:
                return "未找到用户信息"

        except pymysql.Error as e:
            print(f"数据库错误: {e}")
            return "数据库连接错误"
        except KeyError:
            print("用户数据中缺少account字段")
            return "用户信息不完整"

    def get_remain_score(self):
        """从数据库获取当前登录用户的剩余积分"""
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
                sql = "SELECT current_points FROM user_info WHERE account = %s"
                cursor.execute(sql, (self.user_data["account"],))
                result = cursor.fetchone()
            connection.close()
            return result[0] if result else 0
        except pymysql.Error as e:
            print(f"获取积分错误: {e}")
            return 0

    def showEvent(self, event):
        remain_score = self.get_remain_score()
        self.score_label.setText(f"当前剩余积分：{remain_score}")
        super().showEvent(event)

    def show_feedback_dialog(self):
        """显示客服反馈弹窗"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("客服反馈")
        msg_box.setText("用户你好，如果有任何订单问题或其他帮助，欢迎通过邮件联系我们Naplabel@163.edu.com")
        msg_box.setIcon(QMessageBox.Information)
        # 应用配置文件中的样式
        msg_box.setStyleSheet(personal_config.message_box_text_style)
        msg_box.exec_()

    def show_annotation_record_page(self):
        self.stacked_widget.setCurrentWidget(self.annotation_record_page)

    def show_recharge_record_page(self):
        self.stacked_widget.setCurrentWidget(self.recharge_record_page)



def main():
    app = QApplication(sys.argv)
    window = PersonalCenter()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()