"""puma.http — HTTP matching domain.

Provides HttpRequest context, DataInput implementations,
and a Gateway API compiler for route matching.
"""

from puma.http._gateway import (
    HttpHeaderMatch,
    HttpPathMatch,
    HttpQueryParamMatch,
    HttpRouteMatch,
    compile_route_matches,
)
from puma.http._inputs import HeaderInput, MethodInput, PathInput, QueryParamInput
from puma.http._request import HttpRequest

__all__ = [
    # Context
    "HttpRequest",
    # DataInputs
    "PathInput",
    "MethodInput",
    "HeaderInput",
    "QueryParamInput",
    # Gateway API types
    "HttpPathMatch",
    "HttpHeaderMatch",
    "HttpQueryParamMatch",
    "HttpRouteMatch",
    "compile_route_matches",
]
