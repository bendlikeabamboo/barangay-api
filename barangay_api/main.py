"""
Main file for the Barangay API.
"""

import time
import os
from typing import Any, Dict, List, Literal

# TODO: remove type ignores once barangay package ships py.typed stubs and literal defaults are fixed
from barangay import (  # type: ignore[import-untyped]
    BARANGAY,
    BARANGAY_FLAT,
    DataManager,
    current,
    get_available_dates,
    resolve_date,
    search,
)
from dotenv import load_dotenv
from fastapi import APIRouter, BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from scalar_fastapi import Layout, Theme, get_scalar_api_reference

# Loading dotenv
load_dotenv()

# Building FastAPI application descriptions
desc_none = ""
desc_standard = """
A simple API for searching and retrieving information about barangays in the 
Philippines.

- **Source code**: [Barangay-API GitHub](https://github.com/bendlikeabamboo/barangay-api)
- **Docker image**: [Barangay-API v2026.4.13.0](https://hub.docker.com/r/bendlikeabamboo/barangay-api)
- **Philippines Standard Geographic Code PSGC Reference:** [April 13, 2026 Release](https://psa.gov.ph/classification/psgc/node/1684083211)
- **Barangay Package PyPI:** [![PyPI version](https://badge.fury.io/py/barangay.svg)](https://badge.fury.io/py/barangay)
- **Barangay Package Source Code:** [Barangay GitHub](https://github.com/bendlikeabamboo/barangay)
"""
desc_official_deployment = """
Try it out in live in the official deployment: 
- [Barangay-API (Scalar)](https://barangay-api.hawitsu.xyz/scalar)
- [Barangay-API (SwaggerUI)](https://barangay-api.hawitsu.xyz/docs)
- [Barangay-API (Redoc)](https://barangay-api.hawitsu.xyz/redoc)
"""
desc = (
    (desc_none)
    + (
        desc_standard
        if str(os.getenv("DESC_STANDARD", True)).lower() in ("true", "t", "1")
        else ""
    )
    + (
        desc_official_deployment
        if str(os.getenv("DESC_OFFICIAL_DEPLOYMENT", False)).lower()
        in ("true", "t", "1")
        else ""
    )
)

# Initializing application
app = FastAPI(
    title="Barangay API",
    description=desc,
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
    version="2026.4.13.0",
    openapi_tags=[
        {
            "name": "Search",
            "description": " Friendly, quick fuzzy search for barangays."
            " Use these endpoints when you want a fast, easy way to find a barangay"
            " even if the name isn't typed exactly right.",
        },
        {
            "name": "Forms",
            "description": "Simple, hierarchical lookup of Philippine places."
            " These endpoints return the next level in the hierarchy—regions,"
            " provinces, cities/municipalities, and barangays. You can drill down"
            " from one level to the next regardless of how the hierarchy is"
            " structured. Ideal for drop-down forms.",
        },
        {
            "name": "Philippine Standard Geographic Code (PSGC)",
            "description": "Quick access to PSGC information. "
            "These routes return the official PSGC identifiers and their associated"
            " data for any Philippine locality.",
        },
        {
            "name": "Historical Data",
            "description": "Explore historical PSGC data releases. "
            "Use these endpoints to discover available dates and query data "
            "as it was on a specific PSGC release.",
        },
        {
            "name": "Cache",
            "description": "Manage the local PSGC data cache. "
            "Historical data is downloaded on first use and cached locally. "
            "Use these endpoints to pre-warm the cache and avoid cold-start latency.",
        },
    ],
)
# Adding mounts
app.mount("/static", StaticFiles(directory="static"), name="static")

# Adding routers
search_router = APIRouter(tags=["Search"])
forms_router = APIRouter(tags=["Forms"])
psgc_router = APIRouter(tags=["Philippine Standard Geographic Code (PSGC)"])
history_router = APIRouter(tags=["Historical Data"])
cache_router = APIRouter(prefix="/cache", tags=["Cache"])


# Defining RequestForms (for data validation)
class SearchBarangayRequest(BaseModel):
    search_string: str
    match_hooks: List[Literal["province", "municipality", "barangay"]] | None = Field(  # type: ignore[assignment]
        default=["barangay", "municipality", "province"]
    )
    threshold: float | None = 60
    len_results: int | None = 1
    as_of: str | None = None


class Barangay(BaseModel):
    barangay: str
    province_or_huc: str | None = None
    municipality_or_city: str | None = None
    psgc_id: str


class SearchBarangayResult(BaseModel):
    results: List[Barangay]
    elapsed_seconds: float
    resolved_date: str | None = None


dm = DataManager()
_available_dates = get_available_dates()
_admin_area_by_id = {area["psgc_id"]: area for area in BARANGAY_FLAT}


def get_barangay_data(as_of: str | None):
    if as_of is None:
        return BARANGAY
    return dm.get_data(as_of=as_of, data_type="basic")


def get_barangay_flat_data(as_of: str | None):
    if as_of is None:
        return BARANGAY_FLAT
    return dm.get_data(as_of=as_of, data_type="flat")


def resolve_as_of(as_of: str | None) -> str | None:
    if as_of is None:
        return None
    resolved_date, _ = resolve_date(
        as_of=as_of,
        available_dates=_available_dates,
        current_date=current,
    )
    return resolved_date


def _check_region(region: str, data):
    if region not in list(data.keys()):
        raise HTTPException(
            status_code=404, detail=f"No such region: '{region}'.Try `/regions`?"
        )


def _check_province_or_highly_urbanized_city(
    region: str, province_or_highly_urbanized_city: str, data
):
    if province_or_highly_urbanized_city not in list(data[region].keys()):
        raise HTTPException(
            status_code=404,
            detail=f"No such province or highly urbanized city: "
            f"'{province_or_highly_urbanized_city}'. "
            "Try `/{region}/province_or_highly_urbanized_city?",
        )


def _check_municipality_or_city(
    region: str, province_or_highly_urbanized_city: str, municipality_or_city: str, data
):
    if municipality_or_city not in list(
        data[region][province_or_highly_urbanized_city].keys()
    ) and municipality_or_city not in list(data[region].keys()):
        raise HTTPException(
            status_code=404,
            detail=f"No such municipality or city: "
            f"'{municipality_or_city}'. "
            "Try `'/{region}/{province_or_highly_urbanized_city}/municipality_or_city'",
        )


def _check_id(id: str, admin_area_by_id: dict):
    if id not in admin_area_by_id:
        raise HTTPException(
            status_code=404,
            detail=f"No such id: '{id}'. Are you using the 10-digit PSGC format?",
        )


# RestAPI
@app.get("/scalar", include_in_schema=False)
async def scalar_classic_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title="Barangay API",
        layout=Layout.MODERN,
        dark_mode=True,
        theme=Theme.NONE,
        scalar_favicon_url="/static/favicon.ico",
        default_open_all_tags=True,
    )


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/scalar/")


@search_router.post("/search_barangay")
async def search_barangay(
    search_request: SearchBarangayRequest,
) -> SearchBarangayResult:
    """
    Search for a barangay. Uses [barangay](https://pypi.org/project/barangay) Python
    package. Optionally pass `as_of` (YYYY-MM-DD) to search against historical PSGC data.
    """
    t0 = time.time()
    match_hooks = search_request.match_hooks or ["barangay", "municipality"]
    threshold = search_request.threshold or 60
    n = search_request.len_results or 1
    resolved = resolve_as_of(search_request.as_of)

    if "barangay" not in match_hooks:
        raise HTTPException(
            status_code=400,
            detail="Malformed request: `match_hooks` needs at least 'barangay'. "
            "For example ['barangay', 'municipality']",
        )

    results = search(
        search_string=search_request.search_string,
        match_hooks=match_hooks,
        threshold=threshold,
        n=n,
        as_of=resolved,
    )
    validated_results: List[Barangay] = []
    for result in results:
        validated_results.append(Barangay.model_validate(result))
    return SearchBarangayResult(
        results=validated_results,
        elapsed_seconds=time.time() - t0,
        resolved_date=resolved,
    )


@forms_router.get("/regions")
async def get_regions(as_of: str | None = Query(None)) -> List[str]:
    """
    Return a list of all regions in the Philippines. Optionally pass `as_of`
    (YYYY-MM-DD) to use historical PSGC data.
    """
    return list(get_barangay_data(as_of).keys())


@forms_router.get("/{region}/provinces_and_highly_urbanized_cities")
async def get_provinces_and_highly_urbanized_cities(
    region: str, as_of: str | None = Query(None)
) -> List[str]:
    """
    Return a list of all provinces and highly urbanized cities (HUCs) in the Philippines
    given a region. **Note**: in some unusual cases, this may also return a municipality
    (e.g. Pateros in the National Capital Region).
    """
    data = get_barangay_data(as_of)
    _check_region(region=region, data=data)
    return list(data[region].keys())


@forms_router.get(
    "/{region}/{province_or_highly_urbanized_city}/municipalities_and_cities"
)
async def get_municipalities_and_cities(
    region: str,
    province_or_highly_urbanized_city: str,
    as_of: str | None = Query(None),
) -> List[str]:
    """
    Return a list of all municipalities and cities given a region and a province or
    highly urbanized city (HUC) in the Philippines. **Note**: If an HUC is provided,
    this will simply return the HUC back which you can use as a valid municipality or
    city.
    """
    data = get_barangay_data(as_of)
    _check_region(region=region, data=data)
    _check_province_or_highly_urbanized_city(
        region=region,
        province_or_highly_urbanized_city=province_or_highly_urbanized_city,
        data=data,
    )
    if isinstance(data[region][province_or_highly_urbanized_city], dict):
        return list(data[region][province_or_highly_urbanized_city].keys())
    return [province_or_highly_urbanized_city]


@forms_router.get(
    "/{region}/{province_or_highly_urbanized_city}/{municipality_or_city}/barangays"
)
async def get_barangays(
    region: str,
    province_or_highly_urbanized_city: str,
    municipality_or_city: str,
    as_of: str | None = Query(None),
) -> List[str]:
    data = get_barangay_data(as_of)
    _check_region(region=region, data=data)

    _check_province_or_highly_urbanized_city(
        region=region,
        province_or_highly_urbanized_city=province_or_highly_urbanized_city,
        data=data,
    )

    if isinstance(data[region][province_or_highly_urbanized_city], list):
        return list(data[region][province_or_highly_urbanized_city])

    _check_municipality_or_city(
        region=region,
        province_or_highly_urbanized_city=province_or_highly_urbanized_city,
        municipality_or_city=municipality_or_city,
        data=data,
    )
    return data[region][province_or_highly_urbanized_city][municipality_or_city]


@psgc_router.get("/id/{id}")
async def get_administrative_area_by_id(id: str, as_of: str | None = Query(None)):
    """
    Get administrative area using PSGC ID. Optionally pass `as_of` (YYYY-MM-DD)
    to look up the ID in historical PSGC data.
    """
    if as_of is None:
        _check_id(id, admin_area_by_id=_admin_area_by_id)
        return _admin_area_by_id[id]
    flat = get_barangay_flat_data(as_of)
    admin_area_by_id = {area["psgc_id"]: area for area in flat}
    _check_id(id, admin_area_by_id=admin_area_by_id)
    return admin_area_by_id[id]


@psgc_router.get("/name/{name}")
async def get_administrative_area_by_name(
    name: str, as_of: str | None = Query(None)
) -> List[Dict[str, Any]]:
    """
    Get administrative area using official name from PSGC. Name could be region,
    province, highly urbanized city (HUCs), city, municipality, or barangay.
    Optionally pass `as_of` (YYYY-MM-DD) to search historical PSGC data.
    """
    flat = get_barangay_flat_data(as_of)
    res: List[Dict[str, Any]] = []
    for i in flat:
        if i["name"] == name:
            res.append(i)
    return res


@history_router.get("/history/available_dates")
async def get_available_dates_endpoint() -> list[str]:
    """Return all available PSGC release dates."""
    return _available_dates


class WarmUpResult(BaseModel):
    resolved_date: str
    data_types: List[str]


class WarmUpAllResult(BaseModel):
    dates_warmed: List[str]
    data_types_per_date: Dict[str, List[str]]


def _warm_up_single(resolved_date: str) -> Dict[str, None]:
    results: Dict[str, None] = {}
    for dt in ("basic", "flat", "extended", "fuzzer_base"):
        results[dt] = dm.get_data(as_of=resolved_date, data_type=dt)
    return results


@cache_router.get("/warm_up")
async def warm_up_cache(
    as_of: str | None = Query(None),
) -> WarmUpResult:
    """
    Warm up the cache for a specific date. Downloads and caches all data types
    (basic, flat, extended, fuzzer_base) for the resolved date. If `as_of` is
    not provided, defaults to the current bundled dataset (no-op since it's
    already available in the package).
    """
    resolved = resolve_as_of(as_of)
    if resolved is None:
        resolved = current
    _warm_up_single(resolved)
    return WarmUpResult(
        resolved_date=resolved,
        data_types=["basic", "flat", "extended", "fuzzer_base"],
    )


@cache_router.get("/warm_up_all")
async def warm_up_all_cache(
    background_tasks: BackgroundTasks,
) -> WarmUpAllResult:
    """
    Warm up the cache for all available PSGC release dates. This runs in the
    background since it downloads data for every historical release. Returns
    immediately with the list of dates that will be warmed.
    """
    historical_dates = [d for d in _available_dates if d != current]

    def do_warm_up_all():
        for date in historical_dates:
            _warm_up_single(date)

    background_tasks.add_task(do_warm_up_all)
    return WarmUpAllResult(
        dates_warmed=historical_dates,
        data_types_per_date={
            d: ["basic", "flat", "extended", "fuzzer_base"] for d in historical_dates
        },
    )


# Finally, mounting routers to application
app.include_router(search_router)
app.include_router(forms_router)
app.include_router(psgc_router)
app.include_router(history_router)
app.include_router(cache_router)
