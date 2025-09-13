# file: /Users/SL/PythonProject/sl_pos2_api_tool/sl_pos2_api/common.py

import time
import json
import hashlib
import base64
from cryptography.fernet import Fernet


class APPCommon:
    '''
    This class is used to define the common variables and methods for POS2 API.
    '''

    def __init__(self, handle, uid, otp, device_info=None, ticket=None, user_agent=None):
        self.handle = handle
        self.uid = uid
        self.otp = otp
        self.device_info = device_info
        self.ticket = ticket
        if user_agent is None:
            self.user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
