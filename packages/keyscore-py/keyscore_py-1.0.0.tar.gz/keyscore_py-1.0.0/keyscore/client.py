from __future__ import annotations
import json
import typing as t
from dataclasses import asdict
from io import BufferedReader
from urllib.parse import urlencode

import requests

from .models import (
    CountRequest,
    CountResponse,
    DetailedCountResponse,
    DownloadResult,
    HashLookupRequest,
    HashLookupResponse,
    IPLookupRequest,
    IPLookupResponse,
    MachineInfo,
    SearchRequest,
    SearchResponse,
    SourcesResponse,
    HealthResponse,
    SourceInfo,
    HashRecord,
    IPInfo,
)


class APIError(Exception):
    def __init__(self, status_code: int, message: str | None = None):
        self.status_code = status_code
        self.message = message or ""
        super().__init__(f"keysco.re API error: status={status_code} message={self.message!r}" if self.message else f"keysco.re API error: status={status_code}")


class Client:
    def __init__(
        self,
        base_url: str = "https://api.keysco.re",
        api_key: str | None = None,
        session: requests.Session | None = None,
        timeout: float | tuple[float, float] = 60.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = session or requests.Session()
        self.timeout = timeout

    def _headers(self, has_body: bool) -> dict[str, str]:
        h = {}
        if has_body:
            h["Content-Type"] = "application/json"
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def _request(self, method: str, path: str, params: dict[str, t.Any] | None = None, body: t.Any | None = None) -> requests.Response:
        url = f"{self.base_url}{path}"
        if params:
            url = f"{url}?{urlencode(params, doseq=True)}"
        data = None
        if body is not None:
            data = json.dumps(body if not hasattr(body, "__dataclass_fields__") else asdict(body))
        resp = self.session.request(method, url, data=data, headers=self._headers(body is not None), timeout=self.timeout)
        return resp

    def _do_json(self, resp: requests.Response) -> dict[str, t.Any]:
        if not (200 <= resp.status_code < 300):
            try:
                payload = resp.json()
                msg = payload.get("error") if isinstance(payload, dict) else None
            except Exception:
                msg = None
            raise APIError(resp.status_code, msg)
        if resp.content in (b"", None):
            return {}
        try:
            return resp.json()
        except Exception as e:
            raise APIError(resp.status_code, f"decode response: {e}")

    def health(self) -> HealthResponse:
        resp = self._request("GET", "/health")
        data = self._do_json(resp)
        return HealthResponse(**data)

    def sources(self) -> SourcesResponse:
        resp = self._request("GET", "/sources")
        data = self._do_json(resp)
        sources_map = {k: SourceInfo(**v) for k, v in data.get("sources", {}).items()}
        return SourcesResponse(sources=sources_map)

    def count(self, req: CountRequest) -> CountResponse:
        resp = self._request("POST", "/count", body=asdict(req))
        data = self._do_json(resp)
        return CountResponse(**data)

    def count_detailed(self, req: CountRequest) -> DetailedCountResponse:
        resp = self._request("POST", "/count/detailed", body=asdict(req))
        data = self._do_json(resp)
        return DetailedCountResponse(**data)

    def search(self, req: SearchRequest) -> SearchResponse:
        resp = self._request("POST", "/search", body=asdict(req))
        data = self._do_json(resp)
        return SearchResponse(
            results=data.get("results"),
            pages=data.get("pages"),
            size=data.get("size", 0),
            took=data.get("took", 0),
        )

    def hash_lookup(self, req: HashLookupRequest) -> HashLookupResponse:
        resp = self._request("POST", "/hashlookup", body=asdict(req))
        data = self._do_json(resp)
        results = {k: HashRecord(**v) for k, v in data.get("results", {}).items()}
        return HashLookupResponse(
            took=data.get("took", 0),
            size=data.get("size", 0),
            results=results,
        )

    def ip_lookup(self, req: IPLookupRequest) -> IPLookupResponse:
        resp = self._request("POST", "/iplookup", body=asdict(req))
        data = self._do_json(resp)
        results: dict[str, IPInfo] = {}
        for k, v in data.get("results", {}).items():
            v = dict(v)
            if "as" in v:
                v["as_"] = v.pop("as")
            results[k] = IPInfo(**v)
        return IPLookupResponse(
            took=data.get("took", 0),
            size=data.get("size", 0),
            results=results,
            errors=data.get("errors"),
        )

    def machine_info(self, uuid: str) -> MachineInfo:
        resp = self._request("GET", "/machineinfo", params={"uuid": uuid})
        data = self._do_json(resp)
        machine_data = data.get("data", data)

        valid_fields = {
            "buildId", "ip", "userName", "computerName", "operationSystem",
            "processor", "installedRAM", "graphicsCard", "country",
            "systemLanguage", "timeZone", "displayResolution", "fileType", "fileTree"
        }
        
        normalized = {}
        for key, value in machine_data.items():
            if key in ["operatingSystem", "OperatingSystem", "osVersion"]:
                normalized["operationSystem"] = value
            elif key in ["buildId", "BuildID", "buildid"]:
                normalized["buildId"] = value
            elif key in ["ip", "IP", "ipAddress"]:
                normalized["ip"] = value
            elif key in ["userName", "UserName", "username"]:
                normalized["userName"] = value
            elif key in ["computerName", "ComputerName", "computername"]:
                normalized["computerName"] = value
            elif key in ["processor", "Processor", "cpuName"]:
                normalized["processor"] = value
            elif key in ["installedRAM", "InstalledRAM", "ramSize"]:
                normalized["installedRAM"] = value
            elif key in ["graphicsCard", "GraphicsCard"]:
                normalized["graphicsCard"] = value
            elif key == "gpus" and isinstance(value, list) and value:
                normalized["graphicsCard"] = value[0]
            elif key in ["country", "Country"]:
                normalized["country"] = value
            elif key in ["systemLanguage", "SystemLanguage", "language"]:
                normalized["systemLanguage"] = value
            elif key in ["timeZone", "TimeZone", "timezone"]:
                normalized["timeZone"] = value
            elif key in ["displayResolution", "DisplayResolution", "screenResolution"]:
                normalized["displayResolution"] = value
            elif key in ["fileType", "FileType"]:
                normalized["fileType"] = value
            elif key == "fileTree":
                normalized["fileTree"] = value or []
            elif key in valid_fields:
                normalized[key] = value
        
        return MachineInfo(**normalized)

    def download(self, uuid: str, file_path: str | None = None) -> DownloadResult:
        params: dict[str, t.Any] = {"uuid": uuid}
        if file_path:
            params["file"] = file_path
        url = f"{self.base_url}/download?{urlencode(params)}"
        headers = self._headers(False)
        resp = self.session.get(url, headers=headers, timeout=self.timeout, stream=True)
        if not (200 <= resp.status_code < 300):
            try:
                payload = resp.json()
                msg = payload.get("error") if isinstance(payload, dict) else None
            except Exception:
                msg = None
            raise APIError(resp.status_code, msg)
        return DownloadResult(
            body=resp.raw,
            content_type=resp.headers.get("Content-Type", ""),
            content_length=int(resp.headers.get("Content-Length", "0") or 0),
            content_disposition=resp.headers.get("Content-Disposition", ""),
        )