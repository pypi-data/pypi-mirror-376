import json
import time
import uuid
from datetime import datetime
import undetected_chromedriver
from rpa_temu.api.shop import ShopApi,DeliveryLabelApi
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
shopDeliveryLabelApi = DeliveryLabelApi()
# 请求服务
request = Request()

class DeliveryLabel():
    def __init__(self):
        pass
    
    def shop_delivery_label(self, driver:undetected_chromedriver.Chrome, shop_data:dict, options:dict):
        """ temu 发货面单 
        Author: 黄豪杰
        Args:
            driver: 驱动
            shop_data: 店铺数据
            options: 任务参数
        """
        print("发货面单")

        # 站点登录
        temuService.authorize(driver, options)
        
        # 时间
        if 'create_time_start' not in options:
            raise ValueError(f"缺少开始时间")
        create_time_start = int(options.get("create_time_start"))
        print(f"create_time_start: {create_time_start}")

        if 'create_time_end' not in options:
            raise ValueError(f"缺少结束时间")
        create_time_end = int(options.get("create_time_end"))
        print(f"create_time_end: {create_time_end}")

        if 'settle_status' not in options:
            raise ValueError(f"缺少结算状态")
        settle_status = int(options.get("settle_status"))
        print(f"settle_status: {settle_status}")

        # 转换为日期格式
        start_time = datetime.fromtimestamp(create_time_start).strftime('%Y-%m-%d')
        end_time = datetime.fromtimestamp(create_time_end).strftime('%Y-%m-%d')

        print(f"开始时间: {start_time}")
        print(f"结束时间: {end_time}")

        options['start_time'] = start_time
        options['end_time'] = end_time
        
        # 请求ID
        request_id = str(uuid.uuid4())
        data = {
            "request_id":request_id,
            "type_id":options['type_id'],
            "task_id":options['task_id'],
            "account_id":options['account_id'],            
        }

        page_number = 1
        options['rowCount'] = rowCount = 100
        options['settleStatus'] = settle_status
        while True:
            # 获取发货面单列表
            res = shopDeliveryLabelApi.getList(driver, options)
            if 'success' not in res or not res['success']:
                raise ValueError(f"发货面单列表获取失败 - {res}")
            
            key = options['site'].lower() == 'us' and 'sellerBillList' or 'list'
            list_count = len(res['result'][key])
            total_count = res['result']['total']
            
            options['scrollContext'] = res['result']['scrollContext']

            if page_number > 1 and not list_count:
                break
            
            title = settle_status == 1 and "已出账" or "待出账"
            print(f"当前{title} - 第{page_number}页,每页{rowCount} - 共{total_count}条数据")
            
            # 保存数据
            options['request_id'] = request_id
            options['page_number'] = page_number
            options['page_size'] = rowCount
            options['list_count'] = list_count
            options['total_count'] = total_count
            options['response'] = json.dumps(res,ensure_ascii=False)
            taskRequest.save(options)
            
            page_number += 1
        
        print("发货面单结束")
        
        