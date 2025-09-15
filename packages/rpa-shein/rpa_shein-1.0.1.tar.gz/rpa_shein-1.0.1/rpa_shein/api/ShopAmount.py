"""
    资金申报
"""
import uuid
import json
import rpa_common.exceptions as exceptions


from rpa_shein.api.base import BaseData
from selenium.webdriver.chrome.webdriver import WebDriver


class ShopAmount(BaseData):
    def __init__(self) -> None:
        super().__init__()
        host = "https://sso.geiwohuo.com"
        self.urls = {
            # 钱包
            "wallet": f"{host}/mws/mwms/sso/balance/query",
            "overview": f"{host}/gsp/finance/platform/incomeOverview"
        }

    def income_overview(self) -> str:
        """
        在途金额,存在需要二级验证的情况
        """
        head = {
            "accept": "*/*",
            "accept-language": "zh-HK,zh-TW;q=0.9,zh;q=0.8",
            "content-type": "application/json;Charset=utf-8",
            "origin-path": "/finance-management/list",
            "origin-url": "https://sso.geiwohuo.com/#/gsp/finance-management/list",
            "sec-ch-ua-mobile": "?0",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "uber-trace-id": f"{self.uber_trace_id()}",
        }
        temp = f"""
            fetch("{self.urls['overview']}", {{
                "headers": {self.add_visitorid(head)},
                "body": null,
                "method": "GET",
                "mode": "cors",
                "credentials": "include"
                }})            
            .then(r=>r.json())
            .then(r=>callback({{success:true,data:r}}));"""
        return self.execute_script(temp)

    def wallet(self) -> str:
        """
        钱包金额
        """
        body = {
            "reqSystemCode": "mws-front",
            "supplierId": "__supplierId__"
        }
        supplierId = "`"
        supplierId += "${JSON.parse(localStorage.getItem('shein_auth_login_info')).emplid}"
        supplierId += "`"
        body = self.replace_json_rlaceholder(
            body, '"__supplierId__"', supplierId)
        temp = f""" 
        fetch("{self.urls['wallet']}",{{
                "headers": {{
                    "accept": "application/json",
                    "accept-language": "zh-HK,zh-TW;q=0.9,zh;q=0.8",
                    "content-type": "application/json; charset=utf-8",
                    "language": "CN",
                    "origin-url": "https://sso.geiwohuo.com",
                    "sec-ch-ua-mobile": "?0",
                    "sec-fetch-dest": "empty",
                    "sec-fetch-mode": "cors",
                    "sec-fetch-site": "same-origin"
                   }},
                "body": JSON.stringify({body}),
                "method": "POST",
                "mode": "cors",
                "credentials": "include"
                }}) 
            .then(r=>r.json())
            .then(r=>callback({{success:true,data:r}}));
        """
        return self.execute_script(temp)

    def wallet_data(self, *args, **kwargs):
        """钱包"""
        driver, shop_data, options, *_ = args
        driver: WebDriver
        # 获取钱包数据
        wallet_data = driver.execute_async_script(self.wallet())
        assert wallet_data.get( "success") == True, f"获取钱包数据异常:{json.dumps(wallet_data)}"
        self.send_data(options, wallet_data.get("data"))

    def overview_data(self, *args, **kwargs):
        """我的收入 存在需要二级认证的情况"""   
        driver, shop_data, options, *_ = args
        driver: WebDriver
        password = shop_data.get("password")
        if not password:
            raise exceptions.TaskParamsException("未传递密码，无法获取我的收入数据")

        # 经过检测是否需要二级认证的请求会把最外层的解包出来只留下数据
        overview = self.identification(
            driver,
            self.income_overview(),
            password
        )
        assert overview.get("code") == "0", f"获取收入数据异常:{json.dumps(overview)}"
        self.send_data(options, overview)

    def send_data(self, options, data) -> None:
        task_info = {
            "response":  json.dumps(data, ensure_ascii=False),
            "type_id": options['type_id'],
            "task_id": options['task_id'],
            "account_id": options['account_id'],
            "request_id": str(uuid.uuid4())
        }
        self.send(task_info)


if __name__ == "__main__":
    shopAmount = ShopAmount()
    wallet = shopAmount.income_overview()
    print(wallet)
