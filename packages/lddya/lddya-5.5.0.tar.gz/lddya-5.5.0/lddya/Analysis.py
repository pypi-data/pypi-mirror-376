import numpy as np
from scipy import stats

class Analyzer:
    def __init__(self, data=None):
        """
        统计分析工具类
        :param data: list, np.ndarray, or None
        """
        self.data = np.array(data) if data is not None else None

    def set_data(self, data):
        """手动设置/更新数据"""
        self.data = np.array(data)

    def _get_data(self, data):
        """内部方法：获取数据，优先使用参数，其次用类内数据"""
        if data is not None:
            return np.array(data)
        elif self.data is not None:
            return self.data
        else:
            raise ValueError("No data provided. Please pass data or set it first.")

    def mean(self, data=None,axis=None):
        """均值"""
        d = self._get_data(data)
        return np.mean(d,axis=axis)

    def std(self, data=None, ddof=1,axis=None):
        """标准差 (默认样本标准差, ddof=1)"""
        d = self._get_data(data)
        return np.std(d, ddof=ddof,axis=axis)

    def var(self, data=None, ddof=1,axis=None):
        """方差"""
        d = self._get_data(data)
        return np.var(d, ddof=ddof,axis=axis)

    def summary(self, data=None,axis=None):
        """统计摘要：均值、标准差、最小值、最大值"""
        d = self._get_data(data)
        return {
            "mean": np.mean(d,axis=axis),
            "std": np.std(d, ddof=1,axis=axis),
            "min": np.min(d,axis=axis),
            "max": np.max(d,axis=axis)
        }

    def t_test(self,data2,data=None,alpha=0.05):
        """
        独立样本t检验，返回[p值, 是否显著]
        
        参数：
            data, data2 : 两组数据（列表/数组）
            alpha       : 显著性阈值（默认0.05）
            
        返回：
            [p值, 显著性]（p < alpha时显著为True）
        """
        d = self._get_data(data)
        _, p = stats.ttest_ind(d, np.array(data2))
        return [p, p < alpha]
    

