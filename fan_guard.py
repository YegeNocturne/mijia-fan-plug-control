import ctypes
import ctypes.wintypes as wt
import datetime
import io
import json
import os
import subprocess
import sys
import threading
import time

if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()

WM_QUERYENDSESSION = 0x0011
WM_ENDSESSION = 0x0016
WM_DESTROY = 0x0002
WM_LBUTTONUP = 0x0202
WM_LBUTTONDBLCLK = 0x0203
WM_RBUTTONUP = 0x0205
WM_TRAYICON = 0x8001

NIM_ADD = 0
NIM_DELETE = 2
NIF_MESSAGE = 1
NIF_ICON = 2
NIF_TIP = 4
IDI_APPLICATION = 32512
IMAGE_ICON = 1
LR_LOADFROMFILE = 0x00000010
TPM_RIGHTBUTTON = 0x0002
TPM_RETURNCMD = 0x0100
MF_STRING = 0
CREATE_NEW_CONSOLE = 0x00000010
CREATE_NO_WINDOW = 0x08000000

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "fan_guard.log")
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
AUTH_PATH = os.path.expanduser("~/.config/mijia-api/auth.json")
PYTHON_EXE = sys.executable.replace("pythonw.exe", "python.exe")

DEFAULT_CONFIG = {
    "ssid_prefix": "RainOfChaos",
    "device_name": "散热器插座",
    "log_enabled": False,
}

CONFIG = dict(DEFAULT_CONFIG)


def log(msg):
    if not CONFIG.get("log_enabled"):
        return
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} {msg}\n")
    except Exception:
        pass


def load_config():
    global CONFIG
    try:
        if not os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=2)
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        CONFIG = {
            "ssid_prefix": str(data.get("ssid_prefix", DEFAULT_CONFIG["ssid_prefix"])),
            "device_name": str(data.get("device_name", DEFAULT_CONFIG["device_name"])),
            "log_enabled": bool(data.get("log_enabled", DEFAULT_CONFIG["log_enabled"])),
        }
        return True
    except Exception as e:
        log("读取配置失败 %s" % e)
        return False


def get_current_ssid():
    try:
        out = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True,
            timeout=15,
            creationflags=CREATE_NO_WINDOW,
        )
        text = (out.stdout or b"").decode("gbk", errors="ignore")
        for line in text.splitlines():
            s = line.strip()
            if s.lower().startswith("ssid"):
                return s.split(":", 1)[1].strip()
    except Exception as e:
        log("获取 SSID 失败 %s" % e)
    return ""


def set_plug(on):
    try:
        from mijiaAPI import mijiaAPI, mijiaDevice
        api = mijiaAPI()
        device = mijiaDevice(api, dev_name=CONFIG["device_name"], sleep_time=0)
        device.on_2 = bool(on)
        log("插座状态已设置 on=%s" % on)
        return True
    except Exception as e:
        log("设置插座失败 %s" % e)
        return False


def do_shutdown_guard(_done):
    set_plug(False)
    log("关闭指令处理完毕")
    _done.set()


user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
shell32 = ctypes.WinDLL("shell32", use_last_error=True)

LONG_PTR = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(LONG_PTR, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", wt.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wt.HINSTANCE),
        ("hIcon", wt.HICON),
        ("hCursor", wt.HANDLE),
        ("hbrBackground", wt.HBRUSH),
        ("lpszMenuName", wt.LPCWSTR),
        ("lpszClassName", wt.LPCWSTR),
    ]


class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wt.DWORD),
        ("hWnd", wt.HWND),
        ("uID", wt.UINT),
        ("uFlags", wt.UINT),
        ("uCallbackMessage", wt.UINT),
        ("hIcon", wt.HICON),
        ("szTip", wt.WCHAR * 128),
        ("dwState", wt.DWORD),
        ("dwStateMask", wt.DWORD),
        ("szInfo", wt.WCHAR * 256),
        ("uVersion", wt.UINT),
        ("szInfoTitle", wt.WCHAR * 64),
        ("dwInfoFlags", wt.DWORD),
    ]


ShutdownBlockReasonCreate = user32.ShutdownBlockReasonCreate
ShutdownBlockReasonCreate.argtypes = [wt.HWND, wt.LPCWSTR]
ShutdownBlockReasonCreate.restype = wt.BOOL
ShutdownBlockReasonDestroy = user32.ShutdownBlockReasonDestroy
ShutdownBlockReasonDestroy.argtypes = [wt.HWND]
ShutdownBlockReasonDestroy.restype = wt.BOOL
DefWindowProcW = user32.DefWindowProcW
DefWindowProcW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
DefWindowProcW.restype = LONG_PTR
GetModuleHandleW = kernel32.GetModuleHandleW
GetModuleHandleW.argtypes = [wt.LPCWSTR]
GetModuleHandleW.restype = wt.HINSTANCE
RegisterClassW = user32.RegisterClassW
RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
RegisterClassW.restype = wt.ATOM
CreateWindowExW = user32.CreateWindowExW
CreateWindowExW.argtypes = [
    wt.DWORD, wt.LPCWSTR, wt.LPCWSTR, wt.DWORD,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    wt.HWND, wt.HANDLE, wt.HINSTANCE, wt.LPVOID,
]
CreateWindowExW.restype = wt.HWND
CreateMutexW = kernel32.CreateMutexW
CreateMutexW.argtypes = [wt.LPVOID, wt.BOOL, wt.LPCWSTR]
CreateMutexW.restype = wt.HANDLE
GetMessageW = user32.GetMessageW
GetMessageW.argtypes = [ctypes.POINTER(wt.MSG), wt.HWND, wt.UINT, wt.UINT]
GetMessageW.restype = wt.BOOL
TranslateMessage = user32.TranslateMessage
TranslateMessage.argtypes = [ctypes.POINTER(wt.MSG)]
TranslateMessage.restype = wt.BOOL
DispatchMessageW = user32.DispatchMessageW
DispatchMessageW.argtypes = [ctypes.POINTER(wt.MSG)]
DispatchMessageW.restype = LONG_PTR
DestroyWindow = user32.DestroyWindow
DestroyWindow.argtypes = [wt.HWND]
DestroyWindow.restype = wt.BOOL
PostQuitMessage = user32.PostQuitMessage
PostQuitMessage.argtypes = [ctypes.c_int]
SetForegroundWindow = user32.SetForegroundWindow
SetForegroundWindow.argtypes = [wt.HWND]
SetForegroundWindow.restype = wt.BOOL
GetCursorPos = user32.GetCursorPos
GetCursorPos.argtypes = [ctypes.POINTER(wt.POINT)]
GetCursorPos.restype = wt.BOOL
CreatePopupMenu = user32.CreatePopupMenu
CreatePopupMenu.restype = wt.HMENU
AppendMenuW = user32.AppendMenuW
AppendMenuW.argtypes = [wt.HMENU, wt.UINT, ctypes.c_size_t, wt.LPCWSTR]
AppendMenuW.restype = wt.BOOL
TrackPopupMenu = user32.TrackPopupMenu
TrackPopupMenu.argtypes = [wt.HMENU, wt.UINT, ctypes.c_int, ctypes.c_int, ctypes.c_int, wt.HWND, wt.LPVOID]
TrackPopupMenu.restype = ctypes.c_int
DestroyMenu = user32.DestroyMenu
DestroyMenu.argtypes = [wt.HMENU]
DestroyMenu.restype = wt.BOOL
LoadIconW = user32.LoadIconW
LoadIconW.argtypes = [wt.HINSTANCE, wt.LPVOID]
LoadIconW.restype = wt.HICON
Shell_NotifyIconW = shell32.Shell_NotifyIconW
Shell_NotifyIconW.argtypes = [wt.DWORD, ctypes.POINTER(NOTIFYICONDATAW)]
Shell_NotifyIconW.restype = wt.BOOL
LoadImageW = user32.LoadImageW
LoadImageW.argtypes = [wt.HINSTANCE, wt.LPCWSTR, wt.UINT, ctypes.c_int, ctypes.c_int, wt.UINT]
LoadImageW.restype = wt.HICON

_nid = None
panel_lock = threading.Lock()


@WNDPROC
def wnd_proc(hwnd, msg, wparam, lparam):
    if msg == WM_TRAYICON:
        if lparam in (WM_LBUTTONUP, WM_LBUTTONDBLCLK):
            open_panel()
        elif lparam == WM_RBUTTONUP:
            show_tray_menu(hwnd)
        return 0
    if msg == WM_QUERYENDSESSION:
        log("收到 WM_QUERYENDSESSION，开始拦截")
        reason = ctypes.create_unicode_buffer("正在关闭散热器智能插座，请稍候...")
        ShutdownBlockReasonCreate(hwnd, reason)
        done = threading.Event()
        threading.Thread(target=do_shutdown_guard, args=(done,), daemon=True).start()
        done.wait(timeout=45)
        ShutdownBlockReasonDestroy(hwnd)
        log("任务完成，放行关机")
        return 1
    if msg == WM_ENDSESSION and wparam:
        log("收到 WM_ENDSESSION（兜底）")
        done = threading.Event()
        threading.Thread(target=do_shutdown_guard, args=(done,), daemon=True).start()
        done.wait(timeout=45)
        return 0
    if msg == WM_DESTROY:
        if _nid is not None:
            Shell_NotifyIconW(NIM_DELETE, ctypes.byref(_nid))
        PostQuitMessage(0)
        return 0
    return DefWindowProcW(hwnd, msg, wparam, lparam)


def show_tray_menu(hwnd):
    hmenu = CreatePopupMenu()
    AppendMenuW(hmenu, MF_STRING, 1, "打开面板")
    AppendMenuW(hmenu, MF_STRING, 2, "退出")
    pt = wt.POINT()
    GetCursorPos(ctypes.byref(pt))
    SetForegroundWindow(hwnd)
    cmd = TrackPopupMenu(hmenu, TPM_RIGHTBUTTON | TPM_RETURNCMD, pt.x, pt.y, 0, hwnd, None)
    DestroyMenu(hmenu)
    if cmd == 1:
        open_panel()
    elif cmd == 2:
        log("用户通过托盘菜单退出")
        DestroyWindow(hwnd)


def auth_time_text():
    try:
        mtime = os.path.getmtime(AUTH_PATH)
        return datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
    except OSError:
        return "无（尚未登录）"


def open_panel():
    if not panel_lock.acquire(blocking=False):
        return
    threading.Thread(target=panel_main, daemon=True).start()


def panel_main():
    released = [False]

    def release():
        if not released[0]:
            released[0] = True
            panel_lock.release()

    try:
        import tkinter as tk
        root = tk.Tk()
        root.title("散热器插座守护")
        root.resizable(False, False)
        root.attributes("-topmost", True)

        info_var = tk.StringVar()
        status_var = tk.StringVar()

        tk.Label(root, textvariable=info_var, padx=18, pady=8).pack()
        tk.Label(root, textvariable=status_var, fg="#777777").pack()

        def refresh_info():
            info_var.set("上次授权 API 时间：" + auth_time_text())

        def on_open_config():
            try:
                os.startfile(CONFIG_PATH)
                status_var.set("已打开配置文件（编辑后请点击「重新读取配置」）")
            except Exception as e:
                status_var.set("打开失败 %s" % e)

        def on_reload_config():
            if load_config():
                status_var.set(
                    "已重载：SSID前缀=%s 设备=%s 日志=%s（SSID前缀下次启动生效）"
                    % (CONFIG["ssid_prefix"], CONFIG["device_name"], CONFIG["log_enabled"])
                )
            else:
                status_var.set("配置读取失败，请检查 config.json 格式")
            refresh_info()

        def on_relogin():
            status_var.set("已在新的命令行窗口启动重新登录，请扫码...")
            subprocess.Popen(
                [PYTHON_EXE, os.path.join(BASE_DIR, "relogin.py")],
                cwd=BASE_DIR,
                creationflags=CREATE_NEW_CONSOLE,
            )

        refresh_info()
        tk.Button(root, text="打开配置文件", width=20, command=on_open_config).pack(pady=3)
        tk.Button(root, text="重新读取配置", width=20, command=on_reload_config).pack(pady=3)
        tk.Button(root, text="重新登录认证", width=20, command=on_relogin).pack(pady=3)
        tk.Button(root, text="关闭窗口", width=20, command=root.destroy).pack(pady=(3, 10))

        def on_close():
            release()
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_close)
        root.mainloop()
    except Exception as e:
        log("面板异常 %s" % e)
    finally:
        release()


def get_tray_icon():
    ico = os.path.join(BASE_DIR, "logo.ico")
    hicon = LoadImageW(None, ico, IMAGE_ICON, 0, 0, LR_LOADFROMFILE)
    if hicon:
        return hicon
    log("加载托盘图标失败 code=%s" % ctypes.get_last_error())
    return LoadIconW(None, IDI_APPLICATION)


def run_watchdog():
    global _nid
    hinst = GetModuleHandleW(None)
    cls = WNDCLASSW()
    cls.lpfnWndProc = wnd_proc
    cls.lpszClassName = "FanGuardWin"
    cls.hInstance = hinst
    if not RegisterClassW(ctypes.byref(cls)):
        log("注册窗口类失败 code=%s" % ctypes.get_last_error())
        return
    hwnd = CreateWindowExW(
        0, "FanGuardWin", "FanGuard", 0, 0, 0, 0, 0,
        None, None, hinst, None,
    )
    if not hwnd:
        log("创建窗口失败 code=%s" % ctypes.get_last_error())
        return

    _nid = NOTIFYICONDATAW()
    _nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
    _nid.hWnd = hwnd
    _nid.uID = 1
    _nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
    _nid.uCallbackMessage = WM_TRAYICON
    _nid.hIcon = get_tray_icon()
    _nid.szTip = "散热器插座守护"
    if not Shell_NotifyIconW(NIM_ADD, ctypes.byref(_nid)):
        log("托盘图标添加失败 code=%s" % ctypes.get_last_error())

    log("fan_guard 已常驻 (pid=%s)" % os.getpid())
    msg = wt.MSG()
    while GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
        TranslateMessage(ctypes.byref(msg))
        DispatchMessageW(ctypes.byref(msg))


def main():
    mutex = CreateMutexW(None, False, "FanGuardSingleInstanceMutex")
    if ctypes.get_last_error() == 183:
        return

    load_config()

    ssid = ""
    for _ in range(8):
        ssid = get_current_ssid()
        if ssid:
            break
        time.sleep(5)

    if ssid and ssid.startswith(CONFIG["ssid_prefix"]):
        log("SSID [%s] 匹配前缀 %s，开启插座并常驻" % (ssid, CONFIG["ssid_prefix"]))
        set_plug(True)
        run_watchdog()
    else:
        log("SSID [%s] 不匹配 %s，关闭插座后退出" % (ssid, CONFIG["ssid_prefix"]))
        set_plug(False)


if __name__ == "__main__":
    main()