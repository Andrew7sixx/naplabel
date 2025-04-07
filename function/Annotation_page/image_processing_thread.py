from PyQt5.QtCore import QThread, pyqtSignal, QWaitCondition, QMutex, QMutexLocker
import os
import gc
import sys
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO

# COCO 类别列表
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

class ImageProcessingThread(QThread):
    progress = pyqtSignal(int)
    log_message = pyqtSignal(str)
    result_ready = pyqtSignal(str)
    pause_signal = pyqtSignal()
    total_boxes_signal = pyqtSignal(int)
    annotation_record_signal = pyqtSignal(str, int)

    def __init__(self, input_folder, result_folder, annotation_classes, user_info,initial_total_boxes):
        super().__init__()
        self.input_folder = input_folder
        if not annotation_classes:
            raise ValueError("未选择标注类别")
        self.annotation_classes = annotation_classes
        self.user_info = user_info
        self.current_index = 0
        self.paused = False
        self.wait_condition = QWaitCondition()
        self.mutex = QMutex()
        self.result_folder = result_folder  # 用户指定的结果文件夹
        self.initial_total_boxes = initial_total_boxes  # 新增

        # 初始化颜色字典
        self.class_colors = {}  # 格式: {'person': (255,0,0), 'car': (0,255,0)}

        # 定义本地临时目录
        account = self.user_info.get('account', 'default_account')
        self.base_path = os.path.expanduser("~")  # 正确获取用户主目录
        self.temp_dir = os.path.join(self.base_path, f"{account}_temp")
        try:
            os.makedirs(os.path.join(self.temp_dir, "img"), exist_ok=True)
            os.makedirs(os.path.join(self.temp_dir, "label"), exist_ok=True)
        except OSError as e:
            self.log_message.emit(f"创建临时目录出错: {str(e)}")
        try:
            self.log_message.emit("开始加载YOLO模型")

            def resource_path(relative_path):
                """ 获取打包后的资源绝对路径 """
                if hasattr(sys, '_MEIPASS'):
                    base_path = sys._MEIPASS  # 打包后的临时解压目录
                else:
                    base_path = os.path.abspath(".")  # 开发环境当前目录
                return os.path.join(base_path, relative_path)

            # 使用示例（假设代码中加载模型的逻辑）
            yolo_model_path = resource_path("yolo11m.pt")
            # 添加路径验证
            if not os.path.exists(yolo_model_path):
                self.log_message.emit(f"❌ 模型文件未找到：{yolo_model_path}")
                raise FileNotFoundError(f"YOLO模型文件不存在于：{yolo_model_path}")

            self.log_message.emit(f"模型路径：{yolo_model_path}")
            self.model = YOLO(yolo_model_path)  # 修改此处！！！
            self.log_message.emit("YOLO模型加载成功")
        except Exception as e:
            error_msg = f"加载YOLO模型失败: {str(e)}"
            self.log_message.emit(error_msg)
            print(error_msg)
            raise

    def run(self):
        try:
            self.log_message.emit("开始处理图像列表")
            images = [f for f in os.listdir(self.input_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            self.log_message.emit(f"找到 {len(images)} 张图片")
            total_images = len(images)
            self.output_images_list = []
            self.txt_files_list = []

            while self.current_index < total_images:
                image_file = images[self.current_index]
                self.log_message.emit(f"开始处理第 {self.current_index + 1}/{total_images} 张图片: {image_file}")

                # 处理前检查暂停状态
                with QMutexLocker(self.mutex):
                    if self.paused:
                        self.log_message.emit("处理暂停，等待恢复")
                        self.pause_signal.emit()
                        self.wait_condition.wait(self.mutex)

                if self.isInterruptionRequested():
                    self.log_message.emit("线程被中断请求")
                    break

                try:
                    image_path = os.path.join(self.input_folder, image_file)
                    output_images, txt_files, error = self.process_image(image_path)
                    if not error:
                        self.current_index += 1
                    else:
                        continue
                except Exception as e:
                    import traceback
                    error_msg = f"处理图片时发生异常: {str(e)}\n{traceback.format_exc()}"
                    self.log_message.emit(error_msg)
                    continue

                progress_value = int((self.current_index / total_images) * 100)
                self.progress.emit(progress_value)
                self.log_message.emit(f"进度更新到 {progress_value}%")

            self.progress.emit(100)
            self.log_message.emit("所有图片处理完成")
            self.result_ready.emit(f"处理完成，结果已保存")
        except Exception as e:
            import traceback
            error_msg = f"run 方法中出错: {str(e)}\n{traceback.format_exc()}"
            self.log_message.emit(error_msg)
            print(error_msg)
        finally:
            if hasattr(self, 'model'):
                del self.model
                import time
                for _ in range(5):  # 简单等待5次，每次0.1秒，可根据实际情况调整
                    time.sleep(0.1)
                    if not hasattr(self, 'model'):  # 检查模型是否已被正确释放
                        break
                self.log_message.emit("标注任务已结束")
            gc.collect()

    def set_class_color(self, class_name, color):
        """设置某个类别的颜色"""
        self.class_colors[class_name] = color

    def process_image(self, image_path):
        img = None
        draw = None
        try:
            self.log_message.emit(f"⏳ 开始处理图片: {os.path.basename(image_path)}")
            img = Image.open(image_path).convert('RGB')
            img_width, img_height = img.size
            self.log_message.emit(f"📐 图片尺寸: {img_width}x{img_height}")

            results = self.model(img)
            preds = results[0].boxes
            self.log_message.emit(f"🔍 检测到 {len(preds)} 个潜在目标")

            image_name = os.path.basename(image_path)
            name_without_extension = os.path.splitext(image_name)[0]
            output_img_path = os.path.join(self.temp_dir, "img", image_name)
            output_txt_path = os.path.join(self.temp_dir, "label", f"{name_without_extension}.txt")

            draw = ImageDraw.Draw(img)
            txt_content = []
            valid_boxes = 0

            # 使用支持中文的字体
            font = self.load_font("simhei.ttf", 25)

            for box in preds:
                try:
                    conf = box.conf[0].item()
                    cls = int(box.cls[0].item())
                    class_name = coco_classes[cls]

                    if conf < 0.5 or class_name not in self.annotation_classes:
                        continue

                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    color = self.class_colors.get(class_name, (255, 0, 0))

                    draw.rectangle([x1, y1, x2, y2], outline=color, width=6)
                    # 使用中文名称并确保正确显示
                    label_text = f"{class_name.split(' ')[0]} {conf:.2f}"  # 只取英文部分或调整为中文
                    draw.text((x1, y1 - 25), label_text, font=font, fill=color)

                    x_center = (x1 + x2) / 2 / img_width
                    y_center = (y1 + y2) / 2 / img_height
                    width = (x2 - x1) / img_width
                    height = (y2 - y1) / img_height

                    txt_content.append(f"{cls} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")
                    valid_boxes += 1

                except Exception as box_e:
                    self.log_message.emit(f"⚠️ 处理检测框时出错: {str(box_e)}")
                    continue

            img.save(output_img_path, format='JPEG' if image_name.lower().endswith('.jpg') else 'PNG')
            with open(output_txt_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(txt_content))

            self.output_images_list.append(output_img_path)
            self.txt_files_list.append(output_txt_path)

            if valid_boxes > 0:
                self.total_boxes_signal.emit(valid_boxes)
                self.annotation_record_signal.emit(image_name, valid_boxes)
                self.log_message.emit(f"✅ 完成处理: {image_name} (有效框数: {valid_boxes})")
            else:
                self.log_message.emit(f"ℹ️ 图片 {image_name} 无有效标注框")

            return self.output_images_list, self.txt_files_list, None

        except Exception as e:
            error_msg = f"❌ 处理 {image_name} 失败: {str(e)}"
            self.log_message.emit(error_msg)
            import traceback
            print(f"{error_msg}\n{traceback.format_exc()}")
            return None, None, error_msg

        finally:
            if draw:
                del draw
            if img:
                img.close()
            gc.collect()

    def load_font(self, font_path="simhei.ttf", size=25):
        """加载支持中文的字体，失败时回退到默认字体"""
        try:
            # 检查字体文件是否存在，若不存在则使用系统默认中文字体
            if not os.path.exists(font_path):
                # 尝试使用常见的中文字体路径（Windows 示例）
                system_font_path = "C:/Windows/Fonts/simhei.ttf"
                if os.path.exists(system_font_path):
                    return ImageFont.truetype(system_font_path, size)
                else:
                    self.log_message.emit("⚠️ 未找到指定的中文字体文件，将使用默认字体")
                    return ImageFont.load_default()
            return ImageFont.truetype(font_path, size, encoding="utf-8")
        except Exception as e:
            self.log_message.emit(f"⚠️ 加载字体失败: {str(e)}，使用默认字体")
            return ImageFont.load_default()

    def get_class_color(self, class_id):
        """生成基于类别的确定性颜色"""
        colors = [
            (255, 0, 0), (0, 255, 0), (0, 0, 255),
            (255, 255, 0), (0, 255, 255), (255, 0, 255),
            (128, 0, 0), (0, 128, 0), (0, 0, 128)
        ]
        return colors[class_id % len(colors)]

    def resume(self):
        with QMutexLocker(self.mutex):
            self.paused = False
            self.wait_condition.wakeOne()