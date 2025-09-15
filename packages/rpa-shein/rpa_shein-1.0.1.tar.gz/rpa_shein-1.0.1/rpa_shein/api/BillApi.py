
import json
import random
import uuid
import rpa_common.exceptions as exceptions

from typing import Any
from datetime import datetime, timedelta


from rpa_shein.api.base import BaseData

from selenium.webdriver.chrome.webdriver import WebDriver
from rpa_common.request.TaskRequest import TaskRequest
from rpa_shein.command.bill.AnalysisBill import AnalysisBill

analysisBill = AnalysisBill()
taskRequest = TaskRequest()


class billApiCertificationBase(BaseData):
    """
    账单基类
    二次鉴权相关操作及一些通用方法
    """

    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def is_valid_date(date_str: str) -> bool:
        """测试时间是否是yy-mm-dd格式"""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False


class BillApi(billApiCertificationBase):
    """获取shein所选日期账单"""

    def __init__(self) -> None:
        super().__init__()
        host = "https://sso.geiwohuo.com"
        self.certification_urls = {
            # shein账单鉴权url
            "url": f"{host}/gsp/common/user/temporaryAuth",
            # shein账单鉴权路径
            "path": "/acount-verification",
            # shein账单鉴权回调url
            "redirect": "/finance-management/list"
        }
        self.bill_dict = {
            # shein查询是否存在账单数据url
            "find_bill_url": f"{host}/gsp/finance/platform/payedList",
            # shein账单导出
            "export_platform_payed": f"{host}/gspJob/common/file/export/exportPlatformPayedCheck",
            # shein导出账单状态url
            "file_export": f"{host}/sso/common/fileExport/list",
            # shein获取导出id的下载地址
            "get_file_url": f"{host}/sso/common/fileExport/getFileUrl"
        }

    @staticmethod
    def analysis_bill_find(find_bill_result: dict[str, Any]) -> bool:
        """解析查询的数据是否有数据有则进入下一流程"""
        json_data = json.dumps(find_bill_result)
        find_bill_result.get("code") == "0", f"查询账单数据异常,{json_data}"
        info = find_bill_result.get("info", {})
        data = info.get("data")
        meta = info.get("meta")
        return False if isinstance(data, list) and len(data) == 0 and meta.get("count") < 1 else True

    @staticmethod
    def analysis_export(export_data: dict[str, Any]):
        """检查导出账单状态是否正常"""
        export_data.get("code") == "0", f"导出账单异常,{json.dumps(export_data)}"

    @staticmethod
    def analysis_export_status(export_status_data: dict[str, Any]):
        """检查导出的账单是否生成完毕或是否有异常"""
        json_data = json.dumps(export_status_data)
        id = export_status_data.get("id")
        assert id, f"查询导出账单异常,{json_data}"
        return id

    @staticmethod
    def analysis_file_result(file_data: dict[str, Any]):
        """检查使用id查询的url是否有异常"""
        assert file_data.get(
            "code") == "0", f"获取账单下载链接失败,{json.dumps(file_data)}"
        info = file_data.get("info", {})
        url = info.get("url")
        assert url, "获取下载链接为空无法获取数据"
        return url

    def find_bill(self, start_date, end_date):
        """查询当前日期是否有账单数据

        Args:
            start_date :开始时间
            end_date :结束时间
        """
        all(
            [
                self.is_valid_date(start_date),
                self.is_valid_date(end_date)
            ]
        ), "当前传递账单日期格式不是yy-mm-dd"

        head = {
            "accept": "*/*",
            "content-type": "application/json;Charset=utf-8",
            "origin-path":  self.certification_urls['redirect'],
            "origin-url": "https://sso.geiwohuo.com/#/gsp/finance-management/list",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "uber-trace-id": self.uber_trace_id(),

        }
        head = self.add_visitorid(head)
        body = {
            "page": 1,
            "perPage": 10,
            "payBeginTime": f"{start_date} 00:00:00",
            "payEndTime": f"{end_date} 23:59:59"
        }
        temp = f"""
            fetch("{self.bill_dict['find_bill_url']}", {{
              "headers": {head},
              "referrer": "https://sso.geiwohuo.com/",
              "referrerPolicy": "strict-origin-when-cross-origin",
              "body": JSON.stringify({body}),
              "method": "POST",
              "mode": "cors",
              "credentials": "include"
            }})
            .then(r=>r.json())
            .then(r=>callback({{success:true,data:r}}));
        """
        return self.execute_script(temp)

    def export_platform_body(self, start_date:str, end_date:str) -> dict[str, str]:
        """
        生成导出账单body数据
        Args:
            start_date : 开始时间
            end_date : 结束时间
        """
        all(
            [
                self.is_valid_date(start_date),
                self.is_valid_date(end_date)
            ]
        ), "当前传递账单日期格式不是yy-mm-dd"
        body = {
            "type": 29,
            "mode": 2,
            "page": 1,
            "perPage": 10,
            "payBeginTime": f"{start_date} 00:00:00",
            "payEndTime": f"{end_date} 23:59:59"
        }
        return body

    def export_platform_requests(self, start_date: str, end_date: str) -> str:
        """
        生成导出账单js

        Args:
            start_date : 开始时间
            end_date : 结束时间
        """
        head = {
            "accept": "*/*",
            "content-type": "application/json;Charset=utf-8",
            "origin-path":  self.certification_urls['redirect'],
            "origin-url": "https://sso.geiwohuo.com/#/gsp/finance-management/list",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "uber-trace-id": self.uber_trace_id(),
        }
        head = self.add_visitorid(head)
        temp = f"""
            fetch("{ self.bill_dict['export_platform_payed']}", {{
              "headers":{head} ,
              "referrer": "https://sso.geiwohuo.com/",
              "referrerPolicy": "strict-origin-when-cross-origin",
              "body": JSON.stringify({self.export_platform_body(start_date,end_date)}),
              "method": "POST",
              "mode": "cors",
              "credentials": "include"
            }})
            .then(r=>r.json())
            .then(r=>callback({{success:true,data:r}}));
        """
        return self.execute_script(temp)

    def file_export(self) -> str:
        """查询当前导出的账单下载状态"""
        head = {
            "accept": "*/*",
            "content-type": "application/json;Charset=utf-8",
            "origin-path":  self.certification_urls['redirect'],
            "origin-url": "https://sso.geiwohuo.com/#/gsp/finance-management/list",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "uber-trace-id": self.uber_trace_id(),
        }
        head = self.add_visitorid(head)
        now = datetime.now()
        # 生成今天的23.59.59
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=0)
        e = today_end.strftime("%Y-%m-%d %H:%M:%S")

        # 生成昨天的0.0.0
        # 部分账号有时差，在时差范围内的导出就查询不到
        yesterday = now - timedelta(days=1)
        yesterday_start = yesterday.replace(
            hour=0, minute=0, second=0, microsecond=0)
        s = yesterday_start.strftime("%Y-%m-%d %H:%M:%S")
        body = {
            "page": 1,
            "createTimeStart": s,
            "createTimeEnd": e,
            "perPage": 10
        }
        # 生成查询导出数据的js
        return self.file_export_requests(head, body)

    def file_export_requests(self, head: dict[str, Any], body: dict[str, Any]) -> str:
        """
        生成查询导出账单数据请求
        """
        temp = f"""
            async function fileExport() {{
            let response= await  fetch("https://sso.geiwohuo.com/sso/common/fileExport/list", {{
                    "headers": {head},
                    "referrer": "https://sso.geiwohuo.com/",
                    "referrerPolicy": "strict-origin-when-cross-origin",
                    "body": JSON.stringify({body}),
                    "method": "POST",
                    "mode": "cors",
                    "credentials": "include"
            }}).then(r=>r.json());
            return response;
            }};
            (async()=>{{
            for (let index = 0; index < 10; index++) {{
                let response= await  fileExport()
                if (response?.code!=="0"){{
                    await new Promise((resolve) => setTimeout(resolve, 1000 * 3));
                    continue
                }}
                let data = response?.info?.data
                if ((!data && !Array.isArray(data)) || !data?.length) {{
                await new Promise((resolve) => setTimeout(resolve, 1000 * 3));
                continue
            }}
            const [dataResult] = data;
            let {{fileStatus}} = dataResult;
            if (fileStatus == 1) return callback({{success:true,data:dataResult}});
            await new Promise((resolve) => setTimeout(resolve, 1000 * 3));
            }}
            callback({{success:false,data:"轮询多次未查询到已生成完成的账单"}});
            }})();
            """
        return self.execute_script(temp)

    def get_file_url(self, id: int):
        """获取当前id的下载文件地址"""
        head = {
            "accept": "*/*",
            "gmpsso-language": "CN",
            "origin-path":  self.certification_urls['redirect'],
            "origin-url": "https://sso.geiwohuo.com/#/download-management/list",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "uber-trace-id": self.uber_trace_id(),
            "x-bbl-route": "/download-management/list",
            "x-sso-scene": "gmpsso",
        }
        head = self.add_visitorid(head)
        temp = f"""
            fetch("https://sso.geiwohuo.com/sso/common/fileExport/getFileUrl?id={id}", {{
              "headers":{head},
              "referrer": "https://sso.geiwohuo.com/",
              "referrerPolicy": "strict-origin-when-cross-origin",
              "body": null,
              "method": "GET",
              "mode": "cors",
              "credentials": "include"
            }})
            .then(r=>r.json())
            .then(r=>callback({{success:true,data:r}}))
        """
        return self.execute_script(temp)

    def get_bill(self, *args, **kwargs):
        """获取账单"""
        driver, shop_data, params, *_ = args
        driver: WebDriver
        start_date = params.get("start_date")
        end_date = params.get("end_date")
        password = shop_data.get("password")
        if not all([driver, start_date, end_date, password]):
            raise exceptions.TaskParamsException("传递的账单参数不全无法执行任务")

        # 查看是否有符合日期的账单
        find_bill_js = self.find_bill(start_date, end_date)
        find_bill_result = self.identification(driver, find_bill_js, password)
        is_there_data = self.analysis_bill_find(find_bill_result)
        # 没有数据则直接返回空
        if not is_there_data:
            # 直接完成任务
            return taskRequest.save(
                {
                    "request_id": str(uuid.uuid4()),
                    "page_number": 1,
                    "page_size": 1,
                    "list_count": 1,
                    "total_count": 0,
                    "response":  json.dumps([], ensure_ascii=False),
                    "type_id": params['type_id'],
                    "task_id": params['task_id'],
                    "account_id": params['account_id'],
                })

        # 导出符合任务日期账单
        export_js = self.export_platform_requests(start_date, end_date)
        export_result = self.identification(driver, export_js, password)
        # 检查导出状态，导出有异常会直接抛出无需返回值
        self.analysis_export(export_result)

        # 查询导出的账单是否完成
        export_status_result = self.identification(
            driver,
            self.file_export(),
            password
        )

        # 获取下载账单id
        id = self.analysis_export_status(export_status_result)
        # 获取下载账单url
        get_file_url = self.identification(
            driver,
            self.get_file_url(id),
            password
        )
        url = self.analysis_file_result(get_file_url)
        bill_data = analysisBill.analysis_bill_data(url)
        for bill in bill_data:
            data = {
                **bill,
                "type_id": params['type_id'],
                "task_id": params['task_id'],
                "account_id": params['account_id']}
            self.send(data)




if __name__ == "__main__":
    shein_bill = BillApi()
    export_id = shein_bill.get_file_url(18590117)
    print(export_id)
