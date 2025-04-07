#--------laojiang
import json
import shutil
import sys
from datetime import datetime
import os
import pymysql
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPixmap, QIcon, QColor
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QMessageBox, QTextEdit, QFileDialog, QComboBox, QProgressBar, QMenu, QWidgetAction, QSplitter, QSizePolicy,
    QFrame, QDialog, QListWidgetItem, QListWidget, QScrollArea, QTableWidget, QTableWidgetItem, QColorDialog, QDesktopWidget
)
from PyQt5.QtCore import Qt, pyqtSignal, QSortFilterProxyModel, QEvent, QTimer, pyqtSlot
from PyQt5.QtCore import QSize, QMutexLocker
from config import anno_config
from function.Annotation_page.image_processing_thread import ImageProcessingThread
from function.Annotation_page.Manual_annotation import AnnotationTool  # 假设 ManualAnnotation 是手动标注的类
from function.Personal_page.personal_center_ui import PersonalCenter  # 引入你的个人中心页面类
from PyQt5.QtWidgets import QPushButton, QSizePolicy
# 导入充值对话框
from cdk.recharge_dialog import RechargeDialog, ExchangeDialog
import paramiko
from config.ssh_config import ssh_config
from config.db_config import db_config


# 假设这是 COCO 类别列表
coco_classes = [
    'person (人)', 'bicycle (自行车)', 'car (汽车)', 'motorbike (摩托车)', 'airplane (飞机)',
    'bus (公交车)', 'train (火车)', 'truck (卡车)', 'boat (船)', 'traffic light (交通灯)',
    'fire hydrant (消防栓)', 'stop sign (停车标志)', 'parking meter (停车计时器)', 'bench (长椅)',
    'bird (鸟)', 'cat (猫)', 'dog (狗)', 'horse (马)', 'sheep (羊)', 'cow (牛)',
    'elephant (大象)', 'bear (熊)', 'zebra (斑马)', 'giraffe (长颈鹿)', 'backpack (背包)',
    'umbrella (伞)', 'handbag (手提包)', 'tie (领带)', 'suitcase (行李箱)', 'frisbee (飞盘)',
    'skis (滑雪板)', 'snowboard (单板滑雪)', 'sports ball (运动球)', 'kite (风筝)',
    'baseball bat (棒球棒)', 'baseball glove (棒球手套)', 'skateboard (滑板)', 'surfboard (冲浪板)',
    'tennis racket (网球拍)', 'bottle (瓶子)', 'wine glass (酒杯)', 'cup (杯子)', 'fork (叉子)',
    'knife (刀)', 'spoon (勺子)', 'bowl (碗)', 'banana (香蕉)', 'apple (苹果)', 'sandwich (三明治)',
    'orange (橙子)', 'broccoli (西兰花)', 'carrot (胡萝卜)', 'hot dog (热狗)', 'pizza (披萨)',
    'donut (甜甜圈)', 'cake (蛋糕)', 'chair (椅子)', 'couch (沙发)', 'potted plant (盆栽植物)',
    'bed (床)', 'dining table (餐桌)', 'toilet (厕所)', 'tv (电视)', 'laptop (笔记本电脑)',
    'mouse (鼠标)', 'remote (遥控器)', 'keyboard (键盘)', 'cell phone (手机)', 'microwave (微波炉)',
    'oven (烤箱)', 'toaster (烤面包机)', 'sink (水槽)', 'refrigerator (冰箱)', 'book (书)',
    'clock (时钟)', 'vase (花瓶)', 'scissors (剪刀)', 'teddy bear (泰迪熊)', 'hair drier (吹风机)',
    'toothbrush (牙刷)'
]


class AutoAnnotationSystem(QWidget):
    back_to_login_signal = pyqtSignal()
    go_to_personal_center_signal = pyqtSignal()
    switch_to_personal_center_signal = pyqtSignal()  # 定义切换到个人中心的信号

    def __init__(self, user_info=None):  ### 改4.2
        super().__init__()  ### 改4.2
        self.user_info = user_info
        self.setWindowTitle("Nap-Label")
        self.resize(1440, 960)
        self.init_new_layout()
        self.selected_classes = []
        self.process_thread = None
        self.task_file_list_widget = None
        self.search_line_edit = None
        self.is_process_complete = False
        self.result_folder = ""  # 用户选择的结果文件夹路径
        self.input_folder = ""  # 用户选择的输入文件夹路径
        self.set_optimal_size()  ### 改4.2：这句新加的
        self.user_info_popup = None
        self.current_exp = 7932
        self.next_level_exp = 10000
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide_user_info_popup)
        self.total_boxes = 0
        self.annotation_records = {}

        # 用户C盘创建文件夹
        # 修改临时文件夹和正常文件夹的基础路径为用户的C盘用户文件夹下
        base_user_path = os.path.expanduser("~")
        if self.user_info:
            account = self.user_info.get('account', 'default_account')
            self.temp_dir = os.path.join(base_user_path, f"{account}_temp")  # 临时目录
            self.normal_dir = os.path.join(base_user_path, f"{account}_normal")  # 正式目录
            try:
                os.makedirs(os.path.join(self.temp_dir, "img"), exist_ok=True)
                os.makedirs(os.path.join(self.temp_dir, "label"), exist_ok=True)
                os.makedirs(os.path.join(self.normal_dir, "img"), exist_ok=True)
                os.makedirs(os.path.join(self.normal_dir, "label"), exist_ok=True)
            except OSError as e:
                self.log_text_edit.append(f"创建本地目录时出错: {str(e)}")
        # 异常图像文件夹在用户选择保存路径后创建
        self.abnormal_dir = ""

    def update_annotation_records(self, image_name, box_count):
        """更新标注记录字典"""
        self.annotation_records[image_name] = box_count

    def update_user_info_display(self):
        updated_info = self.get_user_info_from_database()
        # 更新顶部状态栏的积分显示
        self.points_label.setText(f"当前剩余积分：{updated_info['remain_score']}")

        # 更新主页面显示的VIP等级
        user_level = self.findChild(QLabel, "user_level")  # 假设VIP等级的QLabel对象名为user_level
        if user_level:
            user_level.setText(f"VIP{self.user_info['vip']}")

        # 如果用户信息弹出菜单已经存在，则重置为 None，迫使下次重新创建更新后的信息
        self.user_info_popup = None
        # 弹窗提示充值成功（可选）
        QMessageBox.information(self, "充值成功", "充值成功，当前积分已更新！")

    def init_new_layout(self):
        main_layout = QVBoxLayout()

        # 顶部状态栏容器
        status_bar_container = QWidget()
        status_bar_container.setFixedHeight(int(self.height() * anno_config.status_bar_container_height_ratio))
        status_bar_container.setStyleSheet(anno_config.status_bar_container_style)

        status_bar_layout = QHBoxLayout(status_bar_container)
        status_bar_layout.setContentsMargins(0, 0, 0, 0)
        status_bar_layout.setSpacing(0)

        # 左侧 Logo
        logo_label = QLabel()
        logo_pixmap = QPixmap("logo.png")  # 替换为左侧Logo路径

        if not logo_pixmap.isNull():
            logo_pixmap = logo_pixmap.scaledToHeight(
                int(self.height() * anno_config.status_bar_container_height_ratio), Qt.SmoothTransformation
            )
            logo_pixmap = logo_pixmap.scaledToWidth(180)
            logo_label.setPixmap(logo_pixmap)
        status_bar_layout.addWidget(logo_label)

        # 添加拉伸项，将积分框置于中间
        status_bar_layout.addStretch(1)

        # 获取用户积分
        user_info = self.get_user_info_from_database()
        self.points_label = QLabel(f"当前剩余积分：{user_info['remain_score']}")
        self.points_label.setStyleSheet(anno_config.new_info_box_style)
        status_bar_layout.addWidget(self.points_label)

        # 再添加拉伸项，将用户区域置于右侧
        status_bar_layout.addStretch(1)

        # 右侧用户区域
        user_widget = QWidget()
        user_layout = QHBoxLayout(user_widget)
        user_layout.setContentsMargins(0, 0, 0, 0)
        user_layout.setSpacing(5)

        # 笑脸头像
        self.avatar_label = QLabel()
        # 修正路径为原始字符串
        avatar_pixmap = QPixmap(r"head.png")
        if not avatar_pixmap.isNull():
            avatar_pixmap = avatar_pixmap.scaledToHeight(
                int(self.height() * anno_config.status_bar_container_height_ratio), Qt.SmoothTransformation
            )
            self.avatar_label.setPixmap(avatar_pixmap)
        user_layout.addWidget(self.avatar_label)
        self.avatar_label.installEventFilter(self)

        # 用户信息垂直布局
        user_info_layout = QVBoxLayout()
        user_info_layout.setContentsMargins(0, 0, 0, 0)
        user_info_layout.setSpacing(0)

        # 修改用户文本
        user_text = QLabel(self.user_info['name'] if self.user_info else "未登录用户")

        # 增大字体大小
        user_text.setStyleSheet("color: #FFFFFF; font-size: 16px;")
        user_info_layout.addWidget(user_text)

        # 修改用户等级显示
        user_level = QLabel(f"VIP{self.user_info['vip']}" if self.user_info else "VIP0")
        user_level.setObjectName("user_level")  # 设置对象名为user_level
        user_level.setStyleSheet("color: #00B4F7; font-weight: bold; font-size: 16px;")
        user_info_layout.addWidget(user_level)

        # # 增大字体大小
        # user_level.setStyleSheet("color: #00B4F7; font-weight: bold; font-size: 16px;")
        # user_info_layout.addWidget(user_level)

        # 将用户信息布局添加到用户布局
        user_layout.addLayout(user_info_layout)

        # 调整用户区域的外边距，向左移动
        user_widget.setStyleSheet("margin-right: 20px;")

        # 将用户区域添加到状态栏布局
        status_bar_layout.addWidget(user_widget)

        main_layout.addWidget(status_bar_container)

        # 中间区域边界设置
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)  # 中间区域布局边距设为0

        # 创建用于左侧栏和主内容区的QSplitter
        left_right_splitter = QSplitter(Qt.Horizontal)

        # 左侧栏设置
        self.left_sidebar = QWidget()  # 保存左侧栏的引用
        self.left_sidebar.setStyleSheet("background-color: #e0e0e0;")
        left_layout = QVBoxLayout(self.left_sidebar)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setAlignment(Qt.AlignTop)


        self.upload_button = QPushButton("上传图片文件夹")
        self.upload_button.setStyleSheet(anno_config.button_style)
        self.upload_button.clicked.connect(self.select_input_folder)
        left_layout.addWidget(self.upload_button)

        # 新增上传文件夹按钮
        self.upload_button = QPushButton("选择保存路径")
        self.upload_button.setStyleSheet(anno_config.button_style)
        self.upload_button.clicked.connect(self.upload_folder)
        left_layout.addWidget(self.upload_button)

        # 搜索标注类型控件
        self.class_combo = QComboBox()
        self.class_combo.setEditable(True)  # 允许输入搜索
        self.class_combo.setInsertPolicy(QComboBox.NoInsert)  # 禁止插入新选项，仅搜索现有
        self.class_combo.setStyleSheet(anno_config.class_combo_style)

        # # 对 coco_classes 列表进行排序
        # coco_classes.sort()

        model = QStandardItemModel()
        for cls in coco_classes:
            item = QStandardItem(cls)
            item.setCheckable(True)
            item.setCheckState(Qt.Unchecked)
            model.appendRow(item)

        proxy_model = QSortFilterProxyModel()
        proxy_model.setSourceModel(model)
        proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.class_combo.setModel(proxy_model)
        self.class_combo.view().pressed.connect(self.handle_item_pressed)  # 连接点击事件处理方法

        left_layout.addWidget(self.class_combo)  # 添加到左侧栏选中保存路径按钮下方

        # 创建一个垂直子布局来包裹任务文件标签和下拉框
        task_file_sub_layout = QVBoxLayout()
        task_file_sub_layout.setSpacing(0)

        # 任务文件文本标签控件
        self.task_file_label = QLabel("任务文件(请选择矩形框颜色，默认白色)")
        self.task_file_label.setStyleSheet(anno_config.task_file_label_style)
        task_file_sub_layout.addWidget(self.task_file_label)

        # # 任务文件下拉框
        # self.task_file_combo = QComboBox()
        # self.task_file_combo.setStyleSheet(anno_config.task_file_combo_style)
        # task_file_sub_layout.addWidget(self.task_file_combo)

        # 将子布局添加到主布局
        left_layout.addLayout(task_file_sub_layout)

        # Adding the table for tag editing
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["序号", "类别", "标签", "颜色", "删除"])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Allow table to expand
        self.table.setMinimumHeight(360)  # Set a reasonable minimum height
        left_layout.addWidget(self.table)

        # Connect resize event to adjust column widths
        left_right_splitter.splitterMoved.connect(self.adjust_table_columns)

        # 待审核按钮
        self.review_btn = QPushButton("待审核")
        self.review_btn.setStyleSheet(anno_config.button_style)
        self.review_btn.clicked.connect(self.show_review_images)
        left_layout.addWidget(self.review_btn)

        # 正常图像按钮
        self.normal_image_btn = QPushButton("正常图像")
        self.normal_image_btn.setStyleSheet(anno_config.button_style)
        self.normal_image_btn.clicked.connect(self.show_normal_images)  # 添加点击事件
        left_layout.addWidget(self.normal_image_btn)

        # 回收站按钮
        self.recycle_btn = QPushButton("异常图像")
        self.recycle_btn.setStyleSheet(anno_config.button_style)
        self.recycle_btn.clicked.connect(self.show_abnormal_images)  # 添加点击事件
        left_layout.addWidget(self.recycle_btn)

        # 添加拉伸项，将下方的日志和进度条布局固定在底部
        left_layout.addStretch(1)

        # 日志标题
        log_title = QLabel("工作日志")
        log_title.setStyleSheet(anno_config.log_title_style)
        left_layout.addWidget(log_title)

        # 日志信息栏和进度条专用子布局（用于管理自适应拉伸）
        log_progress_layout = QVBoxLayout()
        log_progress_layout.setContentsMargins(0, 0, 0, 0)
        log_progress_layout.setSpacing(3)

        # 新增标注日志信息栏，移到左侧菜单栏
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setMinimumHeight(240)
        self.log_text_edit.setStyleSheet(anno_config.log_text_edit_style)

        left_layout.addStretch()  # 添加伸缩项，使日志栏在底部
        left_layout.addWidget(self.log_text_edit)

        # 在日志栏下方添加进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(anno_config.progress_bar_style)
        self.progress_bar.setValue(0)
        # 不设置进度条最小尺寸
        # self.progress_bar.setMinimumSize(*anno_config.progress_bar_min_size)
        left_layout.addWidget(self.progress_bar)

        left_layout.addLayout(log_progress_layout)

        # 右侧主区域（白色）
        right_main = QWidget()
        right_main.setStyleSheet("background-color: white;")
        right_layout = QVBoxLayout(right_main)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setAlignment(Qt.AlignTop)  # 强制布局内控件顶部对齐

        # 将左侧栏和主内容区添加到QSplitter中
        left_right_splitter.addWidget(self.left_sidebar)
        left_right_splitter.addWidget(right_main)

        # 设置初始的大小比例，这里设置为1:3，可根据需求调整
        left_right_splitter.setSizes([int(self.width() * 0.15), int(self.width() * 0.85)])

        # 创建用于主内容区和右侧容器区的QSplitter
        main_right_container_splitter = QSplitter(Qt.Horizontal)
        main_right_container_splitter.addWidget(right_main)

        # 新增右侧容器
        right_container = QWidget()
        right_container.setStyleSheet(anno_config.right_container_style)
        right_container_layout = QVBoxLayout(right_container)
        right_container_layout.setSpacing(5)  # 设置控件之间的间距为5
        right_container_layout.setContentsMargins(5, 5, 5, 5)  # 设置上下左右间距为5

        # 本次总标注框
        total_annotation_label = QLabel("本次消耗矩形框：0")
        total_annotation_label.setObjectName("total_annotation_label")  # 添加对象名
        total_annotation_label.setStyleSheet(anno_config.new_info_box_style)
        # 调整最小高度，根据实际字体大小调整
        total_annotation_label.setMinimumHeight(40)
        total_annotation_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_container_layout.addWidget(total_annotation_label)

        # 修改后的正确代码（删除重复创建）
        annotation_balance_label = QLabel(
            f"矩形框余额：{self.user_info['rectangle_remaining']}"
            if self.user_info and 'rectangle_remaining' in self.user_info
            else "矩形框余额：0"
        )
        annotation_balance_label.setObjectName("annotation_balance_label")  # 设置对象名
        annotation_balance_label.setStyleSheet(anno_config.new_info_box_style)


        annotation_balance_label.setMinimumWidth(150)
        # 调整最小高度，根据实际字体大小调整
        annotation_balance_label.setMinimumHeight(30)
        annotation_balance_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_container_layout.addWidget(annotation_balance_label)

        # 充值按钮
        recharge_button = QPushButton("充值")
        recharge_button.setStyleSheet(anno_config.recharge_exchange_button_style)
        recharge_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        recharge_button.setToolTip("点击进行充值操作")

        def recharge_function():
            # 创建充值对话框
            dialog = RechargeDialog(self.user_info, self)
            # 使用 QueuedConnection 以延时方式调用更新槽函数
            dialog.recharge_success_signal.connect(self.update_user_info_display, Qt.QueuedConnection)
            dialog.show()  # 使用非模态显示

        recharge_button.clicked.connect(recharge_function)
        right_container_layout.addWidget(recharge_button)

        # 兑换按钮
        self.exchange_button = QPushButton("兑换")
        self.exchange_button.setStyleSheet(anno_config.recharge_exchange_button_style)
        self.exchange_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.exchange_button.setToolTip("点击进行兑换操作")
        self.exchange_button.clicked.connect(self.show_exchange_dialog)

        # def show_exchange_dialog(self):
        #     dialog = ExchangeDialog(self.user_info, self)
        #     dialog.exec_()

        def exchange_function():
            print("执行兑换操作")

        self.exchange_button.clicked.connect(exchange_function)
        right_container_layout.addWidget(self.exchange_button)

        # 手动标注按钮
        manual_annotation_button = QPushButton("手动标注")
        manual_annotation_button.setStyleSheet(anno_config.manual_annotation_button_style)
        manual_annotation_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        manual_annotation_button.setToolTip("点击进入手动标注模型")
        manual_annotation_button.clicked.connect(self.show_manual_annotation)

        # 将按钮添加到布局中
        right_container_layout.addWidget(manual_annotation_button)

        # 活动公告栏和友情提示公告板的容器
        activity_and_tips_container = QWidget()
        activity_and_tips_container.setStyleSheet("background-color: #f0f0f0; border:none;")
        activity_and_tips_layout = QVBoxLayout(activity_and_tips_container)
        activity_and_tips_layout.setSpacing(5)  # 设置控件之间的间距为5
        activity_and_tips_layout.setContentsMargins(5, 5, 5, 5)  # 设置上下左右间距为5

        # 活动公告栏容器（占70%高度）
        activity_announcement_container = QWidget()
        activity_announcement_container.setStyleSheet("background-color: #f0f0f0;")  # 设置背景颜色
        activity_announcement_layout = QVBoxLayout(activity_announcement_container)
        activity_announcement_layout.setSpacing(5)  # 设置控件之间的间距为5
        activity_announcement_layout.setContentsMargins(5, 5, 5, 5)  # 设置上下左右间距为5

        # 活动公告栏标题
        activity_announcement_title = QLabel("活动公告栏")
        activity_announcement_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        activity_announcement_layout.addWidget(activity_announcement_title)

        self.activity_announcement_content = QTextEdit()
        self.activity_announcement_content.setReadOnly(True)
        self.activity_announcement_content.setStyleSheet(
            "background-color: #fff; border: 1px solid #ccc; padding: 5px;")
        activity_announcement_layout.addWidget(self.activity_announcement_content)

        # 调用加载公告信息
        self.load_activity_announcements()

        # 将活动公告栏添加到容器布局
        activity_and_tips_layout.addWidget(activity_announcement_container, stretch=5)  # 占70%高度

        # 友情提示公告板容器（占30%高度）
        tips_container = QWidget()
        tips_container.setStyleSheet("background-color: #f0f0f0;")  # 设置背景颜色
        tips_layout = QVBoxLayout(tips_container)
        tips_layout.setSpacing(5)  # 设置控件之间的间距为5
        tips_layout.setContentsMargins(5, 5, 5, 5)  # 设置上下左右间距为5

        # 友情提示公告板标题
        tips_title = QLabel("友情提示")
        tips_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        tips_layout.addWidget(tips_title)

        # 友情提示公告板内容
        tips_content = QTextEdit('')
        tips_content.setReadOnly(True)  # 设置为只读
        tips_content.setStyleSheet("background-color: #fff; border: 1px solid #ccc; padding: 5px;")
        tips_content.setPlainText(
            "由于当前平台规模限制，交易方式暂时只能通过微店购买CDK兑换码进行。\n"
            "我们正在努力升级交易方式，以提供更便捷的购买体验。\n"
            "感谢您的理解与支持，给您带来的不便，敬请谅解！"
        )
        tips_layout.addWidget(tips_content)

        # 将友情提示公告板添加到容器布局
        activity_and_tips_layout.addWidget(tips_container, stretch=5)  # 占30%高度

        # 将活动公告栏和友情提示公告板容器添加到右侧容器布局
        right_container_layout.addWidget(activity_and_tips_container)

        # 将右侧容器添加到主布局
        main_right_container_splitter.addWidget(right_container)

        # 设置主内容区和右侧容器区的初始大小比例，可根据需求调整
        main_right_container_splitter.setSizes([int(self.width() * 0.75), int(self.width() * 0.25)])

        # 创建一个新的QSplitter，将左侧栏 - 主内容区分割器和主内容区 - 右侧容器区分割器添加进去
        overall_splitter = QSplitter(Qt.Horizontal)
        overall_splitter.addWidget(left_right_splitter)
        overall_splitter.addWidget(main_right_container_splitter)

        # 将overall_splitter添加到content_layout中
        content_layout.addWidget(overall_splitter)

        # 底部任务栏（填充整个窗口底部）
        task_bar = QWidget()
        task_bar.setStyleSheet("background-color: white;")
        task_bar.setFixedHeight(anno_config.task_bar_fixed_height)

        task_layout = QHBoxLayout(task_bar)
        task_layout.setContentsMargins(0, 0, 0, 0)
        task_layout.setAlignment(Qt.AlignCenter)

        # 开始标注按钮应用专属样式
        self.start_pause_btn = QPushButton("开始标注")
        self.start_pause_btn.setStyleSheet(anno_config.start_button_style + " QPushButton:focus {outline: none;}")
        self.start_pause_btn.clicked.connect(self.toggle_processing)
        task_layout.addWidget(self.start_pause_btn)

        # 新增退出程序按钮
        self.exit_btn = QPushButton("退出程序")
        self.exit_btn.setStyleSheet(anno_config.exit_button_style + " QPushButton:focus {outline: none;}")
        self.exit_btn.clicked.connect(self.close_app)
        task_layout.addWidget(self.exit_btn)

        # 组装主布局
        main_layout.addWidget(content_widget)
        main_layout.addWidget(task_bar)
        self.setLayout(main_layout)

    def adjust_table_columns(self, pos, index):
        """Adjust table column widths dynamically when splitter is moved."""
        table_width = self.table.viewport().width()  # Get the visible width of the table
        if table_width <= 0:
            return

        # Define proportional widths for each column
        col_widths = {
            0: int(table_width * 0.15),  # 序号 (15%)
            1: int(table_width * 0.35),  # 类别 (35%)
            2: int(table_width * 0.20),  # 标签 (20%)
            3: int(table_width * 0.15),  # 颜色 (15%)
            4: int(table_width * 0.15)  # 删除 (15%)
        }

        # Apply the calculated widths
        for col, width in col_widths.items():
            self.table.setColumnWidth(col, width)

    def show_review_images(self):
        if self.process_thread and self.process_thread.isRunning():
            if not self.process_thread.paused:
                with QMutexLocker(self.process_thread.mutex):
                    self.process_thread.paused = True
                self.start_pause_btn.setText("继续标注")
                self.log_text_edit.append("⏸️ 进入待审核模式，标注已自动暂停")

        if not self.user_info:
            self.log_text_edit.append("用户未登录，无法加载待审核图像")
            return

        local_img_folder = os.path.join(self.temp_dir, "img")
        if not os.path.exists(local_img_folder):
            QMessageBox.information(self, "提示", "目前暂无待审核图像文件，请先进行标注任务")
            self.log_text_edit.append("目前暂无待审核图像文件，请先进行标注任务")
            return

        try:
            # Collect all review image paths into a list
            image_files = [os.path.join(local_img_folder, f) for f in os.listdir(local_img_folder)
                           if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            if not image_files:
                QMessageBox.information(self, "提示", "暂无待审核图像")
                return

            # Create review dialog
            preview_dialog = QDialog(self)
            preview_dialog.setWindowTitle("待审核图像预览")
            preview_dialog.setMinimumSize(800, 600)
            layout = QVBoxLayout(preview_dialog)

            # Initial list view for all images
            image_list_widget = QListWidget()
            image_list_widget.setViewMode(QListWidget.IconMode)
            image_list_widget.setIconSize(QSize(100, 100))
            image_list_widget.setResizeMode(QListWidget.Adjust)
            image_list_widget.setSpacing(10)

            for img_path in image_files:
                pixmap = QPixmap(img_path)
                if not pixmap.isNull():
                    item = QListWidgetItem(os.path.basename(img_path))
                    item.setIcon(QIcon(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
                    item.setData(Qt.UserRole, img_path)
                    image_list_widget.addItem(item)
                else:
                    self.log_text_edit.append(f"无法加载图片: {img_path}")

            layout.addWidget(image_list_widget, stretch=8)

            # Buttons for actions
            button_container = QWidget()
            button_layout = QHBoxLayout(button_container)
            btn_report = QPushButton("反馈异常")
            btn_report.setStyleSheet(anno_config.manual_annotation_button_style)
            btn_confirm = QPushButton("确认无误")
            btn_confirm.setStyleSheet(anno_config.manual_annotation_button_style)
            button_layout.addWidget(btn_report)
            button_layout.addWidget(btn_confirm)
            layout.addWidget(button_container)

            # Smooth-switching dialog
            def show_smooth_switching(start_index):
                smooth_dialog = QDialog(self)
                smooth_dialog.setWindowTitle(f"待审核图像预览 - {os.path.basename(image_files[start_index])}")
                smooth_dialog.setMinimumSize(800, 600)
                smooth_layout = QVBoxLayout(smooth_dialog)

                # Image display area with scroll
                image_widget = QWidget()
                image_layout = QHBoxLayout(image_widget)
                image_layout.setContentsMargins(0, 0, 0, 0)

                # Custom image viewer class for zoom and drag
                class ImageViewer(QLabel):
                    def __init__(self, parent=None):
                        super().__init__(parent)
                        self.scale_factor = 1.0
                        self.setAlignment(Qt.AlignCenter)
                        self.setMouseTracking(True)
                        self.drag_start_pos = None

                    def wheelEvent(self, event):
                        if event.modifiers() & Qt.ControlModifier:
                            delta = event.angleDelta().y()
                            zoom_factor = 1.1 if delta > 0 else 0.9
                            self.scale_factor *= zoom_factor
                            self.update_image()
                            event.accept()
                        else:
                            super().wheelEvent(event)

                    def mousePressEvent(self, event):
                        if event.button() == Qt.RightButton:
                            self.drag_start_pos = event.pos()
                            self.setCursor(Qt.OpenHandCursor)
                            event.accept()

                    def mouseMoveEvent(self, event):
                        if self.drag_start_pos is not None:
                            delta = event.pos() - self.drag_start_pos
                            self.parent().parent().horizontalScrollBar().setValue(
                                self.parent().parent().horizontalScrollBar().value() - delta.x())
                            self.parent().parent().verticalScrollBar().setValue(
                                self.parent().parent().verticalScrollBar().value() - delta.y())
                            self.drag_start_pos = event.pos()
                            event.accept()

                    def mouseReleaseEvent(self, event):
                        if event.button() == Qt.RightButton:
                            self.drag_start_pos = None
                            self.setCursor(Qt.ArrowCursor)
                            event.accept()

                    def update_image(self):
                        if hasattr(self, 'current_pixmap'):
                            scaled_pixmap = self.current_pixmap.scaled(
                                self.current_pixmap.size() * self.scale_factor,
                                Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            self.setPixmap(scaled_pixmap)

                # Scroll area for image
                scroll_area = QScrollArea()
                scroll_area.setWidgetResizable(True)
                self.image_viewer = ImageViewer()
                scroll_area.setWidget(self.image_viewer)
                image_layout.addWidget(scroll_area)

                # Navigation arrows at edges
                prev_button = QPushButton("<")
                prev_button.setFixedSize(40, 40)
                prev_button.setStyleSheet("font-size: 20px;")
                next_button = QPushButton(">")
                next_button.setFixedSize(40, 40)
                next_button.setStyleSheet("font-size: 20px;")
                image_layout.addWidget(prev_button, alignment=Qt.AlignLeft)
                image_layout.addWidget(next_button, alignment=Qt.AlignRight)

                smooth_layout.addWidget(image_widget, stretch=8)

                # Add action buttons in smooth-switching mode
                smooth_button_container = QWidget()
                smooth_button_layout = QHBoxLayout(smooth_button_container)
                smooth_btn_report = QPushButton("反馈异常")
                smooth_btn_report.setFixedWidth(150)
                smooth_btn_report.setStyleSheet(anno_config.exit_button_style)
                smooth_button_layout.addWidget(smooth_btn_report)
                smooth_layout.addWidget(smooth_button_container)

                # Image navigation logic
                self.current_review_index = start_index

                def load_image(index):
                    if 0 <= index < len(image_files):
                        pixmap = QPixmap(image_files[index])
                        if not pixmap.isNull():
                            self.image_viewer.current_pixmap = pixmap
                            self.image_viewer.scale_factor = 1.0
                            self.image_viewer.update_image()
                            smooth_dialog.setWindowTitle(f"待审核图像预览 - {os.path.basename(image_files[index])} "
                                                         f"({index + 1}/{len(image_files)})")
                        else:
                            self.log_text_edit.append(f"无法加载图片: {image_files[index]}")

                def prev_image():
                    self.current_review_index = max(0, self.current_review_index - 1)
                    load_image(self.current_review_index)

                def next_image():
                    self.current_review_index = min(len(image_files) - 1, self.current_review_index + 1)
                    load_image(self.current_review_index)

                def report_abnormal_smooth():
                    self.handle_image_feedback([image_files[self.current_review_index]])
                    # Remove the image from the list and update the list widget
                    img_path = image_files[self.current_review_index]
                    for i in range(image_list_widget.count()):
                        item = image_list_widget.item(i)
                        if item.data(Qt.UserRole) == img_path:
                            image_list_widget.takeItem(i)
                            break
                    image_files.pop(self.current_review_index)
                    if not image_files:
                        smooth_dialog.close()
                        preview_dialog.close()
                    else:
                        self.current_review_index = min(self.current_review_index, len(image_files) - 1)
                        load_image(self.current_review_index)

                prev_button.clicked.connect(prev_image)
                next_button.clicked.connect(next_image)
                smooth_btn_report.clicked.connect(report_abnormal_smooth)

                # Load initial image
                load_image(self.current_review_index)
                smooth_dialog.exec_()

            # Connect list item click to smooth-switching mode
            def on_item_clicked(item):
                img_path = item.data(Qt.UserRole)
                start_index = image_files.index(img_path)
                show_smooth_switching(start_index)

            image_list_widget.itemClicked.connect(on_item_clicked)

            # Action buttons logic
            def report_abnormal():
                selected_items = image_list_widget.selectedItems()
                if not selected_items:
                    QMessageBox.warning(preview_dialog, "提示", "请先选择一张图像")
                    return
                selected_files = [item.data(Qt.UserRole) for item in selected_items]
                self.handle_image_feedback(selected_files)
                for item in selected_items:
                    row = image_list_widget.row(item)
                    image_list_widget.takeItem(row)
                    image_files.remove(item.data(Qt.UserRole))
                if not image_files:
                    preview_dialog.close()

            def confirm_normal():
                if not image_files:
                    QMessageBox.information(preview_dialog, "提示", "暂无剩余图像可确认")
                    return
                self.handle_image_confirm(image_files)
                preview_dialog.close()

            btn_report.clicked.connect(report_abnormal)
            btn_confirm.clicked.connect(confirm_normal)

            preview_dialog.exec_()

        except Exception as e:
            self.log_text_edit.append(f"加载待审核图像时出错: {str(e)}")

    # Helper methods for action buttons
    def handle_image_feedback(self, selected_files):
        """处理异常图片反馈（简化目录结构版本）"""
        try:
            error_log_path = os.path.expanduser("~/annotation_errors.txt")
            total_deduct = 0

            # 确保异常目录存在
            os.makedirs(self.abnormal_dir, exist_ok=True)

            with open(error_log_path, "a", encoding="utf-8") as f:
                for file_path in selected_files:
                    filename = os.path.basename(file_path)
                    f.write(f"{filename}\n")

                    # 在原始输入文件夹中递归搜索匹配文件
                    found = False
                    for root, dirs, files in os.walk(self.input_folder):
                        if filename in files:
                            # 复制原始图片到异常目录（直接根目录）
                            src_img = os.path.join(root, filename)
                            dst_img = os.path.join(self.abnormal_dir, filename)
                            if not os.path.exists(dst_img):  # 避免覆盖已有文件
                                shutil.copy2(src_img, dst_img)
                                self.log_text_edit.append(f"已备份原始文件: {filename}")

                            found = True
                            break

                    if not found:
                        self.log_text_edit.append(f"警告: 未在输入文件夹找到原始文件 {filename}")

                    # 删除临时目录中的文件
                    temp_img_path = os.path.join(self.temp_dir, "img", filename)
                    temp_label_path = os.path.join(self.temp_dir, "label",
                                                   f"{os.path.splitext(filename)[0]}.txt")

                    if os.path.exists(temp_img_path):
                        os.remove(temp_img_path)
                        self.log_text_edit.append(f"已删除临时图片: {filename}")

                    if os.path.exists(temp_label_path):
                        os.remove(temp_label_path)
                        self.log_text_edit.append(f"已删除临时标签: {os.path.basename(temp_label_path)}")

                    # 从记录中获取框数并扣除
                    if filename in self.annotation_records:
                        boxes_to_deduct = self.annotation_records[filename]
                        total_deduct += boxes_to_deduct
                        del self.annotation_records[filename]

            # 更新总消耗框数
            if total_deduct > 0:
                self.total_boxes = max(0, self.total_boxes - total_deduct)
                self.findChild(QLabel, "total_annotation_label").setText(f"本次消耗矩形框：{self.total_boxes}")
                self.log_text_edit.append(f"已扣除异常图片标注数：{total_deduct}")

            self.log_text_edit.append(f"已标记 {len(selected_files)} 张异常图片，减少 {total_deduct} 个矩形框消耗")
            self.log_text_edit.append(f"原始文件已备份至异常目录: {self.abnormal_dir}")

        except Exception as e:
            self.log_text_edit.append(f"异常处理失败: {str(e)}")
            import traceback
            traceback.print_exc()

    def handle_image_confirm(self, selected_files):
        try:
            normal_img = os.path.join(self.normal_dir, "img")
            normal_label = os.path.join(self.normal_dir, "label")
            os.makedirs(normal_img, exist_ok=True)
            os.makedirs(normal_label, exist_ok=True)
            for file_path in selected_files:
                filename = os.path.basename(file_path)
                src_img = os.path.join(self.temp_dir, "img", filename)
                src_label = os.path.join(self.temp_dir, "label", f"{os.path.splitext(filename)[0]}.txt")
                dst_img = os.path.join(normal_img, filename)
                dst_label = os.path.join(normal_label, f"{os.path.splitext(filename)[0]}.txt")
                if os.path.exists(src_img):
                    shutil.move(src_img, dst_img)
                if os.path.exists(src_label):
                    shutil.move(src_label, dst_label)
            self.log_text_edit.append(f"确认 {len(selected_files)} 张图片无误，已转移")
        except Exception as e:
            self.log_text_edit.append(f"转移错误: {str(e)}")

    # 浏览异常图片
    def show_abnormal_images(self):
        if not self.abnormal_dir or not os.path.exists(self.abnormal_dir):
            QMessageBox.information(self, "提示", "目前暂无异常图像文件，请先进行标注任务")
            return

        try:
            # 直接读取根目录下的文件
            image_files = [f for f in os.listdir(self.abnormal_dir)
                           if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

            if not image_files:
                QMessageBox.information(self, "提示", "当前没有异常图像记录")
                return

            preview_dialog = QDialog(self)
            preview_dialog.setWindowTitle(f"异常图像预览 - 共{len(image_files)}张")
            preview_dialog.setMinimumSize(800, 600)

            # 主布局
            main_layout = QVBoxLayout(preview_dialog)

            # 使用QListWidget显示图片
            list_widget = QListWidget()
            list_widget.setViewMode(QListWidget.IconMode)
            list_widget.setIconSize(QSize(120, 120))
            list_widget.setResizeMode(QListWidget.Adjust)
            list_widget.setSpacing(10)
            main_layout.addWidget(list_widget)

            # 底部状态栏
            status_bar = QWidget()
            status_bar.setStyleSheet("background-color: #f0f0f0; padding: 5px;")
            status_layout = QHBoxLayout(status_bar)
            status_layout.setContentsMargins(10, 5, 10, 5)

            # 文件夹路径标签
            path_label = QLabel(f"异常图像文件夹: {self.abnormal_dir}")
            path_label.setStyleSheet("color: #666; font-size: 12px;")
            path_label.setAlignment(Qt.AlignCenter)

            # 将标签添加到布局并居中
            status_layout.addWidget(path_label)
            main_layout.addWidget(status_bar)

            # 加载图片
            for image_file in image_files:
                img_path = os.path.join(self.abnormal_dir, image_file)
                pixmap = QPixmap(img_path)
                if not pixmap.isNull():
                    item = QListWidgetItem(QIcon(pixmap.scaled(120, 120, Qt.KeepAspectRatio)), image_file)
                    item.setData(Qt.UserRole, img_path)
                    list_widget.addItem(item)

            def on_item_double_clicked(item):
                img_path = item.data(Qt.UserRole)
                pixmap = QPixmap(img_path)
                if not pixmap.isNull():
                    image_dialog = QDialog(self)
                    image_dialog.setWindowTitle(os.path.basename(img_path))
                    image_dialog.setFixedSize(800, 600)

                    # 添加滚动区域
                    scroll = QScrollArea()
                    scroll.setWidgetResizable(True)

                    # 显示完整尺寸图片
                    label = QLabel()
                    label.setPixmap(pixmap.scaled(
                        scroll.size(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    ))
                    label.setAlignment(Qt.AlignCenter)

                    scroll.setWidget(label)
                    layout = QVBoxLayout(image_dialog)
                    layout.addWidget(scroll)
                    image_dialog.exec_()
                else:
                    QMessageBox.warning(self, "错误", "无法加载该图片")

            list_widget.itemDoubleClicked.connect(on_item_double_clicked)
            preview_dialog.exec_()

        except Exception as e:
            self.log_text_edit.append(f"加载异常图像时出错: {str(e)}")

    # 浏览正常图片
    def show_normal_images(self):
        if not self.normal_dir or not os.path.exists(self.normal_dir):
            QMessageBox.information(self, "提示", "目前暂无正常图像文件，请先进行标注任务")
            self.log_text_edit.append("目前暂无正常图像文件，请先进行标注任务")
            return
        local_img_folder = os.path.join(self.normal_dir, "img")
        try:
            image_files = [f for f in os.listdir(local_img_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            if not image_files:
                QMessageBox.information(self, "提示", "尚未有任何通过审核的正常图像")
                return

            preview_dialog = QDialog(self)
            preview_dialog.setWindowTitle("正常图像存档")
            preview_dialog.setMinimumSize(800, 600)
            main_layout = QVBoxLayout(preview_dialog)

            button_container = QWidget()
            button_layout = QHBoxLayout(button_container)
            btn_download = QPushButton("下载全部")
            btn_download.setStyleSheet("""
                QPushButton {
                    background-color: rgba(0, 180, 247, 0.8);
                    color: white;
                    padding: 8px;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background-color: rgba(0, 180, 247, 0.5);
                }
            """)
            btn_download.clicked.connect(
                lambda: self.download_normal_images(list_widget)
            )
            button_layout.addWidget(btn_download)
            main_layout.addWidget(button_container)

            list_widget = QListWidget()
            list_widget.setViewMode(QListWidget.IconMode)
            list_widget.setIconSize(QSize(120, 120))
            list_widget.setResizeMode(QListWidget.Adjust)
            list_widget.setSpacing(10)
            main_layout.addWidget(list_widget)

            for image_file in image_files:
                local_path = os.path.join(local_img_folder, image_file)
                pixmap = QPixmap(local_path)
                if pixmap.load(local_path):
                    item = QListWidgetItem(QIcon(pixmap.scaled(120, 120, Qt.KeepAspectRatio)), image_file)
                    item.setData(Qt.UserRole, local_path)
                    list_widget.addItem(item)
                else:
                    self.log_text_edit.append(f"无法加载缩略图: {image_file}")

            def on_item_double_clicked(item):
                local_path = item.data(Qt.UserRole)
                pixmap = QPixmap(local_path)
                if pixmap.load(local_path):
                    image_dialog = QDialog(self)
                    image_dialog.setWindowTitle(item.text())
                    image_dialog.setFixedSize(800, 600)
                    layout = QVBoxLayout(image_dialog)
                    label = QLabel()
                    label.setPixmap(pixmap.scaled(800, 600, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    layout.addWidget(label)
                    image_dialog.exec_()
                else:
                    QMessageBox.warning(self, "错误", "无法加载该图片")

            list_widget.itemDoubleClicked.connect(on_item_double_clicked)
            preview_dialog.exec_()

        except Exception as e:
            self.log_text_edit.append(f"加载正常图像时出错: {str(e)}")

            def on_item_double_clicked(item):
                local_path = item.data(Qt.UserRole)
                pixmap = QPixmap(local_path)
                if pixmap.load(local_path):
                    image_dialog = QDialog(self)
                    image_dialog.setWindowTitle(item.text())
                    image_dialog.setFixedSize(800, 600)
                    layout = QVBoxLayout(image_dialog)
                    label = QLabel()
                    label.setPixmap(pixmap.scaled(800, 600, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    layout.addWidget(label)
                    image_dialog.exec_()
                else:
                    QMessageBox.warning(self, "错误", "无法加载该图片")

            list_widget.itemDoubleClicked.connect(on_item_double_clicked)
            preview_dialog.exec_()

        except Exception as e:
            self.log_text_edit.append(f"加载正常图像时出错: {str(e)}")

    # 在 download_normal_images 方法中添加删除文件夹的逻辑
    def download_normal_images(self, list_widget):
        try:
            # ============ 1. Final Settlement: Deduct the total_boxes from the user's balance ============
            account = self.user_info.get('account', 'default_account')
            used_count = self.total_boxes  # Final number of boxes after refunds

            # Establish database connection
            conn = pymysql.connect(
                host=db_config.HOST,
                port=db_config.PORT,
                user=db_config.USER,
                password=db_config.PASSWORD,
                database=db_config.DATABASE,
                charset='utf8mb4'
            )
            cursor = conn.cursor()

            # Check if the user has enough balance
            select_balance_sql = "SELECT rectangle_remaining FROM user_info WHERE account = %s"
            cursor.execute(select_balance_sql, (account,))
            row = cursor.fetchone()
            current_balance = row[0] if row else 0

            if not used_count:
                cursor.close()
                conn.close()
                QMessageBox.warning(self, "错误",
                                    f"本次标注消耗为零！\n请按正常流程退出程序清理缓存重新标注。")
                return

            if used_count > current_balance:
                cursor.close()
                conn.close()
                QMessageBox.warning(self, "余额不足",
                                    f"当前余额({current_balance})不足以支付本次标注消耗({used_count})！\n请先充值或兑换矩形框。")
                return

            # Deduct the final total_boxes from the user's balance
            update_balance_sql = """
                UPDATE user_info 
                SET rectangle_remaining = rectangle_remaining - %s 
                WHERE account = %s
            """
            cursor.execute(update_balance_sql, (used_count, account))
            conn.commit()

            # Insert annotation history
            insert_history_sql = """
                INSERT INTO annotation_history (account, annotation_type, used_count)
                VALUES (%s, %s, %s)
            """
            cursor.execute(insert_history_sql, (account, "rectangle", used_count))
            conn.commit()

            # Update the user's balance display
            cursor.execute(select_balance_sql, (account,))
            row = cursor.fetchone()
            new_balance = row[0] if row else 0
            self.user_info['rectangle_remaining'] = new_balance
            balance_label = self.findChild(QLabel, "annotation_balance_label")
            if balance_label:
                balance_label.setText(f"矩形框余额：{new_balance}")

            # Reset the total_boxes counter
            self.total_boxes = 0
            total_label = self.findChild(QLabel, "total_annotation_label")
            if total_label:
                total_label.setText("消耗矩形框：0")

            cursor.close()
            conn.close()

            # ============ 2. Download the Images ============
            if not self.result_folder:
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
                self.result_folder = os.path.join(desktop_path, "NapLabel_Downloads")
                os.makedirs(self.result_folder, exist_ok=True)
                self.log_text_edit.append(f"未指定保存路径，默认保存到: {self.result_folder}")

            os.makedirs(self.result_folder, exist_ok=True)

            img_src = os.path.join(self.normal_dir, "img")
            img_dst = os.path.join(self.result_folder, "img")
            os.makedirs(img_dst, exist_ok=True)

            label_src = os.path.join(self.normal_dir, "label")
            label_dst = os.path.join(self.result_folder, "label")
            os.makedirs(label_dst, exist_ok=True)

            if not os.path.exists(img_src) or not os.path.exists(label_src):
                QMessageBox.warning(self, "警告", "没有可下载的正常图像文件")
                return

            img_files = [f for f in os.listdir(img_src) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            label_files = [f for f in os.listdir(label_src) if f.lower().endswith('.txt')]

            if not img_files and not label_files:
                QMessageBox.warning(self, "警告", "没有可下载的文件")
                return

            copied_files = 0
            for img_file in img_files:
                src = os.path.join(img_src, img_file)
                dst = os.path.join(img_dst, img_file)
                shutil.copy2(src, dst)
                copied_files += 1

            for label_file in label_files:
                src = os.path.join(label_src, label_file)
                dst = os.path.join(label_dst, label_file)
                shutil.copy2(src, dst)
                copied_files += 1

            if list_widget:
                list_widget.clear()

            # Delete local folders after download
            self.delete_local_folders()

            QMessageBox.information(
                self,
                "成功",
                f"已成功下载 {copied_files} 个文件到:\n{self.result_folder}\n"
                f"本次任务共消耗 {used_count} 个矩形框"
            )
            self.log_text_edit.append(f"已下载 {copied_files} 个文件到: {self.result_folder}")
            self.log_text_edit.append(f"本次任务共消耗 {used_count} 个矩形框")

        except Exception as e:
            QMessageBox.critical(
                self,
                "错误",
                f"下载失败: {str(e)}\n请检查文件权限或磁盘空间"
            )
            self.log_text_edit.append(f"下载错误: {str(e)}")
            import traceback
            traceback.print_exc()

    # 新增删除本地文件夹的方法
    def delete_local_folders(self):
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                # self.log_text_edit.append(f"已删除本地临时目录")
            if os.path.exists(self.normal_dir):
                shutil.rmtree(self.normal_dir)
                # self.log_text_edit.append(f"已删除本地正常图像目录")
        except Exception as e:
            self.log_text_edit.append(f"删除本地文件夹时出错: {str(e)}")

    # 修改检查文件夹是否存在的方法
    def check_remote_directories_empty(self):
        # 如果文件夹不存在也视为空
        temp_img = os.path.join(self.temp_dir, "img")
        temp_label = os.path.join(self.temp_dir, "label")
        normal_img = os.path.join(self.normal_dir, "img")
        normal_label = os.path.join(self.normal_dir, "label")

        dirs_to_check = [temp_img, temp_label, normal_img, normal_label]

        for path in dirs_to_check:
            if os.path.exists(path) and len(os.listdir(path)) > 0:
                return False
        return True

    def update_total_boxes(self, count):
        """更新总框数并实时检查余额"""
        try:
            # 更新总框数
            self.total_boxes += int(count)

            # 更新UI显示
            total_label = self.findChild(QLabel, "total_annotation_label")
            if total_label:
                total_label.setText(f"本次消耗矩形框：{self.total_boxes}")

            # 更新数据库中的余额显示
            balance_label = self.findChild(QLabel, "annotation_balance_label")
            if balance_label:
                current_balance = self.user_info.get('rectangle_remaining', 0)
                balance_label.setText(f"矩形框余额：{current_balance}")

            # 实时检查余额
            current_balance = self.user_info.get('rectangle_remaining', 0)
            if self.total_boxes >= current_balance:
                if self.process_thread and self.process_thread.isRunning() and not self.process_thread.paused:
                    # 暂停标注线程
                    with QMutexLocker(self.process_thread.mutex):
                        self.process_thread.paused = True

                    # 更新UI状态
                    self.start_pause_btn.setText("继续标注")
                    self.log_text_edit.append("⚠️ 标注余额不足，处理已暂停！")

                    # 显示警告对话框
                    QMessageBox.warning(
                        self,
                        "余额不足",
                        f"当前标注数({self.total_boxes})已超过余额({current_balance})!\n"
                        "请先兑换足够的标注余额后再继续标注。"
                    )
        except Exception as e:
            self.log_text_edit.append(f"更新总框数时出错: {str(e)}")

    def check_balance(self):
        """检查标注余额是否足够"""
        current_balance = self.user_info.get('rectangle_remaining', 0)
        return current_balance >= self.total_boxes

    def show_exchange_dialog(self):
        dialog = ExchangeDialog(self.user_info, self)
        dialog.exec_()

    @pyqtSlot(int, int)  # 声明为Qt槽函数
    def update_ui_after_exchange(self, new_points, new_balance):
        try:
            # 更新顶部积分显示
            self.points_label.setText(f"当前剩余积分：{new_points}")

            # 更新标注余额显示
            balance_label = self.findChild(QLabel, "annotation_balance_label")
            self.user_info_popup = None  # 强制下次重新创建
            if balance_label:
                balance_label.setText(f"标注余额：{new_balance}")

            # 更新本地用户信息
            self.user_info['current_points'] = new_points
            self.user_info['rectangle_remaining'] = new_balance
            self.user_info['rectangle_remaining'] = new_balance

            # 兑换后检查余额是否足够继续
            if self.check_balance() and self.process_thread and self.process_thread.paused:
                self.log_text_edit.append("余额已更新，可以继续标注")
        except Exception as e:
            print(f"UI更新失败: {str(e)}")

    # 进入手动标注模式
    def show_manual_annotation(self):
        """进入手动标注模式"""
        try:
            # 检查并处理已有窗口
            if hasattr(self, 'manual_annotation_window') and self.manual_annotation_window:
                if self.manual_annotation_window.isVisible():
                    self.manual_annotation_window.activateWindow()
                    self.manual_annotation_window.raise_()
                    return
                else:
                    self.manual_annotation_window.show()
                    return

            # 创建新的手动标注窗口并设置父窗口
            self.manual_annotation_window = AnnotationTool(self)  # 关键修改：设置父窗口

            # 设置窗口属性
            self.manual_annotation_window.setAttribute(Qt.WA_DeleteOnClose)

            # 连接窗口关闭信号
            self.manual_annotation_window.destroyed.connect(
                lambda: setattr(self, 'manual_annotation_window', None)
            )

            # 获取自动标注表格内容
            auto_content = self.get_annotation_data()

            # 直接传递数据到手动标注窗口
            if auto_content:
                # 确保窗口初始化完成后再加载数据
                def load_content():
                    try:
                        # 获取表格数据并传递给手动标注窗口
                        table_data = []
                        for row in range(self.table.rowCount()):
                            class_name = self.table.item(row, 0).text()
                            label = self.table.item(row, 1).text()
                            color_button = self.table.cellWidget(row, 2)
                            color = color_button.palette().button().color()
                            table_data.append({
                                'class': class_name,
                                'label': label,
                                'color': color
                            })
                        self.manual_annotation_window.load_auto_content(table_data)
                    except Exception as e:
                        # self.log_text_edit.append(f"加载自动标注内容失败: {str(e)}")
                        pass

                # 使用单次定时器确保窗口初始化完成
                QTimer.singleShot(100, load_content)

            self.manual_annotation_window.show()

        except Exception as e:
            error_msg = f"进入手动标注模式时出错: {str(e)}"
            self.log_text_edit.append(error_msg)
            QMessageBox.critical(
                self,
                "错误",
                f"无法启动手动标注工具:\n{str(e)}"
            )
            if hasattr(self, 'manual_annotation_window'):
                pass

    def open_manual_annotation(self):
        print(f"自动标注页面中的 AutoAnnotationSystem 实例地址: {id(self)}")
        manual_annotation_window = AnnotationTool(self)
        manual_annotation_window.show()

    def resizeEvent(self, event):
        # 计算窗口宽度的 36% 作为左侧栏的最大宽度
        max_left_sidebar_width = int(self.width() * 0.36)
        # 设置左侧栏的最大宽度
        self.left_sidebar.setMaximumWidth(max_left_sidebar_width)
        # 获取左侧栏所在的布局
        left_sidebar_layout = self.left_sidebar.parent().layout()
        if left_sidebar_layout:
            # 强制更新布局
            left_sidebar_layout.update()
        # 调用父类的 resizeEvent 方法，确保其他默认行为正常
        super().resizeEvent(event)

    def start_manual_annotation(self):
        if not hasattr(self, 'manual_annotation_window'):
            try:
                self.manual_annotation_window = AnnotationTool()
                self.manual_annotation_window.show()
            except ImportError:
                print("无法导入 Manual_annotation 相关代码，请检查路径和类名。")
            except Exception as e:
                print(f"进入手动标注模式时出错: {e}")
        else:
            self.manual_annotation_window.show()

    ###改4.2：
    def center(self):
        # qr = self.frameGeometry()
        # cp = QApplication.desktop().screenGeometry().center()
        # qr.moveCenter(cp)
        # self.move(qr.topLeft())
        # 使用 QDesktopWidget 获取屏幕中心点
        screen_rect = QDesktopWidget().availableGeometry()
        window_rect  = self.frameGeometry()
        window_rect.moveCenter(screen_rect.center())
        self.move(window_rect.topLeft())
    ######

    def close_app(self):
        # 改为调用 close() 以触发 closeEvent
        self.close()  # 这将自动触发 closeEvent 中的逻辑

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, '退出确认',
            "退出程序将清除所有标注文件及日志，确定要退出吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.hide()
            self.cleanup_resources()  # 同步执行清理
            QApplication.quit()
            event.accept()
        else:
            event.ignore()

    # 清除资源
    def cleanup_resources(self):
        self.log_text_edit.append("进入 cleanup_resources")
        try:
            if self.process_thread and self.process_thread.isRunning():
                self.process_thread.requestInterruption()
                self.process_thread.wait(2000)  # 等待线程结束，最多 2 秒
                self.log_text_edit.append("线程已停止")

            if self.user_info:
                self.log_text_edit.append(f"用户存在: {self.user_info.get('account', '未知')}")
                # 删除临时文件夹和正常图像文件夹
                if os.path.exists(self.temp_dir):
                    self.log_text_edit.append(f"准备删除: {self.temp_dir}")
                    import shutil
                    shutil.rmtree(self.temp_dir)
                    # self.log_text_edit.append(f"已删除本地临时目录: {self.temp_dir}")
                if os.path.exists(self.normal_dir):
                    self.log_text_edit.append(f"准备删除: {self.normal_dir}")
                    import shutil
                    shutil.rmtree(self.normal_dir)
                    # self.log_text_edit.append(f"已删除本地正常图像目录: {self.normal_dir}")
            else:
                self.log_text_edit.append("无用户信息，跳过删除")

            error_log = os.path.expanduser("~/annotation_errors.txt")
            if os.path.exists(error_log):
                os.remove(error_log)
                self.log_text_edit.append("已删除异常日志文件")
        except Exception as e:
            self.log_text_edit.append(f"清理资源失败: {str(e)}")


    # 退出程序
    def closeEvent(self, event):
        self.log_text_edit.append("退出程序将清除所有标注文件及日志，请确认已标注图片已成功下载")
        reply = QMessageBox.question(
            self, '退出确认',
            "退出程序将清除所有标注文件及日志，请确认已标注图片已成功下载，确定要退出吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.log_text_edit.append("用户选择 Yes")
            self.hide()
            self.cleanup_resources()
            event.accept()
            QApplication.quit()
        else:
            self.log_text_edit.append("用户选择 No")
            event.ignore()

    # 上传标注图片
    def select_input_folder(self):
        if not self.check_remote_directories_empty():
            QMessageBox.warning(
                self, "存在未完成任务",
                "检测到用户存在未清理的标注文件！\n"
                "请先通过以下方式清理：\n"
                "1. 完成当前标注任务并下载结果\n"
                "2. 退出程序自动清理临时文件"
            )
            return

        if self.total_boxes > 0:
            QMessageBox.warning(
                self, "操作禁止",
                "当前存在未完成的标注任务！\n"
                "请完成或重置当前标注任务后再切换文件夹。"
            )
            return

        folder = QFileDialog.getExistingDirectory(self, "选择输入图片文件夹")
        if folder:
            # 计算选中文件夹内所有图片的总大小（单位：MB）
            total_size_bytes = 0
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                        file_path = os.path.join(root, file)
                        total_size_bytes += os.path.getsize(file_path)
            total_size_mb = total_size_bytes / (1024 * 1024)

            # 根据用户VIP等级设置允许上传的文件大小限制（单位：MB）
            vip_limits = {
                1: 100,
                2: 300,
                3: 400,
                4: 500,
                5: 800
            }
            vip_level = int(self.user_info.get('vip', 1))
            allowed_mb = vip_limits.get(vip_level, 100)

            if total_size_mb > allowed_mb:
                QMessageBox.warning(
                    self, "上传限制",
                    f"您目前的VIP等级为VIP{vip_level}，最多可上传{allowed_mb}MB的图片，请重新上传。"
                )
                return
            else:
                # 上传成功后，在日志中输出提示信息
                self.log_text_edit.append(
                    f"您目前的等级为VIP{vip_level}，最多可上传{allowed_mb}MB的图片，"
                    f"您目前已上传图片为{total_size_mb:.2f}MB，感谢您的使用。"
                )
            # +++ 重置标注相关状态 +++
            self.input_folder = folder
            self.total_boxes = 0  # 重置标注计数器
            self.findChild(QLabel, "total_annotation_label").setText("本次总标注：0")  # 更新显示
            self.progress_bar.setValue(0)  # 重置进度条
            self.is_process_complete = False

            self.log_text_edit.append(f"已选择输入图片文件夹: {folder}")
            self.log_text_edit.append("⚠️ 注意：切换文件夹已重置标注计数")

    # 选择标注类别 revise3
    def handle_item_pressed(self, index):
        try:
            integer_index = self.class_combo.model().mapToSource(index).row()
            class_name = self.class_combo.itemText(integer_index)
            current_state = self.class_combo.itemData(integer_index, Qt.CheckStateRole)
            new_state = Qt.Checked if current_state == Qt.Unchecked else Qt.Unchecked
            self.class_combo.setItemData(integer_index, new_state, Qt.CheckStateRole)

            if new_state == Qt.Checked:
                row = self.table.rowCount()
                self.table.insertRow(row)
                index_in_coco = coco_classes.index(class_name)
                self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))  # 标签序号
                self.table.setItem(row, 1, QTableWidgetItem(class_name))  # 类别
                self.table.setItem(row, 2, QTableWidgetItem(str(index_in_coco)))  # 标签
                color_button = QPushButton()
                color_button.setFixedSize(30, 30)
                default_color = QColor(255, 255, 255)
                # 添加居中样式
                color_button.setStyleSheet(
                    f"background-color: {default_color.name()}; border-radius:5px; margin-left: auto; margin-right: auto;"
                )
                color_button.clicked.connect(lambda: self.change_color(row, class_name))
                self.table.setCellWidget(row, 3, color_button)  # 颜色
                delete_button = QPushButton("X")
                delete_button.setFixedSize(20, 20)
                delete_button.setStyleSheet(
                    "color: #ff4444; background-color: transparent; border: none; font-size: 16px;")
                delete_button.clicked.connect(lambda: self.delete_row(row))
                self.table.setCellWidget(row, 4, delete_button)  # 删除标签
            else:
                for row in range(self.table.rowCount()):
                    if self.table.item(row, 1).text() == class_name:
                        self.table.removeRow(row)
                        self.rebind_delete_buttons()  # 重绑定删除按钮
                        break
        except Exception as e:
            self.log_text_edit.append(f"处理类别选择时出错: {str(e)}")

    def change_color(self, row, class_name):
        color = QColorDialog.getColor()
        if color.isValid():
            color_button = self.table.cellWidget(row, 3)
            color_button.setStyleSheet(
                f"background-color: {color.name()}; border-radius:5px; margin-left: auto; margin-right: auto;"
            )

    def delete_row(self, row):
        if 0 <= row < self.table.rowCount():
            class_name = self.table.item(row, 1).text()
            self.table.removeRow(row)
            self.rebind_delete_buttons()
            self.log_text_edit.append(f"已删除类别: {class_name}")

    def rebind_delete_buttons(self):
        for row in range(self.table.rowCount()):
            delete_button = self.table.cellWidget(row, 4)
            if delete_button:
                delete_button.clicked.disconnect()
                delete_button.clicked.connect(lambda r=row: self.delete_row(r))

    #  获取自动标注页面表格的内容 revise5
    def get_annotation_data(self):
        """获取当前自动标注表格数据"""
        annotation_data = []
        for row in range(self.table.rowCount()):
            index_item = self.table.item(row, 0)  # 标签序号
            class_item = self.table.item(row, 1)  # 类别
            label_item = self.table.item(row, 2)  # 标签
            color_button = self.table.cellWidget(row, 3)  # 颜色
            if index_item and class_item and label_item and color_button:
                color = color_button.palette().button().color()
                annotation_data.append({
                    'index': index_item.text(),
                    'class': class_item.text(),
                    'label': label_item.text(),
                    'color': color
                })
        return annotation_data


    def update_selected_classes(self):
        self.selected_classes = []
        model = self.class_combo.model().sourceModel()
        for i in range(model.rowCount()):
            item = model.item(i)
            if item.checkState() == Qt.Checked:
                self.selected_classes.append(item.text())

    def update_task_file_combo(self):
        self.task_file_combo.clear()
        for cls in self.selected_classes:
            self.task_file_combo.addItem(cls)
        if not self.selected_classes:
            self.task_file_combo.setCurrentText("")  # 没有选中类型时清空当前文本，显示占位文本


    def upload_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择上传的结果文件夹")
        if folder:
            self.result_folder = folder
            self.log_text_edit.append(f"已选择结果保存文件夹: {folder}")
            self.log_text_edit.append(f"进行标注任务前， 请先选择标注类别，并在任务文件栏内选择标注框的颜色")
            self.is_process_complete = False  # 重置标注完成标志
            self.abnormal_dir = os.path.join(folder, "abnormal_images")  # 直接使用根目录
            os.makedirs(self.abnormal_dir, exist_ok=True)  # 只创建一级目录
            self.log_text_edit.append(f"异常文件将保存在{self.result_folder}abnormal_images下")

    def toggle_processing(self):
        try:
            # ==================== 状态检查阶段 ====================
            # 处理已完成状态
            if self.is_process_complete:
                QMessageBox.warning(
                    self, "提示",
                    "标注任务已经完成！\n若要重新开始，请重新选择输入文件夹和标注类型。"
                )
                self.start_pause_btn.setText("开始标注")
                self.process_thread = None  # 清除旧线程引用
                return

            # ==================== 线程控制逻辑 ====================
            # 已有线程运行时的控制
            if self.process_thread and self.process_thread.isRunning():
                if self.process_thread.paused:
                    # --- 严格余额检查 ---
                    current_balance = self.user_info.get('rectangle_remaining', 0)
                    if current_balance <= self.total_boxes:
                        QMessageBox.warning(
                            self, "余额不足",
                            f"当前余额({current_balance}) ≤ 总标注数({self.total_boxes})!\n"
                            "请兑换足够额度后再继续标注！"
                        )
                        return  # 阻断恢复操作

                    # --- 安全恢复线程 ---
                    with QMutexLocker(self.process_thread.mutex):
                        self.process_thread.paused = False
                        self.process_thread.wait_condition.wakeOne()
                        self.process_thread.annotation_record_signal.connect(self.update_annotation_records)

                    # 更新UI状态
                    self.start_pause_btn.setText("暂停标注")
                    self.log_text_edit.append("▶️ 继续标注任务")
                    self.log_text_edit.append(f"当前余额：{current_balance} | 已标注：{self.total_boxes}")

                else:  # 暂停运行中的线程
                    with QMutexLocker(self.process_thread.mutex):
                        self.process_thread.paused = True

                    self.start_pause_btn.setText("继续标注")
                    self.log_text_edit.append("⏸️ 标注任务已暂停")

            else:  # 创建新线程
                try:
                    # --- 参数完整性验证 ---
                    account = self.user_info.get('account', 'default_account')
                    account_dir = f"{account}_temp"
                    validation_errors = []

                    # 确保更新了选中的类别
                    self.update_selected_classes()  # 新增：更新选中的类别列表

                    if not self.input_folder:
                        validation_errors.append("未选择输入文件夹")
                    if not os.path.exists(self.input_folder):
                        validation_errors.append(f"路径不存在: {self.input_folder}")
                    if self.result_folder == f"{ssh_config.BASE_PATH}/account_temp/{account_dir}":
                        validation_errors.append("未选择保存文件夹")
                    if not os.path.exists(self.result_folder):
                        validation_errors.append(f"路径不存在: {self.input_folder}")
                    if not self.selected_classes:  # 检查更新后的类别列表
                        validation_errors.append("未选择标注类别")
                    if validation_errors:
                        raise ValueError(" | ".join(validation_errors))

                    # --- 状态重置 ---
                    self.is_process_complete = False
                    self.total_boxes = 0
                    self.findChild(QLabel, "total_annotation_label").setText("本次总标注：0")
                    self.progress_bar.setValue(0)

                    # 获取用户设置的颜色映射
                    class_colors = self.get_class_colors_from_table()  # 新增：获取颜色设置

                    # --- 创建新线程 ---
                    self.log_text_edit.append("🚀 正在初始化标注引擎...")

                    # 确保传递 total_boxes 初始值
                    self.process_thread = ImageProcessingThread(
                        input_folder=self.input_folder,
                        annotation_classes=self.selected_classes,
                        user_info=self.user_info,
                        result_folder=self.result_folder,
                        initial_total_boxes=self.total_boxes  # 新增：传递当前总框数
                    )

                    # 设置颜色映射
                    self.process_thread.class_colors = class_colors  # 新增：传递颜色设置

                    # --- 信号连接 ---
                    # 确保这些连接在启动线程前完成
                    self.process_thread.annotation_record_signal.connect(
                        lambda img, count: self.update_annotation_records(img, count)
                    )
                    self.process_thread.total_boxes_signal.connect(
                        lambda count: self.update_total_boxes(count)
                    )
                    self.process_thread.progress.connect(self.progress_bar.setValue)
                    self.process_thread.log_message.connect(self.append_log)
                    self.process_thread.result_ready.connect(self.finish_processing)
                    self.process_thread.pause_signal.connect(
                        lambda: self.start_pause_btn.setText("继续标注")
                    )

                    # --- 启动线程 ---
                    self.process_thread.start()
                    self.start_pause_btn.setText("暂停标注")
                    self.log_text_edit.append("✅ 标注任务已启动")

                    # 显示当前余额（确保从数据库获取最新值）
                    current_balance = self.user_info.get('rectangle_remaining', 0)
                    self.log_text_edit.append(f"初始余额：{current_balance}")

                except ValueError as ve:
                    # 专门处理验证错误
                    self.log_text_edit.append(f"❌ 参数验证失败: {str(ve)}")
                    QMessageBox.warning(
                        self, "参数错误",
                        f"无法启动标注线程：\n{str(ve)}\n请检查输入参数"
                    )
                    self.process_thread = None
                    self.start_pause_btn.setText("开始标注")

                except Exception as e:
                    # --- 错误处理 ---
                    import traceback
                    error_msg = f"❌ 初始化失败: {str(e)}\n{traceback.format_exc()}"
                    self.log_text_edit.append(error_msg)
                    QMessageBox.critical(
                        self, "致命错误",
                        f"无法启动标注线程：\n{str(e)}\n请检查输入参数后重试"
                    )
                    self.process_thread = None
                    self.start_pause_btn.setText("开始标注")

        except Exception as e:
            # --- 全局异常捕获 ---
            import traceback
            error_msg = f"⚠️ 未处理异常: {traceback.format_exc()}"
            self.log_text_edit.append(error_msg)
            QMessageBox.critical(
                self, "系统错误",
                f"发生未预期的错误：\n{str(e)}\n建议重启应用程序"
            )

    # 新增方法：从表格获取颜色映射
    def get_class_colors_from_table(self):
        """从表格中获取类别颜色映射"""
        class_colors = {}
        for row in range(self.table.rowCount()):
            class_item = self.table.item(row, 1)  # 类别在第1列（索引从0开始）
            color_button = self.table.cellWidget(row, 3)  # 颜色按钮在第3列
            if class_item and color_button:
                class_name = class_item.text()
                color = color_button.palette().button().color()
                class_colors[class_name] = (color.red(), color.green(), color.blue())
        return class_colors

    def update_progress(self, value):
        # 这里可以根据进度条更新界面显示，目前先留空
        pass

    def append_log(self, message):
        self.log_text_edit.append(message)
        with open('../../../../../annotation_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"{message}\n")

    def finish_processing(self, result):
        self.append_log(result)
        self.start_pause_btn.setText("开始标注")
        self.is_process_complete = True
        self.log_text_edit.append(f"标注已完成，本次任务共消耗 {self.total_boxes} 个矩形框")
        # Remove the database deduction logic from here; it will be handled in download_normal_images

    def filter_classes(self, text):
        proxy_model = self.class_combo.model()
        proxy_model.setFilterRegExp(text)

    def switch_to_personal_center(self):
        self.switch_to_personal_center_signal.emit()

    def eventFilter(self, obj, event):
        if obj == self.avatar_label:
            if event.type() == QEvent.Enter:
                self.show_user_info_popup()
            elif event.type() == QEvent.Leave:
                if self.user_info_popup:
                    self.user_info_popup.hide()
        elif self.user_info_popup and obj == self.user_info_popup:
            if event.type() == QEvent.Leave:
                if not self.avatar_label.underMouse():
                    self.user_info_popup.hide()
        return super().eventFilter(obj, event)

    def get_user_info_from_database(self):
        if not self.user_info:
            return {
                "vip_level": "VIP0",
                "current_exp": 0,
                "current_min": 0,
                "next_level_exp": 1090,
                "remain_score": 0
            }

        # 定义VIP等级阈值（格式：最小积分，等级）
        vip_thresholds = [
            (0, 1),  # VIP1: 0-1090
            (1090, 2),  # VIP2: 1090-6800
            (6800, 3),  # VIP3: 6800-88800
            (88800, 4),  # VIP4: 88800-168888
            (168888, 5)  # VIP5: >=168888
        ]

        total_points = self.user_info['total_points']
        vip_level = 1
        current_min = 0
        next_level_exp = 1090  # 默认下一等级阈值

        # 逆序查找匹配的最高等级
        for threshold, level in reversed(vip_thresholds):
            if total_points >= threshold:
                vip_level = level
                current_min = threshold
                # 获取下一等级阈值（如果是最高级则同当前阈值）
                next_level_exp = threshold if level == 5 else \
                    [t for t, l in vip_thresholds if l == level + 1][0]
                break

        return {
            "vip_level": f"VIP{vip_level}",
            "current_exp": total_points,
            "current_min": current_min,
            "next_level_exp": next_level_exp,
            "remain_score": self.user_info['current_points']
        }

    def show_user_info_popup(self):
        try:
            if self.user_info_popup is None:
                self.user_info_popup = QMenu(self)
                self.user_info_popup.setStyleSheet(anno_config.dropdown_menu_style)

                # 从数据库获取用户信息
                user_info = self.get_user_info_from_database()

                # 创建一个主容器用于放置所有内容
                main_widget = QWidget()
                main_layout = QVBoxLayout(main_widget)
                main_layout.setSpacing(2)  # 设置控件之间的间距为 2px
                main_layout.setContentsMargins(5, 5, 5, 5)  # 设置布局的外边距

                # +++ 新增VIP等级显示 +++
                vip_layout = QHBoxLayout()
                vip_label = QLabel("VIP等级：")
                vip_value = QLabel(user_info['vip_level'])
                vip_label.setStyleSheet("color: #666; font-size: 14px;")
                vip_value.setStyleSheet("""
                               color: #FF9900; 
                               font-size: 16px;
                               font-weight: bold;
                               padding-left: 8px;
                           """)
                vip_layout.addWidget(vip_label)
                vip_layout.addWidget(vip_value)
                vip_layout.addStretch()
                main_layout.addLayout(vip_layout)

                # 当前经验值
                current_exp = user_info['current_exp']
                exp_label = QLabel(f"当前经验值：{current_exp}")
                exp_label.setStyleSheet("color: #666; font-size: 14px;")
                main_layout.addWidget(exp_label)

                # 到下一等级所需经验值
                if user_info['vip_level'] != 'VIP5':
                    remaining_exp = user_info['next_level_exp'] - current_exp
                else:
                    remaining_exp = 0
                next_level_exp_label = QLabel(f"到下一等级所需经验值：{remaining_exp}")
                next_level_exp_label.setStyleSheet("color: #666; font-size: 14px;")
                main_layout.addWidget(next_level_exp_label)

                # 创建经验进度条
                exp_progress_bar = QProgressBar()
                if user_info['vip_level'] == 'VIP5':
                    progress_percentage = 100
                else:
                    progress_percentage = (current_exp / user_info['next_level_exp']) * 100 if user_info[
                                                                                                   'next_level_exp'] > 0 else 0
                exp_progress_bar.setRange(0, 100)
                exp_progress_bar.setValue(int(progress_percentage))
                exp_progress_bar.setFormat(f"{progress_percentage:.1f}%")
                exp_progress_bar.setStyleSheet(anno_config.progress_bar_style)
                main_layout.addWidget(exp_progress_bar)

                # 添加分隔线
                separator = QFrame()
                separator.setFrameShape(QFrame.HLine)
                separator.setFrameShadow(QFrame.Sunken)
                main_layout.addWidget(separator)

                # 修改积分显示（找到points_label的创建位置）
                points_label = QLabel(
                    f"当前剩余积分：{self.user_info['current_points']}" if self.user_info else "当前剩余积分：0")
                points_label.setStyleSheet("color: #666; font-size: 14px;")
                main_layout.addWidget(points_label)

                # 设置“进入个人中心”按钮
                go_to_personal_center_button = QPushButton("进入个人中心")
                go_to_personal_center_button.setObjectName("go_to_personal_center")
                go_to_personal_center_button.setStyleSheet(anno_config.go_to_personal_center_button_style)
                go_to_personal_center_button.clicked.connect(self.open_personal_center)
                main_layout.addWidget(go_to_personal_center_button)

                # 将主容器添加到菜单中
                widget_action = QWidgetAction(self.user_info_popup)
                widget_action.setDefaultWidget(main_widget)
                self.user_info_popup.addAction(widget_action)

            pos = self.avatar_label.mapToGlobal(self.avatar_label.rect().bottomLeft())
            self.user_info_popup.popup(pos)
        except Exception as e:
            print(f"显示用户信息弹出框时出错: {e}")

    def open_personal_center(self):
        """连接到 personal_center_ui 页面，假设已有页面实例或创建逻辑"""
        try:
            # print("进入个人中心，user_info =", self.user_info)
            self.personal_center_page = PersonalCenter(self.user_info)
            self.personal_center_page.show()
        except ImportError:
            print("无法导入 personal_center_ui 页面类，请检查路径和类名。")
        except Exception as e:
            print(f"打开个人中心页面时出错: {e}")

    def hide_user_info_popup(self):
        if self.user_info_popup is not None:
            self.user_info_popup.hide()

    def load_activity_announcements(self):
        """
        从服务器加载 message.json 中的公告信息，并显示到活动公告栏中
        """
        try:
            # 建立SSH连接
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ssh_config.HOST, ssh_config.PORT, ssh_config.USER, ssh_config.PASSWORD)
            sftp = ssh.open_sftp()

            # 假设 message.json 文件存放在 BASE_PATH 下
            remote_path = f"{ssh_config.BASE_PATH}/message.json"
            with sftp.open(remote_path, 'r') as f:
                data = json.load(f)

            sftp.close()
            ssh.close()

            # 拼接公告信息字符串（你可以根据需求调整显示格式）
            announcements = data.get("announcements", [])
            content = ""
            for ann in announcements:
                title = ann.get("title", "无标题")
                text = ann.get("content", "")
                content += f"{title}\n{text}\n\n"

            # 假设 activity_announcement_content 是活动公告栏的 QTextEdit 对象
            self.activity_announcement_content.setPlainText(content)
        except Exception as e:
            self.log_text_edit.append("加载活动公告失败：" + str(e))

    ###改：4.2：增加该方法
    def showEvent(self, event):
        super().showEvent(event)
        self.center()  # 在窗口显示后调用居中方法

    ###
    ###改：4.2:
    def set_optimal_size(self):
        # 获取屏幕可用尺寸
        screen = QDesktopWidget().availableGeometry()
        # 设置窗口尺寸为屏幕宽高的80%
        new_width = int(screen.width() * 0.98)
        new_height = int(screen.height() * 0.98)
        self.resize(new_width, new_height)
    ########
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AutoAnnotationSystem()
    window.show()
    sys.exit(app.exec_())