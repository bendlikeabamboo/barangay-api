"""
Main file for the Barangay API.
"""

import time
from typing import Any, Dict, List, Literal

from barangay import BARANGAY, BARANGAY_FLAT, search
from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel

administrative_area_by_id = {area["psgc_id"]: area for area in BARANGAY_FLAT}

app = FastAPI(title="Barangay API")
search_router = APIRouter(tags=["Search"])
forms_router = APIRouter(tags=["Forms"])
psgc_router = APIRouter(tags=["Philippine Standard Geographic Code"])


class SearchBarangayRequest(BaseModel):
    search_string: str
    match_hooks: List[Literal["barangay", "municipality", "province"]] | None = None
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


app.include_router(search_router)
app.include_router(forms_router)
app.include_router(psgc_router)
