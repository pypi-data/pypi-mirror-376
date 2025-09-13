from typing import Any

from mzapi.utlis.tencent_auth import TencentCloudAuth


class GeneralBasicOCR:
    """
    腾讯云通用文字识别 (General Basic OCR)
    文档: https://cloud.tencent.com/document/product/866/33526
    """

    def __init__(self, secret_id:str, secret_key:str):
        """
        初始化

        :param secret_id: 腾讯云 SecretId
        :param secret_key: 腾讯云 SecretKey
        """
        self.auth = TencentCloudAuth(secret_id, secret_key)
        self.service = "ocr"
        self.action = "GeneralBasicOCR"
        self.version = "2018-11-19"
        self.endpoint = "ocr.tencentcloudapi.com"

    def recognize(
        self,
        region: str,
        image_base64: str | None = None,
        image_url: str | None = None,
        language_type: str = "zh",
        is_pdf: bool = False,
        pdf_page_number: int = 1,
        is_words: bool = False
    ) -> dict[str, Any]:
        """
        识别图片中的文字        识别图片中的文字

        :param image_base64: 图片的 Base64 值。
                             支持的图片格式：PNG、JPG、JPEG，暂不支持 GIF 格式。
                             支持的图片大小：所下载图片经 Base64 编码后不超过 7M。图片下载时间不超过 3 秒。
                             图片存储于腾讯云的 Url 可保障更高下载速度和稳定性，建议图片存储于腾讯云。
                             非腾讯云存储的 Url 速度和稳定性可能受一定影响。
        :param image_url: 图片的 Url 地址。
                          支持的图片格式：PNG、JPG、JPEG，暂不支持 GIF 格式。
                          支持的图片大小：所下载图片经 Base64 编码后不超过 7M。图片下载时间不超过 3 秒。
                          图片存储于腾讯云的 Url 可保障更高下载速度和稳定性，建议图片存储于腾讯云。
                          非腾讯云存储的 Url 速度和稳定性可能受一定影响。
        :param language_type: 识别语言类型。
        支持自动识别语言类型，同时支持自选语言种类，默认中英文混合(zh)，各种语言均支持与英文混合的文字识别。
        可选值：zh：中英混合,zh_rare：支持英文、数字、中文生僻字、繁体字，特殊符号等,auto：自动,mix：多语言混排场景中,自动识别混合语言的文本
        jap：日语,kor：韩语,spa：西班牙语,fre：法语,ger：德语,por：葡萄牙语,vie：越语,may：马来语,rus：俄语,ita：意大利语,hol：荷兰语
        swe：瑞典语,fin：芬兰语,dan：丹麦语,nor：挪威语,hun：匈牙利语,tha：泰语,hi：印地语,ara：阿拉伯语
        :param is_pdf: 是否开启PDF识别，默认值为false，开启后可同时支持图片和PDF的识别。
        :param pdf_page_number: 需要识别的PDF页面的对应页码，仅支持PDF单页识别，当上传文件为PDF且IsPdf参数值为true时有效，默认值为1。
        :param is_words: 是否返回单字信息，默认关
        :param region: 地域参数，用来标识希望操作哪个地域的实例。
        :return: API 返回的 JSON 数据
        """
        if not image_base64 and not image_url:
            raise ValueError("图片的 Base64 值和图片的 Url 地址至少传入一个")

        payload = {}
        if image_base64:
            payload["ImageBase64"] = image_base64
        if image_url:
            payload["ImageUrl"] = image_url
        if language_type is not None:
            payload["LanguageType"] = language_type
        if is_pdf:
            payload["IsPdf"] = is_pdf
            if pdf_page_number is not None:
                payload["PdfPageNumber"] = pdf_page_number
            else:
                payload["PdfPageNumber"] = 1
        else:
            payload["IsPdf"] = False
        if is_words is not None:
            payload["IsWords"] = is_words
        else:
            payload["IsWords"] = False

        return self.auth.send_request(
            service=self.service,
            action=self.action,
            version=self.version,
            region=region,
            payload=payload,
            endpoint=self.endpoint
        )