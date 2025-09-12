import json
import time
import uuid
import undetected_chromedriver
from rpa_temu.api.shop import ShopApi, AdsApi
from rpa_common.library import Request
from rpa_common.request import ShopRequest
from rpa_common.request import TaskRequest
from rpa_temu.service import TemuService


# 店铺服务
shopRequest = ShopRequest()
# 任务服务
taskRequest = TaskRequest()
# temu服务
temuService = TemuService()
# 店铺api
shopApi = ShopApi()
# api
adsApi = AdsApi()
# 请求服务
request = Request()


class Ads:
    def __init__(self):
        pass

    def shop_ads(self, driver: undetected_chromedriver.Chrome, shop_data: dict, options: dict):
        """ temu 非本土广告费-广告数据
        Author: 洪润涛
        Args:
            driver: 驱动
            shop_data: 店铺数据
            options: 任务参数
        """
        print("非本土广告费-广告数据")

        # 站点登录
        temuService.authorize(driver, options)

        PAGE = 1
        options['PAGE'] = PAGE
        options['PAGE_SIZE'] = 50
        while True:
            # 获取非本土广告费-广告数据
            res = adsApi.shop_ads(driver, options)
            if 'success' not in res or not res['success']:
                raise ValueError(f"非本土广告费-广告数据 - {res}")

            list_count = len(res['result']['ads_detail'])
            total_count = res['total']
            if not list_count:total_count = 0
            # 保存数据
            options['request_id'] = str(uuid.uuid4())
            options['page_number'] = PAGE  # 页数
            options['page_size'] = 50  # 每页数量
            options['list_count'] = list_count  # 当前页数量
            options['total_count'] = total_count  # 总数据量
            options['response'] = json.dumps(res, ensure_ascii=False)
            print('[options]', options)
            taskRequest.save(options)

            if list_count == 50:
                PAGE += 1
                options['PAGE'] = PAGE
                print(f'【非本土广告费-广告数据 | 第{PAGE}页】')
                time.sleep(0.4)
            else:
                break

        print("非本土广告费-广告数据采集结束")

    def shop_ads_payment(self, driver: undetected_chromedriver.Chrome, shop_data: dict, options: dict):
        """ temu 非本土广告费-广告明细
        Author: 洪润涛
        Args:
            driver: 驱动
            shop_data: 店铺数据
            options: 任务参数
        """
        print("非本土广告费-广告明细")

        # 站点登录
        temuService.authorize(driver, options)

        PAGE = 1
        options['PAGE'] = PAGE
        options['PAGE_SIZE'] = 50
        while True:
            # 获取非本土广告费-广告明细
            res = adsApi.shop_ads_payment(driver, options)
            if 'success' not in res or not res['success']:
                raise ValueError(f"非本土广告费-广告明细 - {res}")

            list_count = len(res['result']['settle_list'])
            total_count = res['total']
            if not list_count:total_count = 0
            # 保存数据
            options['request_id'] = str(uuid.uuid4())
            options['page_number'] = PAGE  # 页数
            options['page_size'] = 50  # 每页数量
            options['list_count'] = list_count  # 当前页数量
            options['total_count'] = total_count  # 总数据量
            options['response'] = json.dumps(res, ensure_ascii=False)
            print('[options]', options)
            taskRequest.save(options)

            if list_count == 50:
                PAGE += 1
                options['PAGE'] = PAGE
                print(f'【非本土广告费-广告明细 | 第{PAGE}页】')
                time.sleep(0.4)
            else:
                break

        print("非本土广告费-广告明细采集结束")




