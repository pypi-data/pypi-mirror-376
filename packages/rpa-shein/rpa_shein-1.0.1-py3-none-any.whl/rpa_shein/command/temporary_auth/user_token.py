"""
shein登录完毕后访问账单还是可能需要二级验证
可能访问不同的模块 会在不同的api认证故保留拓展接口
故需要实现一下
"""
import json
import execjs
import random
import requests
from urllib import parse
from typing import Any


class TemporaryAuth:
    def __init__(self) -> None:
        # shein 登录账号密码加密js
        shein_temporar_url = "https://oss-rpa.oss-cn-shenzhen.aliyuncs.com/uploads/shein_js/shein_temporary_auth.js"
        response = requests.get(shein_temporar_url)
        self.tempora_module = execjs.compile(response.text)

    @staticmethod
    def replace_json_rlaceholder(
            _json: dict[str, Any],
            __old: str,
            __new: str) -> dict[str, Any]:
        """把json中的占位符处理掉"""
        temp_json = json.dumps(_json)
        return temp_json.replace(__old, __new)

    @staticmethod
    def uber_trace_id() -> str:
        """生成访问日志id"""
        hex_chars = "0123456789abcdef"
        suffix = ''.join(random.choice(hex_chars) for _ in range(14))
        id = "ff" + suffix
        u = int(random.random() <= 0.1)
        return f"{id}:{id}:0000000000000000:{u}"

    def headers_base(self, path: str, redirect: str):
        """处理请求头

        Args:
            path : 源路径
            redirect : 重定向的url路由

        """
        _redirect = parse.quote(redirect, safe="!'()*-._~")
        base_head = {
            "content-type": "application/json;Charset=utf-8",
            "origin-path": path,
            "origin-url": f"https://sso.geiwohuo.com/#/gsp/{path}?redirectUrl={_redirect}",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "uber-trace-id": self.uber_trace_id(),
            "x-log-visitorid": "__visitorid__"
        }
        _new = '`' + '${localStorage.getItem("burypoint_visitorId")}' + '`'
        head = self.replace_json_rlaceholder(
            base_head, '"__visitorid__"', _new)
        return head

    def password(self, ps: str) -> str:
        """
        加密认证密码
        """
        return self.tempora_module.call("encrypt_password ", ps)

    def generate_generate_api_token(
        self,
        url: str,
        pass_word: str,
        path: str,
        redirect: str
    ) -> str:
        """
        生成认证请求

        Args:
            url : 当前访问认证的url
            pass_word : 密码
            path : 源路径
            redirect : 重定向的url路由

        """
        head = self.headers_base(path, redirect)
        body = {
            "password": self.password(pass_word),
            "type": 1
        }
        _temp = f"""
            fetch("{url}", {{
              "headers": { head } ,
              "referrer": "https://sso.geiwohuo.com/",
              "referrerPolicy": "strict-origin-when-cross-origin",
              "body": JSON.stringify({ body})  ,
              "method": "POST",
              "mode": "cors",
              "credentials": "include"
            }}).then(r=>r.json()).then(r=>callback({{success:true,data:r}}))
        """
        return """
                let  callback = arguments[arguments.length - 1];
                try{ %s }catch(error){callback({success:false, data:error.toString()})}
            """ % _temp

    def from_requests_js(
            self,
            temporary_url: str,
            pass_word: str,
            path: str,
            redirect: str) -> str:
        """
        生成请求url

        Args:
            temporary_url : 当前访问认证的url
            pass_word : 密码
            path : 源路径
            redirect : 重定向的url路由

        return:
            dict[str, Any]
            {success:true,data:{"code":"0","msg":"OK","info":{},"bbl":{}}} 正确回调
            {success:false,data:`error_info`}  异常回调

        """
        requests_struct = self.generate_generate_api_token(
            temporary_url, pass_word, path, redirect)
        return requests_struct


if __name__ == "__main__":
    temporary_auth = TemporaryAuth()
    str_js = temporary_auth.from_requests_js(
        "https://sso.geiwohuo.com/gsp/common/user/temporaryAuth",
        'dFHVd4b3',
        "/acount-verification",
        "/finance-management/list")
    print(str_js)
