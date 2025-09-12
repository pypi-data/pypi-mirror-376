import requests
import json

from .app_auth import APPAuth


class OrderAPI(APPAuth):
    def hello(self):
        print(self.handle)
        print("hello")
        return "hello"

    def checkout(
            self,
            data,
            lang='zh-hans-cn'
    ):
        """
        发起订单结算请求

        Args:
            request_send_time: 请求发送时间
            otp: 一次性密码
            order_data: 订单数据
        """

        # 构建完整请求URL
        url = f"{self.handle}/sl/apps/pos/app/order/checkout"

        # 请求头
        headers = {
            "content-type": "application/json",
            "uid": self.uid,
            "accept": "*/*",
            "ticket": self.ticket,
            "otp": self.otp,
            "accept-language": "zh-Hans-CN;q=1.0",
            "deviceinfo": self.device_info,
            "user-agent": self.user_agent,
            "lang": lang
        }

        try:
            # 发送POST请求
            response = requests.post(
                url=url,
                headers=headers,
                data=data,
                verify=True
            )
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"请求发生错误: {e}")
            return None

