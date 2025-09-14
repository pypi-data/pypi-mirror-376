# -*- coding: utf-8 -*-
# @QQ      : 6231724
# @Time    : 2025/08/28 00:13
# @Author  : 皖山文武
# @Software: VSCode
from typing import List
from fastapi import Depends, APIRouter, Request, HTTPException
from ygny.util.yg_iot_api import getValueByIntervalAndNum
import pandas as pd

from ..shaojie.device_config import *



# 根据设备配置信息取数，通用
def get_device_data(device):
    points=device["iot_points"]
    df0=getValueByIntervalAndNum(points)
    #检查数据，如空值较多，则抛出异常：
    # total_null_ratio = df0.isnull().sum().sum()# / (df0.shape[0] * df0.shape[1])
    # if total_null_ratio>119:
    #     raise HTTPException(400,f"实时点位数据空值过多，不符合预测条件！{total_null_ratio}")
    empty_columns = df0.columns[df0.isnull().all()]
    if len(empty_columns)>0:
        raise HTTPException(400,f"不符合预测条件！存在以下全空的特征，{empty_columns.tolist()}")

    
    #前后项项填充
    for x in df0.columns:
        df0[x]=df0[x].bfill().ffill()
    #合成数据：
    for vp in device["virtual_points"]:
        if vp["method"]=="mean":
            df0.loc[:,vp["vp"]] = df0.loc[:,vp["points"]].mean(axis=1) 
    # df=df0.loc[:, ['ts']+device["features"]] #保留原始数据到预测时处理
    # print(df.head)            
    return  df0

if __name__ == '__main__':
    print("调试数据接口")
    # df=get_gl2_mq()
    # points=[ 'SSG_YL',                  
    #                'GL12_RFL_LFZG_LL',
    #                'GL12_BT_FZZ_TQ',
    #                'GL12_BT_GLMQCFY_MQRZ',
    #                'RFZG_WD', 
    #                'GL12_BD_GLMQZG_LL',
    #                'GL12_BT_HRQ_HMQ_YL']
    # ##检测数据分布
    # for c in points:
    #     data=df[c]
    #     dct.outlierDetection(data)