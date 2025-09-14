# -*- coding: utf-8 -*-
"""
Created on Wed Sep  3 09:37:55 2025
点位检测及报告工具
@author: 徐斌
"""


import requests
import json
import pandas as pd
from datetime import datetime
import os
import time
import numpy as np
import dfClearTools as dfc
from  yg_iot_api import getHistoryDataByDays,getValueByIntervalAndNum
from ygny.gaolu.device_config import *

# 确保保存目录存在
def outlierDetection(data: pd.Series):    
    print(f"数据【{data.name}】分析报告：")
    s = data.describe()
    print(s)
    u = s["mean"]  # 计算均值
    std = s["std"]  # 计算标准差
    # stats.kstest(data, 'norm', (u, std))
    # print('均值为：%.3f，标准差为：%.3f' % (u,std))
    error = data[np.abs(data - u) > 3*std]    
    print(f'根据3西格玛原则，下限为：{u-3*std:.3f}，上限为：{u+3*std:.3f}')
    print(f'异常值共{len(error)}条')  
    q1 = s['25%']
    q3 = s['75%']
    iqr = q3 - q1
    mi = q1 - 3*iqr
    ma = q3 + 3*iqr
    print('根据IQR法(k=3)，下限为：%.3f，上限为：%.3f，分位差为：%.3f，' % (mi,ma,iqr))
    error = data[(data < mi) | (data > ma)]
    print('异常值共%i条(k=3)' % len(error))
    


def getValueByIntervalAndNum1(subPointCode,dataNum=120,interval=60):  
    url = "http://10.10.0.1/customApi/iot/getValueByIntervalAndNum"
    try:
        paramValueList = []
        paramValueList.append({'subPointCode': subPointCode,  "interval": interval,'dataNum': dataNum})
        res = requests.post(url=url, json=paramValueList)
        res.raise_for_status() 
        response_data = res.json()
        df=pd.DataFrame()    
        if isinstance(response_data, dict) and "data" in response_data:
            res_data = response_data["data"]            
            df_temp=pd.DataFrame(res_data)                
            df['ts'] = pd.to_datetime(df_temp["ts"], unit='ms').dt.tz_localize('UTC').dt.tz_convert('Asia/Shanghai')  # 转换时间戳为可读格式  # 转换时间戳为可读格式
            df[subPointCode] = df_temp["value"]
            return df.iloc[::-1] #将数据倒排      
    except Exception as e:
          print(f"获取数据时发生错误: {e}")



if __name__ == '__main__':
    point="GL12_BYXF_S2HGLCY_Flow"    #点位名称和点数
    df0=getValueByIntervalAndNum(point,120)
    print(df0)
    # num=10000
    # # df0=getValueByIntervalAndNum(point,num)
    # df0=getHistoryDataByDays(point,10)
    # outlierDetection(df0[point])    GL12_RFL_HRQ_HMQ_WD
    # df0=getValueByIntervalAndNum('GL11_BYXF_X1_GLYJS_Flow',2000)
    
    # points=['GL11_RFL_LFZG_WD', 'GL11_RFL_HRQ_HMQ_WD', 'GL11_RFL_HRQ_HKQ_WD', 'GL11_RFL_RFL1_KMB', 'GL11_RFL_RFL2_KMB', 'GL11_RFL_RFL3_KMB', 'GL11_RFL_LFZG_LL', 'GL11_RFL_HV2923_LL', 'GL11_RFL_HV2913_LL', 'GL11_BYXF_X1_GLYJS_Flow']
    # df0=getValueByIntervalAndNum(points,120)
    # df0=getValueByIntervalAndNum('GL12_BT_HRQ_HMQ_YL',200)
    # df0=getHistoryDataByDays('GL12_BT_HRQ_HMQ_YL',1)
    # device=dc_gl2
    # points = dc_gl2["iot_points"]
    # df0=getValueByIntervalAndNum(points,200)
    
    

    


   






