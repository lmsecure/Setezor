from fastapi import APIRouter
from setezor.modules.wappalyzer.wappalyzer import WappalyzerParser

router = APIRouter(
    prefix="/tasks_data",
    tags=["Tasks_data"],
)

@router.get("/wappalyzer-groups")
async def get_wappalyzer_groups():
    wappalyzer_groups = WappalyzerParser.get_groups()
    wappalyzer_name_categories_by_group = WappalyzerParser.get_categories_by_group()
    return {
        "wappalyzer_groups": wappalyzer_groups,
        "wappalyzer_name_categories_by_group": wappalyzer_name_categories_by_group,
    }
