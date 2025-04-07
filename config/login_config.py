# login_config.py

# 标题容器样式
title_container_style = """
    #TitleContainer {
        background-color: #454545;
        width: 100%;
    }
"""

# 主标题样式
main_title_style = """
    #MainTitle {
        color: white;
        font-size: 32px;
        font-family: 'Arial';
        font-weight: bold;
        qproperty-alignment: AlignCenter;
    }
"""

# 副标题样式
sub_title_style = """
    #SubTitle {
        color: #000000;
        font-size: 24px;
        font-family: 'Arial';
        font-weight: bold;
        margin: 0px;
        qproperty-alignment: AlignCenter;
    }
"""

# 描述文字样式
desc_label_style = """
    QLabel {
        color: #828282;
        font-size: 16px;
        font-weight: medium;
        qproperty-alignment: AlignCenter;
    }
"""

# 账号输入框样式
account_edit_style = """
    QLineEdit {
        font-size: 14px;
        font-weight: medium;
        padding: 8px;
        border: 2px solid #E0E0E0;
        border-radius: 8px;
        font-family:'Arial'
    }
"""

# 密码输入框样式
password_edit_style = """
    QLineEdit {
        font-size: 14px;
        font-weight: medium;
        padding: 8px;
        border: 2px solid #E0E0E0;
        border-radius: 8px;
        font-family:'Arial'
    }
"""

# 协议勾选框样式
agreement_check_style = """
    QCheckBox {
        font-size: 14px;
        font-weight: medium;
        color: #454545;
        spacing: 5px;
        font-family:'Arial'
    }
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
    }
"""

# 登录按钮样式
login_button_style = """
    QPushButton {
        background-color: rgba(0, 187, 255, 0.8);
        color: white;
        font-weight: medium;
        font-size: 20px;
        padding: 10px;
        border-radius: 8px;
        margin-top: 15px;
    }
    QPushButton:hover {
        background-color: rgba(0, 187, 255, 0.5);
    }
"""

# 扫码登录标签样式
scan_login_style = """
    QLabel {
        color: #000000;
        font-size: 16px;
        font-weight: medium;
        background-color: #EEEEEE;
        padding: 5px 10px;
        border-radius: 8px;
        font-family: 'Arial'
    }
    QLabel:hover {
        background-color: #E4E5E5;
    }
"""

# 更多选项标签样式
more_options_style = """
    QLabel {
        color: #000000;
        font-size: 16px;
        font-weight: medium;
        background-color: #EEEEEE;
        padding: 5px 10px;
        border-radius: 8px;
        font-family: 'Arial'
    }
    QLabel:hover {
        background-color: #E4E5E5;
    }
"""

# 更多选项菜单内标签样式，修改为与扫码登录样式一致
extra_options_label_style = """
    QLabel {
        color: #000000;
        font-size: 16px;
        font-weight: medium;
        background-color: #EEEEEE;
        padding: 5px 10px;
        border-radius: 8px;
        font-family: 'Arial'
    }
    QLabel:hover {
        background-color: #E4E5E5;
    }
"""

agreement_container_style = """
    QLabel {
        font-size: 12px;
        color: #666;
    }
    QLabel:hover { 
        color: #0056b3; 
    }
"""