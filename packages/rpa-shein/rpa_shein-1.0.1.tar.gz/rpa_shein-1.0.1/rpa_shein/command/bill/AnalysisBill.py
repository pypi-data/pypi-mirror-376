import uuid
import zipfile
import base64
import typing
import binascii
import requests
import json
import pandas as pd

from io import BytesIO


class SheinDataHandle:

    def shein_bill_file_identify(self, _content: bytes):
        """读取下载回来的文件类型 并按照类型处理相对应的处理"""
        header = _content[:4096]
        if not header.startswith(b'PK\x03\x04'):
            raise ValueError(f"当前文件类型不是zip及xlsx，无法处理文件类型相关操作")
        # 判断是XLSX文件还是zip
        is_xlsx = b'[Content_Types].xml' in header and b'xl/' in header
        _temp = []
        if is_xlsx:
            # xlsx 处理
            data = self.bs64_xlsx_to_json(_content, False, 1)
            for sheet in data:
                _temp.extend(data[sheet])
        else:
            # zip 处理
            data_list = self.handle_zip(_content)
            for data in data_list:
                for sheet in data:
                    _temp.extend(data[sheet])
        return _temp

    def handle_zip(self, _content):
        """
        获取所有xlsx相关的名称
        """
        # 读取文件文件列表
        with zipfile.ZipFile(BytesIO(_content)) as zip_ref:
            file_list = zip_ref.namelist()
            xlsx_files = [f for f in file_list if f.lower().endswith('.xlsx')]
            return self.iterative_proces(xlsx_files, zip_ref)

    def iterative_proces(self, file_names, zip_ref):
        """批量读取xlsx"""
        _temp = []
        for file_name in file_names:
            with zip_ref.open(file_name) as excel_file:
                # 使用 BytesIO 作为中间缓冲
                excel_bytes = excel_file.read()
                data = self.bs64_xlsx_to_json(excel_bytes, False, 1)
                _temp.append(data)
        return _temp

    def bs64_xlsx_to_json(self, data, b64=True, header_row=0):
        """
            将Base64编码的xlsx文件转换为JSON格式

        Args:
            data: 输入数据，可以是base64字符串或原始字节
            b64: 是否需要base64解码（默认True）
            header_row: 指定哪一行作为列名（表头），默认第0行（第一行）
            Returns:
        list: 各工作表的数据，格式为 [{sheet_name: records}, ...]
        Raises:
            ValueError: 数据不是有效的Base64或Excel格式
        """
        try:
            decoded_bytes = base64.b64decode(data) if b64 else data
        except binascii.Error:
            """
            参数并不是Base64编码
            """
            raise ValueError("The parameter is not bs64")
        xlsx_file = BytesIO(decoded_bytes)
        try:
            df = pd.read_excel(xlsx_file, sheet_name=None, header=header_row)
        except Exception as e:
            raise ValueError(f"Failed to read Excel: {str(e)}")

        all_sheet_data = {}
        for key in list(df.keys()):
            df[key].fillna("", inplace=True)
            all_sheet_data[key] = df[key].to_dict(orient="records")
        return all_sheet_data


class AnalysisBill:
    """负责解析并下载并处理账单"""

    def __init__(self) -> None:
        self.shein_data_handle = SheinDataHandle()

    def download(self, url, cookies={}) -> typing.Union[None, bytes]:
        """下载表格文件"""
        try:
            response = requests.get(url, cookies=cookies, timeout=30)
        except TimeoutError:
            assert False, "下载文件超时"
        except Exception as error:
            assert False, f"下载文件异常，异常信息{error}"
        assert response.status_code == 200, "下载文件异常响应状态"
        return response.content

    def analysis_bill_data(self, url: str) -> typing. Iterator[dict[str, typing.Any]]:
        """处理账单"""
        response = self.download(url)
        data = self.shein_data_handle.shein_bill_file_identify(response)
        return self.sharding_data(data, 100)

    def sharding_data(
        self,
        data: list[dict[str, typing.Any]],
        number: int
    ) -> typing. Iterator[dict[str, typing.Any]]:
        """
        处理账单并分片
        """
        total = len(data)
        uid = uuid.uuid4()
        _temp = [data[i:i+number] for i in range(0, len(data), number)]
        for idx, data in enumerate(_temp):
            yield {
                "request_id": str(uid),                            # 当前访问uuid
                "page_number": idx+1,                              # 数据页数
                "page_size":  number,                              # 分页大小
                "list_count": len(data),                           # 当前列表数据总数
                "total_count": total,                              # 所有数据总数
                "response":  json.dumps(data, ensure_ascii=False)  # 当前数据列表
            }
