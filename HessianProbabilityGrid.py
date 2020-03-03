import matplotlib.pyplot as plt
import numpy as np
import probscale
import scipy.stats as stats
from scipy.stats import pearson3


class Data:
    """
    # 水文数据类

    ## 构造函数参数
    
    + `arr`：水文数据
    """
    def __init__(self, arr):
        self.arr = arr
        self.n = len(arr)
        if len(arr) < 99:
            self.probLimLeft = 1
        else:
            self.probLimLeft = 10**(2 - np.ceil(np.log10(self.n + 2)))
        self.probLimRight = 100 - self.probLimLeft

    def figure(self, grid=True, logVert=False, font=["Sarasa Gothic CL"]):
        """
        # 绘制图形
        
        ## 输入参数
        
        + `gird`：是否显示背景网格，默认为 `True`
        
        + `logVert`：纵坐标是否为对数坐标，默认为 `False`
        
        + `font`：标签字体，默认为更纱黑体 CL
        """
        fig, ax = plt.subplots()
        plt.rcParams["font.sans-serif"] = font
        ax.set_xscale("prob")
        # 横坐标改为概率坐标
        ax.set_xlim(self.probLimLeft, self.probLimRight)

        plt.grid(grid)
        # 背景网格

    def statParams(self, varSkew=False, output=True):
        """
        # 输出数据的统计参数
        
        ## 输入参数
        
        + `varSkew`：偏态系数计算算法选择，具体可参考 wiki「Skewness」词条
        
        + `output`：是否在控制台输出参数，默认为 True
        """
        self.expectation = np.mean(self.arr)
        # 期望
        self.modulusRatio = self.arr / self.expectation
        # 模比系数
        self.coeffOfVar = np.sqrt(
            np.sum((self.modulusRatio - 1)**2) / (self.n - 1))
        # 变差系数

        if not varSkew:
            self.coeffOfSkew = np.sum((self.modulusRatio - 1)**3) / (
                (self.n - 3) * self.coeffOfVar**3)
        else:
            self.coeffOfSkew = stats.skew(self.arr, bias=False)
        # 偏态系数
        if output:
            print("期望 EX 为 {:.2f}".format(self.expectation))
            print("变差系数 Cv 为 {:.2f}".format(self.coeffOfVar))
            print("偏态系数 Cs 为 {:.3f}".format(self.coeffOfSkew))

    def empiScatter(self, method="expectation"):
        """
        # 点绘经验概率点
        
        ## 输入参数
        
        + `method`：经验频率计算方法，可选值见下列表
        
            - `"expectation"`：数学期望公式，默认
            
            - `"chegdayev"`：切哥达耶夫公式
            
            - `"hessian"`：海森公式
        """
        self.sorted = np.sort(self.arr)[::-1]
        # 逆序排序输入数组

        if method == "expectation":
            self.empiProb = np.arange(1, self.n + 1) / (self.n + 1) * 100
            # 数学期望公式
        elif method == "chegdayev":
            self.empiProb = (np.arange(1, self.n + 1) - 0.3) / (self.n +
                                                                0.4) * 100
            # 切哥达耶夫公式
        elif method == "hessian":
            self.empiProb = (np.arange(1, self.n + 1) - 0.5) / self.n * 100
            # 海森公式
        # 计算经验概率

        plt.scatter(self.empiProb,
                    self.sorted,
                    marker="x",
                    c="k",
                    label="经验概率点")
        # 点绘经验概率

    def momentPlot(self):
        """
        # 绘制矩法估计参数理论概率曲线
        """
        x = np.linspace(self.probLimLeft, self.probLimRight, 1000)
        theoY = (pearson3.ppf(1 - x / 100, self.coeffOfSkew) * self.coeffOfVar
                 + 1) * self.expectation

        plt.plot(x, theoY, "b--", lw=1, label="矩法估计参数概率曲线")
        # 绘制理论曲线

    def plotFitting(self, method="OLS", output=True):
        """
        # 优化适线
        
        ## 输入参数
        
        + `method`：优化适线方法，可选值见下列表
        
            - `"OLS"`，离差平方和最小，默认
        
            - `"ABS"`，离差绝对值最小（没做出来）
            
            - `"WLS"`，相对离差平方和最小（也没做出来）
        """

        if method == "OLS":
            R = []
            for fitCS in np.arange(0, 10 * self.coeffOfVar, 0.001):
                empiPhi = pearson3.ppf(1 - self.empiProb / 100, fitCS)
                fitEX = (np.sum(self.sorted) * np.sum(empiPhi**2) -
                         np.sum(self.sorted * empiPhi) * np.sum(empiPhi)) / (
                             self.n * np.sum(empiPhi**2) - np.sum(empiPhi)**2)

                fitCV = (self.n * np.sum(self.sorted * empiPhi) -
                         np.sum(self.sorted) * np.sum(empiPhi)) / (
                             np.sum(self.sorted) * np.sum(empiPhi**2) -
                             np.sum(self.sorted * empiPhi) * np.sum(empiPhi))

                R.append(
                    np.sum((self.sorted - self.expectation *
                            (1 + fitCV * empiPhi))**2))

                if len(R) > 2 and R[-1] > R[-2]:
                    self.fitEX = fitEX
                    self.fitCV = fitCV
                    self.fitCS = fitCS
                    break
                # ！谁有好算法帮我重构

        if output:
            print("适线后")
            print("期望 EX 为 {:.2f}".format(self.fitEX))
            print("变差系数 Cv 为 {:.2f}".format(self.fitCV))
            print("偏态系数 Cs 为 {:.3f}".format(self.fitCS))

    def fittedPlot(self):
        """
        # 绘制适线后的概率曲线
        
        """

        x = np.linspace(self.probLimLeft, self.probLimRight, 1000)
        theoY = (pearson3.ppf(1 - x / 100, self.fitCS) * self.fitCV +
                 1) * self.fitEX

        plt.plot(x, theoY, "r-", lw=2, label="适线后概率曲线")
        # 绘制理论曲线

    def prob2Value(self, prob):
        """
        # 由设计频率转换设计值
        
        ## 输入参数
        
        + `prob`：设计频率，单位百分数
        
        ## 输出参数
        
        + `value`：设计值
        """

        value = (pearson3.ppf(1 - prob / 100, self.fitCS) * self.fitCV +
                 1) * self.fitEX

        print("{0}% 的设计频率对应的设计值为 {1:.2f}".format(prob, value))

        return value

    def value2Prob(self, value):
        """
        # 由设计值转换设计参数
        
        ## 输入参数
        
        + `value`：设计值
        
        ## 输出参数
        
        + `prob`：设计频率，单位百分数
        """
        prob = pearson3.cdf(
            (value / self.fitEX - 1) / self.fitCV, self.fitCS) * 100

        print("{0} 的设计值对应的设计频率为 {1:.4f}%".format(value, prob))

        return prob


data = Data(
    np.array([
        538.3,
        624.9,
        663.2,
        591.7,
        557.2,
        998,
        641.5,
        341.1,
        964.2,
        687.3,
        546.7,
        509.9,
        769.2,
        615.5,
        417.1,
        789.3,
        732.9,
        1064.5,
        606.7,
        586.7,
        567.4,
        587.7,
        709,
        883.5,
    ]))
# 6.3 题的数据

data.figure()
data.statParams()
data.empiScatter()
data.momentPlot()
data.plotFitting()
data.fittedPlot()

data.prob2Value(prob=10)
data.value2Prob(value=935.18)

plt.legend()
plt.show()