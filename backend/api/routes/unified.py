"""
统一匿名化API路由
提供统一的RESTful API和WebSocket接口
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Set, Optional
import asyncio
import uuid
from datetime import datetime

from backend.api.models.unified import (
    AnonymizationRequest,
    AnonymizationResponse,
    TaskResponse,
    AnonymizationMethod,
    ErrorResponse,
)
from backend.services.strategies.base import StrategyFactory, AnonymizationStrategy
from src.models.providers.registry import get_registry

router = APIRouter(prefix="/api/unified", tags=["unified_anonymization"])

# 全局任务存储
tasks: Dict[str, AnonymizationResponse] = {}
active_websockets: Dict[str, Set[WebSocket]] = {}


class TaskManager:
    """任务管理器"""

    @staticmethod
    def create_task_id() -> str:
        """创建唯一的任务ID"""
        return f"task_{uuid.uuid4().hex[:12]}"

    @staticmethod
    def create_task(request: AnonymizationRequest, task_id: str) -> AnonymizationResponse:
        """创建新任务"""
        return AnonymizationResponse(
            task_id=task_id,
            status="pending",
            method=request.method,
            config=request.config,
        )

    @staticmethod
    def get_task(task_id: str) -> Optional[AnonymizationResponse]:
        """获取任务"""
        return tasks.get(task_id)

    @staticmethod
    def update_task(task_id: str, **updates):
        """更新任务"""
        if task_id in tasks:
            task = tasks[task_id]
            for key, value in updates.items():
                setattr(task, key, value)
            task.updated_at = datetime.now()


@router.post("/anonymize/sync", response_model=AnonymizationResponse)
async def anonymize_sync(request: AnonymizationRequest):
    """
    同步执行匿名化

    适合小文本（< 500字），直接返回结果
    """
    task_id = TaskManager.create_task_id()

    # 创建任务响应
    task = TaskManager.create_task(request, task_id)
    task.status = "running"
    tasks[task_id] = task

    try:
        # 获取策略
        strategy = StrategyFactory.get_strategy(request.method)

        # 执行匿名化
        result = await strategy.execute(
            request.text,
            request.config
        )

        # 更新任务
        task.status = "completed"
        task.result = result
        task.completed_at = datetime.now()

        return task

    except Exception as e:
        # 错误处理
        task.status = "failed"
        task.error = ErrorResponse(
            code="EXECUTION_ERROR",
            message=str(e),
            details={"type": type(e).__name__}
        )
        raise HTTPException(status_code=500, detail=task.error.dict())


@router.post("/anonymize/async", response_model=TaskResponse)
async def anonymize_async(
    request: AnonymizationRequest,
    background_tasks: BackgroundTasks
):
    """
    异步执行匿名化

    适合大文本或批量处理，返回任务ID，通过WebSocket或轮询获取进度
    """
    task_id = TaskManager.create_task_id()

    # 创建任务
    task = TaskManager.create_task(request, task_id)
    tasks[task_id] = task

    # 添加后台任务
    background_tasks.add_task(execute_anonymization_task, task_id, request)

    return TaskResponse(
        task_id=task_id,
        status="pending",
        message="Task created successfully"
    )


async def execute_anonymization_task(task_id: str, request: AnonymizationRequest):
    """在后台执行匿名化任务"""
    task = tasks.get(task_id)
    if not task:
        return

    try:
        # 更新状态为运行中
        TaskManager.update_task(task_id, status="running")

        # 获取策略
        strategy = StrategyFactory.get_strategy(request.method)

        # 定义进度回调
        async def progress_callback(progress):
            """WebSocket进度回调"""
            await broadcast_progress(task_id, {
                "type": "progress",
                "data": progress.dict()
            })

        # 执行匿名化
        result = await strategy.execute(
            request.text,
            request.config,
            progress_callback if request.options.enable_progress_stream else None
        )

        # 更新任务为完成
        TaskManager.update_task(
            task_id,
            status="completed",
            result=result,
            completed_at=datetime.now()
        )

        # 广播完成消息
        await broadcast_progress(task_id, {
            "type": "complete",
            "task_id": task_id,
            "result": result.dict() if hasattr(result, 'dict') else result
        })

    except Exception as e:
        # 更新任务为失败
        TaskManager.update_task(
            task_id,
            status="failed",
            error=ErrorResponse(
                code="EXECUTION_ERROR",
                message=str(e),
                details={"type": type(e).__name__}
            )
        )

        # 广播失败消息
        await broadcast_progress(task_id, {
            "type": "error",
            "task_id": task_id,
            "error": {"message": str(e)}
        })


@router.get("/task/{task_id}", response_model=AnonymizationResponse)
async def get_task_status(task_id: str):
    """
    查询任务状态

    用于轮询任务进度和结果
    """
    task = TaskManager.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


@router.post("/task/{task_id}/cancel")
async def cancel_task(task_id: str):
    """
    取消正在执行的任务

    注意：实际取消功能需要在执行过程中检查取消标志
    """
    task = TaskManager.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status not in ["pending", "running"]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel task with status: {task.status}")

    TaskManager.update_task(task_id, status="cancelled")

    return {"message": "Task cancelled", "task_id": task_id}


@router.websocket("/progress/{task_id}")
async def anonymize_progress(websocket: WebSocket, task_id: str):
    """
    WebSocket 实时进度推送

    连接此端点以接收任务的实时进度更新
    """
    await websocket.accept()

    # 注册WebSocket连接
    if task_id not in active_websockets:
        active_websockets[task_id] = set()
    active_websockets[task_id].add(websocket)

    try:
        # 发送当前状态
        task = TaskManager.get_task(task_id)
        if task:
            await websocket.send_json({
                "type": "connected",
                "task_id": task_id,
                "status": task.status,
                "message": "Connected to task progress stream"
            })

            # 如果任务已完成，立即发送结果
            if task.status == "completed" and task.result:
                await websocket.send_json({
                    "type": "complete",
                    "task_id": task_id,
                    "result": task.result.dict()
                })
            elif task.status == "failed" and task.error:
                await websocket.send_json({
                    "type": "error",
                    "task_id": task_id,
                    "error": task.error.dict()
                })

        # 保持连接并接收消息
        while True:
            try:
                # 接收客户端消息（可用于取消等操作）
                message = await websocket.receive_json()

                if message.get("action") == "cancel":
                    # 取消任务
                    await cancel_task(task_id)
                    await websocket.send_json({
                        "type": "cancelled",
                        "task_id": task_id
                    })

            except WebSocketDisconnect:
                break

    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })

    finally:
        # 清理WebSocket连接
        if task_id in active_websockets:
            active_websockets[task_id].discard(websocket)


async def broadcast_progress(task_id: str, message: dict):
    """向所有连接的WebSocket广播进度"""
    if task_id not in active_websockets:
        return

    disconnected = set()
    for websocket in active_websockets[task_id]:
        try:
            await websocket.send_json(message)
        except Exception:
            disconnected.add(websocket)

    # 清理断开的连接
    active_websockets[task_id] -= disconnected


@router.get("/methods")
async def list_methods():
    """
    列出所有支持的匿名化方法

    返回方法列表和默认配置
    """
    methods = []

    for method in StrategyFactory.list_methods():
        strategy = StrategyFactory.get_strategy(method)
        methods.append({
            "method": method,
            "name": method.replace("_", " ").title(),
            "default_config": strategy.get_default_config()
        })

    return {"methods": methods}


@router.get("/attributes")
async def list_attributes():
    """
    列出所有支持的敏感属性

    返回属性列表和说明
    """
    from backend.api.models.unified import SensitiveAttribute

    attributes = {
        "income": {"label": "收入水平", "description": "推断用户的收入范围"},
        "education": {"label": "教育程度", "description": "推断用户的学历背景"},
        "gender": {"label": "性别", "description": "推断用户的性别"},
        "relationship_status": {"label": "感情状态", "description": "推断用户的婚姻状况"},
        "age": {"label": "年龄", "description": "推断用户的年龄段"},
        "location": {"label": "居住地点", "description": "推断用户的地理位置"},
        "birth_location": {"label": "出生地", "description": "推断用户的出生地点"},
        "occupation": {"label": "职业", "description": "推断用户的职业类型"},
    }

    return {"attributes": attributes}


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "unified_anonymization_api",
        "timestamp": datetime.now().isoformat(),
        "active_tasks": len([t for t in tasks.values() if t.status == "running"]),
        "total_tasks": len(tasks)
    }
