from typing import Any, Dict, Mapping, MutableMapping, Optional

JSON = Dict[str, Any]
Headers = Mapping[str, str]
MutableHeaders = MutableMapping[str, str]
Params = Mapping[str, str | int | float | bool]
Timeout = float | tuple[float, float] | None
