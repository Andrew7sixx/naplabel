import os
import sys
import logging
from functools import partial

from PyQt5 import QtCore
from PyQt5.QtCore import QPointF, Qt, QSize, QRectF
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFileDialog, QLineEdit, QGraphicsView,
                             QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem, QColorDialog,
                             QMessageBox, QSizePolicy, QTextEdit, QTableWidget, QTableWidgetItem,
                             QGroupBox, QGraphicsPixmapItem, QGraphicsItem)
from PyQt5.QtGui import (QPixmap, QColor, QPen, QPainter, QFont, QIntValidator)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

class CustomGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setMouseTracking(True)
        self.current_label = None
        self.current_color = QColor(255, 0, 0)
        self.annotation_mode = False
        self.drawing = False
        self.start_pos = QPointF()
        self.current_rect = None
        self.prev_arrow = None
        self.next_arrow = None
        self.zoom_factor = 1.0
        self.image_item = None
        self.annotation_items = []
        self.arrow_size = QSize(40, 40)
        self.base_scale_factor = 1.0
        self.max_image_width = 0

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            zoom_in_factor = 1.1
            zoom_out_factor = 1 / 1.1
            delta = event.angleDelta().y()
            new_zoom = self.zoom_factor * (zoom_in_factor if delta > 0 else zoom_out_factor)

            if self.image_item:
                viewport_rect = self.viewport().rect()
                viewport_width = viewport_rect.width()
                center_width = viewport_width * 0.8
                side_width = viewport_width * 0.1

                pixmap = self.image_item.pixmap()
                base_scaled_width = pixmap.width() * self.base_scale_factor
                new_scaled_width = base_scaled_width * new_zoom

                if new_scaled_width > center_width:
                    new_zoom = center_width / base_scaled_width
                if new_zoom < 0.1:
                    new_zoom = 0.1

                old_zoom_factor = self.zoom_factor
                self.zoom_factor = new_zoom
                self.image_item.setScale(self.base_scale_factor * self.zoom_factor)

                scaled_width = base_scaled_width * self.zoom_factor
                scaled_height = pixmap.height() * self.base_scale_factor * self.zoom_factor
                image_x = side_width + (center_width - scaled_width) / 2
                image_y = (viewport_rect.height() - scaled_height) / 2
                self.image_item.setPos(image_x, image_y)

                for item in self.annotation_items:
                    if isinstance(item, QGraphicsRectItem):
                        rect = item.rect()
                        scale_factor = self.zoom_factor / old_zoom_factor
                        scaled_rect = QRectF(
                            rect.x() * scale_factor,
                            rect.y() * scale_factor,
                            rect.width() * scale_factor,
                            rect.height() * scale_factor
                        )
                        item.setRect(scaled_rect)
                    elif isinstance(item, QGraphicsTextItem):
                        pos = item.pos()
                        scale_factor = self.zoom_factor / old_zoom_factor
                        item.setPos(
                            pos.x() * scale_factor,
                            pos.y() * scale_factor
                        )

                event.accept()
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.setCursor(Qt.OpenHandCursor)
        elif self.annotation_mode and event.button() == Qt.LeftButton:
            parent_table = self.parent.manual_table
            current_label_text = self.current_label
            label_exists = False
            if parent_table.rowCount() > 0:
                for row in range(parent_table.rowCount()):
                    item = parent_table.item(row, 1)
                    if item and item.text() == current_label_text:
                        label_exists = True
                        break
            if not label_exists:
                self.parent.statusBar().showMessage("所选标签不存在或已被删除")
                return
            self.start_pos = self.mapToScene(event.pos())
            self.drawing = True
            if self.scene().sceneRect().contains(self.start_pos):
                self.current_rect = QGraphicsRectItem()
                self.current_rect.setPen(QPen(self.current_color, 2))
                self.scene().addItem(self.current_rect)
        else:
            pos = self.mapToScene(event.pos())
            if event.button() == Qt.LeftButton:
                if self.prev_arrow and self.prev_arrow.sceneBoundingRect().contains(pos):
                    self.parent.prevImage()
                    return
                elif self.next_arrow and self.next_arrow.sceneBoundingRect().contains(pos):
                    self.parent.nextImage()
                    return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.drawing and self.current_rect:
            end_pos = self.mapToScene(event.pos())
            rect = QRectF(self.start_pos, end_pos).normalized()
            self.current_rect.setRect(rect)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self.setDragMode(QGraphicsView.NoDrag if self.annotation_mode else QGraphicsView.ScrollHandDrag)
            self.setCursor(Qt.CrossCursor if self.annotation_mode else Qt.ArrowCursor)
        elif self.drawing and self.current_rect:
            end_pos = self.mapToScene(event.pos())
            rect = QRectF(self.start_pos, end_pos).normalized()
            if rect.width() > 5 and rect.height() > 5 and self.scene().sceneRect().contains(rect):
                image_pos = self.image_item.pos()
                adjusted_rect = QRectF(
                    rect.x() - image_pos.x(),
                    rect.y() - image_pos.y(),
                    rect.width(),
                    rect.height()
                )

                original_rect = QRectF(
                    adjusted_rect.x() / (self.base_scale_factor * self.zoom_factor),
                    adjusted_rect.y() / (self.base_scale_factor * self.zoom_factor),
                    adjusted_rect.width() / (self.base_scale_factor * self.zoom_factor),
                    adjusted_rect.height() / (self.base_scale_factor * self.zoom_factor)
                )

                perm_rect = QGraphicsRectItem(rect)
                perm_rect.setPen(QPen(self.current_color, 2))
                self.scene().addItem(perm_rect)
                self.annotation_items.append(perm_rect)

                text_item = QGraphicsTextItem(self.current_label)
                text_item.setDefaultTextColor(self.current_color)
                text_item.setFont(QFont("Arial", 10))
                text_item.setPos(rect.x(), rect.y() - 20)
                self.scene().addItem(text_item)
                self.annotation_items.append(text_item)

                current_image = self.parent.image_list[self.parent.current_index]
                self.parent.annotations.setdefault(current_image, []).append({
                    'rect': original_rect,
                    'label': self.current_label,
                    'color': self.current_color
                })

                # Update button state after adding an annotation
                self.parent.updateButtonState()
            self.scene().removeItem(self.current_rect)
            self.drawing = False
            self.current_rect = None
        super().mouseReleaseEvent(event)

    def init_navigation_arrows(self):
        if not self.prev_arrow:
            self.prev_arrow = QGraphicsTextItem("<")
            self.prev_arrow.setFont(QFont("Arial", 20))
            self.prev_arrow.setDefaultTextColor(QColor(0, 0, 0))
            self.prev_arrow.setFlag(QGraphicsItem.ItemIsSelectable, True)
            self.scene().addItem(self.prev_arrow)

        if not self.next_arrow:
            self.next_arrow = QGraphicsTextItem(">")
            self.next_arrow.setFont(QFont("Arial", 20))
            self.next_arrow.setDefaultTextColor(QColor(0, 0, 0))
            self.next_arrow.setFlag(QGraphicsItem.ItemIsSelectable, True)
            self.scene().addItem(self.next_arrow)

        self.update_arrow_positions()

    def update_arrow_positions(self):
        if not self.scene() or not self.prev_arrow or not self.next_arrow:
            return

        viewport_rect = self.viewport().rect()
        scene_rect = self.mapToScene(viewport_rect).boundingRect()
        viewport_width = viewport_rect.width()

        side_width = viewport_width * 0.1
        center_width = viewport_width * 0.8

        arrow_y = scene_rect.center().y() - self.arrow_size.height() / 2

        left_arrow_x = scene_rect.left() + side_width / 2 - self.arrow_size.width() / 2
        self.prev_arrow.setPos(left_arrow_x, arrow_y)

        right_arrow_x = scene_rect.right() - side_width / 2 - self.arrow_size.width() / 2
        self.next_arrow.setPos(right_arrow_x, arrow_y)

    def loadImage(self, index):
        if 0 <= index < len(self.parent.image_list):
            if self.image_item:
                self.scene().removeItem(self.image_item)
                self.image_item = None
            for item in self.annotation_items:
                self.scene().removeItem(item)
            self.annotation_items.clear()

            pixmap = QPixmap(self.parent.image_list[index])
            if pixmap.isNull():
                QMessageBox.critical(self.parent, '错误', f'无法加载图片：{self.parent.image_list[index]}')
                return

            self.image_item = QGraphicsPixmapItem(pixmap)
            self.scene().addItem(self.image_item)

            viewport_rect = self.viewport().rect()
            viewport_width = viewport_rect.width()
            center_width = viewport_width * 0.8
            side_width = viewport_width * 0.1

            pixmap_width = pixmap.width()
            pixmap_height = pixmap.height()
            self.base_scale_factor = min(center_width / pixmap_width, viewport_rect.height() / pixmap_height)

            scaled_width = pixmap_width * self.base_scale_factor
            scaled_height = pixmap_height * self.base_scale_factor

            image_x = side_width + (center_width - scaled_width) / 2
            image_y = (viewport_rect.height() - scaled_height) / 2

            self.image_item.setPos(image_x, image_y)
            self.image_item.setScale(self.base_scale_factor)

            self.scene().setSceneRect(0, 0, viewport_width, viewport_rect.height())
            self.setSceneRect(0, 0, viewport_width, viewport_rect.height())

            self.zoom_factor = 1.0
            self.init_navigation_arrows()

            current_image = self.parent.image_list[index]
            if current_image in self.parent.annotations:
                for ann in self.parent.annotations[current_image]:
                    rect = QRectF(
                        (ann['rect'].x() * self.base_scale_factor * self.zoom_factor) + image_x,
                        (ann['rect'].y() * self.base_scale_factor * self.zoom_factor) + image_y,
                        ann['rect'].width() * self.base_scale_factor * self.zoom_factor,
                        ann['rect'].height() * self.base_scale_factor * self.zoom_factor
                    )
                    rect_item = QGraphicsRectItem(rect)
                    rect_item.setPen(QPen(ann['color'], 2))
                    self.scene().addItem(rect_item)
                    self.annotation_items.append(rect_item)

                    text_item = QGraphicsTextItem(ann['label'])
                    text_item.setDefaultTextColor(ann['color'])
                    text_item.setFont(QFont("Arial", 10))
                    text_item.setPos(rect.x(), rect.y() - 20 * self.base_scale_factor * self.zoom_factor)
                    self.scene().addItem(text_item)
                    self.annotation_items.append(text_item)

            # Update button state after loading image
            self.parent.updateButtonState()

class AnnotationTool(QMainWindow):
    def __init__(self, auto_annotation_window=None, parent=None):
        super().__init__(parent)
        if auto_annotation_window is not None:
            self.auto_annotation_window = auto_annotation_window
        else:
            raise ValueError("auto_annotation_window 不能为 None")
        self.label_color_mapping = {}
        self.initUI()  # No change here, but ensure setupVariables is called early in initUI
        self.process_thread = None
        self.manual_annotation_window = None

    def initUI(self):
        self.setWindowTitle('Advanced Image Annotation Tool')
        self.setGeometry(200, 200, 1280, 800)
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            QPushButton {
                padding: 6px 10px;
                border: none;
                border-radius: 8px;
                background-color: rgba(0, 180, 247, 0.8);
                color: white;
                font-size: 12px;
                font-weight: Medium;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: rgba(0, 180, 247, 0.5);
            }
            QLineEdit {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 8px;
                font-size: 12px;
            }
            QLabel {
                font-size: 12px;
            }
            QTableWidget {
                font-size: 11px;
            }
        """)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        self.graphics_view = CustomGraphicsView(self)
        self.scene = QGraphicsScene()
        self.graphics_view.setScene(self.scene)
        self.graphics_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.graphics_view, 4)

        control_panel = QWidget()
        control_panel.setFixedWidth(300)
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(5, 5, 5, 5)
        control_layout.setSpacing(8)

        file_group = QGroupBox("文件操作")
        file_group.setStyleSheet("QGroupBox { font-weight: medium; }")
        file_layout = QVBoxLayout(file_group)
        file_layout.setContentsMargins(5, 15, 5, 5)
        file_layout.setSpacing(5)

        self.btn_open = QPushButton('打开图片文件夹')
        self.btn_open.clicked.connect(self.openFolder)
        file_layout.addWidget(self.btn_open)

        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(5)
        self.btn_prev = QPushButton('上一张')
        self.btn_prev.clicked.connect(self.prevImage)
        self.btn_next = QPushButton('下一张')
        self.btn_next.clicked.connect(self.nextImage)
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.btn_next)
        file_layout.addLayout(nav_layout)
        control_layout.addWidget(file_group)

        label_group = QGroupBox("标签管理")
        label_group.setStyleSheet("QGroupBox { font-weight: medium; }")
        label_layout = QVBoxLayout(label_group)
        label_layout.setContentsMargins(5, 15, 5, 5)
        label_layout.setSpacing(5)

        self.manual_table = QTableWidget()
        self.manual_table.setColumnCount(5)
        self.manual_table.setHorizontalHeaderLabels(["序号", "类别", "标签", "颜色", "删除"])
        self.manual_table.verticalHeader().setVisible(False)
        self.manual_table.horizontalHeader().setStretchLastSection(True)
        self.manual_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.manual_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.manual_table.setMinimumHeight(150)
        self.manual_table.cellClicked.connect(self.handleLabelClick)
        label_layout.addWidget(self.manual_table)

        self.btn_get_auto = QPushButton('从自动标注获取')
        self.btn_get_auto.clicked.connect(self.load_auto_content)
        label_layout.addWidget(self.btn_get_auto)
        control_layout.addWidget(label_group)

        annotate_group = QGroupBox("标注操作")
        annotate_group.setStyleSheet("QGroupBox { font-weight: medium; }")
        annotate_layout = QVBoxLayout(annotate_group)
        annotate_layout.setContentsMargins(5, 15, 5, 5)
        annotate_layout.setSpacing(5)

        # Replace QTextEdit with QLabel for a non-editable tip
        self.tip_text = QLabel("请确保标注时矩形框不超出图片范围")
        self.tip_text.setMaximumHeight(30)  # Fixed height for consistency
        self.tip_text.setAlignment(Qt.AlignCenter)  # Center the text
        self.tip_text.setStyleSheet("""
            QLabel {
                font-size: 14px;  /* Slightly smaller for better fit */
                font-weight: bold;  /* Bold for emphasis */
                color: #D32F2F;  /* A softer red for better readability */
                background-color: #FFF3E0;  /* Light orange background for warmth */
                border: 1px solid #FFCC80;  /* Subtle border for definition */
                border-radius: 5px;  /* Rounded corners for modern look */
                padding: 4px;  /* Inner padding for breathing room */
            }
        """)
        self.tip_text.setToolTip("矩形框超出图片边界将导致标注被清除")  # Add tooltip for extra context
        annotate_layout.addWidget(self.tip_text)

        self.btn_annotate = QPushButton('开始标注')
        self.btn_annotate.clicked.connect(self.toggleAnnotation)
        annotate_layout.addWidget(self.btn_annotate)

        self.btn_undo = QPushButton('撤回')
        self.btn_undo.clicked.connect(self.undoAnnotation)
        self.btn_undo.setStyleSheet("""
            QPushButton {
                background-color: #FFC107;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 12px;
                font-weight: medium;
            }
            QPushButton:hover {
                background-color: #FFA000;
            }
        """)
        annotate_layout.addWidget(self.btn_undo)

        self.btn_save = QPushButton('保存结果')
        self.btn_save.clicked.connect(self.saveAnnotations)
        annotate_layout.addWidget(self.btn_save)
        control_layout.addWidget(annotate_group)

        log_group = QGroupBox("操作日志")
        log_group.setStyleSheet("QGroupBox { font-weight: medium; }")
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(5, 15, 5, 5)
        log_layout.setSpacing(5)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(300)
        self.log_output.setMinimumHeight(200)
        log_layout.addWidget(self.log_output)
        control_layout.addWidget(log_group)

        self.btn_exit = QPushButton('退出程序')
        self.btn_exit.setStyleSheet("""
            QPushButton {
                background-color: #FF3030;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: medium;
            }
            QPushButton:hover {
                background-color: #B90505;
            }
        """)
        self.btn_exit.clicked.connect(self.confirm_exit)
        control_layout.addWidget(self.btn_exit)

        main_layout.addWidget(control_panel)

        self.statusBar().showMessage('准备就绪')
        # Move setupVariables before updateButtonState
        self.setupVariables()
        self.updateButtonState()  # Now safe to call after variables are initialized

    def updateButtonState(self):
        """Update the state of all buttons based on current conditions."""
        has_images = len(self.image_list) > 0 and self.current_index != -1
        has_annotations = has_images and len(self.annotations.get(self.image_list[self.current_index], [])) > 0
        self.btn_prev.setEnabled(has_images and self.current_index > 0)
        self.btn_next.setEnabled(has_images and self.current_index < len(self.image_list) - 1)
        self.btn_annotate.setEnabled(has_images)
        self.btn_save.setEnabled(has_images)
        self.btn_undo.setEnabled(has_annotations)

    def undoAnnotation(self):
        """Undo the last annotation."""
        if self.current_index == -1 or self.current_index >= len(self.image_list):
            return

        current_image = self.image_list[self.current_index]
        if current_image in self.annotations and self.annotations[current_image]:
            # Remove the last annotation from the list
            self.annotations[current_image].pop()
            if not self.annotations[current_image]:
                del self.annotations[current_image]

            # Remove the last two items (rectangle and text) from the scene
            if len(self.graphics_view.annotation_items) >= 2:
                for _ in range(2):  # Remove text and rectangle
                    item = self.graphics_view.annotation_items.pop()
                    self.graphics_view.scene().removeItem(item)

            self.log_action(f"撤回了 {current_image} 的最后一次标注")
            self.statusBar().showMessage("已撤回最后一次标注")
            self.updateButtonState()

    def setupVariables(self):
        self.image_folder = ''
        self.image_list = []
        self.current_index = -1
        self.annotations = {}
        self.current_color = QColor(255, 0, 0)
        self.default_size = QSize(800, 600)

    def loadImage(self, index):
        if 0 <= index < len(self.image_list):
            try:
                self.graphics_view.loadImage(index)
                self.log_action(f"加载图片: {self.image_list[index]}")
                self.statusBar().showMessage(f"当前图片: {self.current_index + 1}/{len(self.image_list)}")
            except Exception as e:
                import traceback
                error_msg = f"加载图片时出错: {str(e)}\n{traceback.format_exc()}"
                self.log_action(error_msg)
                QMessageBox.critical(self, '错误', f"加载图片失败:\n{str(e)}")
        else:
            self.log_action("无效的图片索引")

    def openFolder(self):
        try:
            folder = QFileDialog.getExistingDirectory(self, '选择包含图片的文件夹')
            if folder:
                self.log_action(f"打开文件夹: {folder}")
                self.image_folder = folder
                valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')
                self.image_list = sorted([
                    os.path.join(folder, f) for f in os.listdir(folder)
                    if f.lower().endswith(valid_extensions)
                ])

                if self.image_list:
                    self.current_index = 0
                    self.loadImage(self.current_index)
                    self.updateButtonState()
                    self.statusBar().showMessage(f'已加载 {len(self.image_list)} 张图片')
                else:
                    QMessageBox.warning(self, '错误', '未找到支持的图片格式（png/jpg/jpeg/bmp/webp）')
        except Exception as e:
            import traceback
            error_msg = f"打开文件夹时出错: {str(e)}\n{traceback.format_exc()}"
            self.log_action(error_msg)
            QMessageBox.critical(self, "错误", f"无法打开文件夹:\n{str(e)}")

    def prevImage(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.loadImage(self.current_index)
            self.updateButtonState()

    def nextImage(self):
        if self.current_index < len(self.image_list) - 1:
            self.current_index += 1
            self.loadImage(self.current_index)
            self.updateButtonState()

    def toggleAnnotation(self):
        self.graphics_view.annotation_mode = not self.graphics_view.annotation_mode
        mode_text = '退出标注' if self.graphics_view.annotation_mode else '开始标注'
        self.log_action('开始标注' if mode_text == '退出标注' else '退出标注')
        self.btn_annotate.setText(f'🖌 {mode_text}')

        if self.graphics_view.annotation_mode:
            self.graphics_view.setDragMode(QGraphicsView.NoDrag)
            self.graphics_view.setCursor(Qt.CrossCursor)
            self.statusBar().showMessage('标注模式：按住鼠标左键绘制矩形框')
        else:
            self.graphics_view.setDragMode(QGraphicsView.ScrollHandDrag)
            self.graphics_view.setCursor(Qt.ArrowCursor)
            self.statusBar().showMessage('浏览模式：按住空格拖动图片')

    def saveAnnotations(self):
        if not self.image_list or self.current_index == -1:
            QMessageBox.warning(self, '警告', '请先打开图片文件夹')
            return

        save_dir = QFileDialog.getExistingDirectory(self, '选择保存路径')
        if not save_dir:
            self.log_action(f"取消保存标注")
            return

        try:
            current_image = self.image_list[self.current_index]
            base_name = os.path.basename(current_image)
            save_path = os.path.join(save_dir, base_name)

            if not os.access(current_image, os.R_OK):
                raise Exception("原图不可读或不存在")

            pixmap = QPixmap(current_image)
            if pixmap.isNull():
                raise Exception("无法加载原始图片")

            img = pixmap.toImage()
            painter = QPainter(img)
            painter.setRenderHint(QPainter.Antialiasing)

            if current_image in self.annotations:
                for ann in self.annotations[current_image]:
                    rect = ann['rect'].toRect()
                    color = ann['color']
                    painter.setPen(QPen(color, 2))
                    painter.drawRect(rect)

                    painter.setFont(QFont("SimHei", 12))
                    painter.setPen(QPen(color))
                    painter.drawText(rect.topLeft() + QPointF(0, -5), ann['label'])

            painter.end()

            file_format = os.path.splitext(base_name)[1][1:].upper()
            supported_formats = ['JPG', 'JPEG', 'PNG']
            if file_format not in supported_formats:
                self.log_action(f"不支持的图片格式 {file_format}，将转换为 JPEG")
                save_path = os.path.splitext(save_path)[0] + '.jpg'
                file_format = 'JPEG'

            if file_format in ['JPG', 'JPEG']:
                if not img.save(save_path, "JPEG", 95):
                    raise Exception("保存JPEG图片失败")
            else:
                if not img.save(save_path, "PNG"):
                    raise Exception("保存PNG图片失败")

            txt_path = os.path.join(save_dir, os.path.splitext(base_name)[0] + '.txt')
            img_w = pixmap.width()
            img_h = pixmap.height()

            with open(txt_path, 'w', encoding='utf-8') as f:
                for ann in self.annotations.get(current_image, []):
                    rect = ann['rect']
                    if rect.x() < 0 or rect.y() < 0 or rect.right() > img_w or rect.bottom() > img_h:
                        if current_image in self.annotations:
                            del self.annotations[current_image]
                        for item in self.graphics_view.annotation_items:
                            self.graphics_view.scene().removeItem(item)
                        self.graphics_view.annotation_items.clear()
                        self.log_action(f"检测到标注坐标超出范围，已清除 {current_image} 的所有标注")
                        QMessageBox.warning(self, '警告',
                                            '检测到标注坐标超出图片范围，已清除所有标注，请重新标注。\n'
                                            '注意：矩形框不能超出图片边界。')
                        self.updateButtonState()
                        return

                    x_center = (rect.x() + rect.width() / 2) / img_w
                    y_center = (rect.y() + rect.height() / 2) / img_h
                    width = rect.width() / img_w
                    height = rect.height() / img_h

                    label_id = next((i for i, cls in enumerate(coco_classes) if cls.startswith(ann['label'])), 0)
                    f.write(f"{label_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")

            self.log_action(f"保存标注到: {save_path}")
            QMessageBox.information(self, '保存成功',
                                    f'文件已保存至：\n{save_dir}\n'
                                    f'图片尺寸：{img_w}x{img_h}\n'
                                    f'标注数量：{len(self.annotations.get(current_image, []))}')

        except Exception as e:
            import traceback
            error_msg = f"保存失败: {str(e)}\n{traceback.format_exc()}"
            self.log_action(error_msg)
            QMessageBox.critical(self, '保存失败',
                                 f'错误详情：\n{str(e)}\n\n'
                                 f'建议操作：\n1. 检查文件写入权限\n2. 确认磁盘空间充足\n3. 验证图片格式有效性')

    def resizeEvent(self, event):
        super().resizeEvent(event)
        table_width = self.manual_table.viewport().width()
        if table_width > 0:
            col_widths = {
                0: int(table_width * 0.15),
                1: int(table_width * 0.35),
                2: int(table_width * 0.20),
                3: int(table_width * 0.15),
                4: int(table_width * 0.15)
            }
            for col, width in col_widths.items():
                self.manual_table.setColumnWidth(col, width)

    def handleLabelClick(self, row, column):
        """Handle clicks on the label table."""
        if column == 1 or column == 2:  # Clicking "类别" or "标签" selects the label
            label = self.manual_table.item(row, 1).text()
            if label in self.label_color_mapping:
                self.graphics_view.current_label = label
                self.graphics_view.current_color = self.label_color_mapping[label]
                self.statusBar().showMessage(f"已选择标签 {label} 和颜色 {self.label_color_mapping[label].name()}")
            else:
                self.statusBar().showMessage(f"标签 {label} 的颜色未设置")
        elif column == 3:  # Clicking "颜色" changes the color
            self.change_label_color(row)
        elif column == 4:  # Clicking "删除" removes the row
            self.delete_manual_row(row)

    # def add_label_from_input(self):
    #     """Add a new label from the input field."""
    #     label_id = self.label_input.text().strip()
    #     if not label_id:
    #         return
    #
    #     try:
    #         label_idx = int(label_id)
    #         if 0 <= label_idx < len(coco_classes):
    #             label = coco_classes[label_idx].split(' ')[0]  # Extract the English name
    #             if label not in [self.manual_table.item(r, 1).text() for r in range(self.manual_table.rowCount()) if self.manual_table.item(r, 1)]:
    #                 row = self.manual_table.rowCount()
    #                 self.manual_table.insertRow(row)
    #                 self.manual_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
    #                 self.manual_table.setItem(row, 1, QTableWidgetItem(label))
    #                 self.manual_table.setItem(row, 2, QTableWidgetItem(label))
    #
    #                 color_button = QPushButton()
    #                 default_color = QColor(255, 255, 255)
    #                 color_button.setFixedSize(30, 30)
    #                 color_button.setStyleSheet(f"background-color: {default_color.name()}; border-radius: 5px;")
    #                 color_button.clicked.connect(partial(self.change_label_color, row))
    #                 self.manual_table.setCellWidget(row, 3, color_button)
    #
    #                 delete_button = QPushButton("X")
    #                 delete_button.setFixedSize(20, 20)
    #                 delete_button.setStyleSheet("color: #ff4444; background-color: transparent; border: none; font-size: 16px;")
    #                 delete_button.clicked.connect(partial(self.delete_manual_row, row))
    #                 self.manual_table.setCellWidget(row, 4, delete_button)
    #
    #                 self.label_color_mapping[label] = default_color
    #                 self.log_action(f"添加标签: {label}")
    #                 self.label_input.clear()
    #     except ValueError:
    #         self.statusBar().showMessage("请输入有效的类别ID")

    def load_auto_content(self):
        """Load labels from the automatic annotation window."""
        try:
            if hasattr(self, 'auto_annotation_window') and self.auto_annotation_window:
                auto_data = self.auto_annotation_window.get_annotation_data()
                if not auto_data:
                    QMessageBox.information(self, "提示", "自动标注表格为空")
                    return
            else:
                QMessageBox.information(self, "提示", "无法获取自动标注数据")
                return

            self.manual_table.setRowCount(0)
            for row, item in enumerate(auto_data):
                self.manual_table.insertRow(row)
                self.manual_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
                self.manual_table.setItem(row, 1, QTableWidgetItem(item['class']))
                self.manual_table.setItem(row, 2, QTableWidgetItem(item['label']))

                color_button = QPushButton()
                color = item.get('color', QColor(255, 255, 255))
                color_button.setFixedSize(30, 30)
                color_button.setStyleSheet(f"background-color: {color.name()}; border-radius: 5px;")
                color_button.clicked.connect(partial(self.change_label_color, row))
                self.manual_table.setCellWidget(row, 3, color_button)

                delete_button = QPushButton("X")
                delete_button.setFixedSize(20, 20)
                delete_button.setStyleSheet("color: #ff4444; background-color: transparent; border: none; font-size: 16px;")
                delete_button.clicked.connect(partial(self.delete_manual_row, row))
                self.manual_table.setCellWidget(row, 4, delete_button)

                self.label_color_mapping[item['class']] = color

            if auto_data:
                first_label = auto_data[0]['class']
                self.graphics_view.current_label = first_label
                self.graphics_view.current_color = self.label_color_mapping[first_label]
                self.statusBar().showMessage(f"已选择标签 {first_label} 和颜色 {self.label_color_mapping[first_label].name()}")

            self.log_action("已从自动标注窗口加载标签")
            self.statusBar().showMessage("成功加载自动标注内容")
        except Exception as e:
            logging.error(f"加载自动标注内容时出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载自动标注内容失败: {str(e)}")


    def confirm_exit(self):
        """Confirm program exit."""
        reply = QMessageBox.question(self, '确认退出', '你确定要退出程序吗？',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.close()

    def change_label_color(self, row):
        """Change the color of a label."""
        if 0 <= row < self.manual_table.rowCount():
            label = self.manual_table.item(row, 1).text()
            color = QColorDialog.getColor()
            if color.isValid():
                self.label_color_mapping[label] = color
                color_button = self.manual_table.cellWidget(row, 3)
                color_button.setStyleSheet(f"background-color: {color.name()}; border-radius: 5px;")
                self.graphics_view.current_label = label
                self.graphics_view.current_color = color
                self.statusBar().showMessage(f"已更新标签 {label} 的颜色为 {color.name()}")
                self.log_action(f"更改标签 {label} 的颜色为 {color.name()}")

    def delete_manual_row(self, row):
        """Delete a row from the manual table."""
        if 0 <= row < self.manual_table.rowCount():
            label = self.manual_table.item(row, 1).text()
            if label in self.label_color_mapping:
                del self.label_color_mapping[label]
            self.manual_table.removeRow(row)
            self.rebind_delete_buttons()
            self.log_action(f"删除标签: {label}")
            if self.manual_table.rowCount() == 0:
                self.graphics_view.current_label = None
                self.graphics_view.current_color = QColor(255, 0, 0)
                self.statusBar().showMessage("已删除所有标签，当前无可用标签")

    def rebind_delete_buttons(self):
        """Rebind delete button signals after row deletion."""
        for row in range(self.manual_table.rowCount()):
            delete_button = self.manual_table.cellWidget(row, 4)
            if delete_button:
                delete_button.clicked.disconnect()
                delete_button.clicked.connect(partial(self.delete_manual_row, row))

    def log_action(self, action):
        """Log an action to the log output."""
        timestamp = QtCore.QDateTime.currentDateTime().toString("hh:mm:ss")
        self.log_output.append(f"[{timestamp}] {action}")
        self.log_output.verticalScrollBar().setValue(self.log_output.verticalScrollBar().maximum())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    from function.Annotation_page.auto_annotation_main import AutoAnnotationSystem
    auto_annotation = AutoAnnotationSystem()
    window = AnnotationTool(auto_annotation)
    window.show()
    sys.exit(app.exec_())