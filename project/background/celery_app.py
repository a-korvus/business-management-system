"""Celery app in project."""

import asyncio
import functools
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    ParamSpec,
    Self,
    Tuple,
    TypeAlias,
    TypeVar,
    overload,
)

from celery import Celery
from celery.app.task import Task
from celery.schedules import crontab
from kombu.utils.objects import cached_property  # type:ignore [import-untyped]

from project.config import settings

P = ParamSpec("P")
R = TypeVar("R")

P_deco = ParamSpec("P_deco")
R_deco = TypeVar("R_deco")

DecoratorFactoryType: TypeAlias = Callable[
    [Callable[P_deco, Awaitable[R_deco]]], Task
]


class AsyncCelery(Celery):
    """Async Celery object."""

    @cached_property
    def loop(self) -> asyncio.AbstractEventLoop:
        """Ensure that event loop exists."""
        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop

    @overload
    def W(self: Self, func: Callable[P_deco, Awaitable[R_deco]]) -> Task: ...

    @overload
    def W(
        self: Self,
        *task_options_args: Any,
        **task_options_kwargs: Any,
    ) -> DecoratorFactoryType[P_deco, R_deco]: ...

    def W(
        self: Self,
        *task_options_args: Any,
        **task_options_kwargs: Any,
    ) -> Task | DecoratorFactoryType[P_deco, R_deco]:
        """Wrapper for async tasks.

        Enable use of async def functions as Celery tasks.

        Can be used as a simple decorator:
            @app.W
            async def my_async_task(x, y):
                return await ...

        Or with Celery task options:
            @app.W(name="custom_task_name", bind=True, rate_limit='10/m')
            async def another_async_task(self, a, b): # 'self' if bind=True
                return await ...
        """
        func_to_decorate: Callable[P_deco, Awaitable[R_deco]] | None = None
        actual_celery_task_args: Tuple[Any, ...] = task_options_args

        if (
            len(task_options_args) == 1
            and callable(task_options_args[0])
            and not task_options_kwargs
        ):
            func_to_decorate = task_options_args[0]
            actual_celery_task_args = ()

        def decorator_logic(
            async_func_inner: Callable[P_deco, Awaitable[R_deco]],
        ) -> Task:
            """Inner logic creating Celery Task."""
            synchronous_wrapper: Callable[P_deco, R_deco] = (
                _async_task_wrapper(async_func_inner)
            )

            celery_task_options: Dict[str, Any] = {"accept_greenlet": True}
            celery_task_options.update(task_options_kwargs)

            return self.task(*actual_celery_task_args, **celery_task_options)(
                synchronous_wrapper
            )

        if func_to_decorate:
            return decorator_logic(func_to_decorate)
        else:
            return decorator_logic


def _async_task_wrapper(
    async_func: Callable[P, Awaitable[R]],
) -> Callable[P, R]:
    """Inner wrapper to run async functions inside the Celery."""

    @functools.wraps(async_func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            coro = async_func(*args, **kwargs)
            future = asyncio.run_coroutine_threadsafe(coro, loop)
            return future.result()
        else:
            try:
                return loop.run_until_complete(async_func(*args, **kwargs))
            finally:
                if not loop.is_running() and not loop.is_closed():
                    loop.run_until_complete(loop.shutdown_asyncgens())
                    loop.close()
                    if (
                        asyncio.get_event_loop_policy().get_event_loop()
                        is loop
                    ):
                        asyncio.set_event_loop(None)

    return wrapper


celery_app = AsyncCelery(
    __name__,
    broker=settings.REDIS.url_celery_broker,
    backend=settings.REDIS.url_celery_backend,
    broker_connection_retry_on_startup=True,
    worker_hijack_root_logger=False,
    include=["project.background.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "remove_old_deactivate_users": {
            "task": "project.background.tasks.clear_old_deactivated",
            "schedule": crontab(hour="01", minute="00"),  # каждый день в 01:00
            # "schedule": 30.0,  # каждые 30 сек
            "options": {
                "expires": 300  # истекает через 5 мин после времени запуска
            },
            # 'args': (2, 10),
        },
    },
)
