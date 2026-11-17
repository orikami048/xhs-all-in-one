import json
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.core.database import SessionLocal
from backend.app.models import User, PublishJob, PublishAsset
from backend.app.api.publish import publish_job_to_creator, get_creator_publish_adapter_factory

def main():
    title = "发大视频总卡死？开源神器一句话无损压制"

    body = (
        "谁懂周五晚上9点58分，老板突然在群里艾特你发视频的绝望……\n\n"
        "活动刚结束，手机随手拍的现场 4K 视频整整 480MB。往聊天软件对话框一拖，直接弹出冷冰冰的红感叹号：“无法发送超过限制的超大视频”。\n\n"
        "以前我的渡劫循环：\n"
        "1. 搜“免费在线压缩”：排队两分钟，压缩完要下载，跳出弹窗“充值 19.9 元去水印 VIP”，还把公司内部未公开视频传到了不知名云端服务器；\n"
        "2. 咬牙开剪映或 PR：启动转圈半天，风扇呼啸像起飞，到处找导出设置，导出一半电脑卡死弹出“应用无响应”，咖啡凉了，整个人都麻了。\n\n"
        "直到我换了 GitHub 上的开源神器 ffmpeg-skill……\n"
        "不用装几个 G 的臃肿软件，不用花一分钱，完全在本地跑。直接拖进终端对 AI 说一句话：\n"
        "“@ffmpeg 帮我压到 20MB 以内群聊秒发，保留 1080P 画质，切掉前 3 秒黑屏”\n\n"
        "底层秒级跑完，2.3 秒搞定，大小精准卡在 19.2MB，画质丝滑清晰！直接秒发，关电脑准时下班！\n\n"
        "三个打工人每天都在用的杀手级功能：\n"
        "1️⃣ 无痛保真极速压缩：输入目标大小（比如 20M / 90M），自动计算最优码率，清晰度吊打在线网页。\n"
        "2️⃣ 秒级无损切片：不用重新渲染，直接指定时间切片，1秒出片，画质零损失。\n"
        "3️⃣ 提取纯音频/转GIF表情包：一句话抽离会议录音 mp3，或者把精彩镜头转成超清动图。\n\n"
        "小白安装与使用方法：\n"
        "• 底层引擎安装（完全免费开源）：\n"
        "  - Windows：打开 PowerShell 运行 winget install Gyan.FFmpeg\n"
        "  - Mac：终端运行 brew install ffmpeg\n"
        "• 搭配任何 AI 编程/Agent 助手（如 Antigravity / Cursor / Claude Code），挂载开源 ffmpeg-skill，即可用日常大白话调动所有音视频功能。\n\n"
        "💡 打工人避坑经验：\n"
        "1. 压视频记得跟 AI 提一句“用通用兼容编码（H.264 + AAC）”，避免部分老机型点开黑屏。\n"
        "2. 文件名和路径尽量别带奇怪的特殊符号，纯本地处理，速度极快还不泄露任何隐私！\n\n"
        "大家平时还被哪些臃肿软件折磨（比如转换格式、去水印、提取文字）？评论区告诉我，下期继续深扒能一键平替的开源宝藏神器~"
    )

    tags = ["开源实用AI工具提效", "AI工具", "生产力工具", "高效办公", "打工人日常", "实用小工具", "GitHub开源"]

    db = SessionLocal()
    user = db.get(User, 1)

    publish_options = {
        "topics": tags,
        "draft_tags": [{"id": "", "name": t} for t in tags],
        "is_private": False,
        "privacy_type": 0,
        "location": "上海"
    }

    job = PublishJob(
        platform_account_id=2,
        platform="xhs",
        title=title,
        body=body,
        publish_mode="immediate",
        publish_options=json.dumps(publish_options, ensure_ascii=False),
        status="pending",
        user_id=1
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    print(f"Created Job ID: {job.id}", flush=True)

    asset = PublishAsset(
        publish_job_id=job.id,
        asset_type="image",
        file_path="/api/files/media/ffmpeg_skill_scene.jpg",
        upload_status="pending",
        creator_media_id="",
        upload_error="",
        creator_upload_info="{}"
    )
    db.add(asset)
    db.commit()
    print(f"Created Asset ID: {asset.id}", flush=True)

    print("Publishing job to Xiaohongshu Creator API...", flush=True)
    try:
        res = publish_job_to_creator(
            job_id=job.id,
            current_user=user,
            db=db,
            adapter_factory=get_creator_publish_adapter_factory()
        )
        print("PUBLISH SUCCESS!", flush=True)
        print(f"External Note ID: {res.get('external_note_id')}", flush=True)
        print(f"Published At: {res.get('published_at')}", flush=True)
        print(f"Status: {res.get('status')}", flush=True)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
