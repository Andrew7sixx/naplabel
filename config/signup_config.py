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

# 登录页面副标题样式
login_sub_title_style = """
    #SubTitle {
        color: #000000;
        font-size: 24px;
        font-family: 'Arial';
        font-weight: bold;
        margin: 0px;
        qproperty-alignment: AlignCenter;
    }
"""

# 注册页面副标题样式
signup_sub_title_style = """
    #SubTitle {
        color: #000000;
        font-size: 18px;
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

# 账号/用户名/手机号码输入框样式
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

# 验证码输入框样式
verification_code_edit_style = """
    QLineEdit {
        font-size: 14px;
        font-weight: medium;
        padding: 10px;  # 与按钮的 padding 一致
        border: 4px solid #00BBFF;
        border-radius: 8px;
        font-family:'Arial';
        width: 25%;
        height: auto;  # 自动调整高度
        box-sizing: border-box;  # 确保 padding 和 border 包含在高度内
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

# 登录/注册按钮样式
button_style = """
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

# 发送验证码按钮样式
send_verification_code_button_style = """
    QPushButton {
        background-color: rgba(0, 187, 255, 0.8);
        color: white;
        font-weight: medium;
        font-size: 14px;
        padding: 5px;
        border-radius: 8px;
        margin-top: 0px;
        width: 75%;
        height:25px
    }
    QPushButton:hover {
        background-color: rgba(0, 187, 255, 0.5);
    }
"""

# 扫码登录/返回登录标签样式
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

# 返回登录按钮样式
back_button_style = """
    QPushButton {
        font-size: 16px;
        font-weight: medium;
        color: #333333; /* 字体颜色 */
        border-radius: 8px; /* 边框圆角 */
        padding: 8px 16px; /* 内边距 */
    }
    QPushButton:hover {
        background-color: #e0e0e0; /* 鼠标悬停时的背景颜色 */
    }
"""