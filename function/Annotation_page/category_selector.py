from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QScrollArea, QWidget, QHBoxLayout, QPushButton, QCheckBox, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal


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


class CategorySelector(QDialog):
    """手动选择标注类型的对话框"""
    selected_classes = pyqtSignal(list)

    def __init__(self, parent=None, pre_selected=None):
        super().__init__(parent)
        self.setWindowTitle("手动选择标注类型")
        self.coco_classes = coco_classes  # 使用全局定义的COCO类别
        self.selected = set(pre_selected) if pre_selected is not None else set()

        # 创建主布局
        self.main_layout = QVBoxLayout()

        # 搜索框
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("搜索类别...")
        self.search_box.setStyleSheet("font-weight: medium;")
        self.search_box.textChanged.connect(self.filter_classes)
        self.main_layout.addWidget(self.search_box)

        # 类别列表区域
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        self.main_layout.addWidget(self.scroll_area)

        # 初始化类别列表
        self.checkboxes = []
        for cls in self.coco_classes:
            checkbox = QCheckBox(cls)
            checkbox.setStyleSheet("font-weight: medium;")
            checkbox.setChecked(cls in self.selected)
            checkbox.clicked.connect(self.toggle_selection)
            self.scroll_layout.addWidget(checkbox)
            self.checkboxes.append(checkbox)

        # 操作按钮
        self.button_layout = QHBoxLayout()
        self.confirm_btn = QPushButton("确认选择")
        self.confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 180, 247, 0.8);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: medium;
            }
            QPushButton:hover {
                background-color: rgba(0, 180, 247, 0.5);
            }
        """)
        self.confirm_btn.clicked.connect(self.confirm_selection)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #454545;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: medium;
            }
            QPushButton:hover {
                background-color: #828282;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        self.button_layout.addWidget(self.confirm_btn)
        self.button_layout.addWidget(self.cancel_btn)
        self.main_layout.addLayout(self.button_layout)

        self.setLayout(self.main_layout)

    def filter_classes(self, text):
        """根据搜索框内容过滤类别"""
        search_text = text.lower()
        for checkbox in self.checkboxes:
            cls = checkbox.text()
            checkbox.setVisible(search_text in cls.lower())

    def toggle_selection(self):
        """切换选中状态"""
        sender = self.sender()
        if sender.isChecked():
            self.selected.add(sender.text())
        else:
            self.selected.discard(sender.text())

    def confirm_selection(self):
        """确认选择并发送信号"""
        self.selected_classes.emit(list(self.selected))
        self.close()