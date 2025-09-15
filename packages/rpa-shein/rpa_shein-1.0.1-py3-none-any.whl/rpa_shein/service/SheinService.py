
import time
import json
import random
import execjs
import typing
import requests
from rpa_common import Common
from rpa_common.request import ShopRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from rpa_common.service.EmailService import EmailService
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC

common = Common()
shopRequest = ShopRequest()
emailService = EmailService()


class SheinService:
    """负责shein账号密码登录
    """

    def __init__(self) -> None:
        self.private_key = "c9c793e1aaacb20a3bb2c40b6aadad120e8825898809a95e90462ca91b1ae416"
        # 当前文件负责生成shein body参数加密
        response = requests.get(
            "https://oss-rpa.oss-cn-shenzhen.aliyuncs.com/uploads/shein_js/shein_encrypt.js")
        self.login_encrypy = execjs.compile(response.text)

    @staticmethod
    def execute_script(code: str) -> str:
        _temp_code = """
                let  callback = arguments[arguments.length - 1];
                try{ %s }catch(error){callback({success:false, data:error.toString()})}
            """ % code
        return _temp_code

    @staticmethod
    def saveStorage(
        driver: WebDriver,
        shop_global_id: dict[str, typing.Any]
    ) -> None:

        cookies = driver.execute_cdp_cmd(
            "Network.getCookies", {}).get("cookies")
        storage_data = {
            "shop_global_id": shop_global_id,
            "cookies": json.dumps(cookies)
        }
        # 存储cookie 异常的话不管
        shopRequest.saveStorage(storage_data)

    @staticmethod
    def uber_trace_id() -> str:
        """生成访问日志id"""
        hex_chars = "0123456789abcdef"
        suffix = ''.join(random.choice(hex_chars) for _ in range(14))
        id = "ff" + suffix
        u = int(random.random() <= 0.1)
        return f"{id}:{id}:0000000000000000:{u}"

    def generate_request_login_str(self, body) -> str:
        """生成登录请求"""
        request_str = """
                    (async () => {
                        fetch("https://sso.geiwohuo.com/sso/authenticate/login",
                            {
                                headers: {
                                    "accept": "*/*",
                                    "origin-url": location.href,
                                    "Content-Type": "application/json",
                                    // 就一个随机值估计记录id
                                    "uber-trace-id": '%s',
                                    "time-zone": Intl.DateTimeFormat().resolvedOptions().timeZone,
                                    "gmpsso-language": "CN",
                                    // shein 自研人机校验
                                    "anti-in": await window.AntiIn.getAllEncrypted(),
                                    // shein 自研设备指纹
                                    "uberctx-armortoken": window.AntiDevices.getArmorToken(),
                                    // 数美环境校验
                                    "uberctx-smdeviceid": window.SMSdk.getDeviceId(),
                                    "x-bbl-route": location.hash.replace("#", ""),
                                    "x-sso-scene": "gmpsso",
                                    "SSO-Frontend-Version": "1.0.0"
                                },
                                body: JSON.stringify(%s),
                                "method": "POST",
                                "mode": "cors",
                                credentials: "include"
                            })
                            .then(r => r.json())
                            .then(r => {
                                  if (r.code === "E10302") {
                                        setTimeout(()=>{  location.href = r.info.redirect },500)
                                        callback(
                                            { success: true, data: JSON.stringify(r) })

                                     }
                                    else {
                                        callback(
                                            { success: false, data: JSON.stringify(r) })
                                    }
                            })})()  """
        return request_str % (self.uber_trace_id(), body)

    def generate_js_request(
            self,
            username: str,
            pass_word: str,
            *,
            to=True,
            riskControl={"blackbox": "__JS_BLACKBOX__"},
            validCode="") -> str:
        """
        处理占位符并生成加密js
        to  是否生成to访问参数
        riskControl 验证时候的凭证
        validCode 验证码
        """
        enc_pass_word = self.encrypy_pass_word(pass_word)
        # 让其他验证的地方直接访问到账号密码
        self.username = username
        self.pass_word = pass_word

        sing = self.encrypy_sing(username, enc_pass_word)
        body = {
            "username": username,
            "password": enc_pass_word,
            "verificationType": "2",
            "validCode": validCode,
            "service": "",
            "to": "",
            "challenge": "",
            "riskControl": riskControl,
            "sign": sing,
        }
        if to:
            body["to"] = "__JS_TO_"
        body_json = json.dumps(body)
        body_json = body_json.replace(
            '"__JS_TO_"', '`' + '${location.href.split("/").slice(-1).join("")}' + '`')
        body_json = body_json.replace(
            '"__JS_BLACKBOX__"', '`' + '${window.blackbox}||""' + '`,')
        return self.generate_request_login_str(body_json)

    def encrypy_pass_word(self, password: str) -> str:
        """加密密码"""
        return self.login_encrypy.call("fnencrypt", password)

    def encrypy_sing(self, username: str, enc_pass_word: str) -> str:
        """获取账号密码私钥凭证"""
        _temp = self.private_key + '&' + username + '&' + enc_pass_word
        return self.login_encrypy.call("sing", _temp, self.private_key)

    def execute_login_script(
            self,
            driver: WebDriver,
            js_code: str,
            email: str,
            auth_code: str
    ) -> typing.Union[None, bool]:
        """ 登录shein """
        result: typing.Dict = driver.execute_async_script(
            self.execute_script(js_code))
        result_login = result.get('data', '{}')
        result_login = json.loads(result_login)
        login_info = result_login.get("info", {})
        #  022008 则表示需要登录
        if result_login.get("code", "") == "022008":
            bizId = login_info.get("bizId", "")
            riskId = login_info.get("riskId", "")
            email = email
            auth_code = auth_code
            code = False
            start = time.time()
            # shein验证码延迟较高故等待5秒
            time.sleep(5)
            while time.time() - start < 30:
                get_verify_code = emailService.get_verify_code(
                    "shein_verifycode", {
                        "platform": "163",
                        "email": email,
                        "auth_code": auth_code
                    })
                code = get_verify_code.get("data", False)
                if code:
                    break
                time.sleep(1)

            assert code, "未获取到邮件验证码"

            js_code = self.generate_js_request(
                self.username,
                self.pass_word,
                to=False,
                riskControl={
                    "bizId": bizId,
                    "riskId": riskId,
                    "blackbox": "__JS_BLACKBOX__"
                },
                validCode=code
            )
            js_code = self.execute_script(js_code)

            email_verify = driver.execute_async_script(js_code)
            if not email_verify.get("success"):
                data = json.loads(email_verify.get('data', '{}'))
                raise Exception(f"登录失败:{data.get('msg','')}")
            return True

        # 其他异常直接抛出
        assert result.get('success', False), f"登录异常：{ result_login}"

        return result.get('data', "")

    def login(
        self,
        driver: WebDriver,
        data: typing.Dict,
        options: typing.Dict
    ) -> typing.Union[bool, None]:

        login_name = data.get("login_name")
        password = data.get("password")
        email_data = data.get("email_data", {})

        email = email_data.get("email")
        auth_code = email_data.get("auth_code")

        params = options.get("params", {})
        shop_global_id = params.get("shop_global_id")

        error_str = f"缺少必要登录数据,login_name:{login_name},\
              password:{password},\
              email:{email},\
              auth_code:{auth_code},\
              shop_global_id:{shop_global_id}"
        assert all([login_name, password, email, auth_code]), error_str

        driver.get("https://sso.geiwohuo.com/#/login")
        # 等待登录按钮元素出现
        wait = WebDriverWait(driver, 15)
        try:
            wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".so-button")))
        except Exception as error:
            raise Exception(f"SHEIN等待登录首页加载超时,{error}")

        storage_data = data.get("storage_data", {})
        if storage_data and storage_data.get("cookies"):
            cookies = storage_data.get("cookies")
            for cookie in cookies:
                driver.execute_cdp_cmd("Network.setCookie", cookie)
            driver.get("https://sso.geiwohuo.com/#/home")
            WebDriverWait(driver, 15)
            # 查看是否出现了首页
            try:
                wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".shein-components_soc-fe-sso-sdk_label")))
                self.saveStorage(driver, shop_global_id)
                return True
            except Exception:
                # 等待首页超时 走账号密码登录逻辑
                ...
        requset_str = self.generate_js_request(login_name, password)
        login_result = self.execute_login_script(
            driver, requset_str, email, auth_code)

        self.saveStorage(driver, shop_global_id)
        return login_result


if __name__ == "__main__":
    test = SheinService()
    username = "test"
    password = "test"
    requset_str = test.generate_js_request(username, password)
    print(requset_str)
