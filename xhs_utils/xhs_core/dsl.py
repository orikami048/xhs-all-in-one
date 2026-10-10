"""Fetch the server-issued ``window._dsl`` anchor for an explicit Web appId."""

from __future__ import annotations

import json
import os
import re
import tempfile
import threading
import time
from typing import Optional


_GETDSS_RE = re.compile(r"function\s+getdss\s*\(\s*\)\s*\{\s*return\s+'(\d+)'")
_TTL = 300


class DsFetcher:
    def __init__(
        self,
        app_id: str,
        *,
        referer: str,
        ttl: int = _TTL,
    ) -> None:
        self.app_id = str(app_id)
        self.referer = str(referer)
        self._ttl = int(ttl)
        self._value: Optional[str] = None
        self._program: Optional[str] = None
        self._fetched_at = 0.0
        self._lock = threading.Lock()
        self._cache_file = os.path.join(tempfile.gettempdir(), f'xhs_ds_cache_{self.app_id}.json')
        self._load_disk_cache()

    def _load_disk_cache(self) -> None:
        try:
            if os.path.exists(self._cache_file):
                with open(self._cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('value') and data.get('program'):
                        self._value = str(data['value'])
                        self._program = str(data['program'])
                        self._fetched_at = float(data.get('fetched_at', 0.0))
        except Exception:
            pass

    def _save_disk_cache(self, value: str, program: str, fetched_at: float) -> None:
        try:
            with open(self._cache_file, 'w', encoding='utf-8') as f:
                json.dump(
                    {'value': value, 'program': program, 'fetched_at': fetched_at},
                    f,
                    ensure_ascii=False,
                )
        except Exception:
            pass

    @property
    def url(self) -> str:
        return f'https://as.xiaohongshu.com/api/sec/v1/ds?appId={self.app_id}'

    def get(self, proxies: Optional[dict] = None, force: bool = False) -> str:
        return self.get_bundle(proxies=proxies, force=force)[0]

    def get_bundle(
        self,
        proxies: Optional[dict] = None,
        force: bool = False,
        http_client=None,
    ) -> tuple[str, str]:
        """Return the server anchor and its DS program from one cached fetch."""
        now = time.time()
        if (
            not force
            and self._value
            and self._program
            and now - self._fetched_at < self._ttl
        ):
            return self._value, self._program
        with self._lock:
            now = time.time()
            if (
                not force
                and self._value
                and self._program
                and now - self._fetched_at < self._ttl
            ):
                return self._value, self._program
            try:
                value, program = self._fetch(
                    proxies=proxies,
                    http_client=http_client,
                )
                self._value = value
                self._program = program
                self._fetched_at = now
                self._save_disk_cache(value, program, now)
                return value, program
            except Exception as exc:
                if self._value and self._program:
                    return self._value, self._program
                raise RuntimeError(
                    f'ds fetch failed for appId={self.app_id}: {exc}'
                ) from exc

    def _fetch(
        self,
        proxies: Optional[dict] = None,
        http_client=None,
    ) -> tuple[str, str]:
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/150.0.0.0 Safari/537.36'
            ),
            'Referer': self.referer,
            'Accept': '*/*',
        }
        last_exc: Optional[Exception] = None
        for attempt in range(2):
            try:
                response = None
                if http_client is not None:
                    try:
                        response = http_client.get(
                            self.url,
                            headers=headers,
                            proxies=proxies,
                            timeout=15,
                        )
                    except Exception as client_err:
                        last_exc = client_err
                if response is None:
                    import requests

                    response = requests.get(
                        self.url,
                        headers=headers,
                        proxies=proxies,
                        timeout=15,
                    )
                response.raise_for_status()
                match = _GETDSS_RE.search(response.text)
                if not match:
                    raise ValueError('ds response does not contain getdss()')
                if '_dsf' not in response.text and '__$c' not in response.text:
                    raise ValueError('ds response does not contain the DS runtime program')
                return match.group(1), response.text
            except Exception as e:
                last_exc = e
                time.sleep(0.5)

        if last_exc:
            raise last_exc
        raise RuntimeError('Unknown error fetching ds')

    def peek(self) -> Optional[str]:
        return self._value

    def peek_program(self) -> Optional[str]:
        return self._program


__all__ = ['DsFetcher']

