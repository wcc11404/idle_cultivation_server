"""测试支持 API。"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import time

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.InitPlayerInfo import reset_player_data_record
from app.core.Dependencies import GameContext, get_game_context, get_write_game_context, get_token_info
from app.core.Logger import logger
from app.schemas.test import (
    ApplyPresetRequest,
    GrantTestPackRequest,
    ResetTestAccountRequest,
    SetEquippedSpellsRequest,
    SetInventoryItemsRequest,
    SetPlayerStateRequest,
    SetProgressStateRequest,
    SetRuntimeStateRequest,
    TestActionResponse,
    UnlockContentRequest,
)
from unit_test.presets.test_presets import get_supported_presets
from unit_test.support.test_state_support import (
    apply_preset,
    build_state_summary,
    grant_test_pack,
    is_test_account,
    reset_context_to_initial,
    set_equipped_spells,
    set_inventory_items_exact,
    set_player_state,
    set_progress_state,
    set_runtime_state,
    unlock_content,
    validate_equipped_spells,
    validate_inventory_items,
    validate_progress_state,
    validate_realm_and_level,
    validate_runtime_state,
    validate_unlock_content,
)

router = APIRouter()


def _build_response(
    success: bool,
    operation_id: str,
    timestamp: float,
    reason_code: str,
    reason_data: dict | None = None,
    state_summary: dict | None = None,
) -> TestActionResponse:
    return TestActionResponse(
        success=success,
        operation_id=operation_id,
        timestamp=timestamp,
        reason_code=reason_code,
        reason_data=reason_data or {},
        state_summary=state_summary or {},
    )


def _require_test_account(ctx: GameContext) -> None:
    if not is_test_account(ctx):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅测试账号可调用测试接口"
        )


async def _persist_context(ctx: GameContext) -> None:
    ctx.save()
    ctx.player_data.last_online_at = datetime.now(timezone.utc)
    await ctx.player_data.save()


@router.post("/reset_account", response_model=TestActionResponse)
async def reset_account(
    request: ResetTestAccountRequest,
    ctx: GameContext = Depends(get_write_game_context),
    token_info: dict = Depends(get_token_info),
):
    start_time = time.time()
    _require_test_account(ctx)
    logger.info(
        f"[IN] POST /test/reset_account - {json.dumps(request.dict(), ensure_ascii=False)}"
        f" - account_id: {token_info['account_id']}"
    )

    state_summary = reset_context_to_initial(ctx, include_test_pack=True)
    await reset_player_data_record(
        ctx.account,
        ctx.player_data,
        datetime.now(timezone.utc),
        include_test_pack=True,
    )

    response_data = _build_response(
        True,
        request.operation_id,
        request.timestamp,
        "TEST_RESET_ACCOUNT_SUCCEEDED",
        state_summary=state_summary,
    )
    logger.info(f"[OUT] POST /test/reset_account - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/set_player_state", response_model=TestActionResponse)
async def set_player_state_api(
    request: SetPlayerStateRequest,
    ctx: GameContext = Depends(get_write_game_context),
    token_info: dict = Depends(get_token_info),
):
    start_time = time.time()
    _require_test_account(ctx)
    logger.info(
        f"[IN] POST /test/set_player_state - {json.dumps(request.dict(), ensure_ascii=False)}"
        f" - account_id: {token_info['account_id']}"
    )

    realm_for_validation = request.realm if request.realm is not None else (ctx.player.realm if request.realm_level is not None else None)
    validation_error = validate_realm_and_level(realm_for_validation, request.realm_level)
    if validation_error:
        return _build_response(False, request.operation_id, request.timestamp, validation_error)

    realm_to_apply = request.realm if request.realm is not None else (ctx.player.realm if request.realm_level is not None else None)
    state_summary = set_player_state(
        ctx,
        realm=realm_to_apply,
        realm_level=request.realm_level,
        spirit_energy=request.spirit_energy,
        health=request.health,
    )
    await _persist_context(ctx)

    response_data = _build_response(
        True,
        request.operation_id,
        request.timestamp,
        "TEST_SET_PLAYER_STATE_SUCCEEDED",
        state_summary=state_summary,
    )
    logger.info(f"[OUT] POST /test/set_player_state - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/set_inventory_items", response_model=TestActionResponse)
async def set_inventory_items_api(
    request: SetInventoryItemsRequest,
    ctx: GameContext = Depends(get_write_game_context),
    token_info: dict = Depends(get_token_info),
):
    start_time = time.time()
    _require_test_account(ctx)
    logger.info(
        f"[IN] POST /test/set_inventory_items - {json.dumps(request.dict(), ensure_ascii=False)}"
        f" - account_id: {token_info['account_id']}"
    )

    validation_error = validate_inventory_items(request.items)
    if validation_error:
        return _build_response(False, request.operation_id, request.timestamp, validation_error)

    try:
        state_summary = set_inventory_items_exact(ctx, request.items)
    except ValueError:
        return _build_response(False, request.operation_id, request.timestamp, "TEST_SET_INVENTORY_ITEMS_CAPACITY_EXCEEDED")

    await _persist_context(ctx)
    response_data = _build_response(
        True,
        request.operation_id,
        request.timestamp,
        "TEST_SET_INVENTORY_ITEMS_SUCCEEDED",
        state_summary=state_summary,
    )
    logger.info(f"[OUT] POST /test/set_inventory_items - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/unlock_content", response_model=TestActionResponse)
async def unlock_content_api(
    request: UnlockContentRequest,
    ctx: GameContext = Depends(get_write_game_context),
    token_info: dict = Depends(get_token_info),
):
    start_time = time.time()
    _require_test_account(ctx)
    logger.info(
        f"[IN] POST /test/unlock_content - {json.dumps(request.dict(), ensure_ascii=False)}"
        f" - account_id: {token_info['account_id']}"
    )

    validation_error = validate_unlock_content(request.spell_ids, request.recipe_ids, request.furnace_ids)
    if validation_error:
        return _build_response(False, request.operation_id, request.timestamp, validation_error)

    state_summary = unlock_content(
        ctx,
        spell_ids=request.spell_ids,
        recipe_ids=request.recipe_ids,
        furnace_ids=request.furnace_ids,
    )
    await _persist_context(ctx)
    response_data = _build_response(
        True,
        request.operation_id,
        request.timestamp,
        "TEST_UNLOCK_CONTENT_SUCCEEDED",
        state_summary=state_summary,
    )
    logger.info(f"[OUT] POST /test/unlock_content - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/set_equipped_spells", response_model=TestActionResponse)
async def set_equipped_spells_api(
    request: SetEquippedSpellsRequest,
    ctx: GameContext = Depends(get_write_game_context),
    token_info: dict = Depends(get_token_info),
):
    start_time = time.time()
    _require_test_account(ctx)
    logger.info(
        f"[IN] POST /test/set_equipped_spells - {json.dumps(request.dict(), ensure_ascii=False)}"
        f" - account_id: {token_info['account_id']}"
    )

    validation_error = validate_equipped_spells(ctx, request.breathing, request.active, request.opening)
    if validation_error:
        return _build_response(False, request.operation_id, request.timestamp, validation_error)

    state_summary = set_equipped_spells(
        ctx,
        breathing=request.breathing,
        active=request.active,
        opening=request.opening,
    )
    await _persist_context(ctx)
    response_data = _build_response(
        True,
        request.operation_id,
        request.timestamp,
        "TEST_SET_EQUIPPED_SPELLS_SUCCEEDED",
        state_summary=state_summary,
    )
    logger.info(f"[OUT] POST /test/set_equipped_spells - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/set_progress_state", response_model=TestActionResponse)
async def set_progress_state_api(
    request: SetProgressStateRequest,
    ctx: GameContext = Depends(get_write_game_context),
    token_info: dict = Depends(get_token_info),
):
    start_time = time.time()
    _require_test_account(ctx)
    logger.info(
        f"[IN] POST /test/set_progress_state - {json.dumps(request.dict(), ensure_ascii=False)}"
        f" - account_id: {token_info['account_id']}"
    )

    validation_error = validate_progress_state(request.tower_highest_floor, request.daily_dungeon_remaining_counts)
    if validation_error:
        return _build_response(False, request.operation_id, request.timestamp, validation_error)

    state_summary = set_progress_state(
        ctx,
        tower_highest_floor=request.tower_highest_floor,
        daily_dungeon_remaining_counts=request.daily_dungeon_remaining_counts,
    )
    await _persist_context(ctx)
    response_data = _build_response(
        True,
        request.operation_id,
        request.timestamp,
        "TEST_SET_PROGRESS_STATE_SUCCEEDED",
        state_summary=state_summary,
    )
    logger.info(f"[OUT] POST /test/set_progress_state - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/set_runtime_state", response_model=TestActionResponse)
async def set_runtime_state_api(
    request: SetRuntimeStateRequest,
    ctx: GameContext = Depends(get_write_game_context),
    token_info: dict = Depends(get_token_info),
):
    start_time = time.time()
    _require_test_account(ctx)
    logger.info(
        f"[IN] POST /test/set_runtime_state - {json.dumps(request.dict(), ensure_ascii=False)}"
        f" - account_id: {token_info['account_id']}"
    )

    validation_error = validate_runtime_state(request.current_area_id)
    if validation_error:
        return _build_response(False, request.operation_id, request.timestamp, validation_error)

    state_summary = set_runtime_state(
        ctx,
        is_cultivating=request.is_cultivating,
        is_alchemizing=request.is_alchemizing,
        is_in_lianli=request.is_in_lianli,
        is_battling=request.is_battling,
        current_area_id=request.current_area_id,
    )
    await _persist_context(ctx)
    response_data = _build_response(
        True,
        request.operation_id,
        request.timestamp,
        "TEST_SET_RUNTIME_STATE_SUCCEEDED",
        state_summary=state_summary,
    )
    logger.info(f"[OUT] POST /test/set_runtime_state - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/apply_preset", response_model=TestActionResponse)
async def apply_preset_api(
    request: ApplyPresetRequest,
    ctx: GameContext = Depends(get_write_game_context),
    token_info: dict = Depends(get_token_info),
):
    start_time = time.time()
    _require_test_account(ctx)
    logger.info(
        f"[IN] POST /test/apply_preset - {json.dumps(request.dict(), ensure_ascii=False)}"
        f" - account_id: {token_info['account_id']}"
    )

    if request.preset_name not in get_supported_presets():
        return _build_response(
            False,
            request.operation_id,
            request.timestamp,
            "TEST_APPLY_PRESET_NOT_FOUND",
            {"preset_name": request.preset_name},
        )

    state_summary = apply_preset(ctx, request.preset_name)
    await _persist_context(ctx)
    response_data = _build_response(
        True,
        request.operation_id,
        request.timestamp,
        "TEST_APPLY_PRESET_SUCCEEDED",
        {"preset_name": request.preset_name},
        state_summary=state_summary,
    )
    logger.info(f"[OUT] POST /test/apply_preset - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/grant_test_pack", response_model=TestActionResponse)
async def grant_test_pack_api(
    request: GrantTestPackRequest,
    ctx: GameContext = Depends(get_write_game_context),
    token_info: dict = Depends(get_token_info),
):
    start_time = time.time()
    _require_test_account(ctx)
    logger.info(
        f"[IN] POST /test/grant_test_pack - {json.dumps(request.dict(), ensure_ascii=False)}"
        f" - account_id: {token_info['account_id']}"
    )

    try:
        state_summary = grant_test_pack(ctx)
    except ValueError:
        return _build_response(False, request.operation_id, request.timestamp, "TEST_GRANT_TEST_PACK_INVENTORY_FULL")

    await _persist_context(ctx)
    response_data = _build_response(
        True,
        request.operation_id,
        request.timestamp,
        "TEST_GRANT_TEST_PACK_SUCCEEDED",
        state_summary=state_summary,
    )
    logger.info(f"[OUT] POST /test/grant_test_pack - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.get("/state_summary", response_model=TestActionResponse)
async def get_state_summary(
    ctx: GameContext = Depends(get_game_context),
    token_info: dict = Depends(get_token_info),
):
    start_time = time.time()
    _require_test_account(ctx)
    logger.info(f"[IN] GET /test/state_summary - account_id: {token_info['account_id']}")
    response_data = TestActionResponse(
        success=True,
        operation_id="",
        timestamp=time.time(),
        reason_code="TEST_STATE_SUMMARY_SUCCEEDED",
        reason_data={},
        state_summary=build_state_summary(ctx),
    )
    logger.info(f"[OUT] GET /test/state_summary - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data
