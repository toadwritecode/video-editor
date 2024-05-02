import asyncio
import json
import os.path
import uuid
from typing import Callable

from message_buffer import BaseMessageBuffer

mb = BaseMessageBuffer()


def _load_json() -> dict | None:
    if os.path.exists('db/results.json'):
        with open('db/results.json', "r", encoding='utf-8') as f:
            data = json.load(f)
        return data


def get_result_task(task_id: str):
    results_tasks = _load_json()

    if results_tasks:
        return results_tasks.get(task_id)


def save_results_task(task: dict):
    results_tasks = _load_json() or {}

    results_tasks.update({task.get("task"): task.get('result')})

    with open('db/results.json', "w", encoding='utf-8') as f:
        json.dump(results_tasks, f)


def create_task(func: Callable, kwargs: dict):
    task_id = uuid.uuid4()
    mb.put({'id': str(task_id), 'task': func, 'kwargs': kwargs})
    return task_id


def execute_task(task):
    if task:
        return {'task': task.get('id'),
                'result': task.get('task')(**task.get('kwargs'))}


async def run_async_tasks_handling():
    while True:
        task = mb.get()

        result = execute_task(task)
        if result:
            save_results_task(result)

        await asyncio.sleep(1)


if __name__ == '__main__':
    try:
        asyncio.run(run_async_tasks_handling())
    except (KeyboardInterrupt, SystemExit):
        raise
