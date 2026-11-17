import json
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.core.database import SessionLocal
from backend.app.models import User, PublishJob, PublishAsset
from backend.app.api.publish import publish_job_to_creator, get_creator_publish_adapter_factory

def main():
    title = "左手冰美式右手陈皮水？当代脆皮人自救🌿"

    body = (
        "不瞒你们说，照片里背景那杯贴着“多冰”的冷饮，就是我今天早上下单的“罪证”……"
        "明明知道自己是寒湿体质，早晨起来眼皮微肿、舌苔厚腻齿痕明显，但下午一犯困，还是下意识想靠冰饮续命。\n\n"
        "后来一位学中医的朋友一句话把我点醒：“你每天往胃里灌冰水，中焦本来就虚弱的那点脾阳全被你生生浇灭了。"
        "脾胃运化不动水湿，你肚子不鼓鼓囊囊、整天昏昏沉沉才怪！”\n\n"
        "从那之后，我把工位的冷水杯换成了这碗温润理气的陈皮水。喝了快一个月，整个人通透太多，分享这套亲测最省心的工位自救方：\n\n"
        "1️⃣ 经典温润基底：新会老陈皮 5g + 炒白术 8g\n"
        "千万别买劣质硫熏陈皮，选 5 年以上干仓新会陈皮，表面油胞丰富、气味醇香。配上炒白术，慢冲慢饮，专门化解中焦痰湿，帮脾胃“把困住的水排出去”，喝完全身是暖暖的包裹感。\n\n"
        "2️⃣ 容易腹胀打嗝：加 2 小片新鲜老姜\n"
        "如果平时容易受凉腹泻、吃一点凉的就胃痛，在杯里加两片薄生姜。辛温散寒、温中和胃，那股辛香顺着喉咙下去，瞬间打通全身气机。\n\n"
        "3️⃣ 工位极简泡法避坑：\n"
        "不要直接拿 100 度滚水把陈皮当茶叶闷死，稍微静置成 85 度左右的温热水冲泡。前两泡醒皮倒掉，第三泡开始汤色金黄澄亮，一小壶可以续水喝一整个下午。\n\n"
        "💡 亲测真实体感：\n"
        "最明显的变化是，下午四点不再习惯性胃胀反酸，早晨起来嘴巴苦黏的感觉轻了大半，最重要的是肚子没有以前那么硬邦邦了。身体真的会用舒服来回报你的每一次克制。\n\n"
        "⚠️ 走心避坑与免责：\n"
        "- 舌苔黄厚、经常口舌生疮、咽干便干的湿热/阴虚体质慎喝（陈皮性温，容易加重内热）。\n"
        "- 本文仅为个人日常茶饮调养与古籍研读心得分享，不构成任何医疗诊断或用药处方，身体明显不适请务必前往正规医疗机构辨证就医。\n\n"
        "大家平时在工位最爱喝什么自救续命？是冰美式还是养生壶？评论区互相抄抄作业🍵"
    )

    tags = ["中医养生", "工位养生", "新会陈皮", "健脾祛湿", "当代打工人", "自学中医", "生活需要仪式感"]

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
        file_path="/api/files/media/office_chenpi_tea_lifestyle.jpg",
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
