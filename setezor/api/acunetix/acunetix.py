from fastapi import APIRouter

from .routes.config import router as acunetix_config_router
from .routes.group import router as acunetix_group_router
from .routes.scan import router as acunetix_scan_router
from .routes.target import router as acunetix_target_router
from .routes.report import router as acunetix_report_router


router = APIRouter(prefix="/acunetix", tags=["Acunetix"])

router.include_router(router=acunetix_config_router)
router.include_router(router=acunetix_group_router)
router.include_router(router=acunetix_scan_router)
router.include_router(router=acunetix_target_router)
router.include_router(router=acunetix_report_router)
