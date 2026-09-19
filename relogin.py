import os
import shutil

from mijiaAPI import mijiaAPI

AUTH = os.path.expanduser("~/.config/mijia-api/auth.json")

if os.path.exists(AUTH):
    shutil.copy2(AUTH, AUTH + ".bak")
    os.remove(AUTH)
    print("旧认证数据已备份为 auth.json.bak 并移除")

api = mijiaAPI()
api.QRlogin()
print("重新登录完成。")
input("按回车键退出...")