from time import sleep
from typing import Any, Dict, List

from loguru import logger as LOGGER

from dagwapi.utils import helper
from dagwapi.models.atvr import ATvR_DeviceInfo_popo, ATvR_Status_popo, ATvr_StreamerHost_popo


# -----------------------------------------------------------------------------------
class ATvR_API():
    """
    Interface to the DAGateway service for AndroidTV Remote API
    """
    def __init__(self, gateway_url: str):
        self._base_url: str = f'{gateway_url}/stream'
        self._gateway_connected: bool = False
        self.StreamerApplications: Dict[str, str] = []

    def connect(self):
        LOGGER.warning('check if gateway is available.')
        if not helper.is_gateway_available(self._base_url):
            raise RuntimeError(f'- Unable to connect to gateway {self._base_url}. Down?')

        self.StreamerApplications = self._get_streamer_application_dict()
        self._gateway_connected = True

    #--------------------------------------------------------------
    def discover(self) -> List[ATvr_StreamerHost_popo]:
        """
        Discover AndriodStreamers on local network

        Returns:
            List: List of streamer info dictionaries
        """
        url = f'{self._base_url}/discover'        
        resp = helper.call_api(url)
        self._log_errors(resp.get('errors', {}))
        streamer_hosts: List[ATvr_StreamerHost_popo] = []
        for streamer_dict in resp['payload']:
            host = ATvr_StreamerHost_popo()
            host.load(streamer_dict)
            streamer_hosts.append(host)
        return streamer_hosts

    #--------------------------------------------------------------
    def is_valid(self, mac: str) -> bool:
        """
        Insure a valid connection to the target device (mac)
        
        Args:
            mac (str): Streamer MAC address
        
            Returns:
                True if valid, false if not.
        """
        is_valid = self._gateway_connected
        if is_valid:
            status = self.status(mac)
            is_valid = status.is_valid and status.to_dict().get('is_authorized', False)
        LOGGER.warning(f'- is_valid({mac}): {is_valid} - gateway_connected: {self._gateway_connected}   status.is_valid: {status.is_valid}')
        return is_valid
    
    #--------------------------------------------------------------
    def info(self, mac: str) -> ATvR_DeviceInfo_popo:
        """
        Android Streamer info

        Args:
            mac (str): Streamer MAC address

        Returns:
            ATvR_Device_Info_popo
            
        """        
        url = f'{self._base_url}/info/{mac}'
        resp = helper.call_api(url)
        info_obj: ATvR_DeviceInfo_popo = ATvR_DeviceInfo_popo()
        if resp.get('success', False):
            info_obj.load(resp['payload'])
        else:
            LOGGER.warning(f'info: {resp["msg"]}') # type: ignore
        
        self._log_errors(resp.get('errors', {}))     
        return info_obj

    def status(self, mac: str) -> ATvR_Status_popo:
        """
        Get status info for target streamer

        Args:
            mac (str): Streamer MAC address

        Returns:
            StreamerStatus object
        """
        url = f'{self._base_url}/status/{mac}'
        resp = helper.call_api(url)
        status_obj = ATvR_Status_popo()
        if resp.get('success', False):
            status_obj.load(resp['payload'])
        else:
            LOGGER.warning(f'status: {resp["msg"]}')

        self._log_errors(resp.get('errors', {})) 
        return status_obj

    #--------------------------------------------------------------
    def get_app(self, mac: str) -> str:
        """
        Get streamer current applciation id

        Args:
            mac (str): Streamer MAC address

        Returns:
            str: Resulting application id
        """
        url = f'{self._base_url}/app/{mac}'
        resp = helper.call_api(url)
        # app_id = resp['payload'] if resp['success'] else None
        self._log_errors(resp.get('errors', {})) 
        return resp['payload']

    def set_app(self, mac: str, app_id: str) -> str:
        """
        Set streamer application

        Args:
            mac (str): Streamer MAC address
            app_id (str): Desired application

        Returns:
            str: Resulting input source
        """
        url = f'{self._base_url}/app/{mac}?app_id={app_id}'
        resp = helper.call_api(url, is_post=True)

        self._log_errors(resp.get('errors', {})) 
        LOGGER.warning(f'** set_app() requested: {app_id} returns: {resp["payload"]}')
        return resp['payload']

    #--------------------------------------------------------------
    def turn_on(self, mac: str) -> bool:
        """
        Turn on receiver

        Args:
            mac (str): Streamer MAC address

        Returns:
            bool: Device on = True else False
        """
        url = f'{self._base_url}/on_state/{mac}?on_state=True'
        resp = helper.call_api(url, is_post=True)
        power_state = self.get_power(mac)
        retry_cnt = 0
        while power_state != True and retry_cnt < 3:
            retry_cnt += 1
            LOGGER.warning(f'- Checking streamer is on, actual power is [{power_state}] retry {retry_cnt}')
            sleep(.5)
            power_state = self.get_power(mac)

        if power_state == False:
            LOGGER.error('Unable to turn Android Streamer ON.')

        self._log_errors(resp.get('errors', {})) 
        return power_state
        
    def turn_off(self, mac: str) -> bool:
        """
        Turn off receiver

        Args:
            mac (str): Streamer MAC address

        Returns:
            bool: Device off = True else False
        """
        url = f'{self._base_url}/on_state/{mac}?on_state=False'
        resp = helper.call_api(url, is_post=True)
        power_state = self.get_power(mac)
        retry_cnt = 0
        while power_state != False and retry_cnt < 3:
            retry_cnt += 1
            LOGGER.warning(f'- Checking streamer is off, actual power is [{power_state}] retry {retry_cnt}')
            sleep(1)
            power_state = self.get_power(mac)

        if power_state == True:
            # TODO: Update resp['errors']  (.add_error())
            LOGGER.error('Unable to turn Android Streamer OFF.')

        self._log_errors(resp.get('errors', {})) 
        return not power_state
    
    def get_power(self, mac: str) -> bool:
        """
        Receiver power state

        Args:
            mac (str): Streamer MAC address

        Returns:
            bool: Receiver power state - True or False
        """
        url = f'{self._base_url}/on_state/{mac}'
        resp = helper.call_api(url)
        return resp['payload']

    #--------------------------------------------------------------
    def get_muted(self, mac: str) -> bool:
        """
        Get receiver mute state

        Args:
            mac (str): Streamer MAC address

        Returns:
            bool: mute state (True or False)
        """        
        url = f'{self._base_url}/mute_state/{mac}'
        resp = helper.call_api(url)

        self._log_errors(resp.get('errors', {})) 
        return resp['payload']

    def toggle_mute(self, mac: str) -> bool:
        """
        Toggle receiver mute state

        Args:
            mac (str): Streamer MAC address

        Returns:
            bool: resulting mute state (True or False)
        """
        is_muted = self.get_muted(mac)
        if is_muted:
            url = f'{self._base_url}/mute_state/{mac}?mute=False'
        else:
            url = f'{self._base_url}/mute_state/{mac}?mute=True'
        resp = helper.call_api(url, is_post=True)
        
        is_muted = self.get_muted(mac)
        
        self._log_errors(resp.get('errors', {})) 
        return is_muted

    def set_muted(self, mac: str, value: bool) -> bool:
        """
        Set receiver mute state

        Args:
            mac (str): Streamer MAC address
            value (bool): True (mute receiver) False (unmute receiver)

        Returns:
            bool: Resulting mute state (True-muted/False-unmuted)
        """
        url = f'{self._base_url}/mute_state/{mac}?mute={value}'
        resp = helper.call_api(url, is_post=True)

        self._log_errors(resp.get('errors', {})) 
        return resp['payload']

    #--------------------------------------------------------------
    def whats_playing(self, mac: str) -> str:
        """
        Get what's playing on the receiver

        Args:
            mac (str): Streamer MAC address

        Returns:
            str: Title of what's playing or None (if nothing is playing)
        """
        # url = f'{self._base_url}/status/{mac}'
        # resp = helper.call_api(url)
        # return resp['value']['title']
        return self.get_app(mac)
    
    #--------------------------------------------------------------
    def get_volume(self, mac: str) -> float:
        """
        Get volume level on reciever

        Args:
            mac (str): Streamer MAC address

        Returns:
            float: resulting volume level
        """
        url = f'{self._base_url}/volume/{mac}'
        resp = helper.call_api(url)

        self._log_errors(resp.get('errors', {})) 
        return resp['payload']
    
    def volume_up(self, mac: str) -> float:
        """
        Turn up volume on reciever (incr of 5)

        Args:
            mac (str): Streamer MAC address

        Returns:
            float: resulting volume level
        """
        url = f'{self._base_url}/volume/{mac}?direction=up'
        resp = helper.call_api(url, is_post=True)
        self._log_errors(resp.get('errors', {})) 
        return resp['payload']

    def volume_down(self, mac: str) -> float:
        """
        Turn down volume on reciever (incr of 5)

        Args:
            mac (str): Streamer MAC address

        Returns:
            float: resulting volume level
        """
        url = f'{self._base_url}/volume/{mac}?direction=down'
        resp = helper.call_api(url, is_post=True)
        self._log_errors(resp.get('errors', {})) 
        return resp['payload']

    #--------------------------------------------------------------
    def go_to_homescreen(self, mac):
        url = f'{self._base_url}/send_key/{mac}?key=HOME'
        resp = helper.call_api(url, is_post=True)

        self._log_errors(resp.get('errors', {})) 
        return resp['payload']

    def go_to_screensaver(self, mac):
        url = f'{self._base_url}/send_key/{mac}?key=HOME'
        resp = helper.call_api(url, is_post=True)
        if resp['success']:
            url = f'{self._base_url}/send_key/{mac}?key=BACK'
            resp = helper.call_api(url, is_post=True)

        self._log_errors(resp.get('errors', {})) 
        return resp['payload']
    
    #--------------------------------------------------------------
    def _get_streamer_application_list(self) -> List[str]:
        '''
        Get list of streamer Application Ids
        '''
        url = f'{self._base_url}/applist'        
        resp = helper.call_api(url)

        self._log_errors(resp.get('errors', {})) 
        return resp['payload']        

    def _get_streamer_application_dict(self) -> Dict:
        '''
        Get application dictionary
        (id, friendly_name)
        '''
        url = f'{self._base_url}/appdict'        
        resp = helper.call_api(url)

        self._log_errors(resp.get('errors', {})) 
        return resp['payload']        

    def _get_streamer_keys_list(self) -> Dict:
        url = f'{self._base_url}/keylist'        
        resp = helper.call_api(url)

        self._log_errors(resp.get('errors', {})) 
        return resp['payload']        

    #--------------------------------------------------------------
    def _log_errors(self, errors: dict):
        for error in errors:
            LOGGER.error(f'- {error["detail"]}')

if __name__ == '__main__':
    import dt_tools.logger.logging_helper as lh    
    import json
    lh.configure_logger(log_level="DEBUG", log_format=lh.DEFAULT_CONSOLE_LOGFMT)
    
    # streamer_api = ATvR_API('http://localhost:8900')
    streamer_api = ATvR_API('http://raspiapp4b:8900')
    streamer_api.connect()
    # LOGGER.info(f'Application dict:\n{streamer_api._get_streamer_application_dict()}')
    LOGGER.info('Discover streamers...')
    remotes = streamer_api.discover()
    LOGGER.info('Streamer(s) discovered:')
    for remote in remotes:
        LOGGER.info(f'  ip: {remote.ip_address:15}  mac: {remote.mac}  bt_mac: {remote.bt_mac}  name: {remote.name}')
    LOGGER.info('')
    # exit()

    LOGGER.info('='*80)
    mac = 'E8:5C:5F:4D:07:57'  # LR-GTV
    mac = '2A:B2:C0:9B:91:31'  # BR1-GTV
    # mac = 'A4:E8:8D:B0:EF:40'  # BR-GTV
    LOGGER.info(f'Using streamer MAC: {mac}')
    LOGGER.info(f'  is_valid: {streamer_api.is_valid(mac)}')
    LOGGER.info(f'Info:\n{json.dumps(streamer_api.info(mac).to_dict(),indent=2)}')
    LOGGER.info(f'status:\n{json.dumps(streamer_api.status(mac).to_dict(),indent=2)}')
    # sleep(2)
    # LOGGER.info('='*80)
    # LOGGER.info(f'GoHome: {json.dumps(streamer_api.go_to_homescreen(mac))}')
    # sleep(2)

    # LOGGER.info('='*80)
    # LOGGER.info(f'NETFLIX: {json.dumps(streamer_api.set_app(mac,"NETFLIX"))}')
    # sleep(2)
    # LOGGER.info(f'status:\n{json.dumps(streamer_api.status(mac).to_dict(),indent=2)}')

    # LOGGER.info('='*80)
    # LOGGER.info(f'ScreenSaver: {json.dumps(streamer_api.go_to_screensaver(mac))}')
    # sleep(3)
    # LOGGER.info(f'status:\n{json.dumps(streamer_api.status(mac).to_dict(),indent=2)}')

    # LOGGER.info('='*80)
    # LOGGER.info(f'APPLETV: {json.dumps(streamer_api.set_app(mac,"APPLETV"))}')
    # sleep(2)
    # LOGGER.info(f'status:\n{json.dumps(streamer_api.status(mac).to_dict(),indent=2)}')
    # LOGGER.info(f'go_home: {json.dumps(streamer_api.go_to_homescreen(mac))}')
    # LOGGER.info(f'status:\n{json.dumps(streamer_api.status(mac).to_dict(),indent=2)}')
    # sleep(2)
    # LOGGER.info('='*80)
    # LOGGER.info(f'turn_off: {json.dumps(streamer_api.turn_off(mac))}')
    # sleep(5)
    # LOGGER.info(f'status:\n{json.dumps(streamer_api.status(mac).to_dict(),indent=2)}')

    # LOGGER.info('='*80)
    # LOGGER.info(f'turn_on: {json.dumps(streamer_api.turn_on(mac))}')
    # LOGGER.info(f'status:\n{json.dumps(streamer_api.status(mac).to_dict(),indent=2)}')
    # sleep(3)

    LOGGER.info('')
    LOGGER.info('Thats all!')
    