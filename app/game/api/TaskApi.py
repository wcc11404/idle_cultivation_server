"""任务系统 API。"""

from datetime import datetime, timezone
import json
import time

from fastapi import APIRouter, Depends

from app.game.application.Dependencies import GameContext, get_game_context, get_token_info, get_write_game_context
from app.core.logging.Logger import logger
from app.game.schemas.TaskSchema import TaskClaimRequest, TaskClaimResponse, TaskListResponse

router = APIRouter()


@router.get("/task/list", response_model=TaskListResponse)
async def task_list(
    ctx: GameContext = Depends(get_game_context),
    token_info: dict = Depends(get_token_info),
):
    start_time = time.time()
    logger.info(
        f"[IN] GET /game/task/list - token: {token_info['token']} - "
        f"account_id: {token_info['account_id']} - token_version: {token_info['token_version']}"
    )
    ctx.task_system.ensure_task_states()
    daily_tasks, newbie_tasks = ctx.task_system.get_task_list_payload()
    response = TaskListResponse(
        success=True,
        operation_id="",
        timestamp=time.time(),
        reason_code="TASK_LIST_SUCCEEDED",
        reason_data={},
        daily_tasks=daily_tasks,
        newbie_tasks=newbie_tasks,
    )
    logger.info(f"[OUT] GET /game/task/list - {json.dumps(response.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response


@router.post("/task/claim", response_model=TaskClaimResponse)
async def task_claim(
    request: TaskClaimRequest,
    ctx: GameContext = Depends(get_write_game_context),
    token_info: dict = Depends(get_token_info),
):
    start_time = time.time()
    logger.info(
        f"[IN] POST /game/task/claim - {json.dumps(request.dict(), ensure_ascii=False)} - "
        f"token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}"
    )
    ctx.task_system.ensure_task_states()
    result = ctx.task_system.claim_task(request.task_id, ctx.inventory_system)
    if result.get("success", False):
        ctx.db_data["task_system"] = ctx.task_system.to_dict()
        ctx.db_data["inventory"] = ctx.inventory_system.to_dict()
        ctx.player_data.data = ctx.db_data
        ctx.player_data.last_online_at = datetime.now(timezone.utc)
        await ctx.player_data.save()

    response = TaskClaimResponse(
        success=bool(result.get("success", False)),
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        reason_code=str(result.get("reason_code", "")),
        reason_data=result.get("reason_data", {}),
        rewards_granted=result.get("rewards_granted", {}),
    )
    logger.info(f"[OUT] POST /game/task/claim - {json.dumps(response.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response
