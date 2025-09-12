from typing import Any, Dict

class LoaderEnabled():
    def __init__(self):
        self._loaded = False
    
    @property
    def is_valid(self) -> bool:
        return self._loaded
    
    def load(self, data_dict: dict):
        # self.__dict__.update(data_dict)
        for key, val in data_dict.items():
            setattr(self, key, val)
            self._loaded = True

    def to_dict(self) -> Dict[str, Any]:
        data_dict: dict = {}
        for key, val in self.__dict__.items():
            if not key.startswith('_'):
                data_dict[key] = val
        return data_dict
        
# popo = Property Only, Python Object
class ATvr_StreamerHost_popo(LoaderEnabled):
    def __init__(self):
        self.name: str       = '' 
        self.ip_address: str = ''
        self.mac: str        = ''
        self.bt_mac: str     = ''

class ATvR_DeviceInfo_popo(LoaderEnabled):
    def __init__(self):
        self.host: str           = ''
        self.mac: str          = ''
        self.manufacturer: str = ''
        self.model: str        = ''
        self.sw_version: str   = ''

class ATvR_Status_popo(LoaderEnabled):
    def __init__(self):
        self.on_state: bool  = False
        self.muted: bool     = False
        self.volume: int     = -1
        self.max_volume: int = -1
        self.current_app: str = ''
