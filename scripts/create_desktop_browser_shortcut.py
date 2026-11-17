import pylnk3
from pathlib import Path

target_exe = r"D:\Tools\AliasMode\firefox\aliasmode.exe"
profile_dir = r"C:\Users\kami\.gemini\antigravity\scratch\XHS_ALL_IN_ONE\data\xhs_camoufox_profile"
url = "https://creator.xiaohongshu.com/publish/publish"
arguments = f'-profile "{profile_dir}" "{url}"'
desktop_lnk = r"C:\Users\kami\Desktop\小红书防封浏览器.lnk"

lnk = pylnk3.for_file(
    target_exe,
    lnk_name=desktop_lnk,
    arguments=arguments,
    description="小红书 AliasMode 防封浏览器（扫码登录与免密环境）",
    icon_file=target_exe
)
lnk.save()
print(f"Created shortcut at: {desktop_lnk}")
