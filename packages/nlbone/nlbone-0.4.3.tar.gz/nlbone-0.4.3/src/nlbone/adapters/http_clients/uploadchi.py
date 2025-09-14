from __future__ import annotations

import json
from typing import Any, Optional
from urllib.parse import urlparse, urlunparse

import httpx
import requests

from nlbone.adapters.auth.token_provider import ClientTokenProvider
from nlbone.config.settings import get_settings
from nlbone.core.ports.files import FileServicePort


class UploadchiError(RuntimeError):
    def __init__(self, status: int, detail: Any | None = None):
        super().__init__(f"Uploadchi HTTP {status}: {detail}")
        self.status = status
        self.detail = detail


def _resolve_token(explicit: str | None) -> str | None:
    if explicit is not None:
        return explicit
    s = get_settings()
    return s.UPLOADCHI_TOKEN.get_secret_value() if s.UPLOADCHI_TOKEN else None


def _auth_headers(token: str | None) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"} if token else {}


def _build_list_query(
        limit: int, offset: int, filters: dict[str, Any] | None, sort: list[tuple[str, str]] | None
) -> dict[str, Any]:
    q: dict[str, Any] = {"limit": limit, "offset": offset}
    if filters:
        q["filters"] = json.dumps(filters)
    if sort:
        q["sort"] = ",".join([f"{f}:{o}" for f, o in sort])
    return q


def _filename_from_cd(cd: str | None, fallback: str) -> str:
    if not cd:
        return fallback
    if "filename=" in cd:
        return cd.split("filename=", 1)[1].strip("\"'")
    return fallback


def _normalize_https_base(url: str) -> str:
    p = urlparse(url.strip())
    p = p._replace(scheme="https")  # enforce https
    if p.path.endswith("/"):
        p = p._replace(path=p.path.rstrip("/"))
    return str(urlunparse(p))


class UploadchiClient(FileServicePort):
    def __init__(
            self,
            token_provider: ClientTokenProvider | None = None,
            base_url: Optional[str] = None,
            timeout_seconds: Optional[float] = None,
            client: httpx.Client | None = None,
    ) -> None:
        s = get_settings()
        self._base_url = _normalize_https_base(base_url or str(s.UPLOADCHI_BASE_URL))
        self._timeout = timeout_seconds or float(s.HTTP_TIMEOUT_SECONDS)
        self._client = client or requests.session()
        self._token_provider = token_provider

    def close(self) -> None:
        self._client.close()

    def upload_file(
            self, file_bytes: bytes, filename: str, params: dict[str, Any] | None = None, token: str | None = None
    ) -> dict:
        tok = _resolve_token(token)
        files = {"file": (filename, file_bytes)}
        data = (params or {}).copy()
        r = self._client.post(self._base_url, files=files, data=data, headers=_auth_headers(tok))
        if r.status_code >= 400:
            raise UploadchiError(r.status_code, r.text)
        return r.json()

    def commit_file(self, file_id: str, token: str | None = None) -> None:
        if not token and not self._token_provider:
            raise UploadchiError(detail="token_provider is not provided", status=400)
        tok = _resolve_token(token)
        r = self._client.post(
            f"{self._base_url}/{file_id}/commit",
            headers=_auth_headers(tok),
        )
        if r.status_code not in (204, 200):
            raise UploadchiError(r.status_code, r.text)

    def rollback(self, file_id: str, token: str | None = None) -> None:
        if not token and not self._token_provider:
            raise UploadchiError(detail="token_provider is not provided", status=400)
        tok = _resolve_token(token)
        r = self._client.post(
            f"{self._base_url}/{file_id}/rollback",
            headers=_auth_headers(tok),
        )
        if r.status_code not in (204, 200):
            raise UploadchiError(r.status_code, r.text)

    def list_files(
            self,
            limit: int = 10,
            offset: int = 0,
            filters: dict[str, Any] | None = None,
            sort: list[tuple[str, str]] | None = None,
            token: str | None = None,
    ) -> dict:
        tok = _resolve_token(token)
        q = _build_list_query(limit, offset, filters, sort)
        r = self._client.get(self._base_url, params=q, headers=_auth_headers(tok))
        if r.status_code >= 400:
            raise UploadchiError(r.status_code, r.text)
        return r.json()

    def get_file(self, file_id: str, token: str | None = None) -> dict:
        tok = _resolve_token(token)
        r = self._client.get(f"{self._base_url}/{file_id}", headers=_auth_headers(tok))
        if r.status_code >= 400:
            raise UploadchiError(r.status_code, r.text)
        return r.json()

    def download_file(self, file_id: str, token: str | None = None) -> tuple[bytes, str, str]:
        tok = _resolve_token(token)
        r = self._client.get(f"{self._base_url}/{file_id}/download", headers=_auth_headers(tok))
        if r.status_code >= 400:
            raise UploadchiError(r.status_code, r.text)
        filename = _filename_from_cd(r.headers.get("content-disposition"), fallback=f"file-{file_id}")
        media_type = r.headers.get("content-type", "application/octet-stream")
        return r.content, filename, media_type

    def delete_file(self, file_id: str, token: str | None = None) -> None:
        tok = _resolve_token(token)
        r = self._client.delete(f"{self._base_url}/{file_id}", headers=_auth_headers(tok))
        if r.status_code not in (204, 200):
            raise UploadchiError(r.status_code, r.text)
