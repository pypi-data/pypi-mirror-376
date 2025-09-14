# -*- coding: utf-8 -*-
# @QQ      : 6231724
# @Time    : 2025/08/28 00:13
# @Author  : 皖山文武
# @Software: VSCode
import requests
import json
import pandas as pd
from datetime import datetime,timedelta
import os
import time

def getValueByIntervalAndNum(subPointCode,dataNum=120,interval=60):
    ''' 
    按默认60秒间隔取固定间隔的指定点位的指定数量的最新数据,可传入点个点或列表，返回dataframe  
    select last_value(${subPointCode}) As 'value' from ${subPointCode} GROUP BY ([now() - 1d, now()), ${interval}s) order by time desc limit ${dataNum}
    '''    
    url = "http://10.10.0.1/customApi/iot/getValueByIntervalAndNum"
    try:
        paramValueList = []
        if isinstance(subPointCode, (list, tuple)):
            #("是列表或元组")            
            for v in subPointCode:
                paramValueList.append({'subPointCode': v,  "interval": interval,'dataNum': dataNum})
        else:
            paramValueList.append({'subPointCode': subPointCode,  "interval": interval,'dataNum': dataNum})
             
        # 发送POST请求,统一使用列表参数处理
        res = requests.post(url=url, json=paramValueList)
        res.raise_for_status()  # 检查请求是否成功    
        # 解析JSON响应
        response_data = res.json()
        df=pd.DataFrame()
        # 提取数据部分  
        if isinstance(response_data, dict) and "data" in response_data:
            res_data = response_data["data"]
            # print(res_data)
            point_len=len(paramValueList)
            if point_len > 1:
                for el in res_data:
                    i=int(el["index"])
                    df_temp=pd.DataFrame(el["list"])
                    if i==0:
                        df['ts'] = pd.to_datetime(df_temp["ts"], unit='ms').dt.tz_localize('UTC').dt.tz_convert('Asia/Shanghai')  # 转换时间戳为可读格式
                    df[paramValueList[i]["subPointCode"]]=df_temp["value"] 
                return df.iloc[::-1] #将数据倒排
            else:
                df_temp=pd.DataFrame(res_data)                
                df['ts'] = pd.to_datetime(df_temp["ts"], unit='ms').dt.tz_localize('UTC').dt.tz_convert('Asia/Shanghai')  # 转换时间戳为可读格式
                df[subPointCode] = df_temp["value"]
                return df.iloc[::-1] #将数据倒排      
    except Exception as e:
          print(f"获取数据时发生错误: {e}")

def getSingleSubpoint(subPointCode,dataNum):
    # url = "http://10.10.0.1/customApi/iot/getFsValueInterval"
    url = "http://10.10.0.1/customApi/iot/getHistoryWithNum"
    print(f"开始测试点位 {subPointCode} ...")
    try:
        # 构建请求数据，替换subPointCode
        data = {
            "subPointCode": subPointCode,
            "dataNum":dataNum
        }    
        # 发送POST请求
        res = requests.post(url=url, json=data)
        res.raise_for_status()  # 检查请求是否成功    
        # 解析JSON响应
        response_data = res.json()
        return response_data
    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}") 
        return 0,e.strerror
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        return 0,e.strerror
    except Exception as e:
        print(f"处理数据时发生错误: {e}")
        return 0,e.strerror
    # 输出处理结果汇总




    
def datetime_to_timestamp(date_str=None):
    """
    将日期字符串或当前时间转换为时间戳
    :param date_str: 格式为"YYYY-MM-DD"的字符串，不传则使用当前时间
    :return: 时间戳(秒级)
    """
    if date_str:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    else:
        # 当前时间转毫秒级时间戳
        dt = datetime.now()
    return int(dt.timestamp() * 1000)
     


def timestamp_to_datetime(timestamp=None):
    """
    将时间戳转换为日期时间字符串
    :param timestamp: 时间戳(秒级)，不传则使用当前时间戳
    :return: 格式为"YYYY-MM-DD HH:MM:SS"的字符串
    """
    dt = datetime.fromtimestamp(timestamp / 1000)  # 注意要除以1000转换为秒
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")


def handleColTime(df:pd.DataFrame):
    # 处理时间列
    for col in df.columns:
        if any(keyword in col.lower() for keyword in ['time', 'ts', 'timestamp', '日期', '时间']):
            try:
                df[col] = pd.to_numeric(df[col])
                df[col] = pd.to_datetime(df[col], unit='ms')
                df[col] = df[col].dt.strftime("%Y/%#m/%#d")  # Windows系统
                # Linux/Mac系统: df[col] = df[col].dt.strftime("%Y/%m/%d").str.replace(r'/0', '/', regex=True)
            except Exception:
                try:
                    df[col] = pd.to_datetime(df[col])
                    df[col] = df[col].dt.strftime("%Y/%#m/%#d")  # Windows系统
                    # Linux/Mac系统: df[col] = df[col].dt.strftime("%Y/%m/%d").str.replace(r'/0', '/', regex=True)
                except Exception as e2:
                    print(f"无法解析时间列 {col}: {e2}")
    return df
    
def getFsValueInterval(subPointCode,startTs,endTs,interval=60):
    url = "http://10.10.0.1/customApi/iot/getFsValueInterval"   
    # getFsValueInterval ,每个区间的最新值   
    # select last_value(${subPointCode}) As `value` from ${subPointCode} GROUP BY ([${startTs}, ${endTs}) ,${interval}s , ${interval}s )
    # subHistoryDataAvginterval，每个区间的平均值
    # select avg(${subPointCode}) AS `value` from ${subPointCode} GROUP BY ([${startTs}, ${endTs}), ${interval}s, ${interval}s)
    # 记录成功和失败的点位

    try:
        paramValueList = []
        if isinstance(subPointCode, (list, tuple)):
            #("是列表或元组")            
            for p in subPointCode:
                paramValueList.append(
                   {
                       "subPointCode": p,
                       "startTs":startTs,
                       "endTs": endTs,
                       "interval": interval
                   }
                    
                    )
        else:
            paramValueList.append(
                   {
                       "subPointCode": subPointCode,
                       "startTs":startTs,
                       "endTs": endTs,
                       "interval": interval
                   }                
                )
        # print(paramValueList)
        #     #串行：
        # for x in  paramValueList:    
        # 发送POST请求,统一使用列表参数处理
        res = requests.post(url=url, json=paramValueList)
        res.raise_for_status()  # 检查请求是否成功    
        # 解析JSON响应
        response_data = res.json()
        # 提取数据部分 
        df=pd.DataFrame()    
        if isinstance(response_data, dict) and "data" in response_data:
            res_data = response_data["data"]
            point_len=len(paramValueList)
            if point_len > 1:
                for el in res_data:
                    i = int(el["index"])
                    df_temp=pd.DataFrame(el["list"])
                    if i==0:
                        df.loc[:,'ts'] = pd.to_datetime(df_temp["ts"], unit='ms').dt.tz_localize('UTC').dt.tz_convert('Asia/Shanghai')  # 转换时间戳为可读格式
                    df.loc[:,subPointCode[i]]=df_temp["value"]  
                return df            
               
            else:
                df_temp=pd.DataFrame(res_data)                
                df.loc[:,'ts']  = pd.to_datetime(df_temp["ts"], unit='ms').dt.tz_localize('UTC').dt.tz_convert('Asia/Shanghai')  # 转换时间戳为可读格式  # 转换时间戳为可读格式
                df.loc[:,subPointCode] = df_temp["value"]
                return df     
    except Exception as e:
          print(f"获取数据时发生错误: {e}")
   
def getHistoryData(points,startTime="2025-07-01 12:00:00"):
    now=datetime.now()
    # startTs=(now- timedelta(days=90)).timestamp() * 1000
    endTime= now.strftime("%Y-%m-%d %H:%M:%S")  
    startTs=datetime_to_timestamp(startTime)
    endTs=datetime_to_timestamp(endTime)  
    print(f"start:{startTime},{startTs};end:{endTime},{endTs}")
    return getFsValueInterval(points, startTs, endTs)  

def getHistoryDataByDays(points,days=10):
    endTime=datetime.now()
    startTime = endTime - timedelta(days=days)
    startTs = int(startTime.timestamp() * 1000)
    # startTime= (now- timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    # endTime= now.strftime("%Y-%m-%d %H:%M:%S")  
    # startTs=datetime_to_timestamp(startTime)
    endTs= int(endTime.timestamp() * 1000) #datetime_to_timestamp(endTime)  
    print(f"start:{startTime},{startTs};end:{endTime},{endTs}")
    return getFsValueInterval(points, startTs, endTs)  


if __name__ == "__main__":
  
    sub_point_codes = [
        # "GL11_RFL_LFZG_LL",#1#高炉风量
        # "GL11_BT_LDSSG_WD4",#1#高炉炉顶温度4
        # "GL11_BT_LDSSG_WD3",
        # "GL11_BT_LDSSG_WD2",
        # "GL11_BT_LDSSG_WD1",
        "GL11_RFL_GLMQLLFS_LL",#1#高炉产出高炉煤气压力	
    	"GL11_BT_GLMQZG_YL",#1#高炉产出高炉煤气流量
        # "GL12_BT_SSG_YL3",#1#高炉理论高炉煤气发生量
    ]
    
    df=getValueByIntervalAndNum(sub_point_codes,10)
    # df=getValueByIntervalAndNum("GL12_BT_SSG_YL2",10)
    print(df)
 
    
  

