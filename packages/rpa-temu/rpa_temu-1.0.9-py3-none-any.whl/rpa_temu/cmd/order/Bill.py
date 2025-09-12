import json
import time
import uuid
from datetime import datetime
import undetected_chromedriver
from rpa_temu.api.shop import ShopApi
from rpa_temu.api.order import BillApi
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
orderBillApi = BillApi()
# 请求服务
request = Request()

class Bill():
    def __init__(self):
        pass
    
    def order_bill(self, driver:undetected_chromedriver.Chrome, shop_data:dict, options:dict):
        """ temu 订单账单 
        Author: 黄豪杰
        Args:
            driver: 驱动
            shop_data: 店铺数据
            options: 任务参数
        """        
        print("订单账单")

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
        
        # 导出账单
        res = orderBillApi.export(driver, options)
        if ('success' not in res or not res['success']) and res['errorMsg'] != "导出任务已存在, 请勿重复创建, 请前往【导出历史】查看":
            raise ValueError(f"导出账单表格失败 - {res}")
         
        time.sleep(1)
        # 获取账单列表
        res = orderBillApi.getList(driver, options)
        if 'success' not in res or not res['success']:
            raise ValueError(f"获取账单列表失败 - {res}")
        fileId = res['result']['merchantMerchantFileExportHistoryList'][0]['id']
        
        num = 0
        while True:
            if num > 10:
                raise ValueError(f"获取账单下载链接超时")
            time.sleep(1)

            # 获取账单下载链接
            res = orderBillApi.getDownloadLink(driver, options,fileId)
            print("res", res)

            success = res.get("success", False)
            result  = res.get("result", {})

            if success and "fileUrl" in result:
                break
            
            num += 1
            
        fileUrl = res['result']['fileUrl']
        
        print(f"账单下载链接：{fileUrl}")
        
        cookies = {item['name']:item['value'] for item in driver.get_cookies()}
        
        dataXlsx = request.downloadExcel(fileUrl,{"cookies": cookies})
        # 请求ID
        request_id = str(uuid.uuid4())

        options['request_id'] = request_id
        options['response'] = json.dumps(dataXlsx,ensure_ascii=False)
        
        # 保存数据
        taskRequest.save(options)
        
        print("订单账单结束")
