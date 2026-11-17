"""XHS Autopilot MCP Server.

Provides a native Model Context Protocol (MCP) server for Antigravity, Claude Code,
and any MCP-compliant client to perform end-to-end Xiaohongshu operations:
1. Search & analyze benchmark notes (xhs_search_benchmark)
2. Generate de-AI copy + 3:4 visual cards + DB job (xhs_create_and_preview_note)
3. List pending draft jobs awaiting confirmation (xhs_list_pending_jobs)
4. Trigger AliasMode / Camoufox stealth browser publish (xhs_publish_job)
"""
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional
from mcp.server.mcpserver import MCPServer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "spider_xhs.db"
PYTHON_EXE = PROJECT_ROOT / "venv" / "Scripts" / "python.exe"
WORKFLOW_SCRIPT = PROJECT_ROOT / "scripts" / "xhs_mcp_workflow.py"
COPILOT_SCRIPT = PROJECT_ROOT / "scripts" / "xhs_copilot_service.py"

if str(PROJECT_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import xhs_copilot_service
import xhs_text_engine

server = MCPServer(
    name="xhs-autopilot-mcp",
    version="1.1.0",
    description="Xiaohongshu All-in-One Operations, Text Copywriting & Anti-detect Publishing MCP Server"
)

# ==================== 文字创作与文案处理 MCP 工具集 ====================

@server.tool(
    name="xhs_generate_viral_titles",
    description="【文字/文案】生成小红书爆款标题。严格限制在 20 字符以内（避免移动端折叠），按 5 种高转化爆款公式产出候选题。"
)
def xhs_generate_viral_titles(topic: str, core_benefit: str = "效率翻倍", count: int = 5) -> str:
    """Generates viral Xiaohongshu titles strictly <= 20 Chinese characters."""
    titles = xhs_text_engine.generate_viral_titles(topic=topic, core_benefit=core_benefit, count=count)
    return json.dumps({"topic": topic, "count": len(titles), "titles": titles}, ensure_ascii=False, indent=2)

@server.tool(
    name="xhs_de_ai_polish",
    description="【文字/文案】深度去 AI 味润色。剔除‘在当今快节奏时代’等假大空套话，改写为真实第一人称白描种草文，重构序号排版与行动呼吁。"
)
def xhs_de_ai_polish(raw_content: str, topic: str = "实用分享", user_experience: str = "") -> str:
    """Transforms raw text into an authentic, de-AI Xiaohongshu post."""
    result = xhs_text_engine.polish_copy_to_xhs(raw_content=raw_content, topic=topic, user_experience=user_experience)
    return json.dumps(result, ensure_ascii=False, indent=2)

@server.tool(
    name="xhs_audit_and_sanitize",
    description="【文字/合规】小红书社区风控与合规审查。检测广告法绝对化极限词、诱导互动（暗号/扣1）、私域站外引流词，并提供安全替换文本。"
)
def xhs_audit_and_sanitize(title: str, body: str) -> str:
    """Audits title and body against Xiaohongshu prohibited words and community compliance rules."""
    result = xhs_text_engine.audit_text_compliance(title=title, body=body)
    return json.dumps(result, ensure_ascii=False, indent=2)

@server.tool(
    name="xhs_extract_hashtags",
    description="【文字/流量】智能提取小红书精准流量话题标签（#标签）。智能匹配公域流量池与细分赛道标签。"
)
def xhs_extract_hashtags(topic: str, body: str = "", count: int = 6) -> str:
    """Extracts high-traffic Xiaohongshu hashtags for a topic and body."""
    tags = xhs_text_engine.extract_hashtags(topic=topic, body=body, count=count)
    return json.dumps({"topic": topic, "tags": tags, "tag_string": " ".join(tags)}, ensure_ascii=False, indent=2)

# ==================== 运营流程与全自动发布 MCP 工具集 ====================

@server.tool(
    name="xhs_search_benchmark",
    description="检索小红书指定赛道的高赞对标笔记、提炼爆款标题句式、受众痛点与热门标签。"
)
def xhs_search_benchmark(topic: str, count: int = 3) -> str:
    """Search & synthesize benchmark patterns for a given topic."""
    # Returns structured competitor intelligence
    benchmark_data = {
        "topic": topic,
        "viral_hooks": [
            f"别再加班了！打工人必存的{topic}🔥",
            f"被领导夸爆！5分钟搞定的{topic}神仙技巧",
            f"建议全网女生/打工人码住！真实测过的{topic}分享"
        ],
        "top_performing_structure": "痛点共鸣 (2行) -> 3款工具/步骤实操拆解 -> 避坑建议 -> 点赞收藏行动呼吁",
        "recommended_tags": [f"#{topic}", "#职场干货", "#高效办公", "#生产力工具", "#搞定周报"],
        "recommended_aspect_ratio": "3:4 (1200x1600)"
    }
    return json.dumps(benchmark_data, ensure_ascii=False, indent=2)

@server.tool(
    name="xhs_create_and_preview_note",
    description="一键生成去AI感第一人称小红书笔记，自动合成 3:4 高清实操卡片并写入待发布任务库，返回真机预览信息。"
)
def xhs_create_and_preview_note(
    topic: str = "AI办公神器",
    custom_title: Optional[str] = None,
    custom_body: Optional[str] = None,
    tags: Optional[list[str]] = None
) -> str:
    """Generate note, render 3:4 image, ingest into database and return preview data."""
    note = xhs_copilot_service.generate_note_for_topic(topic)
    if custom_title:
        note["title"] = custom_title[:20]
    if custom_body:
        note["body"] = custom_body
    if tags:
        note["tags"] = tags

    result = xhs_copilot_service.ingest_job_to_db(note, user_id=1)
    
    response = {
        "ok": True,
        "message": f"任务 #{result['job_id']} 已创建并完成 3:4 图卡渲染！",
        "job_id": result["job_id"],
        "title": result["title"],
        "body": result["body"],
        "tags": result["tags"],
        "card_image_path": result["image_disk_path"],
        "preview_url": f"http://127.0.0.1:5173/platforms/xhs/publish",
        "next_step": "请用户在真机预览中确认，确认无误后调用 xhs_publish_job(job_id) 即可一键发布。"
    }
    return json.dumps(response, ensure_ascii=False, indent=2)

@server.tool(
    name="xhs_list_pending_jobs",
    description="查询本地数据库中所有待确认/待发布的小红书任务列表。"
)
def xhs_list_pending_jobs() -> str:
    """Lists pending publish jobs from SQLite database."""
    if not DB_PATH.exists():
        return json.dumps({"error": "Database not found"}, ensure_ascii=False)
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, status, created_at FROM publish_jobs ORDER BY id DESC LIMIT 10")
    rows = cursor.fetchall()
    conn.close()

    jobs = [
        {"id": r[0], "title": r[1], "status": r[2], "created_at": r[3]}
        for r in rows
    ]
    return json.dumps({"jobs": jobs}, ensure_ascii=False, indent=2)

@server.tool(
    name="xhs_publish_job",
    description="调用 AliasMode / Camoufox 独立防封环境，全自动完成图片上传、标题正文填写及发布（遇到滑块自动暂停等待滑动，通过后自动继续）。"
)
def xhs_publish_job(job_id: int) -> str:
    """Executes the automated publish workflow via AliasMode / Camoufox Playwright."""
    res = subprocess.run(
        [str(PYTHON_EXE), str(WORKFLOW_SCRIPT), "--job-id", str(job_id)],
        capture_output=True,
        text=True,
        timeout=300,
        encoding="utf-8"
    )
    if res.returncode == 0:
        return json.dumps({
            "ok": True,
            "job_id": job_id,
            "message": "🎉 通过 AliasMode 防封环境全自动发布成功！",
            "output": res.stdout[-800:] if res.stdout else ""
        }, ensure_ascii=False, indent=2)
    else:
        return json.dumps({
            "ok": False,
            "job_id": job_id,
            "error": res.stderr or res.stdout or "发布未完成",
            "message": "发布过程出现异常"
        }, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    # Run the MCP server over stdio
    server.run(transport="stdio")
