from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, List, Optional


TCM_MANDATORY_DISCLAIMER = (
    "💡 温馨提示与免责声明：\n"
    "本文仅为中医古籍文献研读与个人日常学习心得探讨，不构成任何医疗诊断建议、用药处方或疗效保证。"
    "中医讲究辨证论治、一人一方，如身体感到不适，请务必前往正规医疗机构遵医嘱诊疗。"
)

COMPLIANCE_CATEGORIES = {
    "ENGAGEMENT_BAIT": {
        "id": "engagement_bait",
        "name": "诱导互动与虚假营销",
        "description": "严禁使用暗号、资料领取、连环福利等方式强行索要点赞、收藏、评论，会被平台判定为作弊刷量严重限流。",
        "severity": "high",
        "penalty": "限流、判定违规营销、屏蔽评论区",
    },
    "MEDICAL_CLAIMS": {
        "id": "medical_claims",
        "name": "医疗绝对化与疗效承诺",
        "description": "大健康/中医类严禁承诺彻底治愈、使用神医神药绝对词，必须明确保留非诊疗学习免责声明。",
        "severity": "high",
        "penalty": "违规下架、严重者账号禁言或封禁",
    },
    "EXTERNAL_DIVERSION": {
        "id": "external_diversion",
        "name": "站外导流与私域引流",
        "description": "严禁在正文、标题、图片中出现微信、公众号、网盘、淘宝等站外导流敏感词或变体。",
        "severity": "high",
        "penalty": "限流、私信降权、账号封禁",
    },
    "EXTREME_WORDS": {
        "id": "extreme_words",
        "name": "广告法绝对化与夸大词汇",
        "description": "禁止使用最强、第一、万能、绝无仅有等广告法违禁词。",
        "severity": "medium",
        "penalty": "笔记限流、审核驳回",
    },
}

# Rule definitions
RULES = [
    # 1. 诱导互动 (Engagement Bait) - 高危
    {
        "category": "ENGAGEMENT_BAIT",
        "name": "暗号/扣数字诱导互动",
        "regex": r"(?:扣\s*[1-9一二两]|扣个\s*[1-9一二两]|公屏\s*扣|评论区\s*扣|评论区\s*留|评论区\s*打|打在公屏|打在评论)",
        "advice": "严禁要求读者在评论区扣1或留下暗号，小红书文本审核100%命中拦截！",
        "replacement": "欢迎在评论区一起讨论交流你的自用体会~",
    },
    {
        "category": "ENGAGEMENT_BAIT",
        "name": "利益/资料诱导互动",
        "regex": r"(?:私发(?:你|资料)|回复(?:领取|获取)|免费送|免费领(?:取)?|发给你们|回给你们|留邮箱|求点赞|求收藏|点赞收藏不迷路|收藏防走丢|点赞过\d+|三连)",
        "advice": "不得以资料包、私发表格等噱头诱导三连，平台严打刷量行为。",
        "replacement": "感兴趣的朋友可以一起交流探讨学习心得~",
    },
    # 2. 医疗绝对化 (Medical Claims) - 高危
    {
        "category": "MEDICAL_CLAIMS",
        "name": "包治/根治等绝对疗效承诺",
        "regex": r"(?:包治|根治|彻底断根|药到病除|百分之百治好|100%治好|一吃就灵|马上见效|绝不复发|替代(?:医生|医院)|不用去医院)",
        "advice": "严禁承诺具体医疗疗效或使用包治、根治等绝对化用语，必须声明辨证调理及遵医嘱。",
        "replacement": "温和调理改善",
    },
    {
        "category": "MEDICAL_CLAIMS",
        "name": "神医/神药夸大宣传",
        "regex": r"(?:神药|神医|天下第一方|万能方|仙方|起死回生|百病皆治)",
        "advice": "禁止将经典经方夸大宣传为神医神药，保持严谨客观的传统文化传承态度。",
        "replacement": "传统经典经方",
    },
    # 3. 站外导流 (External Diversion) - 高危
    {
        "category": "EXTERNAL_DIVERSION",
        "name": "站外社交/私域联系方式",
        "regex": r"(?:微\s*信|威\s*信|v\s*x|vx\b|v信|薇信|溦信|公众号|企鹅号|加\s*我|加\s*v|加\s*群|进\s*群|私信我|主页有惊喜|点击链接)",
        "advice": "正文严禁引导添加外部社交软件或私聊，会导致笔记直接被屏蔽降权。",
        "replacement": "",
    },
    # 4. 极限词 (Extreme Words) - 中危
    {
        "category": "EXTREME_WORDS",
        "name": "绝对化极限词汇",
        "regex": r"(?:最强|最好|第一名|顶级|绝无仅有|无可匹敌|独一无二|全网唯一)",
        "advice": "避免使用违反广告法的最高级词汇，建议改为温和中立的表述。",
        "replacement": "经典",
    },
]


@dataclass
class ComplianceIssue:
    category: str
    category_name: str
    rule_name: str
    severity: str
    matched_text: str
    location: str  # "title" or "body"
    advice: str
    replacement: str


@dataclass
class ComplianceReport:
    is_valid: bool
    score: int
    danger_count: int
    warning_count: int
    issues: List[ComplianceIssue] = field(default_factory=list)
    cleaned_title: str = ""
    cleaned_body: str = ""


def audit_content(title: str, body: str) -> ComplianceReport:
    """全面审查标题与正文是否符合小红书 2026 最新合规标准。"""
    issues: List[ComplianceIssue] = []
    text_to_check = [("title", title or ""), ("body", body or "")]

    for loc, text in text_to_check:
        for rule in RULES:
            matches = list(re.finditer(rule["regex"], text, flags=re.IGNORECASE))
            for m in matches:
                matched_str = m.group(0)
                cat_info = COMPLIANCE_CATEGORIES.get(rule["category"], {})
                issues.append(
                    ComplianceIssue(
                        category=rule["category"],
                        category_name=cat_info.get("name", "合规审查"),
                        rule_name=rule["name"],
                        severity=cat_info.get("severity", "medium"),
                        matched_text=matched_str,
                        location="标题" if loc == "title" else "正文",
                        advice=rule["advice"],
                        replacement=rule["replacement"],
                    )
                )

    danger_count = sum(1 for i in issues if i.severity == "high")
    warning_count = sum(1 for i in issues if i.severity == "medium")

    # 评分计算：满分100，高危每个扣25分，中危每个扣10分
    score = max(0, 100 - danger_count * 25 - warning_count * 10)
    is_valid = danger_count == 0 and score >= 80

    cleaned_title, cleaned_body = sanitize_content(title, body)

    return ComplianceReport(
        is_valid=is_valid,
        score=score,
        danger_count=danger_count,
        warning_count=warning_count,
        issues=issues,
        cleaned_title=cleaned_title,
        cleaned_body=cleaned_body,
    )


def sanitize_content(title: str, body: str) -> tuple[str, str]:
    """对内容进行自动化脱敏净化，将违规用语转换为合规表述并补齐免责声明。"""
    new_title = title or ""
    new_body = body or ""

    for rule in RULES:
        regex = rule["regex"]
        replacement = rule["replacement"]
        new_title = re.sub(regex, replacement, new_title, flags=re.IGNORECASE)
        new_body = re.sub(regex, replacement, new_body, flags=re.IGNORECASE)

    # 清理多余空行和前后空格
    new_title = re.sub(r"\s+", " ", new_title).strip()
    new_body = re.sub(r"\n{3,}", "\n\n", new_body).strip()

    # 检查并确保正文末尾包含医疗免责声明
    if "温馨提示与免责声明" not in new_body and "免责声明" not in new_body:
        new_body = f"{new_body}\n\n---\n{TCM_MANDATORY_DISCLAIMER}"

    return new_title, new_body


def get_all_rules_catalog() -> list[dict[str, Any]]:
    """获取面向创作者的完整避坑规则手册。"""
    catalog = []
    for cat_key, cat_meta in COMPLIANCE_CATEGORIES.items():
        cat_rules = [r for r in RULES if r["category"] == cat_key]
        catalog.append({
            "category_key": cat_key,
            "name": cat_meta["name"],
            "description": cat_meta["description"],
            "severity": cat_meta["severity"],
            "penalty": cat_meta["penalty"],
            "rules": [
                {
                    "name": r["name"],
                    "advice": r["advice"],
                    "replacement": r["replacement"],
                }
                for r in cat_rules
            ],
        })
    return catalog
