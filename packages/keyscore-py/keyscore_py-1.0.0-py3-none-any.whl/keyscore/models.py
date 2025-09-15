from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, IO


@dataclass
class HealthResponse:
    status: str


@dataclass
class SourceInfo:
    Key: str
    DisplayName: str
    AllowedTypes: List[str]
    SubSources: Dict[str, str]
    CompositeOf: List[str]


@dataclass
class SourcesResponse:
    sources: Dict[str, SourceInfo]


@dataclass
class HashLookupRequest:
    terms: List[str]


@dataclass
class HashRecord:
    hash: str
    type: str
    plaintext: str
    source: str
    first_seen: str


@dataclass
class HashLookupResponse:
    took: int
    size: int
    results: Dict[str, HashRecord]


@dataclass
class IPLookupRequest:
    terms: List[str]


@dataclass
class IPInfo:
    as_: str | None = None
    city: str | None = None
    country: str | None = None
    countryCode: str | None = None
    isp: str | None = None
    lat: float | None = None
    lon: float | None = None
    org: str | None = None
    region: str | None = None
    regionName: str | None = None
    status: str | None = None
    timezone: str | None = None
    zip: str | None = None


@dataclass
class IPLookupResponse:
    took: int
    size: int
    results: Dict[str, IPInfo]
    errors: Dict[str, str] | None = None


@dataclass
class CountRequest:
    terms: List[str]
    types: List[str]
    source: Optional[str] = None
    wildcard: Optional[bool] = None
    regex: Optional[bool] = None
    operator: Optional[str] = None
    dateFrom: Optional[str] = None
    dateTo: Optional[str] = None


@dataclass
class CountResponse:
    count: int


@dataclass
class DetailedCountResponse:
    counts: Dict[str, int]
    total_count: int
    took: int


@dataclass
class SearchRequest:
    terms: List[str]
    types: List[str]
    source: str
    wildcard: Optional[bool] = None
    regex: Optional[bool] = None
    operator: Optional[str] = None
    dateFrom: Optional[str] = None
    dateTo: Optional[str] = None
    page: Optional[int] = None
    pages: Optional[Any] = None
    pagesize: Optional[int] = None


@dataclass
class SearchResponse:
    results: Dict[str, List[Dict[str, Any]]] | None
    pages: Dict[str, Any] | None
    size: int
    took: int


@dataclass
class MachineInfo:
    buildId: str | None = None
    ip: str | None = None
    userName: str | None = None
    computerName: str | None = None
    operationSystem: str | None = None
    processor: str | None = None
    installedRAM: str | None = None
    graphicsCard: str | None = None
    country: str | None = None
    systemLanguage: str | None = None
    timeZone: str | None = None
    displayResolution: str | None = None
    fileType: str | None = None
    fileTree: List[str] = field(default_factory=list)


@dataclass
class DownloadResult:
    body: IO[bytes]
    content_type: str
    content_length: int
    content_disposition: str