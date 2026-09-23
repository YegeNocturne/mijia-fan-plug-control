# fan-plug-control

控制笔记本电脑外置散热器的开关。散热器由米家智能插座供电，本程序在**电脑开机时开启插座（风扇启动）**、在**关机前关闭插座（风扇停止）**。

## 工作原理

1. 开机后 `fan_guard.py` 常驻运行，读取当前 WLAN SSID，与 `config.json` 中的 `ssid_prefix` 做前缀匹配。匹配则开启插座并继续常驻；不匹配则关闭插座并退出（例如不在家里时不启动散热器）。
2. 常驻期间注册 Windows 关机消息 `WM_QUERYENDSESSION`，收到关机请求时在进程内直连米家 API 关闭插座，完成后放行关机。

## 环境要求

- Windows 10 及以上
- Python 3（含 `tkinter`）
- [mijia-api](https://github.com/Do1e/mijia-api)

```bash
pip install mijia-api
```

## 文件说明

| 文件 | 说明 |
| --- | --- |
| `fan_guard.py` | 主程序：开机开启插座、常驻拦截关机消息并关闭插座 |
| `fan_guard_start.vbs` | 无窗口启动脚本，供开机自启使用 |
| `relogin.py` | 米家认证过期时重新扫码登录 |
| `config.json` | 本地配置（仓库内未包含，程序首次运行自动生成） |
| `logo.png` | 可选：自定义图标原图（仓库内未包含） |
| `logo.ico` | 可选：由 `logo.png` 生成的托盘图标（仓库内未包含） |
| `convert_logo.py` | 一次性脚本：由 `logo.png` 生成 `logo.ico` |

## 配置

`config.json`：

```json
{
  "ssid_prefix": "YourWLANSSID",
  "device_name": "散热器插座",
  "log_enabled": false
}
```

- `ssid_prefix`：家庭 WLAN 名称前缀，只有当前 SSID 以其开头时才开启插座
- `device_name`：米家 APP 中智能插座的设备名称
- `log_enabled`：是否写入 `fan_guard.log`，默认关闭

## 使用

1. 首次使用先登录米家账号（显示二维码，用米家 APP 扫码）：

   ```bash
   python relogin.py
   ```

   认证数据保存在 `~/.config/mijia-api/auth.json`，不在本项目目录内。

2. 按实际情况修改 `fan_guard_start.vbs` 中的 Python 解释器路径与脚本路径：

   ```vbs
   Set ws = CreateObject("WScript.Shell")
   ws.Run """C:\Python314\pythonw.exe"" ""D:\Program\fan-plug-control\fan_guard.py""", 0, False
   ```

3. 加入开机启动：按 `Win + R` 输入 `shell:startup` 打开启动文件夹，把 `fan_guard_start.vbs`（或其快捷方式）放进去即可。启动脚本以无窗口方式运行，启动后可在系统托盘看到图标。

4. 手动运行：双击 `fan_guard_start.vbs`，或执行 `pythonw fan_guard.py`。

托盘图标左键打开面板（可打开配置文件、重载配置、重新登录认证），右键菜单可退出。

## 自定义图标

图标为可选配置，仓库不包含图标文件：

- 没有 `logo.png` / `logo.ico` 时使用默认图标：托盘为系统默认应用图标，面板窗口为 tk 默认图标
- 需要自定义时，把图标图片命名为 `logo.png` 放到项目目录，执行：

  ```bash
  python convert_logo.py
  ```

  生成 `logo.ico` 后重启程序。托盘图标使用 `logo.ico`，面板窗口优先使用 `logo.png`（缺失时用 `logo.ico`）。

### 图标文件要求

- 文件名固定为 `logo.png`（原图）和 `logo.ico`（托盘图标），放在项目根目录（与 `fan_guard.py` 同级）
- `logo.png` 必须为 **PNG** 格式（tk 不识别 JPG/BMP 等），且必须为**正方形**，推荐 256×256；非正方形会被拉伸变形
- `logo.ico` 由 `convert_logo.py` 从 `logo.png` 生成，内含 16/24/32/48 四种尺寸
- 只提供 `logo.png` 而不生成 `logo.ico` 时，面板窗口图标生效，托盘图标仍为系统默认

`logo.png` 与 `logo.ico` 已加入 `.gitignore`，不会提交到仓库。

## 上游与致谢

- 插座控制基于 [Do1e/mijia-api](https://github.com/Do1e/mijia-api)，采用 GPL-3.0 许可

## 开源许可

本项目采用 [GNU General Public License v3.0](LICENSE)（GPL-3.0）许可，与上游 mijia-api 保持一致。

```
Copyright (C) 2026 YegeNocturne

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
```
