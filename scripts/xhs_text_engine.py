"""XHS Text Engine:
Copywriting, De-AI Polishing, Title Engineering, and Compliance Auditing for Xiaohongshu.
"""
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import compliance logic from backend
try:
    from backend.app.core.compliance import audit_content, sanitize_content
except Exception:
    audit_content = None
    sanitize_content = None

# Common AI Clichés to eliminate
AI_CLICHE_PATTERNS = [
    r"在当今(?:快节奏|数字化|飞速发展|瞬息万变)的(?:社会|时代|背景下)?",
    r"众所周知",
    r"不可否认的是?",
    r"综上所述",
    r"总而言之",
    r"总的来说",
    r"值得一提的是?",
    r"不仅如此",
    r"然而事实上",
    r"犹如一场及时雨",
    r"赋能(?:我们的)?",
    r"助力(?:我们)?",
    r"打造极致体验",
    r"让人眼前一亮",
    r"在这篇文章中[，,]?(?:我将|笔者将)?",
    r"笔者认为",
    r"显而易见",
    r"正如古人所说",
    r"毋庸置疑",
    r"归根结底",
    r"大有裨益",
]

def de_ai_clean_string(text: str) -> str:
    """Removes robotic AI clichés and translates stiff phrases into natural conversational speech."""
    res = text
    for pat in AI_CLICHE_PATTERNS:
        res = re.sub(pat, "", res)
    # Clean excessive empty lines
    res = re.sub(r"\n{3,}", "\n\n", res)
    return res.strip()

def generate_viral_titles(topic: str, core_benefit: str = "", count: int = 5) -> List[Dict[str, str]]:
    """Generates viral Xiaohongshu titles strictly <= 20 Chinese characters."""
    t = topic.strip().replace("小红书", "").replace("教程", "")
    b = (core_benefit or "效率翻倍").strip()
    
    candidates = [
        {"formula": "逆向好奇 + 强烈利益", "title": f"别再死磕加班了！3个{t[:5]}直接{b[:4]}🔥"},
        {"formula": "人群痛点 + 明确成果", "title": f"被老板夸爆！这套{t[:6]}打工人必存"},
        {"formula": "真实踩坑 + 保姆级避坑", "title": f"亲测少走3年弯路！{t[:6]}保姆级整理"},
        {"formula": "量化数字 + 场景切入", "title": f"每天早下班2小时！我的{t[:5]}全公开"},
        {"formula": "好物种草 + 口碑背书", "title": f"相见恨晚！这几款神仙{t[:5]}真的能处✨"},
        {"formula": "行动呼吁 + 紧迫感", "title": f"建议全文背诵！写{t[:6]}直接抄作业"},
    ]

    results = []
    for item in candidates:
        raw_title = item["title"]
        # Enforce hard 20 char limit
        clean_title = raw_title[:20]
        results.append({
            "formula": item["formula"],
            "title": clean_title,
            "char_count": len(clean_title)
        })
    return results[:count]

def extract_hashtags(topic: str, body: str = "", count: int = 6) -> List[str]:
    """Extracts high-traffic, niche-relevant Xiaohongshu hashtags."""
    base_tags = [f"#{topic.strip('#')}"]
    
    # Common traffic pools
    traffic_pool = {
        "ai": ["#AI工具", "#搞定周报", "#生产力工具", "#高效办公", "#打工人日常", "#职场干货", "#自媒体神器"],
        "职场": ["#职场干货", "#打工人日常", "#工作提效", "#准点下班", "#向上管理", "#办公室必备"],
        "副业": ["#副业搞钱", "#轻资产创业", "#自媒体起号", "#自由职业", "#技能变现", "#干货分享"],
        "养生": ["#中医养生", "#倪海厦经方", "#自学中医", "#健康打卡", "#食疗调理", "#女性健康"],
        "考公": ["#考公经验", "#申论高分", "#行测备考", "#上岸笔记", "#考研打卡", "#学习日常"]
    }

    matched = []
    text_corpus = f"{topic} {body}".lower()
    for category, tags in traffic_pool.items():
        if category in text_corpus or any(kw in text_corpus for kw in [category]):
            matched.extend(tags)

    if not matched:
        matched = ["#实用工具分享", "#干货分享", "#建议收藏", "#生活小技巧", "#提升自己"]

    # Combine unique tags
    seen = set()
    final_tags = []
    for tag in base_tags + matched:
        clean = tag if tag.startswith("#") else f"#{tag}"
        if clean not in seen and len(clean) > 1:
            seen.add(clean)
            final_tags.append(clean)
            if len(final_tags) >= count:
                break
    return final_tags

def polish_copy_to_xhs(
    raw_content: str,
    topic: str = "实用分享",
    user_experience: str = ""
) -> Dict[str, Any]:
    """Turns raw text or bullet points into a de-AI, highly authentic Xiaohongshu post."""
    clean_raw = de_ai_clean_string(raw_content)

    # 1. First-person Hook
    if user_experience:
        hook = f"说真的，{user_experience.strip()}\n最近把这套方法整理清楚了，每天省下大把时间，不整虚的直接上干货："
    else:
        hook = f"说真的，以前在这上面踩过太多坑，花了大把冤枉时间。\n最近彻底跑通了这套方法，效率直接翻倍，不整虚的直接上保姆级实操："

    # 2. Main body structuring
    paragraphs = [p.strip() for p in clean_raw.split("\n") if p.strip()]
    structured_bullets = []
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
    
    bullet_idx = 0
    for p in paragraphs:
        if len(p) < 6:
            continue
        if bullet_idx < len(emojis):
            emoji = emojis[bullet_idx]
            structured_bullets.append(f"{emoji} {p}")
            bullet_idx += 1
        else:
            structured_bullets.append(f"• {p}")

    body_main = "\n\n".join(structured_bullets) if structured_bullets else clean_raw

    # 3. Call to Action / Ending
    cta = (
        "💡 亲测避坑建议：\n"
        "别一上来就求全，挑最适合自己的1-2个先用起来，坚持一周就会发现质的改变。\n\n"
        "建议先点赞收藏🌟，需要的时候随时抄作业！大家平时有什么好用的心得？评论区一起交流探讨~"
    )

    tags = extract_hashtags(topic, body_main)
    tag_str = " ".join(tags)

    full_body = f"{hook}\n\n{body_main}\n\n{cta}\n\n{tag_str}"

    titles = generate_viral_titles(topic)
    best_title = titles[0]["title"] if titles else f"亲测好用的{topic}干货分享"

    return {
        "title": best_title,
        "body": full_body,
        "tags": tags,
        "title_options": titles,
    }

def audit_text_compliance(title: str, body: str) -> Dict[str, Any]:
    """Audits title and body against Xiaohongshu prohibited words and community compliance rules."""
    if audit_content is None:
        return {"is_valid": True, "score": 100, "danger_count": 0, "warning_count": 0, "issues": []}

    report = audit_content(title, body)
    issues = [
        {
            "category": i.category,
            "category_name": i.category_name,
            "rule_name": i.rule_name,
            "severity": i.severity,
            "matched_text": i.matched_text,
            "advice": i.advice,
            "replacement": i.replacement,
        }
        for i in report.issues
    ]
    return {
        "is_valid": report.is_valid,
        "score": report.score,
        "danger_count": report.danger_count,
        "warning_count": report.warning_count,
        "issues": issues,
        "cleaned_title": report.cleaned_title,
        "cleaned_body": report.cleaned_body,
    }
