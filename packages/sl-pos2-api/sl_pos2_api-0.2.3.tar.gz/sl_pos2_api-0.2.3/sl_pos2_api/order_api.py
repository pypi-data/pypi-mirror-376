import requests
import json

from sl_pos2_api.app_auth import APPAuth


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
        # 完成认证流程

        # 构建完整请求URL
        url = f"{self.handle}/sl/apps/pos/app/order/checkout"

        # 请求头
        headers = {
            "content-type": "application/json",
            "uid": self.uid,
            "accept": "*/*",
            "ticket": json.dumps(self.ticket),
            "otp": self.otp,
            "accept-language": "zh-Hans-CN;q=1.0",
            "deviceinfo": json.dumps(self.device_info),
            "user-agent": self.user_agent,
            "lang": lang
        }
        print('checkout headers:', headers)
        print('checkout data:', data)

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


if __name__ == '__main__':
    zpf_url = 'https://uizidonghuaceshi.myshoplinestg.com'
    zpf_uid = '4600508114'
    otp = '0501000001560297eac3686000139605a5cfdde0a32600fff8b7594b202054ee07df66f92139c8c53ae104e68eb515c5ee2fbd36e9a9d24747a6c30bb110bbec94e202291714228352bb5285f4c7a3da34c643b1edab8ddc4db44ce6af56071f4ba537e5494991ba80607f9c299a0000c08b3e109a000290004d3a559b9ed5a9e624c1323e0fb7c58175898f0a09de4b9700f824478461c9324f887207df0b0b8f29c2e672942efbe8520e108ba98bbd4fd684f92e56ebc0fb5ff9fc04cbdc57521d113369bb1d2f2f1310e862f4f675f25c7cbf690e3456b87d82cbbcdf8bac21e45192a4b2a9be6916e57f6a463d3183fef9c491fb605077c89e2c6a3f6cc7ed7613a6aec85782a7'
    ticket = {"storeId": 1709983459019,
              "merchantId": "4600508114",
              "offlineStoreId": 6369562508760987402,
              "posStaffId": 3787}

    device_info = {"os": "ios", "appVersion": "2.15.0", "newDeviceId": "b099a7742a01db20d33a21934ae129d5bbbec77f",
                   "deviceId": "7C92D974-C934-4D63-BC24-DC208916A14D", "brand": "Apple", "osVersion": "17.3.1",
                   "model": "iPhone 13"}

    orderapi = OrderAPI(zpf_url, zpf_uid, otp, ticket=ticket, device_info=device_info)
    data = {
        "openDutyFree": False,
        "productInfos": [
            {
                "price": "100.00",
                "quantity": 1,
                "serviceCharge": False,
                "skuId": "18063695978625661748802405",
                "source": 1,
                "spuId": "16063695978613582153162405",
                "title": "单库存商品001"
            }
        ],
        "roundingType": 0
    }

    data2 = {
        "offlineStoreId": "6369562508760987402",
        "storeId": "1709983459019",
        "uid": "4600508114"
    }
    inner_token = orderapi.get_staff_detail(data2)

    print(orderapi.checkout(data))
