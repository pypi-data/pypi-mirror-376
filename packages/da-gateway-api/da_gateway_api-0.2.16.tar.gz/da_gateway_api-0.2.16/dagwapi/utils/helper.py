import random
from threading import Lock
from time import sleep
from typing import Dict

import requests
from loguru import logger as LOGGER

# ==================================================================================
class SingletonMeta(type):
    """
    This is a thread-safe implementation of Singleton.
    """
    _instances = {}
    _lock: Lock = Lock()
    """
    We now have a lock object that will be used to synchronize threads during
    first access to the Singleton.
    """
    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        # Now, imagine that the program has just been launched. Since there's no
        # Singleton instance yet, multiple threads can simultaneously pass the
        # previous conditional and reach this point almost at the same time. The
        # first of them will acquire lock and will proceed further, while the
        # rest will wait here.
        with cls._lock:
            # The first thread to acquire the lock, reaches this conditional,
            # goes inside and creates the Singleton instance. Once it leaves the
            # lock block, a thread that might have been waiting for the lock
            # release may then enter this section. But since the Singleton field
            # is already initialized, the thread won't create a new object.
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs) 
                cls._instances[cls] = instance
        return cls._instances[cls]

# ==================================================================================
def call_api(url: str, is_post: bool = False) -> Dict:
    LOGGER.info(f'DAGatewayAPI call: {url}')
    retry = 0
    server_error = True  # default for 1st cycle
    # Retry up to 3 times on http 500 error
    while server_error and retry < 3:
        if is_post:
            resp = requests.post(url)
        else:
            resp = requests.get(url)
        server_error = True if resp.status_code in [500] else False
        if server_error:
            resp.connection.close()
            retry += 1
            LOGGER.warning(f'{url} retry [{retry}]')
            sleep_secs = random.choice([0.5, 1.0 ,1.5 ,2.0 ])
            sleep(sleep_secs)

    resp_json: dict = {}
    resp_json['success'] = False
    resp_json['command'] = f"[{'POST' if is_post else 'GET'}] {url}"
    resp_json['msg'] = f'[{resp.status_code}] {resp.reason}'
    if resp.status_code < 400:
        try:
            resp_json = resp_json | resp.json()
            resp_json['success'] = True
        except requests.exceptions.JSONDecodeError() as jde: # type: ignore
            LOGGER.error(jde)
        
    log_lvl = "DEBUG" if resp_json['success'] else "ERROR"
    LOGGER.log(log_lvl, f'** {resp_json["msg"]} | {resp_json["command"]} ')

    resp.raise_for_status()
    
    return resp_json

# ==================================================================================
def is_gateway_available(base_url: str) -> bool:
    is_available = False
    try:
        url = f'{base_url}/ping'
        call_api(url)
        is_available = True
    except Exception as ex:
        msg = f'Unable to connect [{url}].\n{ex}.\nIs the site down?'
        LOGGER.error(msg)
    
    return is_available
