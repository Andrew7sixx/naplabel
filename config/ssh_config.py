import paramiko
from config.db_config import db_config

def get_db_connection():
    import mysql.connector  # 确保已安装mysql-connector-python
    return mysql.connector.connect(
        host=db_config.HOST,
        port=db_config.PORT,
        user=db_config.USER,
        password=db_config.PASSWORD,
        database=db_config.DATABASE
    )

class ssh_config:
    # 连接参数
    HOST = "39.108.104.215"  # 服务器IP/域名
    PORT = 22  # SSH端口（默认为22）
    USER = "root"  # 登录用户名
    PASSWORD = "Qwertyuiop123456"  # 登录密码

    # 服务器路径配置
    BASE_PATH = "/home/project"  # 服务器上的工作根目录
    UPLOAD_FOLDER = "uploads"  # 默认上传目录名称

    @staticmethod
    def update_user_balance(account, new_balance):
        """更新数据库中的标注余额"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # 执行带参数化查询的更新语句
            update_query = """
                    UPDATE user_info 
                    SET rectangle_remaining = %s 
                    WHERE account = %s
                """
            cursor.execute(update_query, (new_balance, account))

            # 验证受影响行数
            if cursor.rowcount == 0:
                raise ValueError(f"未找到账户: {account}")

            conn.commit()
            return True

        except Exception as e:
            if conn:
                conn.rollback()
            raise RuntimeError(f"数据库更新失败: {str(e)}") from e
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    @staticmethod
    def create_remote_user_directory(account_dir):
        """在服务器上创建用户临时目录"""
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ssh_config.HOST, ssh_config.PORT, ssh_config.USER, ssh_config.PASSWORD)
            sftp = ssh.open_sftp()

            base_path = f"{ssh_config.BASE_PATH}/account_temp/{account_dir}"
            for folder in ['', '/img', '/label']:
                try:
                    sftp.mkdir(base_path + folder)
                except IOError:
                    pass  # 文件夹已存在
            sftp.close()
            ssh.close()
            return True
        except Exception as e:
            print(f"创建目录失败: {str(e)}")
            return False

    @staticmethod
    def create_remote_normal_directory(account):
        """在服务器上创建用户普通目录"""
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ssh_config.HOST, ssh_config.PORT, ssh_config.USER, ssh_config.PASSWORD)
            sftp = ssh.open_sftp()

            # 确保account_normal目录存在
            base_dir = f"{ssh_config.BASE_PATH}/account_normal"
            try:
                sftp.mkdir(base_dir)
            except IOError:
                pass  # 父目录已存在

            # 创建用户专属目录
            user_dir = f"{base_dir}/{account}_normal"
            try:
                sftp.mkdir(user_dir)
            except IOError:
                pass  # 用户目录已存在

            sftp.close()
            ssh.close()
            return True
        except Exception as e:
            print(f"创建普通目录失败: {str(e)}")
            return False