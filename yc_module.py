import json
import subprocess
from io import BytesIO
from typing import List
from config import Settings
import concurrent.futures as concurent_f

import logging
logger = logging.getLogger(__name__)


class NoInstancesException(Exception):
    def __init__(self, message="No Instances for watching"):
        self.message = message
        super().__init__(self.message)


def _get_instances(
        config: Settings, timeout: float = 1.0) -> BytesIO:
    result: BytesIO = BytesIO()
    commands: List[str] = [
        "yc",
        "compute", "instance", "list",
        *config.model_dump()
    ]
    logger.debug(f"Command: {' '.join(commands)}")
    # Выполняем команду в системном шелле
    try:
        process = subprocess.run(
            commands,
            check=True,
            timeout=timeout,
            capture_output=True)
        result.write(process.stdout)
    except subprocess.CalledProcessError as e:
        raise Exception(
            f"Произошла ошибка при получении списка вм {e}")
    except subprocess.TimeoutExpired as e:
        raise Exception(
            f"Процесс завершён по таймауту {e}")
    result.seek(0)
    return result


def _list_unhealthy_instances_ids(
        id2status_list: List) -> List:
    return [id2status["id"] for id2status in id2status_list if id2status["status"] == "STOPPED"]


def _extract_list_instances(yc_data: BytesIO) -> List:
    try:
        instances_list_dict = json.loads(yc_data.getvalue())
    except json.JSONDecodeError as e:
        raise Exception(f"Invalid JSON syntax: {e.msg}")

    list_instances = []
    for instance_dict in instances_list_dict:
        temp_dict = {}
        temp_dict["id"] = instance_dict["id"]
        temp_dict["status"] = instance_dict["status"]
        list_instances.append(temp_dict)

    return list_instances


def _send_up_command(config: Settings, id: str,
                     timeout: float = 10.0) -> BytesIO:
    result: BytesIO = BytesIO()
    commands: List[str] = [
        "yc",
        "compute", "instance",
        "start", id,
        *config.model_dump()
    ]
    # Выполняем команду в системном шелле
    try:
        process = subprocess.run(
            commands,
            check=True,
            timeout=timeout,
            capture_output=True)
        result.write(process.stdout)
    except subprocess.CalledProcessError as e:
        raise Exception(
            f"Произошла ошибка при включении вм {e}")
    except subprocess.TimeoutExpired as e:
        raise Exception(
            f"Процесс завершён по таймауту {e}")
    result.seek(0)
    return result


def up_instances(config: Settings):
    result: BytesIO = _get_instances(config=config, timeout=10.0)
    id2status_list: list = _extract_list_instances(
        yc_data=result)

    logger.debug(id2status_list)
    if len(id2status_list) == 0:
        raise NoInstancesException()

    unhealthy_ids: list = _list_unhealthy_instances_ids(
        id2status_list)

    with concurent_f.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(_send_up_command, config, id)
            for id in unhealthy_ids]
        for future in concurent_f.as_completed(
            futures, timeout=15.0
            ):
            data = future.result()
            logger.debug(
                msg=f"instance {data.getvalue().decode()}")
