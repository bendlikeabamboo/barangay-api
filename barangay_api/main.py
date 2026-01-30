"""
Main file for the Barangay API.
"""

import time
import os
from typing import Any, Dict, List, Literal

from barangay import BARANGAY, BARANGAY_FLAT, search
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, HTTPException
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
- **Docker image**: [Barangay-API v2026.1.13.0](https://hub.docker.com/r/bendlikeabamboo/barangay-api)
- **Philippines Standard Geographic Code PSGC Reference:** [January 13, 2026 Release](https://psa.gov.ph/classification/psgc/node/1684082306)
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
    version="2026.1.13.0",
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
    ],
)
# Adding mounts
app.mount("/static", StaticFiles(directory="static"), name="static")

# Adding routers
search_router = APIRouter(tags=["Search"])
forms_router = APIRouter(tags=["Forms"])
psgc_router = APIRouter(tags=["Philippine Standard Geographic Code (PSGC)"])


# Defining RequestForms (for data validation)
class SearchBarangayRequest(BaseModel):
    search_string: str
    match_hooks: List[Literal["province", "municipality", "barangay"]] | None = Field(
        default=["barangay", "municipality", "province"]
    )
    threshold: float | None = 60
    len_results: int | None = 1


class Barangay(BaseModel):
    barangay: str
    province_or_huc: str | None = None
    municipality_or_city: str | None = None
    psgc_id: str


class SearchBarangayResult(BaseModel):
    results: List[Barangay]
    elapsed_seconds: float


# Helper functions
administrative_area_by_id = {area["psgc_id"]: area for area in BARANGAY_FLAT}


def _check_region(region: str):
    if region not in list(BARANGAY.keys()):
        raise HTTPException(
            status_code=404, detail=f"No such region: '{region}'." "Try `/regions`?"
        )


def _check_province_or_highly_urbanized_city(
    region: str, province_or_highly_urbanized_city: str
):
    if province_or_highly_urbanized_city not in list(BARANGAY[region].keys()):
        raise HTTPException(
            status_code=404,
            detail=f"No such province or highly urbanized city: "
            f"'{province_or_highly_urbanized_city}'. "
            "Try `/{region}/province_or_highly_urbanized_city?",
        )


def _check_municipality_or_city(
    region: str, province_or_highly_urbanized_city: str, municipality_or_city: str
):
    if municipality_or_city not in list(
        BARANGAY[region][province_or_highly_urbanized_city].keys()
    ) and municipality_or_city not in list(BARANGAY[region].keys()):
        raise HTTPException(
            status_code=404,
            detail=f"No such municipality or city: "
            f"'{municipality_or_city}'. "
            "Try `'/{region}/{province_or_highly_urbanized_city}/municipality_or_city'",
        )


def _check_id(id: str):
    if id not in administrative_area_by_id:
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
        theme=Theme.DEEP_SPACE,
        scalar_favicon_url="/static/favicon.ico",
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
    package.
    """
    t0 = time.time()
    match_hooks = search_request.match_hooks or ["barangay", "municipality"]
    threshold = search_request.threshold or 60
    n = search_request.len_results or 1

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
    )
    validated_results: List[Barangay] = []
    for result in results:
        validated_results.append(Barangay.model_validate(result))
    return SearchBarangayResult(
        results=validated_results, elapsed_seconds=time.time() - t0
    )


@forms_router.get("/regions")
async def get_regions() -> List[str]:
    """
    Return a list of all regions in the Philippines.
    """
    return list(BARANGAY.keys())


@forms_router.get("/{region}/provinces_and_highly_urbanized_cities")
async def get_provinces_and_highly_urbanized_cities(region: str) -> List[str]:
    """
    Return a list of all provinces and highly urbanized cities (HUCs) in the Philippines
    given a region. **Note**: in some unusual cases, this may also return a municipality
    (e.g. Pateros in the National Capital Region).
    """
    _check_region(region=region)
    return list(BARANGAY[region].keys())


@forms_router.get(
    "/{region}/{province_or_highly_urbanized_city}/municipalities_and_cities"
)
async def get_municipalities_and_cities(
    region: str, province_or_highly_urbanized_city: str
) -> List[str]:
    """
    Return a list of all municipalities and cities given a region and a province or
    highly urbanized city (HUC) in the Philippines. **Note**: If an HUC is provided,
    this will simply return the HUC back which you can use as a valid municipality or
    city.
    """
    _check_region(region=region)
    _check_province_or_highly_urbanized_city(
        region=region,
        province_or_highly_urbanized_city=province_or_highly_urbanized_city,
    )
    if isinstance(BARANGAY[region][province_or_highly_urbanized_city], dict):
        return list(BARANGAY[region][province_or_highly_urbanized_city].keys())
    return [province_or_highly_urbanized_city]


@forms_router.get(
    "/{region}/{province_or_highly_urbanized_city}/{municipality_or_city}/barangays"
)
async def get_barangays(
    region: str, province_or_highly_urbanized_city: str, municipality_or_city: str
) -> List[str]:
    _check_region(region=region)

    _check_province_or_highly_urbanized_city(
        region=region,
        province_or_highly_urbanized_city=province_or_highly_urbanized_city,
    )

    if isinstance(BARANGAY[region][province_or_highly_urbanized_city], list):
        return list(BARANGAY[region][province_or_highly_urbanized_city])

    _check_municipality_or_city(
        region=region,
        province_or_highly_urbanized_city=province_or_highly_urbanized_city,
        municipality_or_city=municipality_or_city,
    )
    return BARANGAY[region][province_or_highly_urbanized_city][municipality_or_city]


@psgc_router.get("/id/{id}")
async def get_administrative_area_by_id(id: str):
    """
    Get administrative area using PSGC ID
    """
    _check_id(id)
    return administrative_area_by_id[id]


@psgc_router.get("/name/{name}")
async def get_administrative_area_by_name(name: str) -> List[Dict[str, Any]]:
    """
    Get administrative area using official name from PSGC. Name could be region,
    province, highly urbanized city (HUCs), city, municipality, or barangay.
    """
    res: List[Dict[str, Any]] = []
    for i in BARANGAY_FLAT:
        if i["name"] == name:
            res.append(i)
    return res


# Finally, mounting routers to application
app.include_router(search_router)
app.include_router(forms_router)
app.include_router(psgc_router)
