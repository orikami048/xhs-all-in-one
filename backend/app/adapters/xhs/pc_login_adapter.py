from __future__ import annotations

from typing import Any

from backend.app.adapters.xhs.request_env import direct_xhs_request_env


class XhsPcLoginAdapter:
    def create_qrcode(self) -> dict[str, Any]:
        with direct_xhs_request_env():
            from apis.xhs_pc_login_apis import XHSLoginApi

            api = XHSLoginApi()
            cookies = api.generate_init_cookies()
            success, message, payload = api.generate_qrcode(cookies)
        if not success or not payload:
            raise RuntimeError(message)
        return {
            "cookies": payload["cookies"],
            "qr_id": payload["qr_id"],
            "code": payload["code"],
            "qr_url": payload["qr_url"],
        }

    def check_qrcode_status(self, qr_id: str, code: str, cookies: dict[str, Any]) -> dict[str, Any]:
        with direct_xhs_request_env():
            from apis.xhs_pc_login_apis import XHSLoginApi

            api = XHSLoginApi()
            success, message, updated_cookies = api.check_qrcode_status(qr_id, code, cookies)
        status = "confirmed" if success else "pending"
        if "过期" in message or "expired" in message.lower():
            status = "expired"
        elif not success and ("请确认登录" in message or message == "scanned"):
            status = "scanned"
        return {"status": status, "cookies": updated_cookies}

    def get_user_info(self, cookies: dict[str, Any]) -> dict[str, Any]:
        with direct_xhs_request_env():
            from apis.xhs_pc_login_apis import XHSLoginApi

            api = XHSLoginApi()
            try:
                success, data, _ = api.get_user_info(cookies)
            except Exception:
                success, data = False, {}
        user_id = (data or {}).get("user_id") or ""
        nickname = (data or {}).get("nickname") or "小红书用户"
        return {
            "external_user_id": user_id,
            "nickname": nickname,
            "avatar_url": (data or {}).get("images") or (data or {}).get("imageb") or "",
            "profile": {
                "red_id": (data or {}).get("red_id") or (data or {}).get("redId") or "",
                "followers": (data or {}).get("fans") or (data or {}).get("followers") or (data or {}).get("follower_count"),
                "following": (data or {}).get("follows") or (data or {}).get("following") or (data or {}).get("following_count"),
                "likes": (data or {}).get("liked_count") or (data or {}).get("likes") or (data or {}).get("like_count"),
                "raw": data or {},
            },
        }

    def create_phone_session(self, phone: str) -> dict[str, Any]:
        with direct_xhs_request_env():
            from apis.xhs_pc_login_apis import XHSLoginApi

            api = XHSLoginApi()
            cookies = api.generate_init_cookies()
            success, message, _ = api.send_phone_code(phone, cookies)
        if not success:
            raise RuntimeError(message)
        return {"cookies": cookies, "message": message or "sent"}

    def confirm_phone_login(self, phone: str, code: str, cookies: dict[str, Any]) -> dict[str, Any]:
        with direct_xhs_request_env():
            from apis.xhs_pc_login_apis import XHSLoginApi

            api = XHSLoginApi()
            success, message, payload = api.login_by_phone(phone, code, cookies)
        if not success or not payload:
            raise RuntimeError(message)
        return {"status": "confirmed", "cookies": payload["cookies"]}
