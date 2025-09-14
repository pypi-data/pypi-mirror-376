# -*- coding: utf-8 -*-
"""
Created on Wed Aug 13 20:43:59 2025
Created on Tue Aug 12 15:46:03 2025
代码实现了完整的LSTM时间序列预测流程，包括数据预处理、模型构建、训练和评估
支持预测未来30/60/90/120分钟的标签值累加和，可通过修改Config类中的selected_step参数调整
使用MinMaxScaler对数据进行归一化处理，确保模型训练稳定性
实现了自定义数据集类TimeSeriesDataset和数据加载器，便于批量处理数据
包含训练和评估循环，自动保存最佳模型，并绘制损失曲线和预测结果对比图
提供了独立的预测函数predict_future，可用于新数据的预测
代码自动检测GPU可用性，优先使用GPU加速训练
输出多种评估指标(MAE, MSE, RMSE)来衡量模型性能
使用说明：

将代码中的'your_data.csv'替换为实际数据文件路径
根据需要调整Config类中的参数
运行main()函数开始训练和评估
使用predict_future函数进行新数据的预测


以下是代码中所有配置参数的含义解析，按功能模块分类说明：

1. 数据预处理参数
seq_length：输入序列的时间步长（60分钟），表示模型每次分析的历史数据范围
predict_steps：可选预测步长数组（[30,60,90,120]），定义模型可预测的未来时间窗口
selected_step：当前选定的预测步长（60分钟），决定模型输出标签的累加范围
2. 模型训练参数
batch_size：每批次训练样本数（64），影响内存使用和梯度更新频率
hidden_size：LSTM隐藏层维度（128），决定模型记忆容量和特征提取能力
num_layers：LSTM堆叠层数（2），增加网络深度可提升复杂模式学习能力
learning_rate：优化器步长（0.001），控制参数更新幅度
epochs：训练轮次（100），需平衡欠拟合与过拟合风险
3. 系统配置参数
device：自动选择训练设备（GPU/CPU），加速计算过程
test_size：测试集比例（0.2），验证模型泛化能力
random_state：随机种子（42），确保实验可复现
4. 模型结构参数
input_size：动态获取的特征数（7列），对应输入数据的维度
output_size：输出维度（1），预测目标为单值累加和
5. 数据标准化参数
MinMaxScaler：将特征和标签归一化到[0,1]区间，提升训练稳定性
label_scaler：单独保存标签的缩放器，用于预测结果反归一化
6. 评估指标
MAE/MSE/RMSE：衡量预测值与真实值的平均偏差程度,MAE （平均绝对误差）、 MSE （均方误差）、 RMSE （均方根误差）
best_model.pth：自动保存验证损失最小的模型参数

注：参数设计遵循深度学习工程最佳实践，在内存效率、训练速度和预测精度之间取得平衡。实际应用中可根据数据特性调整隐藏层维度、学习率等关键参数。

@author: benxu
"""
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
# from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.base import BaseEstimator, TransformerMixin
import matplotlib.pyplot as plt
from tqdm import tqdm

class LSTM_Config:
    def __init__(self, features:pd.DataFrame,
                 feature_range:list,
                 labels:pd.DataFrame,
                 label_range:list,
                 # input_size=7,output_size=8,                         
                         seq_length:int = 120, 
                         batch_size:int = 64,
                         hidden_size:int = 128,
                         num_layers:int = 2,
                         dropout:float = 0.2,
                         learning_rate:float  = 0.001,
                         epochs:int = 100,
                         test_size:float  = 0.2,
                         random_state:int = 42,
                         model_path:str='best_model.pth',                         
                         ):
        '''
        1. 数据预处理参数
        seq_length (int)：输入序列的时间步长（60分钟），表示模型每次分析的历史数据范围
        predict_steps：可选预测步长数组（[30,60,90,120]），定义模型可预测的未来时间窗口
        selected_step：当前选定的预测步长（60分钟），决定模型输出标签的累加范围
        2. 模型训练参数
        batch_size：每批次训练样本数（64），影响内存使用和梯度更新频率
        hidden_size：LSTM隐藏层维度（128），决定模型记忆容量和特征提取能力
        num_layers：LSTM堆叠层数（2），增加网络深度可提升复杂模式学习能力
        learning_rate：优化器步长（0.001），控制参数更新幅度
        epochs：训练轮次（100），需平衡欠拟合与过拟合风险
        3. 系统配置参数
        device：自动选择训练设备（GPU/CPU），加速计算过程
        test_size：测试集比例（0.2），验证模型泛化能力
        random_state：随机种子（42），确保实验可复现
        4. 模型结构参数
        input_size：动态获取的特征数（7列），对应输入数据的维度
        output_size：输出维度（1），预测目标为单值累加和
        Returns
        -------
        None.

        '''
        # self.input_size = input_size
        # self.output_size = output_size
        self.seq_length = seq_length  # 输入序列长度(分钟)
        # self.predict_steps = [30, 60, 90, 120]  # 预测步长选项
        # self.selected_step = 30  # 当前选择的预测步长
        self.batch_size = batch_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.dropout =dropout
        self.learning_rate =learning_rate
        self.epochs = epochs
        self.features=features
        self.feature_range=feature_range
        self.labels=labels
        self.label_range=label_range
        self.input_size = features.shape[1]
        self.output_size =  labels.shape[1]
        
        self.test_size = test_size
        self.random_state = random_state
        self.model_path =model_path
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    # 训练函数
    def train_model(self,model, train_loader, criterion, optimizer):
        model.train()
        train_loss = 0
        for batch_X, batch_y in train_loader:
            batch_X = batch_X.to(self.device)
            batch_y = batch_y.to(self.device)
            
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()        
            train_loss += loss.item()    
        return train_loss / len(train_loader)
    
    # 评估函数
    def evaluate_model(self, model, test_loader, criterion):
        model.eval()
        test_loss = 0
        with torch.no_grad():
            for batch_X, batch_y in test_loader:
                batch_X = batch_X.to(self.device)
                batch_y = batch_y.to(self.device)
                
                outputs = model(batch_X)
                loss = criterion(outputs, batch_y)
                test_loss += loss.item()    
        return test_loss / len(test_loader) 
         
    
 
# LSTM模型
class LSTMModel(nn.Module):
    def __init__(self, input_size=7, hidden_size=128, num_layers=2, output_size=8, dropout=0.2):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=dropout)
        self.fc = nn.Linear(hidden_size, output_size)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    @classmethod 
    def from_config(cls,config:LSTM_Config):
        return cls(input_size=config.input_size,
                   output_size=config.output_size,
                   hidden_size=config.hidden_size,
                   num_layers=config.num_layers, 
                   dropout=config.dropout
                   )
        # super().__init__()
        # self.hidden_size = config.hidden_size
        # self.num_layers = config.num_layers
        # self.input_size = config.input_size
        # self.dropout = config.dropout
        # self.output_size=config.output_size        
        # self.lstm = nn.LSTM(self.input_size, self.hidden_size, self.num_layers, batch_first=True, dropout=self.dropout)
        # self.fc = nn.Linear(self.hidden_size, self.output_size)
    # @classmethod    
    # def from_api(cls, input_size=7, hidden_size=128, num_layers=2, output_size=1, dropout=0.2):
    #     '''
    #     简易初始化，供api调用
    #     '''
    #     _config=LSTM_Config(
    #         input_size=input_size,
    #         hidden_size=hidden_size,
    #         num_layers=num_layers,
    #         output_size=output_size,
    #         dropout=dropout
    #     )
    #     return cls(_config)
        
    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)        
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])
        return out

        




# 自定义数据集类
class TimeSeriesDataset(Dataset):
    def __init__(self, X, y):
        self.X = X
        self.y = y
        
    def __len__(self):
        return len(self.X)
    
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

class ArrayMinMaxScaler(BaseEstimator, TransformerMixin):
    """支持数组输入的自定义极值标准化器    
    参数:
        feature_ranges (list): 每个特征的(min,max)元组列表
        clip (bool): 是否裁剪数据到指定范围
    """
    def __init__(self, feature_ranges=None, clip=True):
        self.feature_ranges = feature_ranges or []
        self.clip = clip
        self.scale_params_ = []
        
    def fit(self, X=None, y=None):
        # if len(self.feature_ranges) != X.shape[1]:
        #     raise ValueError("特征范围数量与输入维度不匹配")            
        for i, (min_val, max_val) in enumerate(self.feature_ranges):
            self.scale_params_.append({
                'min': min_val,
                'max': max_val,
                'range': max_val - min_val
            })
        return self
    
    def transform(self, X):
        if len(self.feature_ranges) != X.shape[1]:
            raise ValueError("特征范围数量与输入维度不匹配")
        X = np.asarray(X, dtype=np.float32)
        X_trans = np.empty_like(X)
        
        for i in range(X.shape[1]):
            params = self.scale_params_[i]
            col_data = X[:, i]
            
            if self.clip:
                col_data = np.clip(col_data, params['min'], params['max'])
                
            X_trans[:, i] = (col_data - params['min']) / params['range']
            
        return X_trans
    
    def inverse_transform(self, X):
        X = np.asarray(X, dtype=np.float32)
        X_inv = np.empty_like(X)
        
        for i in range(X.shape[1]):
            params = self.scale_params_[i]
            X_inv[:, i] = X[:, i] * params['range'] + params['min']
            
        return X_inv


def autoTrain(config:LSTM_Config):
    features=config.features.values
    feature_scaler = ArrayMinMaxScaler(config.feature_range)    
    features = feature_scaler.fit_transform(features)
    labels=config.labels.values
    label_scaler = ArrayMinMaxScaler(config.label_range)    
    labels = label_scaler.fit_transform(labels)

    # 创建序列数据
    X, y = [], []
    for i in range(len(features) - config.seq_length):
        # 输入序列
        X.append(features[i:i+config.seq_length])
        # 输出为未来n分钟标签的累加和,已提前处理到标签中
        # target_sum = np.sum(labels[i+config.seq_length:i+config.seq_length+config.selected_step])
        y.append(labels[i+config.seq_length-1])
    
    if config.input_size==1:
        X=np.array(X).reshape(-1, 1)
    else:
        X = np.array(X)
    if config.output_size==1:
        y = np.array(y).reshape(-1, 1)
    else:
        y = np.array(y)  

    # 划分训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=config.test_size, shuffle=False,random_state=config.random_state)#时间序列数据需设置shuffle=False,random_state=config.random_state)
    
    # 转换为张量
    X_train = torch.FloatTensor(X_train)
    y_train = torch.FloatTensor(y_train)
    X_test = torch.FloatTensor(X_test)
    y_test = torch.FloatTensor(y_test)
    # return X_train, X_test, y_train, y_test, label_scaler
    train_dataset = TimeSeriesDataset(X_train, y_train)
    test_dataset = TimeSeriesDataset(X_test, y_test)   
   
    train_loader = DataLoader(train_dataset, batch_size=config.batch_size, shuffle=False)#打乱shuffle=False
    test_loader = DataLoader(test_dataset, batch_size=config.batch_size, shuffle=False)
    
    # 初始化模型
    # input_size = X_train.shape[2]  # 特征数量
    model = LSTMModel.from_config(config).to(config.device)
    # 定义损失函数和优化器
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    
    # 训练循环
    best_loss = float('inf')
    train_losses, test_losses = [], []
    for epoch in tqdm(range(config.epochs)):
        train_loss = config.train_model(model, train_loader, criterion, optimizer)
        test_loss = config.evaluate_model(model, test_loader, criterion)
        
        train_losses.append(train_loss)
        test_losses.append(test_loss)
        
        # 保存最佳模型
        if test_loss < best_loss:
            best_loss = test_loss
            torch.save(model.state_dict(), config.model_path)
        
        print(f'Epoch {epoch+1}/{config.epochs}, Train Loss: {train_loss:.6f}, Test Loss: {test_loss:.6f}')
    
    # 绘制损失曲线
    plt.plot(train_losses, label='Train Loss')
    plt.plot(test_losses, label='Test Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.show()
    

def testModel(config:LSTMModel):
    model = LSTMModel.from_config(config).to(config.device)
    model.load_state_dict(torch.load(config.model_path)) 
    
    features=config.features.values
    feature_scaler = ArrayMinMaxScaler(config.feature_range)    
    features = feature_scaler.fit_transform(features)
    labels=config.labels.values
    label_scaler = ArrayMinMaxScaler(config.label_range) 
    label_scaler.fit()
    # labels = label_scaler.fit_transform(labels)

    # 创建序列数据
    X, y = [], []
    for i in range(len(features) - config.seq_length):
        # 输入序列
        X.append(features[i:i+config.seq_length])
        # 输出为未来n分钟标签的累加和,已提前处理到标签中
        # target_sum = np.sum(labels[i+config.seq_length:i+config.seq_length+config.selected_step])
        y.append(labels[i+config.seq_length-1])
    
    if config.input_size==1:
        X=np.array(X).reshape(-1, 1)
    else:
        X = np.array(X)
    if config.output_size==1:
        y = np.array(y).reshape(-1, 1)
    else:
        y = np.array(y)  
        
    
    model.eval()
    with torch.no_grad():
        X = torch.FloatTensor(X)
        X = X.to(config.device)
        predictions1 = model(X)
        predictions = predictions1.cpu().numpy()
        actuals = y             
        # 反归一化,需要考虑步长
        predictions = label_scaler.inverse_transform(predictions) 
        # 计算评估指标
        mae = np.mean(np.abs(predictions - actuals))
        mse = np.mean((predictions - actuals)**2)
        rmse = np.sqrt(mse)
        print(f'MAE: {mae:.4f}, MSE: {mse:.4f}, RMSE: {rmse:.4f}')        
        # 绘制预测结果
        return predictions,actuals

# 预测函数
def predict_future(model, input_data, config, label_scaler):
    model.eval()
    with torch.no_grad():
        input_tensor = torch.FloatTensor(input_data).unsqueeze(0).to(config.device)
        prediction = model(input_tensor).cpu().numpy()
        prediction = label_scaler.inverse_transform(prediction)
        return prediction[0]
    
    
# 批量测试
def testBatch(config:LSTM_Config):
    model = LSTMModel.from_config(config).to(config.device)
    model.load_state_dict(torch.load(config.model_path))   
    features=config.features.values   
    feature_scaler = ArrayMinMaxScaler(config.feature_range)    
    features = feature_scaler.fit_transform(config.features)    
    labels = config.labels.values#.reshape(-1, 1)   
    label_scaler = ArrayMinMaxScaler(config.label_range)
    label_scaler.fit()  

    # 创建序列数据
    X, y = [], []
    for i in range(len(features) - config.seq_length):
        # 输入序列
        X.append(features[i:i+config.seq_length])
        y.append(labels[i+config.seq_length-1])    
    x = np.array(X)
    y = np.array(y)#.reshape(-1, 1)   
    print('x',x)
    rs1=[]    
    for i in range(len(x)):
        rs=predict_future(model, x[i], config, label_scaler)
        print(f'x{i}', x[i])
        print('rs',rs)
        rs1.append(rs)
    rs=np.array(rs1)
    return rs,y

# 单点测试
def test_Point(config:LSTM_Config):
    model = LSTMModel.from_config(config).to(config.device)
    model.load_state_dict(torch.load(config.model_path))   
    features=config.features.values   
    feature_scaler = ArrayMinMaxScaler(config.feature_range)    
    features = feature_scaler.fit_transform(config.features)    
    labels = config.labels.values#.reshape(-1, 1)   
    label_scaler = ArrayMinMaxScaler(config.label_range)
    label_scaler.fit()  
    x=features[0:120]
    # print("x",x)
    rs=predict_future(model,x, config, label_scaler)
    y=labels[119]
    return rs,y
