import json
import time
import uuid
import undetected_chromedriver
from rpa_temu.api.shop import ShopApi,BillDetailApi
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
shopBillDetailApi = BillDetailApi()
# 请求服务
request = Request()

class BillDetail():
    def __init__(self):
        pass
    
    def shop_bill_detail(self, driver:undetected_chromedriver.Chrome, shop_data:dict, options:dict):
        """ temu 财务明细 
        Author: 黄豪杰
        Args:
            driver: 驱动
            shop_data: 店铺数据
            options: 任务参数
        """
        print("订单账单")

        
        # 测试固定时间
        if 'start_time' not in options and 'end_time' not in options:
            options['start_time'] = '2025-06-01'
            options['end_time'] = '2025-06-30'
        
        # 请求ID
        request_id = str(uuid.uuid4())
        data = {
            "request_id":request_id,
            "type_id":options['type_id'],
            "task_id":options['task_id'],
            "account_id":options['account_id'],            
        }
            
        options['pageNum'] = pageNum = 1
        options['pageSize'] = pageSize = 100
        while True:
                            
            res = shopBillDetailApi.getList(driver, options)
            if 'success' not in res or not res['success']:
                raise ValueError(f"财务明细列表获取失败 - {res}")
            
            list_count = len(res['result']['resultList'])
            total_count = res['result']['total']
            
            # 列表数量小于1
            if list_count < 1:
                # 当页面如果是第一页没有数据的话需要保存没有数据
                if pageNum == 1:
                    data = {
                        **data,
                        "response":json.dumps(res,ensure_ascii=False),
                    }
                    # 保存数据
                    taskRequest.save(data)
                break
            
            print(f"当前第{pageNum}页,每页{pageSize} - 共{total_count}条数据")

            data = {
                **data,
                "response":json.dumps(res,ensure_ascii=False),
                "page_number":pageNum, # 页码
                "page_size":pageSize, # 每页数量
                "list_count":list_count, # 当前页数量
                "total_count":total_count # 总数量
            }
            # 保存数据
            taskRequest.save(data)
            
            # 下一页
            pageNum += 1
            options['pageNum'] = pageNum
            
        print("财务明细结束")
            