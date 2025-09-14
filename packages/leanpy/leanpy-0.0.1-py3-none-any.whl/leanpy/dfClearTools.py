# -*- coding: utf-8 -*-
"""
Created on Mon Aug 11 20:28:50 2025
数据清洗工具
@author: benxu
outlierDetection(data: pd.Series):#数据异常检测，出报告并绘图
get_column_MaxMin(df, column_name) #取列的MaxMin值
view_single_Col(df,col):#数据分布观测
"""
#import numpy as np
import pandas as pd
# import seaborn as sns    #箱线图工具
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from scipy import stats
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt
#import torch
#import torch.nn as nn
#from torch.utils.data import Dataset, DataLoader
#from sklearn.preprocessing import MinMaxScaler
#import matplotlib.pyplot as plt


def trim_null_rows(df, threshold=0.7):
    """
    截断DataFrame开头空值较多的连续行
    参数:
        df: 原始DataFrame (需包含时间序列)
        threshold: 空值比例阈值(默认0.7表示当行空值率>70%时被标记)
    返回:
        处理后的DataFrame (保留连续时间序列)
    """
    print(f"原始数据形状: {df.shape}")  
    # 计算每行的空值比例
    null_ratio = df.isnull().mean(axis=1)
    
    # 找到第一个空值比例低于阈值的行索引
    keep_index = np.argmax(null_ratio < threshold)
    
    # 如果全部行都超过阈值则保留最后一行（避免全删）
    if keep_index == 0 and null_ratio.iloc[0] >= threshold:
        return df.iloc[-1:] 
    # 截断前面空值较多的行
    cleaned_df= df.iloc[keep_index:]  
    print(f"处理后形状: {cleaned_df.shape}")    

    return cleaned_df

#异常数据处理--对上下限超限的取上下限
def clip_dataframe(df, col_ranges):
    """
    对DataFrame各列进行数值限幅处理
    :param df: 原始DataFrame
    :param col_ranges: 字典格式 {列名: (最小值, 最大值)}
    :return: 处理后的DataFrame副本
    """
    df_clipped = df.copy()
    for col, (min_val, max_val) in col_ranges.items():
        if col in df.columns:
            df_clipped[col] = df[col].clip(lower=min_val, upper=max_val)
    return df_clipped



def outlierDetection(data: pd.Series,plot_out:bool=False):
    '''
    #异常值检测，先进行正态性检验，绘制数据密度曲线，
    #然后根据3西格玛原则，检测异常值，
    #然后使用箱型图查看数据分布，计算分位差。
    #最后，绘图标注异常数据
    Parameters
    ----------
    data : pd.Series
        注意切片方法获得不似乎series而是dataframe.
    plot_out:False 是否输出绘图

    Returns
    -------
    检测报告打印在终端，图片输出在./pic目录下

    '''
    print(f"数据【{data.name}】分析报告：")
    s = data.describe()
    print(s)
    u = s["mean"]  # 计算均值
    std = s["std"]  # 计算标准差
    # stats.kstest(data, 'norm', (u, std))
    # print('均值为：%.3f，标准差为：%.3f' % (u,std))
    error = data[np.abs(data - u) > 3*std]
    data_c = data[np.abs(data - u) <= 3*std]
    print(f'根据3西格玛原则，下限为：{u-3*std:.3f}，上限为：{u+3*std:.3f}')
    print(f'异常值共{len(error)}条')
    
    if plot_out:
        fig = plt.figure(figsize = (10,6))
        ax1 = fig.add_subplot(2,1,1)
        data.plot(kind = 'kde',grid = True,style = '-k',title = f'KED: Density curve({data.name})',label=data.name)
        fig.add_subplot(2,1,2)
        plt.scatter(data_c.index, data_c, color = 'k',marker='.',alpha = 0.2)
        plt.scatter(error.index, error, color = 'r',marker='.',alpha = 0.5)
        plt.xlim([-10,100010])
        plt.grid()
        plt.savefig(f"./pic./2号高炉数据检测-KDE分析-{data.name}.png")        
        fig = plt.figure(figsize = (10,6))
        ax1 = fig.add_subplot(2,1,1)
        color = dict(boxes='DarkGreen', whiskers='DarkOrange', medians='DarkBlue', caps='Gray')
        data.plot.box(vert=False, grid = True,color = color,ax = ax1,title = f'IQR:k=3({data.name})',label= data.name)
   
    q1 = s['25%']
    q3 = s['75%']
    iqr = q3 - q1
    mi = q1 - 3*iqr
    ma = q3 + 3*iqr
    print('根据IQR法(k=3)，下限为：%.3f，上限为：%.3f，分位差为：%.3f，' % (mi,ma,iqr))
    error = data[(data < mi) | (data > ma)]
    data_c = data[(data >= mi) & (data <= ma)]
    print('异常值共%i条(k=3)' % len(error))
    
    if plot_out:
        fig.add_subplot(2,1,2)
        plt.scatter(data_c.index,data_c,color = 'k',marker='.',alpha = 0.2)
        plt.scatter(error.index,error,color = 'r',marker='.',alpha = 0.5)
        plt.xlim([-10,100010])
        plt.grid()
        plt.savefig(f"./pic./2号高炉数据检测-IQR分析-{data.name}.png")

def view_single_Col(df,col):
    plt.rcParams['font.family'] = 'SimHei'  # 设置字体为黑体
    plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号
    plt.figure(figsize=(50, 15))
    plt.plot(df[col], label=col)
    plt.title(f'{col}数据分布观测')
    plt.legend()
    plt.show()

def get_column_MaxMin(df, column_name):
    """
    获取DataFrame指定列的最大值和最小值
    :param df: pandas DataFrame对象
    :param column_name: 要计算的列名
    :return: 包含max和min的字典
    """
    if column_name not in df.columns:
        raise ValueError(f"列名'{column_name}'不存在于DataFrame中")
    max=df[column_name].max()
    min=df[column_name].min()    
    print(f"列{column_name}的最大值: {max}, 最小值: {min}")
    return {
        'max': max,
        'min': min
    }

def checkData(df):
    i,j=df.shape
    print(f"数据形状：{i}行，{j}列")
    print("检查存在空值的列：")
    for col in df.columns:
        # 检查单列
        if df[col].isnull().any():
            print(f"列:{col:20}存在空值{df[col].isnull().sum():8}个")
    print("数据检查完毕！")
            
def checkTimeContinuous(df,timeKey="time",intervalSeconds=60):
    # df[timeKey] = pd.to_datetime(df[timeKey]).apply(lambda x: x.replace(tzinfo=None))#去掉时区
     df[timeKey] = pd.to_datetime(df[timeKey])
     for i in range(len(df)-1):
         timediff=df[timeKey][i+1]-df[timeKey][i]
         sec=timediff.total_seconds()
         if sec>intervalSeconds:
             print(f"行{i}--{i+1}间隔异常："+str(df[timeKey][i]),'--',str(df[timeKey][i+1]))
 
 #以时间为主键合并两个dataframe，采用左联结方式，左边的df为主，需要检查其他列名是否重复
def mergeDfByTime(df1, df2, time_col='time'):    
 # df['dtime'] = pd.to_datetime(df['dtime']).apply(lambda x: x.replace(tzinfo=None))   #去掉时区
     df1[time_col] = pd.to_datetime(df1[time_col]).apply(lambda x: x.replace(tzinfo=None)) 
     df2[time_col] = pd.to_datetime(df2[time_col]).apply(lambda x: x.replace(tzinfo=None)) 
     #检查是否存在重复列名
     # 获取两表列名集合
     cols1 = set(df1.columns)
     cols2 = set(df2.columns)           
     # 计算交集并排除索引列
     common = cols1 & cols2
     common.discard('time')
     if len(common)>0:
         print(f"存在重复列名：{common}，不能直接合并！")
         return    

     # 确保时间列是索引
     if time_col in df1.columns:
         df1 = df1.set_index(time_col)
     if time_col in df2.columns:
         df2 = df2.set_index(time_col)        
     # 只保留df2中与df1时间索引匹配的行
     df2_filtered = df2[df2.index.isin(df1.index)]        
     # 合并DataFrame
     merged_df = df1.join(df2_filtered, how='left')
     return merged_df.reset_index()  # 将时间索引恢复为列

 #判断非空行的起始行
def findDataStartTime(df):
     for i in range(len(df)):
         if not df.iloc[i].isna().any():
             print(f"从{i}行开始数据非空：{df.iloc[i]}")
             break

#填充指定列，默认为均值
def fillNaCol(df,col,m="mean"):
    if m=="mean":
        df[col]=df[col].fillna(df[col].mean())

#填充整个数据集，默认为均值
def fillNaDf(df,m="mean"):
    if m=="mean":
        for col in df.columns:
            df[col]=df[col].fillna(df[col].mean())
        return df

#滚动计算整个列的区间累加值            
def calculate_rolling_sum(df, column_name, window=30):
    """
    计算指定列的每行与其后30行的累加值    
    参数:
        df: 输入的DataFrame
        column_name: 需要计算的列名
        window: 滚动窗口大小(默认为30)    
    返回:
        包含滚动累加结果的新Series
    """
    # 使用rolling窗口计算，设置min_periods=1保留所有结果
    rolling_sum = df[column_name].rolling(window=window, min_periods=1).sum()    
    # 由于rolling是向前计算，我们需要将结果向下平移(window-1)行
    shifted_sum = rolling_sum.shift(-(window-1))    
    return shifted_sum

#滚动计算整个列的区间累加值  
# def column(df,cumKey,step=1):
#     for i in range(0,len(df)-step):
#         dfRes = df[cumKey].apply(lambda x: df[cumKey][i+step]-df[cumKey][i])
#     return dfRes

# 从累计值推算出递增值，形成新列,步长默认1
# def CumToAcc(df,cumKey,step=1):
#     # for i in range(0,len(df)-step):
#         dfRes = df[cumKey].apply(lambda x: df[cumKey][i+step]-df[cumKey][i])
#     return dfRes

# 箱线图
# def boxplot(df):
#     sns.boxplot(data=df)            
         
 #自定义MinMaxScaler，可传入极值数组
 # custom_scaler = CustomMinMaxScaler(min_val=[0,5], max_val=[10,20])
 # custom_scaler.fit(X_train)  # 仅未预设的特征会重新计算
class CustomMinMaxScaler(MinMaxScaler):
    def __init__(self, feature_range=(0,1), max_val=None, min_val=None):
        super().__init__(feature_range)
        self.data_min_ = min_val  # 允许手动预设最小值
        self.data_max_ = max_val  # 允许手动预设最大值    
    def fit(self, X):
        if self.data_min_ is None: 
            self.data_min_ = X.min(axis=0)  # 未预设时才计算
        if self.data_max_ is None:
            self.data_max_ = X.max(axis=0)
        return self           




class TimeSeriesAnomalyDetector:
    def __init__(self, df, timestamp_col=None):
        """
        初始化异常检测器
        :param df: 输入的DataFrame
        :param timestamp_col: 时间戳列名(可选)
        """
        self.df = df.copy()
        self.timestamp_col = timestamp_col
        self.numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
    def detect_iqr(self, factor=1.5):
        """
        IQR四分位距法检测异常值
        :param factor: IQR乘数因子
        :return: 异常值标记的DataFrame
        """
        df_clean = self.df.copy()
        anomalies = pd.DataFrame(index=self.df.index, columns=self.numeric_cols, data=False)
        
        for col in self.numeric_cols:
            q1 = df_clean[col].quantile(0.25)
            q3 = df_clean[col].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - factor * iqr
            upper_bound = q3 + factor * iqr
            
            col_anomalies = (df_clean[col] < lower_bound) | (df_clean[col] > upper_bound)
            anomalies[col] = col_anomalies
            
        return anomalies
    
    def detect_zscore(self, threshold=3):
        """
        Z-score法检测异常值
        :param threshold: Z-score阈值
        :return: 异常值标记的DataFrame
        """
        df_clean = self.df.copy()
        anomalies = pd.DataFrame(index=self.df.index, columns=self.numeric_cols, data=False)
        
        for col in self.numeric_cols:
            z_scores = np.abs(stats.zscore(df_clean[col]))
            anomalies[col] = z_scores > threshold
            
        return anomalies
    
    def detect_isolation_forest(self, contamination=0.05):
        """
        隔离森林检测异常值
        :param contamination: 预期异常值比例
        :return: 异常值标记的Series
        """
        if len(self.numeric_cols) == 0:
            raise ValueError("没有可用的数值列进行检测")
            
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(self.df[self.numeric_cols])
        
        clf = IsolationForest(contamination=contamination, random_state=42)
        preds = clf.fit_predict(scaled_data)
        
        return pd.Series(preds == -1, index=self.df.index)
    
    def remove_anomalies(self, method='iqr', **kwargs):
        """
        检测并移除异常值
        :param method: 检测方法(iqr/zscore/isolation)
        :param kwargs: 各检测方法的参数
        :return: 清洗后的DataFrame
        """
        if method == 'iqr':
            anomalies = self.detect_iqr(**kwargs)
            mask = ~anomalies.any(axis=1)
        elif method == 'zscore':
            anomalies = self.detect_zscore(**kwargs)
            mask = ~anomalies.any(axis=1)
        elif method == 'isolation':
            mask = ~self.detect_isolation_forest(**kwargs)
        else:
            raise ValueError("不支持的检测方法，请选择 'iqr'、'zscore' 或 'isolation'")
            
        return self.df[mask].copy()

# if __name__ == "__main__":
#     # 示例用法
#     # 读取CSV文件
#     df = pd.read_csv('timeseries_data.csv', parse_dates=['timestamp'])
    
#     # 初始化检测器
#     detector = TimeSeriesAnomalyDetector(df, timestamp_col='timestamp')
    
#     # 使用IQR方法检测并移除异常值
#     clean_df_iqr = detector.remove_anomalies(method='iqr')
    
#     # 使用Z-score方法检测并移除异常值
#     clean_df_zscore = detector.remove_anomalies(method='zscore', threshold=3)
    
#     # 使用隔离森林方法检测并移除异常值
#     clean_df_isolation = detector.remove_anomalies(method='isolation', contamination=0.05)




class DataClearTools:
    def __init__(self):
        self.data = ''
        
    def checkData(self,df):
        i,j=df.shape
        print(f"数据形状：{i}行，{j}列")
        print("检查存在空值的列：")
        for col in df.columns:
            # 检查单列
            if df[col].isnull().any():
                print(f"列{col}存在{df[col].isnull().sum()}个空值")
    
    def checkTimeContinuous(self,df,timeKey="time",intervalSeconds=60):
       # df[timeKey] = pd.to_datetime(df[timeKey]).apply(lambda x: x.replace(tzinfo=None))#去掉时区
        df[timeKey] = pd.to_datetime(df[timeKey])
        for i in range(len(df)-1):
            timediff=df[timeKey][i+1]-df[timeKey][i]
            sec=timediff.total_seconds()
            if sec>intervalSeconds:
                print(f"行{i}--{i+1}间隔异常："+str(df[timeKey][i]),'--',str(df[timeKey][i+1]))
    
    #以时间为主键合并两个dataframe，采用左联结方式，左边的df为主，需要检查其他列名是否重复
    def mergeDfByTime(df1, df2, time_col='time'):    
    # df['dtime'] = pd.to_datetime(df['dtime']).apply(lambda x: x.replace(tzinfo=None))   #去掉时区
        df1[time_col] = pd.to_datetime(df1[time_col]).apply(lambda x: x.replace(tzinfo=None)) 
        df2[time_col] = pd.to_datetime(df2[time_col]).apply(lambda x: x.replace(tzinfo=None)) 
        #检查是否存在重复列名
        # 获取两表列名集合
        cols1 = set(df1.columns)
        cols2 = set(df2.columns)           
        # 计算交集并排除索引列
        common = cols1 & cols2
        common.discard('time')
        if len(common)>0:
            print(f"存在重复列名：{common}，不能直接合并！")
            return    
   
        # 确保时间列是索引
        if time_col in df1.columns:
            df1 = df1.set_index(time_col)
        if time_col in df2.columns:
            df2 = df2.set_index(time_col)        
        # 只保留df2中与df1时间索引匹配的行
        df2_filtered = df2[df2.index.isin(df1.index)]        
        # 合并DataFrame
        merged_df = df1.join(df2_filtered, how='left')
        return merged_df.reset_index()  # 将时间索引恢复为列

    #判断非空行的起始行
    def findDataStartTime(df):
        for i in range(len(df)):
            if not df.iloc[i].isna().any():
                print(f"从{i}行开始数据非空：{df.iloc[i]}")
                break
        
        