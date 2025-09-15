"""
    数据鉴权及获取基类
    添加一些基础的功能
"""
import json
import random
from typing import Any

from selenium.webdriver.chrome.webdriver import WebDriver

from rpa_common.request.TaskRequest import TaskRequest
from rpa_shein.command.temporary_auth import user_token

taskRequest = TaskRequest()


class BaseData():
    def __init__(self) -> None:
        self.temporary_auth = user_token.TemporaryAuth()

    @staticmethod
    def execute_script(code: str):
        """处理js回调"""
        _temp_code = """
                let  callback = arguments[arguments.length - 1];
                try{ %s }catch(error){callback({success:false, data:error.toString()})}
            """ % code
        return _temp_code

    @staticmethod
    def send(data):
        res = taskRequest.save(data)
        # 存储都异常了无需执行后面的直接报错
        assert res.get("code") == 1, f"存储数据异常:{res.get('msg')}"

    @staticmethod
    def uber_trace_id() -> str:
        """生成访问日志id"""
        hex_chars = "0123456789abcdef"
        suffix = ''.join(random.choice(hex_chars) for _ in range(14))
        id = "ff" + suffix
        u = int(random.random() <= 0.1)
        return f"{id}:{id}:0000000000000000:{u}"

    @staticmethod
    def replace_json_rlaceholder(
        _json: dict[str, Any],
        __old: str,
        __new: str
    ) -> dict[str, Any]:
        """把json中的占位符处理掉"""
        temp_json = json.dumps(_json)
        return temp_json.replace(__old, __new)

    def identification(self, driver: WebDriver, js: str, password: str):
        """查看当前请求是否需要二次验证需要则验证后再次请求"""
        result = driver.execute_async_script(js)
        find_bill_result_data = result.get("data", {})
        find_code = find_bill_result_data.get('code')
        # 9993003就是需要二次验证
        if find_code == "9993003":
            # pdb.set_trace()
            certification = self.certification(
                temporary_url="https://sso.geiwohuo.com/gsp/common/user/temporaryAuth",
                pass_word=password,
                path="/acount-verification",
                redirect="/finance-management/list")
            # 二次认证
            certification_result = driver.execute_async_script(certification)
            success = certification_result.get("success")
            assert success, f"当前二次认证失败{json.dumps(certification_result)}"
            # 认证完毕后再次运行js
            result = driver.execute_async_script(js)
            find_bill_result_data = result.get("data", {})

        return find_bill_result_data

    def add_visitorid(self, head: dict[str, Any]):
        """给请求头添加日志id"""
        head.update({"x-log-visitorid": "__visitorid__"})
        _new = '`'
        _new += '${localStorage.getItem("burypoint_visitorId")}'
        _new += '`'
        return self.replace_json_rlaceholder(head, '"__visitorid__"', _new)

    def certification(
        self,
        *,
        temporary_url: str,
        pass_word: str,
        path: str,
        redirect: str
    ) -> str:
        """
            鉴权
            部分数据访问前都需要先鉴权一波
        """
        return self.temporary_auth.\
            from_requests_js(
                temporary_url,
                pass_word,
                path,
                redirect
            )
