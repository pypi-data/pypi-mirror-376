import json
import time
from datetime import datetime, timedelta

from rpa_temu.api.BaseApi import BaseApi
from rpa_common.service import ExecuteService
import undetected_chromedriver
import rpa_common.exceptions as exceptions

executeService = ExecuteService()


class AdsApi(BaseApi):
    """ temu 非本土广告费-广告数据
    """

    def __init__(self):
        super().__init__()

    def shop_ads(self, driver: undetected_chromedriver.Chrome, options: dict):
        """
        @Desc    : 非本土广告费-广告数据
        @Author  : 洪润涛
        @Time    : 2024/08/25 11:38:22
        """
        site = options.get("site")
        shop_id = options.get("shop_id")
        PAGE = options.get('PAGE')
        PAGE_SIZE = options.get('PAGE_SIZE')

        if not site:
            raise exceptions.TaskParamsException("站点site不能为空")
        if not shop_id:
            raise exceptions.TaskParamsException("店铺ID不能为空")

        # 结束时间  使用当前时间转 %Y-%m-%d  eg：2025-07-07
        now = datetime.now()
        end_time = now.strftime("%Y-%m-%d")
        print('[结束时间]', end_time)

        # 开始时间 使用当前时间的前一周转 %Y-%m-%d   eg：2025-07-01
        one_week_ago = now - timedelta(days=7)
        start_time = one_week_ago.strftime("%Y-%m-%d")
        print('[开始时间]', start_time)

        # 日期格式转时间戳
        start_time = int(datetime.strptime(start_time + ' 00:00:00', "%Y-%m-%d %H:%M:%S").timestamp() * 1000)
        end_time = int(datetime.strptime(end_time + ' 23:59:59', "%Y-%m-%d %H:%M:%S").timestamp() * 1000)

        # 获取 广告平台 授权码
        obtain_url = f"{self.site_url[site.lower()]}/bg/swift/api/auth/obtainCode"
        driver.get(obtain_url)
        obtain_data = {"redirectUrl": f'https://{site.lower()}.ads.temu.com/index.html?source={1 if site.upper() == "US" else 3}&seller_source={12 if site.upper() == "US" else 13}'}
        headers = {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "mallid": shop_id
        }
        response = executeService.request(driver, url=obtain_url, data=obtain_data, headers=headers)
        print('********请求【广告平台-授权码】得到的数据：', type(response), response)
        obtainCode = json.loads(response).get('result', {}).get('code')
        print('【广告平台-登录授权码】：', obtainCode)
        if not obtainCode:
            raise ValueError('获取授权码失败')

        headers_bak = {
            "content-type": "application/json",
        }

        # 访问登录页
        login_url = f'https://{site.lower()}.ads.temu.com/login.html?redirectUrl=https://{site.lower()}.ads.temu.com/index.html?source={1 if site.upper() == "US" else 3}&seller_source={12 if site.upper() == "US" else 13}&userType=1&mallType=2&ticket={obtainCode}&adLoginMallId={shop_id}&source={1 if site.upper() == "US" else 3}&seller_source={12 if site.upper() == "US" else 13}'
        driver.get(login_url)
        # 使用授权码进行登录
        login_request_url = f'https://{site.lower()}.ads.temu.com/api/v1/coconut/account/login?mallType=2&ticket={obtainCode}&userType=1&mallId={shop_id}&source={1 if site.upper() == "US" else 3}'
        print(login_request_url)
        login_data = {
            "user_type": 1,
            "mall_id": shop_id,
            "mall_type": 2,
            "ticket": obtainCode,
        }
        response = executeService.request(driver, url=login_request_url, data=login_data, headers=headers_bak)
        print(response)

        # 登录后的账户首页
        index_url = driver.current_url
        # 站点区分标志
        site_exists = None
        if f'{site.lower()}.ads.temu.com' in index_url:
            site_exists = True
        if site_exists:
            request_url = f'https://{site.lower()}.ads.temu.com/api/v1/coconut/ad/ads_report'
        else:
            request_url = f'https://ads.temu.com/api/v1/coconut/ad/ads_report'
        driver.get(request_url)
        load_data = {
            "ad_status": [],
            "ad_phase": -1,
            "page_number": PAGE,
            "page_size": PAGE_SIZE,
            "specific_query_info": "",
            "sort_by": 0,
            "sort_type": "desc",
            "start_time": start_time,
            "end_time": end_time,
            "source": 0,
            "need_del_status_ad": True,
            "need_calculate_goods_summary": True,
            "selected_site_id": -1,
        }
        res = executeService.request(driver, url=request_url, data=load_data, headers=headers_bak)
        print('**********请求【非本土广告费-广告数据】获取到的数据', type(res),res)
        try:
            res = json.loads(res)
        except Exception as e:
            raise ValueError(f"非本土广告费-广告数据 - {res}")
        return res

    def shop_ads_payment(self, driver: undetected_chromedriver.Chrome, options: dict):
        """
        @Desc    : 非本土广告费-广告明细
        @Author  : 洪润涛
        @Time    : 2024/08/25 15:20:35
        """
        site = options.get("site")
        shop_id = options.get("shop_id")
        PAGE = options.get('PAGE')
        PAGE_SIZE = options.get('PAGE_SIZE')

        if not site:
            raise exceptions.TaskParamsException("站点site不能为空")
        if not shop_id:
            raise exceptions.TaskParamsException("店铺ID不能为空")

        # 结束时间  使用当前时间转 %Y-%m-%d  eg：2025-07-07
        now = datetime.now()
        end_time = now.strftime("%Y-%m-%d")
        print('[结束时间]', end_time)

        # 开始时间 使用当前时间的前一周转 %Y-%m-%d   eg：2025-07-01
        one_week_ago = now - timedelta(days=7)
        start_time = one_week_ago.strftime("%Y-%m-%d")
        print('[开始时间]', start_time)

        # 日期格式转时间戳
        start_time = int(datetime.strptime(start_time + ' 00:00:00', "%Y-%m-%d %H:%M:%S").timestamp() * 1000)
        end_time = int(datetime.strptime(end_time + ' 23:59:59', "%Y-%m-%d %H:%M:%S").timestamp() * 1000)

        # 获取 广告平台 授权码
        obtain_url = f"{self.site_url[site.lower()]}/bg/swift/api/auth/obtainCode"
        driver.get(obtain_url)
        obtain_data = {"redirectUrl": f'https://{site.lower()}.ads.temu.com/index.html?source={1 if site.upper() == "US" else 3}&seller_source={12 if site.upper() == "US" else 13}'}
        headers = {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "mallid": shop_id
        }
        response = executeService.request(driver, url=obtain_url, data=obtain_data, headers=headers)
        print('********请求【广告平台-授权码】得到的数据：', type(response), response)
        obtainCode = json.loads(response).get('result', {}).get('code')
        print('【广告平台-登录授权码】：', obtainCode)
        if not obtainCode:
            raise ValueError('获取授权码失败')

        headers_bak = {
            "content-type": "application/json",
        }

        login_url = f'https://{site.lower()}.ads.temu.com/login.html?redirectUrl=https://{site.lower()}.ads.temu.com/index.html?source={1 if site.upper() == "US" else 3}&seller_source={12 if site.upper() == "US" else 13}&userType=1&mallType=2&ticket={obtainCode}&adLoginMallId={shop_id}&source={1 if site.upper() == "US" else 3}&seller_source={12 if site.upper() == "US" else 13}'
        driver.get(login_url)
        # 使用授权码进行登录
        login_request_url = f'https://{site.lower()}.ads.temu.com/api/v1/coconut/account/login?mallType=2&ticket={obtainCode}&userType=1&mallId={shop_id}&source={1 if site.upper() == "US" else 3}'
        print(login_request_url)
        login_data = {
            "user_type": 1,
            "mall_id": shop_id,
            "mall_type": 2,
            "ticket": obtainCode,
        }
        response = executeService.request(driver, url=login_request_url, data=login_data, headers=headers_bak)
        print(response)

        # 登录后的账户首页
        index_url = driver.current_url
        # 站点区分标志
        site_exists = None
        if f'{site.lower()}.ads.temu.com' in index_url:
            site_exists = True

        if site_exists:
            # 如果存在站点区分，进行ads.temu.com授权
            url = f'https://{site.lower()}.ads.temu.com/api/v1/coconut/account/deployment_switch?source=2'
            response1 = executeService.request(driver, url=url, data={"source": 2}, headers=headers_bak)
            print('【ads.temu.com】授权：', response1)
            error_code = json.loads(response1).get('error_code')
            if not error_code or error_code != 1000000:
                raise ValueError('【ads.temu.com】授权失败')

        request_url = f'https://ads.temu.com/api/v1/coconut/wallet/payment_summary'
        driver.get(request_url)
        load_data = {
            "start_time": start_time,
            "end_time": end_time,
            "page_number": PAGE,
            "page_size": PAGE_SIZE,
            "summary_type": 100,
            "query_by": 0,
            "sort_by": 0,
            "sort_type": 0,
        }
        res = executeService.request(driver, url=request_url, data=load_data, headers=headers_bak)
        print('**********请求【非本土广告费-广告明细】获取到的数据', type(res),res)
        try:
            res = json.loads(res)
        except Exception as e:
            raise ValueError(f"非本土广告费-广告明细 - {res}")
        return res
