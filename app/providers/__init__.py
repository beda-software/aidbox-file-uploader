from typing import TypedDict


class DownloadHeaders(TypedDict):
    url: str
    headers: dict[str, str]
