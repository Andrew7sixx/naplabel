# # anno_config.py
# -------laojiang
# anno_config.py

### 改4.2
# 按钮样式
button_style = """
    QPushButton {
        background-color: rgba(0, 180, 247, 0.8);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-size: 13px;
        height: 13px
    }
    QPushButton:hover {
        background-color: rgba(0, 180, 247, 0.5);
    }
"""
###

# 标签样式
label_style = """
    QLabel {
        background-color: white;
        border-radius: 8px;
        padding: 8px 12px;
        font-weight: medium;
        font-size: 16px;
        width: 78px
    }
"""

# 任务文件标签样式
task_file_label_style = """
    QLabel {
        background-color: #E0E0E0;
        border: None;
        border-radius: 8px;
        padding: 8px 12px;
        font-weight: bold;
        font-size: 17px;
        color: #333;
        font-family: "Arial";
        font-style: Normal
    }
"""

# 任务文件下拉框样式
task_file_combo_style = """
    QComboBox {
        background-color: white;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 8px;
        font-size: 14px;
    }
"""

# 顶部状态栏容器样式
status_bar_container_style = """
    background-color: #828282;
    color: white;
    font-size: 14px;
"""

# 标注日志标签样式
log_info_label_style = """
    color: #555555;
    font-size: 12px;
    padding-bottom: 5px;
"""

# 进度条样式
progress_bar_style = """
    QProgressBar {
        border: 1px solid #ccc;
        border-radius: 8px;
        background-color: #FFFFFF;
        height: 15px;
    }
    QProgressBar::chunk {
        background-color: #00B4F7;
        border-radius: 5px;
    }
"""

# 搜索框样式
search_line_edit_style = """
    QLineEdit {
        background-color: white;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 8px;
        font-size: 14px;
    }
"""

# 类别下拉框样式
class_combo_style = """
    QComboBox {
        background-color: white;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 8px;
        font-size: 14px;
    }
"""

# 日志信息栏样式
log_text_edit_style = """
    QTextEdit {
        background-color: white;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 8px;
        font-size: 14px;
    }
"""

# 退出程序按钮样式
exit_button_style = """
    QPushButton {
        background-color: #FF3030;
        color: white;
        border: none;
        border-radius: 14px;
        padding: 12px 24px;
        font-size: 16px;
        font-family: "Arial";
        height: 24px;
    }
    QPushButton:hover {
        background-color: #B90505;
    }
"""

# 单独为“开始标注”按钮定义的样式（含尺寸调整）
start_button_style = """
    QPushButton {
        background-color: rgba(0, 180, 247, 0.8);
        color: white;
        border: none;
        border-radius: 14px;
        padding: 12px 24px;
        font-size: 16px;
        font-family: "Arial";
        height: 24px;
    }
    QPushButton:hover {
        background-color: rgba(0, 180, 247, 0.5);
    }
"""

# 添加返回登录按钮样式，复用标注按钮样式
back_to_login_button_style = start_button_style

# 窗口标题和固定大小
window_title = "Nap-Label_Auto-annotation"

# 顶部状态栏容器高度
status_bar_container_height_ratio = 0.05 ### 改4.2

# 左侧边栏宽度
left_sidebar_width = 210

# 日志信息栏最小尺寸
log_text_edit_min_size = (180, 150)

# 进度条最小尺寸
progress_bar_min_size = (180, 20)

# 可搜索的类别下拉框固定宽度
class_combo_fixed_width = 200

# 底部任务栏固定高度
task_bar_fixed_height = 40  ### 改4.2

# 日志标题样式
log_title_style = """
    QLabel {
        background-color: #454545;
        color: white;
        border-radius: 8px;
        padding: 8px 12px;
        font-weight: bold;
        font-size: 16px;
    }
"""

# 用户信息悬浮框样式
user_info_popup_style = """
    QWidget {
        background-color: white;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 10px;
    }
    QLabel {
        background-color: transparent;
        font-size: 14px;
    }
"""

# 用户信息悬浮框的宽度和高度
user_info_popup_width = 256
user_info_popup_height = 256

# 新增容器样式
right_container_style = """
    QWidget {
        background-color: white;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 0px;
    }
"""

# 新的信息框样式
new_info_box_style = """
    QLabel {
        background-color: #F7F7F7;  /* 背景颜色为浅灰色 */
        border: 1px solid #828282;  /* 边框颜色为深灰色 */
        border-radius: 8px;        /* 圆角半径 */
        padding: 2px;             /* 内边距 */
        font-size: 16px;           /* 字体大小 */
        color: #333;               /* 字体颜色为深灰色 */
        min-width: 150px;          /* 最小宽度 */
        min-height: 35px;          /* 最小高度 */
        max-height:35px
    }
"""

# 充值和兑换按钮样式
recharge_exchange_button_style = """
    QPushButton {
        background-color: rgba(0, 180, 247, 0.8);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px;
        font-size: 16px;
    }
    QPushButton:hover {
        background-color: rgba(0, 180, 247, 0.5);
    }
"""

# 新增右侧容器宽度
right_container_width = 200

# 新增右侧容器文本框样式
info_label_style = """
    QLabel {
        background-color: #F7F7F7;
        border: 1px solid #828282;
        border-radius: 8px;
        padding: 10px;
        font-size: 16px;  /* 设置字体大小为 16px */
        min-height: 30px;
        min-width: 60px;
    }
"""

# anno_config.py

# 进入个人中心按钮样式
go_to_personal_center_button_style = """
    QPushButton#go_to_personal_center {
        background-color: rgba(0, 180, 247, 0.8);
        color: white;

        border-radius: 8px;
        padding: 0px 0px;
        font-size: 16px;
        width: 160px;
        height: 36px;
        margin-left: 14px;
        margin-right: 14px;
        margin-bottom: 0;
        margin-top: 0
    }
    QPushButton#go_to_personal_center:hover {
        background-color: rgba(0, 180, 247, 0.5);

    }
"""

# 下拉菜单样式
dropdown_menu_style = """
    QMenu {
        background-color: white;
        border: 1px solid #ccc;
        min-width: 200px;  /* 菜单栏最小宽度 */
        min-height: 220px; /* 菜单栏最小高度 */
    }
    QLabel {
        padding: 5px;
    }
    QPushButton {
        padding: 8px;
    }
    QProgressBar {
        padding: 2px;
    }
    QFrame {
        margin: 5px 0;
    }
"""

# 手动标注按钮样式（蓝色）
manual_annotation_button_style = """
    QPushButton {
        background-color: rgba(0, 180, 247, 0.8);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 2px;
        font-size: 18px;
    }
    QPushButton:hover {
        background-color: rgba(0, 180, 247, 0.5);
    }
"""

exchange_dialog_style = """
    QDialog {
        background-color: #ffffff;
        border: 1px solid #cccccc;
    }
    QLabel {
        color: #333333;
        font-size: 14px;
    }
    QLineEdit {
        border: 1px solid #cccccc;
        padding: 5px;
        border-radius: 3px;
    }
    QPushButton {
        background-color: #4CAF50;
        color: white;
        padding: 8px;
        border-radius: 4px;
    }
"""