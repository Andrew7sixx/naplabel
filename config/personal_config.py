# 顶部信息栏样式
info_widget_style = """
    QWidget {
        background-color: #F0F8FF;
        border-bottom: 1px solid #ccc;
        padding: 0px 0px;
    }
"""

# 顶部信息栏内标签样式
info_widget_label_style = """
    QLabel {
        font-size: 24px;
        color: black;
        margin: 0 0px;
        background-color: #F0F8FF;
        min-width: 150px;
        min-height: 20px;
        text-align: center;
        border-radius: 5px;
    }
"""

# 左侧菜单栏样式
menu_widget_style = """
    QWidget {
        background-color: #e0e0e0;
        border-right: 1px solid #ccc;
    }
"""

# 左侧菜单栏内按钮通用样式
menu_widget_button_style = """
    QPushButton {
        background-color: #0099FF;
        color: white;
        border: none;
        border-radius: 12px;
        padding: 10px 0px;
        font-size: 14px;
        height: 14px;
        text-align: center;
        transition: background-color 0.3s ease;
        margin: 5px;
    }
    QPushButton:hover {
        background-color: #007BFF;
    }
"""

# 客服反馈按钮样式
customer_feedback_button_style = """
    QPushButton {
        background-color: transparent;  /* 背景透明 */
        color: blue;
        border: none;  /* 边框透明（无绘制） */
        border-radius: 12px;
        padding: 12px 24px;
        font-size: 20px;
        height: 24px;
        text-align: center;
        transition: background-color 0.3s ease;
        margin: 5px;
    }
    QPushButton:hover {
        background-color: #F3F2F2;
    }
"""

# 表格样式
table_widget_style = """
    QTableWidget {
        border: 1px solid #ccc;
        border-radius: 8px;
        background-color: white;
        font-size: 14px;
        gridline-color: #e0e0e0;
        outline: none;
    }
    QTableWidget::item {
        padding: 8px;
        border: none;
    }
    QTableWidget::item:selected {
        background-color: #e6f2ff;
        color: #333;
        border: none;
    }
"""

# 表格水平表头样式
table_widget_horizontal_header_style = """
    QHeaderView::section {
        background-color: #f5f8ff;
        color: black;
        font-size: 14px;
        font-weight: medium;
        border-bottom: 1px solid #e0e0e0;
    }
"""

# 表格垂直表头样式
table_widget_vertical_header_style = """
    QHeaderView::section {
        background-color: #f5f8ff;
        color: #333;
        font-size: 14px;
        border-right: 1px solid #e0e0e0;
    }
"""

# 个人中心标题样式
center_title_style = """
    QLabel {
        font-size: 20px;
        font-weight: bold;
        color: #333;
        height: 100%;
        display: flex;
        align-items: center;
        margin-left: 10px;
    }
"""

# 账号信息文本样式
account_info_text_style = """
    QLabel {
        background-color: #0099FF;
        color: white;
        border: none;
        border-radius: 12px;
        padding: 10px 0px;
        font-size: 14px;
        height: 14px;
        text-align: center;
        transition: background-color 0.3s ease;
        margin: 5px;
    }

"""

### 历史标注记录页面
# 搜索框样式
search_box_style = """
    QLineEdit {
        background-color: white;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 8px;
        font-size: 14px;
    }
"""

# 表格标题标签样式
# 直接设置样式：字体大小 16px、加粗、颜色深蓝色
title_label_style = """
            font-size: 24px;
            font-weight: meduim;
            color: blcak;
            margin-bottom: 10px;  /* 标题与下方组件的间距 */
            hover: red
    """

# 定义 QMessageBox 的样式，设置文字大小为 16px
message_box_text_style = """
    QLabel {
        font-size: 16px;
    }
"""