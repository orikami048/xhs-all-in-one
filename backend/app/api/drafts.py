from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from backend.app.core.config import get_settings
from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user
from backend.app.models import AiDraft, DraftAsset, Note, NoteAsset, PlatformAccount, PublishAsset, PublishJob, User
from backend.app.schemas.common import paginated

router = APIRouter(prefix="/drafts", tags=["drafts"])


class DraftCreateRequest(BaseModel):
    platform: str = Field(pattern="^xhs$")
    source_note_id: Optional[int] = None
    title: str = ""
    body: str = ""
    intent: str = Field(default="publish", max_length=32)


class DraftUpdateRequest(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    tags: Optional[list[dict]] = None


class DraftSendToPublishRequest(BaseModel):
    platform_account_id: Optional[int] = None
    publish_mode: str = Field(default="immediate", pattern="^(immediate|scheduled)$")
    scheduled_at: Optional[datetime] = None
    topics: Optional[list[str]] = None
    location: Optional[str] = None
    privacy_type: Optional[int] = Field(default=None, ge=0, le=1)
    is_private: Optional[bool] = None


def _clean_topics(topics: Optional[list[str]]) -> list[str]:
    if topics is None:
        return []
    return [topic.strip() for topic in topics if topic and topic.strip()]


def _build_publish_options(payload: DraftSendToPublishRequest) -> dict[str, Any]:
    options: dict[str, Any] = {}
    topics = _clean_topics(payload.topics)
    if topics:
        options["topics"] = topics
    if payload.location and payload.location.strip():
        options["location"] = payload.location.strip()
    if payload.is_private is not None:
        options["is_private"] = payload.is_private
        options["privacy_type"] = 1 if payload.is_private else 0
    elif payload.privacy_type is not None:
        options["privacy_type"] = payload.privacy_type
        options["is_private"] = payload.privacy_type == 1
    return options


def _serialize_draft(draft: AiDraft) -> dict:
    return {
        "id": draft.id,
        "platform": draft.platform,
        "title": draft.title,
        "body": draft.body,
        "tags": draft.tags or [],
        "source_note_id": draft.source_note_id,
        "created_at": draft.created_at.isoformat(),
    }


def _serialize_publish_job(job: PublishJob) -> dict:
    try:
        publish_options = json.loads(job.publish_options or "{}")
    except json.JSONDecodeError:
        publish_options = {}
    return {
        "id": job.id,
        "platform_account_id": job.platform_account_id,
        "source_draft_id": job.source_draft_id,
        "platform": job.platform,
        "title": job.title,
        "body": job.body,
        "publish_mode": job.publish_mode,
        "publish_options": publish_options,
        "status": job.status,
        "scheduled_at": job.scheduled_at.isoformat() if job.scheduled_at else None,
        "created_at": job.created_at.isoformat(),
    }


def _get_owned_source_note(db: Session, current_user: User, note_id: int) -> Note:
    note = db.get(Note, note_id)
    if note is None or note.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source note not found")
    return note


@router.get("")
def get_drafts(
    platform: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    statement = select(AiDraft).where(AiDraft.user_id == current_user.id)
    if platform:
        statement = statement.where(AiDraft.platform == platform)
    drafts = db.scalars(statement.order_by(AiDraft.created_at.desc())).all()
    return paginated([_serialize_draft(draft) for draft in drafts], page, page_size)


@router.post("")
def create_draft(
    payload: DraftCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    source_note = None
    if payload.source_note_id is not None:
        source_note = _get_owned_source_note(db, current_user, payload.source_note_id)

    # Extract tags from source note
    tags = None
    if source_note and source_note.raw_json:
        raw = source_note.raw_json if isinstance(source_note.raw_json, dict) else {}
        tag_list = raw.get("tags") or raw.get("tag_list")
        if not tag_list:
            data = raw.get("data")
            if isinstance(data, dict):
                items = data.get("items") or []
                if items and isinstance(items[0], dict):
                    card = items[0].get("note_card") or {}
                    if isinstance(card, dict):
                        tag_list = card.get("tag_list")
        if isinstance(tag_list, list):
            tags = []
            for t in tag_list:
                if isinstance(t, str):
                    tags.append({"name": t})
                elif isinstance(t, dict) and t.get("name"):
                    tags.append({"id": str(t.get("id", "")), "name": str(t["name"])})

    draft = AiDraft(
        user_id=current_user.id,
        platform=payload.platform,
        title=payload.title or (source_note.title if source_note else ""),
        body=payload.body or (source_note.content if source_note else ""),
        tags=tags,
        source_note_id=source_note.id if source_note else None,
    )
    db.add(draft)
    db.flush()

    if source_note:
        source_assets = db.scalars(
            select(NoteAsset).where(NoteAsset.note_id == source_note.id).order_by(NoteAsset.sort_order.asc(), NoteAsset.id.asc())
        ).all()
        for idx, na in enumerate(source_assets):
            db.add(DraftAsset(
                draft_id=draft.id,
                asset_type=na.asset_type,
                url=na.url,
                local_path=na.local_path,
                sort_order=idx,
            ))

    db.commit()
    db.refresh(draft)
    return _serialize_draft(draft)


class TcmNihaixiaDraftRequest(BaseModel):
    angle: str = Field(default="tool_sharing")
    custom_title: Optional[str] = None
    custom_topic: Optional[str] = None
    attach_promo_images: bool = True


TCM_TEMPLATES = {
    "tool_sharing": {
        "title": "有没有平时用倪海厦老师经方解决过小病的朋友？🙋",
        "body": (
            "有没有平时也爱看倪海厦老师《人纪》、喜欢中医经方养生的小伙伴？🌿\n\n"
            "我自己平时自学钻研经方，但说实话，每次一到实际需要查方的时候就很头大——"
            "厚厚的讲义翻半天，要么在十几个人群里和备忘录里搜来搜去，药味配比、剂量换算和倪师讲的临证心得总是对不上号…🤦‍♂️\n\n"
            "因为查药方实在太折腾了，我自己花了两个多月业余时间，把倪师讲过的经典经方、汉唐100方系列、原方组成、剂量参考和临证要点，一条条归纳整理出了一个网页版速查小工具。📱\n"
            "现在手机一打开，随手搜个症状或者方名就能秒出配伍，再也不用像大海捞针一样翻几百页讲义了！\n\n"
            "想和同好们交流一下：大家平时日常调理或者家里人遇到换季小不适，最常用的是哪张经方？\n"
            "欢迎在评论区一起交流探讨你的自学与经方使用体会~🌿\n\n"
            "————————————\n"
            "⚠️【温馨提示与免责说明】\n"
            "本文仅为中医古籍爱好者个人学习心得与工具交流，不构成任何医疗诊断或用药处方建议。中医讲究辨证论治、一人一方，若有身体不适请务必前往正规医院在专业中医师指导下辨证调理。"
        ),
        "tags": [
            {"name": "倪海厦"},
            {"name": "倪海厦经方"},
            {"name": "中医养生"},
            {"name": "自学中医"},
            {"name": "伤寒论"},
            {"name": "健康日常"},
            {"name": "实用工具分享"},
        ],
    },
    "cold_fever": {
        "title": "换季受寒打喷嚏，大家平时用倪海厦老师讲的哪张经方？🍵",
        "body": (
            "最近早晚温差大，办公室空调一吹，身边不少朋友开始喷嚏连天、怕冷发紧。🤧\n\n"
            "以前一受凉就乱喝药，后来反复听倪海厦老师讲《伤寒论》，才搞懂刚受表寒时，解肌发表、调和营卫才是核心（比如大家熟悉的桂枝汤、麻黄汤经方体系）。\n"
            "每次家里人有这种小苗头，对症喝点热汤发个微汗，整个人就舒坦多了。\n\n"
            "不过学经方最大的痛点就是：方子太多，每张方的轻重主次和倪师临证加减太容易混！之前翻书做笔记找半天，后来我自己索性开发了一个经方检索小站，把倪师讲过的汉唐方和伤寒方分类整理好了，手机随时点开就能对照。📱\n\n"
            "各位经方同好，你们在对付轻度受寒时最喜欢用哪张经方？欢迎在评论区一起交流你的自用经验~🌿\n\n"
            "————————————\n"
            "⚠️【温馨提示与免责说明】\n"
            "本文仅为个人学习心得交流，非医疗建议。经方药力严谨，各人体质不同，用药务必遵医嘱，切勿自行盲目套用。"
        ),
        "tags": [
            {"name": "倪海厦"},
            {"name": "受寒感冒"},
            {"name": "桂枝汤"},
            {"name": "中医经方"},
            {"name": "养生日常"},
            {"name": "自学中医"},
        ],
    },
    "spleen_stomach": {
        "title": "舌苔厚白、早起口苦？倪海厦老师讲脾胃湿气真的透彻！",
        "body": (
            "有没有跟我一样，平时总觉得容易乏力、舌苔发白厚腻、早起嘴巴苦苦的？🥱\n\n"
            "后来精读了倪海厦老师讲脾胃和湿气的部分才恍然大悟：现代人很多小毛病，根子都在中焦脾胃运化无力、寒湿互结。倪师常强调“去湿先温阳，运脾为主”，很多时候盲目喝凉茶反倒伤了胃气。\n\n"
            "为了搞清楚倪师讲过的各种理中、四逆、苓桂术甘这类健脾利湿名方及其适应症，我花了不少心血把390多首方剂、组成剂量与倪师独家批注全部搬到了一个线上检索站里，现在遇到情况对照着看特别清晰。📱\n\n"
            "想问问大家，调理脾胃湿气你们觉得倪师讲的哪一条思路最受用？欢迎在评论区一起交流探讨自学体会~🌱\n\n"
            "————————————\n"
            "⚠️【温馨提示与免责说明】\n"
            "本笔记仅作中医文化交流与学习记录，不作临床处方依据。体质各异，用药请咨询专业中医师。"
        ),
        "tags": [
            {"name": "倪海厦"},
            {"name": "脾胃虚弱"},
            {"name": "祛湿气"},
            {"name": "中医养生"},
            {"name": "自学中医"},
            {"name": "舌苔厚白"},
        ],
    },
}


@router.post("/tcm-nihaixia")
def create_tcm_nihaixia_draft(
    payload: TcmNihaixiaDraftRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from backend.app.core.compliance import sanitize_content

    template = TCM_TEMPLATES.get(payload.angle) or TCM_TEMPLATES["tool_sharing"]
    final_title = payload.custom_title.strip() if payload.custom_title else template["title"]
    final_body = template["body"]
    final_tags = list(template["tags"])

    if payload.angle == "custom" and payload.custom_topic:
        topic = payload.custom_topic.strip()
        final_title = payload.custom_title.strip() if payload.custom_title else f"关于倪海厦老师讲{topic}，分享我的经方自用心得与整理！"
        final_body = (
            f"有没有平时也爱看倪海厦老师讲{topic}的朋友？🌿\n\n"
            f"在学医的过程中，关于{topic}的经方运用，倪师有很多非常精辟独到的临证见解。"
            "但每次要查具体药味配伍和加减变化时，翻看长篇讲义真的很耗费时间。\n\n"
            "为了方便自己和身边的经方爱好者查阅，我花了很长时间把倪海厦老师讲过的390多首经典经方及汉唐方剂体系，"
            "整理成了一个随时随地可以检索的经方小工具。输入症状或药方名就能直接看完整组成与倪师注解。📱\n\n"
            "想和同好们交流：在面对这类调理时，你们觉得倪师讲的哪一个方剂思路最受启发？欢迎在评论区一起讨论交流~💬\n\n"
            "————————————\n"
            "⚠️【温馨提示与免责说明】\n"
            "本文仅为中医古籍爱好者个人学习心得与工具交流，不构成任何医疗诊断或用药处方建议。中医讲究辨证论治、一人一方，若有身体不适请务必前往正规医院在专业中医师指导下辨证调理。"
        )
        final_tags = [
            {"name": "倪海厦"},
            {"name": f"{topic}"},
            {"name": "中医养生"},
            {"name": "自学中医"},
            {"name": "经方"},
            {"name": "健康日常"},
        ]

    # 全自动经过合规引擎审查脱敏
    final_title, final_body = sanitize_content(final_title, final_body)

    draft = AiDraft(
        user_id=current_user.id,
        platform="xhs",
        title=final_title,
        body=final_body,
        tags=final_tags,
    )
    db.add(draft)
    db.flush()

    if payload.attach_promo_images:
        promo_dir = Path(r"C:\Users\kami\.gemini\antigravity\scratch\fangji\promo_assets")
        if promo_dir.exists():
            media_dir = Path(get_settings().storage_dir) / "media"
            media_dir.mkdir(parents=True, exist_ok=True)
            image_candidates = [
                "real_1_home.png",
                "real_2_search.png",
                "3_rx_card.png",
                "real_4_compare.png",
            ]
            sort_idx = 0
            for img_name in image_candidates:
                src_file = promo_dir / img_name
                if src_file.exists():
                    target_filename = f"xhs-asset-u{current_user.id}-fangji-{img_name}"
                    shutil.copy2(src_file, media_dir / target_filename)
                    db.add(DraftAsset(
                        draft_id=draft.id,
                        asset_type="image",
                        local_path=target_filename,
                        sort_order=sort_idx,
                    ))
                    sort_idx += 1

    db.commit()
    db.refresh(draft)
    return _serialize_draft(draft)


@router.post("/{draft_id}/send-to-publish")
def send_draft_to_publish(
    draft_id: int,
    payload: DraftSendToPublishRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    draft = db.get(AiDraft, draft_id)
    if draft is None or draft.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")

    account_id: Optional[int] = None
    if payload.platform_account_id is not None:
        account = db.get(PlatformAccount, payload.platform_account_id)
        if account is None or account.user_id != current_user.id or account.platform != draft.platform:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Platform account not found")
        account_id = account.id

    options = _build_publish_options(payload)
    if draft.tags:
        options["draft_tags"] = draft.tags

    job = PublishJob(
        user_id=current_user.id,
        platform_account_id=account_id,
        source_draft_id=draft.id,
        platform=draft.platform,
        title=draft.title,
        body=draft.body,
        publish_mode=payload.publish_mode,
        publish_options=json.dumps(options, ensure_ascii=False, separators=(",", ":")),
        scheduled_at=payload.scheduled_at,
        status="pending",
    )
    db.add(job)
    db.flush()

    draft_assets = db.scalars(
        select(DraftAsset).where(DraftAsset.draft_id == draft.id).order_by(DraftAsset.sort_order.asc(), DraftAsset.id.asc())
    ).all()
    for da in draft_assets:
        if da.local_path:
            file_path = f"/api/files/media/{da.local_path}"
        else:
            file_path = da.url
        pa = PublishAsset(
            publish_job_id=job.id,
            asset_type=da.asset_type,
            file_path=file_path,
            upload_status="pending",
        )
        db.add(pa)

    db.commit()
    db.refresh(job)
    return _serialize_publish_job(job)


@router.patch("/{draft_id}")
def update_draft(
    draft_id: int,
    payload: DraftUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    draft = db.get(AiDraft, draft_id)
    if draft is None or draft.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")

    if payload.title is not None:
        draft.title = payload.title
    if payload.body is not None:
        draft.body = payload.body
    if payload.tags is not None:
        draft.tags = list(payload.tags)
        flag_modified(draft, "tags")

    db.commit()
    db.refresh(draft)
    return _serialize_draft(draft)


@router.delete("/{draft_id}")
def delete_draft(
    draft_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    draft = db.get(AiDraft, draft_id)
    if draft is None or draft.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    db.execute(select(DraftAsset).where(DraftAsset.draft_id == draft.id))
    for asset in db.scalars(select(DraftAsset).where(DraftAsset.draft_id == draft.id)).all():
        db.delete(asset)
    db.delete(draft)
    db.commit()
    return {"id": draft_id, "status": "deleted"}


# ---------------------------------------------------------------------------
# Draft assets
# ---------------------------------------------------------------------------

def _serialize_draft_asset(asset: DraftAsset) -> dict:
    display_url = f"/api/files/media/{asset.local_path}" if asset.local_path else asset.url
    return {
        "id": asset.id,
        "draft_id": asset.draft_id,
        "asset_type": asset.asset_type,
        "url": display_url,
        "local_path": asset.local_path,
        "sort_order": asset.sort_order,
    }


class DraftAssetCreateRequest(BaseModel):
    asset_type: str = Field(pattern="^(image|video)$")
    url: str = Field(default="", max_length=2048)
    local_path: str = Field(default="", max_length=512)


class DraftAssetReorderRequest(BaseModel):
    asset_ids: list[int] = Field(min_length=1)


@router.get("/{draft_id}/assets")
def get_draft_assets(
    draft_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    draft = db.get(AiDraft, draft_id)
    if draft is None or draft.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Draft not found")
    assets = db.scalars(
        select(DraftAsset).where(DraftAsset.draft_id == draft.id).order_by(DraftAsset.sort_order.asc(), DraftAsset.id.asc())
    ).all()
    return {"items": [_serialize_draft_asset(a) for a in assets]}


@router.post("/{draft_id}/assets")
def add_draft_asset(
    draft_id: int,
    payload: DraftAssetCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    draft = db.get(AiDraft, draft_id)
    if draft is None or draft.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Draft not found")
    max_order = db.scalar(select(func.max(DraftAsset.sort_order)).where(DraftAsset.draft_id == draft.id)) or 0
    asset = DraftAsset(
        draft_id=draft.id,
        asset_type=payload.asset_type,
        url=payload.url,
        local_path=payload.local_path,
        sort_order=max_order + 1,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return _serialize_draft_asset(asset)


@router.delete("/{draft_id}/assets/{asset_id}")
def delete_draft_asset(
    draft_id: int,
    asset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    draft = db.get(AiDraft, draft_id)
    if draft is None or draft.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Draft not found")
    asset = db.scalars(select(DraftAsset).where(DraftAsset.id == asset_id, DraftAsset.draft_id == draft.id)).first()
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    db.delete(asset)
    db.commit()
    return {"id": asset_id, "status": "deleted"}


class DraftAssetUpdateRequest(BaseModel):
    url: Optional[str] = Field(default=None, max_length=2048)
    local_path: Optional[str] = Field(default=None, max_length=512)


@router.patch("/{draft_id}/assets/{asset_id}")
def update_draft_asset(
    draft_id: int,
    asset_id: int,
    payload: DraftAssetUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    draft = db.get(AiDraft, draft_id)
    if draft is None or draft.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Draft not found")
    asset = db.scalars(select(DraftAsset).where(DraftAsset.id == asset_id, DraftAsset.draft_id == draft.id)).first()
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    if payload.url is not None:
        asset.url = payload.url
    if payload.local_path is not None:
        asset.local_path = payload.local_path
    db.commit()
    db.refresh(asset)
    return _serialize_draft_asset(asset)


@router.put("/{draft_id}/assets/reorder")
def reorder_draft_assets(
    draft_id: int,
    payload: DraftAssetReorderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    draft = db.get(AiDraft, draft_id)
    if draft is None or draft.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Draft not found")
    assets = db.scalars(select(DraftAsset).where(DraftAsset.draft_id == draft.id)).all()
    asset_map = {a.id: a for a in assets}
    for idx, aid in enumerate(payload.asset_ids):
        if aid in asset_map:
            asset_map[aid].sort_order = idx
    db.commit()
    return {"ok": True}
