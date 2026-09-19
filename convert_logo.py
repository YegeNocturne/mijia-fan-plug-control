import os

from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
Image.open(os.path.join(BASE_DIR, "logo.png")).save(
    os.path.join(BASE_DIR, "logo.ico"),
    format="ICO",
    sizes=[(16, 16), (24, 24), (32, 32), (48, 48)],
)
print("logo.ico 已生成")