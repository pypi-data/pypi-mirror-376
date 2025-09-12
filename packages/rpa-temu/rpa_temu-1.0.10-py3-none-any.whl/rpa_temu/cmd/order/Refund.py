import json
import time
import uuid
from datetime import datetime
import undetected_chromedriver
from rpa_temu.api.shop import ShopApi
from rpa_temu.api.order import RefundRetApi
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
refundRetApi = RefundRetApi()
# 请求服务
request = Request()

class Refund():
    def __init__(self):
        pass

    def order_refund(self, driver:undetected_chromedriver.Chrome, shop_data:dict, options:dict):
        """ temu 退货退款列表
        Author: 黄豪杰
        Args:
            driver: 驱动
            shop_data: 店铺数据
            options: 任务参数
        """        
        print("退货退款列表")

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
        options['pageNumber'] = pageNumber = 1
        options['pageSize'] = pageSize = 100
        
        while True:
            res = refundRetApi.getRefundRetList(driver, options)
            if 'success' not in res or not res['success']:
                raise ValueError(f"订退货退款列表获取失败 - {res}")
                
            list_count = len(res['result']['mmsPageVO']['data'] or [])
            total_count = res['result']['mmsPageVO']['totalCount']

            if pageNumber > 1 and not list_count:
                break

            print(f"当前第{pageNumber}页,每页{pageSize} - 共{total_count}条数据")

            # 保存数据
            options['request_id'] = request_id
            options['page_number'] = pageNumber
            options['page_size'] = pageSize
            options['list_count'] = list_count
            options['total_count'] = total_count
            options['response'] = json.dumps(res,ensure_ascii=False)
            taskRequest.save(options)
            
            # 下一页
            pageNumber += 1
            options['pageNumber'] = pageNumber
            
        print("退货退款列表结束")
    
    def order_refund_detail(self, driver:undetected_chromedriver.Chrome, shop_data:dict, options:dict):
        """ temu 退货退款详情
        Author: 黄豪杰
        Args:
            driver: 驱动
            shop_data: 店铺数据
            options: 任务参数
        """
        print("订单违规详情")

        # 站点登录
        temuService.authorize(driver, options)
        
        # 请求ID
        request_id = str(uuid.uuid4())
        data = {
            "request_id":request_id,
            "type_id":options['type_id'],
            "task_id":options['task_id'],
            "account_id":options['account_id'],            
        }
        
        res = refundRetApi.getRefundRetDetail(driver, options)
        if 'success' not in res or not res['success']:
            raise ValueError(f"退货退款详情获取失败 - {res}")
        
        data = {
            **data,
            "response":json.dumps(res,ensure_ascii=False),
        }
        
        # 保存数据
        taskRequest.save(data)
        
        print("退货退款详情结束")
        