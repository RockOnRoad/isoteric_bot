"""Handlers package."""

__all__ = (
    "start_rtr",
    "admin_rtr",
    "ai_portraits_rtr",
    "bio_rtr",
    "dc_rtr",
    "lk_rtr",
    "mnt_rtr",
    "tu_rtr",
    "readings_rtr",
    "witch_rtr",
)

from aiogram import Router

from routers.start_hand import rtr as start_rtr
from routers.admin_hand import rtr as admin_rtr
from routers.ai_portraits_hand import ai_portraits_rtr
from routers.bio_hand import bio_rtr
from routers.daily_card import dc_rtr
from routers.lk_hand import lk_rtr
from routers.maintenance_hand import mnt_rtr
from routers.deposit_hand import tu_rtr
from routers.readings_hand import readings_rtr
from routers.witch_hand import witch_rtr

router = Router(name=__name__)
router.include_routers(
    start_rtr,
    admin_rtr,
    ai_portraits_rtr,
    bio_rtr,
    dc_rtr,
    lk_rtr,
    mnt_rtr,
    tu_rtr,
    readings_rtr,
    witch_rtr,
)
