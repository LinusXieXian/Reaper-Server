# -*- coding: utf-8 -*-
# @author: xiexian
import math
import numpy
import pandas as pd
import pymysql
import sys
from datetime import datetime, timedelta
from sklearn.cross_validation import train_test_split  # 引用交叉验证
from sklearn.linear_model import LinearRegression

Number_Of_Trading_Days = 245  # 一年的交易日个数
conn = pymysql.connect(host='101.132.182.30', user='reaper', passwd='reaper112233', db='reaper', port=3306,
                       charset='utf8')
cur = conn.cursor()
fundDict = {}


# 计算标准差,参数类型：列表
def standardDeviation(rate):
    return numpy.std(rate)


# 计算下行标准差，参数类型：列表
def downsideStdDev(rate, rf):  # rf:risk-free rate
    rateLen = len(rate)
    smallerRate = []
    smallerLen = 0
    squareSum = 0
    for i in range(rateLen):
        if (rate[i] < rf[i]):
            smallerRate.append(rate[i])
            squareSum += (rate[i] - rf[i]) * (rate[i] - rf[i])
            smallerLen += 1
    if (smallerLen <= 1):
        return 0
    else:
        return math.sqrt(squareSum / (float)(smallerLen - 1))


# 计算协方差，参数类型：列表
def countCovariance(x, y):
    xy = []
    xyLen = min(len(x), len(y))
    for i in range(xyLen):
        xy.append(x[i] * y[i])
    xAvg = (float)(sum((x))) / len(x)
    yAvg = (float)(sum(y)) / len(y)
    xyAvg = (float)(sum(xy)) / len(xy)
    # Cov(x,y)=E[xy]-E[x]E[y]
    cov = xyAvg - xAvg * yAvg
    return cov


# 计算Beta值，参数类型：列表
def countBeta(resultRate, marketRate):
    x = resultRate
    y = marketRate
    cov = countCovariance(x, y)
    var = numpy.var(marketRate)
    if (0 == var):
        return 0
    beta = (float)(cov) / var
    return beta


# 计算Alpha，参数类型：前三个为列表，beta为数值
def countAlpha(resultRate, marketRate, rf, beta):
    alpha = []
    alphaLen = min(len(resultRate), len(marketRate))
    for i in range(alphaLen):
        alpha.append((resultRate[i] - rf[i]) - beta * (marketRate[i] - rf[i]))
    return alpha


# 计算夏普比，参数类型：列表
def countSharpeRatio(resultRate, rf):
    Erp = sum(resultRate) / len(resultRate)
    Erf = sum(rf) / len(rf)
    std = standardDeviation(resultRate)
    if (0 == std):
        return 0
    else:
        return (Erp - Erf) / std


# 计算两个序列的相关系数，参数类型：列表
def countCorrelation(r1, r2):
    return countCovariance(r1, r2) / (numpy.std(r1) * numpy.std(r2))


# 计算在险价值，参数类型：数值
def countValue_at_risk(yearlySigam):
    return 2.33 * yearlySigam / math.sqrt(52)


# 计算年化波动率，参数类型：列表
def annualizedVolatility(r):
    return standardDeviation(r) * math.sqrt(Number_Of_Trading_Days)


# 计算年化收益率，参数类型：列表
def annualizedRate(dailyRate, days):
    result = 0
    countLen = 0
    while (countLen < len(dailyRate) and countLen < Number_Of_Trading_Days):
        result += dailyRate[countLen]
        countLen += 1
    return result / days * 365


# 计算特雷诺比率，参数类型：前两个为列表，beta为数值
def TreynorRatio(resultRate, rf, beta):
    if (0 == beta):
        return 0
    Erp = sum(resultRate) / len(resultRate)
    Erf = sum(rf) / len(rf)
    return (Erp - Erf) / beta


# 求两个列表的差
def ListSub(l1, l2):
    rtn = []
    length = min(len(l1), len(l2))
    for i in range(length):
        rtn.append(l1[i] - l2[i])
    return rtn


def ListSubSqare(l1, l2):
    rtn = []
    length = min(len(l1), len(l2))
    for i in range(length):
        rtn.append((l1[i] - l2[i]) * (l1[i] - l2[i]))
    return rtn


# 获取数据库里基金的所有代码
def getCode():
    try:
        cur.execute('SELECT  distinct code FROM reaper.fund_netValue')
        data = cur.fetchall()
        code = []
        for d in data:
            code.append(str(d[0]))
    except Exception:
        print("查询失败")
    return code


# 基金类
class Fund:
    def __init__(self, code):
        self.code = code  # 基金代码
        self.date = []
        self.accNetValue = []
        self.nav = []  # 单位净值
        self.dailyRate = []  # 日收益率


# 根据基金代码从数据库里获取某个基金的信息
def getFund(code):
    fund = Fund(code)
    try:
        cur.execute(
            'SELECT  date,unitNetValue,dailyRate,cumulativeNetValue FROM reaper.fund_netValue WHERE code=' + code + ' ORDER BY date DESC')
        data = cur.fetchall()
        for d in data:
            fund.date.append((str(d[0]))[:10])  # 去掉时分秒
            nav = filter(lambda ch: ch in '0123456789.', str(d[1]))
            if ('' == nav):  # 缺失值处理
                appNav = sum(fund.nav[-11:-1]) / 10
                fund.nav.append(appNav)
            else:
                fund.nav.append(float(nav))

            dailyRate = filter(lambda ch: ch in '-0123456789.', str(d[2]))
            if ('' == dailyRate):
                dIndex = data.index(d)
                appDailyRate = 0
                if (dIndex + 1 < len(data)):
                    yesterdayNav = filter(lambda ch: ch in '-0123456789.', str(data[dIndex + 1][1]))
                    if (yesterdayNav != ''):
                        yesterdayNav = float(yesterdayNav)
                        appDailyRate = (fund.nav[-1] - yesterdayNav) / yesterdayNav
                    else:
                        pass
                else:
                    appDailyRate = sum(fund.dailyRate[-11:-1]) / 10

                fund.dailyRate.append(appDailyRate)
            else:
                fund.dailyRate.append((float(dailyRate)) / 100)  # 数据库里的利率省略了百分号的，除回来
            # print (float(d[2]))/100

            accNetValue = filter(lambda ch: ch in '0123456789.', str(d[3]))
            if ('' == accNetValue):  # 缺失值处理
                appNav = sum(fund.accNetValue[-11:-1]) / 10
                fund.accNetValue.append(appNav)
            else:
                fund.accNetValue.append(float(accNetValue))

    except Exception:
        print(code + "查询失败")
    return fund


def countMarketReturn(startTime, endTime):
    data = []
    cur.execute('SELECT closePrice FROM basic_stock_index where stockId="000001" and date=' + '\'' + startTime.strftime(
        '%Y-%m-%d') + ' 00:00:00' + '\'')
    data = cur.fetchall()
    while (0 == len(data)):  # 若数据库里无数据（这天不是交易日），则后退到最近的一个交易日
        startTime = startTime - timedelta(days=1)
        cur.execute(
            'SELECT closePrice FROM basic_stock_index where stockId="000001" and date=' + '\'' + startTime.strftime(
                '%Y-%m-%d') + ' 00:00:00' + '\'')
        data = cur.fetchall()

    startPrice = (float)(filter(lambda ch: ch in '0123456789.', str(data[0][0])))

    cur.execute('SELECT closePrice FROM basic_stock_index where stockId="000001" and date=' + '\'' + endTime.strftime(
        '%Y-%m-%d') + ' 00:00:00' + '\'')
    data = cur.fetchall()
    while (0 == len(data)):
        endTime = endTime - timedelta(days=1)
        cur.execute(
            'SELECT closePrice FROM basic_stock_index where stockId="000001" and date=' + '\'' + endTime.strftime(
                '%Y-%m-%d') + ' 00:00:00' + '\'')
        data = cur.fetchall()

    endPrice = (float)(filter(lambda ch: ch in '0123456789.', str(data[0][0])))

    return (endPrice - startPrice) / startPrice


# 解决日期与收益率以及净值的对应问题，返回的对象的属性包括：
# 各个日期序列的交集，以及该时间序列对应的基金收益率，市场收益率和无风险利率(通过相同的下标对应，如fundRate[i],rm[i],rf[i]同为date[i]这一天的数据）
class corrDate:
    def __init__(self, date1, l1, date2, l2, date3=0, l3=0, nav=[], accNetValue=[]):
        self.date = []  # date1，date2，date3这三个日期序列的交集
        self.fundRate = []
        self.rm = []
        self.rf = []
        self.nav = []
        self.accNetValue = []
        if (0 == date3):  # 只有两个时间序列的情况
            i1 = 0
            i2 = 0
            while (i1 < len(date1) and i2 < len(date2)):
                if (date1[i1] > date2[i2]):
                    while (i1 < len(date1) and date1[i1] > date2[i2]):
                        i1 += 1
                else:
                    while (i2 < len(date2) and date2[i2] > date1[i1]):
                        i2 += 1

                if (i1 < len(date1) and i2 < len(date2)):
                    # 此处有date1[i1]=date2[i2]
                    self.date.append(date1[i1])
                    self.fundRate.append(l1[i1])
                    self.rm.append(l2[i2])
                    i1 += 1
                    i2 += 1
        else:  # 三个时间序列
            i1 = 0
            i2 = 0
            i3 = 0
            while (i1 < len(date1) and i2 < len(date2) and i3 < len(date3)):
                if ((date1[i1] < date2[i2] or date1[i1] == date2[i2]) and (
                                date1[i1] < date3[i3] or date1[i1] == date3[i3])):
                    while (i2 < len(date2) and date1[i1] < date2[i2]):
                        i2 += 1
                    while (i3 < len(date3) and date1[i1] < date3[i3]):
                        i3 += 1

                elif ((date2[i2] < date1[i1] or date2[i2] == date1[i1]) and (
                                date2[i2] < date3[i3] or date2[i2] == date3[i3])):
                    while (i1 < len(date1) and date2[i2] < date1[i1]):
                        i1 += 1
                    while (i3 < len(date3) and date2[i2] < date3[i3]):
                        i3 += 1

                else:
                    while (i1 < len(date1) and date3[i3] < date1[i1]):
                        i1 += 1
                    while (i2 < len(date2) and date3[i3] < date2[i2]):
                        i2 += 1

                if (i1 < len(date1) and i2 < len(date2) and i3 < len(date3)):
                    self.date.append(date1[i1])
                    self.fundRate.append(l1[i1])
                    if (len(nav) != 0):
                        self.nav.append(nav[i1])
                    if (len(accNetValue) != 0):
                        self.accNetValue.append(accNetValue[i1])
                    self.rm.append(l2[i2])
                    self.rf.append(l3[i3])
                    i1 += 1
                    i2 += 1
                    i3 += 1
                    # 按起始时间计算(如用户要求计算某一段时间的波动率）

    def countByDate(self, startTime, endTime):
        i = 0
        tempDate = []
        tempFundRate = []
        tempRm = []
        tempRf = []
        tempNav = []
        tempAccNetValue = []
        while (i < len(self.date) and self.date[i] > endTime):
            i += 1
        while (i < len(self.date) and self.date[i] >= startTime):
            tempDate.append(self.date[i])
            tempFundRate.append(self.fundRate[i])
            tempRm.append(self.rm[i])
            tempRf.append(self.rf[i])
            if (len(self.nav) != 0):
                tempNav.append(self.nav[i])
            if (len(self.accNetValue) != 0):
                tempAccNetValue.append(self.accNetValue[i])
            i += 1

        self.date = tempDate
        self.fundRate = tempFundRate
        self.rm = tempRm
        self.rf = tempRf
        self.nav = tempNav
        self.accNetValue = tempAccNetValue


# 市场收益率对象，从数据库里读取数据（日更新）
class Rm:
    def __init__(self):
        self.date = []
        self.closingPrice = []
        self.dayRate = []
        self.monthRate = []

        cur.execute(
            'SELECT  date,beforeClosePrice,closePrice FROM basic_stock_index where stockId="000001" order by date DESC ')
        data = cur.fetchall()
        dataLen = len(data)
        i = 0

        while (i + 20 < dataLen):
            d = data[i]
            self.date.append((filter(lambda ch: ch in '-0123456789', str(d[0].strftime('%Y-%m-%d')))))
            beforePrice = (float)(filter(lambda ch: ch in '0123456789.', str(d[1])))
            curPrice = (float)(filter(lambda ch: ch in '0123456789.', str(d[2])))
            monthAgoPrice = (float)(filter(lambda ch: ch in '0123456789.', str(data[i + 20][2])))  # 设每月20个交易日
            self.closingPrice.append(curPrice)
            dateRate = (curPrice - beforePrice) / beforePrice
            if ('' == dateRate):
                dateRate = '0'
                # print dateRate,self.date[-1]
            self.dayRate.append(float(dateRate))
            self.monthRate.append((curPrice - monthAgoPrice) / monthAgoPrice)
            i += 1


# 无风险收益率对象，从数据库读取数据（日更）
class Rf:
    def __init__(self):
        self.date = []
        self.rfDaily = []
        self.rfWeekly = []
        self.rfMonthly = []
        self.rfYearly = []

        cur.execute(
            'SELECT date,closePrice,priceFluctuation from basic_stock_index where stockId="000012" order by date DESC ')
        data = cur.fetchall()
        dataLen = len(data)
        i = 0
        date = data[i][0].strftime('%Y-%m-%d')
        while (date > '2016-12-30'):
            self.date.append(date)
            self.rfDaily.append(data[i][2])
            self.rfWeekly.append((data[i][1] - data[i + 5][1]) / data[i + 5][1])
            self.rfMonthly.append((data[i][1] - data[i + 20][1]) / data[i + 20][1])
            self.rfYearly.append(
                (data[i][1] - data[i + Number_Of_Trading_Days][1]) / data[i + Number_Of_Trading_Days][1])
            i += 1
            date = data[i][0].strftime('%Y-%m-%d')

        cur.execute('SELECT date,rfYearly,rfDaily,rfWeekly,rfMonthly from rf order by date DESC ')
        data = cur.fetchall()
        dataLen = len(data)
        for d in data:
            self.date.append(filter(lambda ch: ch in '0123456789-', str(d[0])))
            self.rfYearly.append(((float)(filter(lambda ch: ch in '-0123456789.', str(d[1])))) / 100)
            self.rfDaily.append(((float)(filter(lambda ch: ch in '-0123456789.', str(d[2])))) / 100)
            self.rfWeekly.append(((float)(filter(lambda ch: ch in '-0123456789.', str(d[3])))) / 100)
            self.rfMonthly.append(((float)(filter(lambda ch: ch in '-0123456789.', str(d[4])))) / 100)


# 构造基金组合
def fundGroup(codeList, pencentage):
    code0 = codeList[0]
    if (len(codeList) != len(pencentage)):
        print "基金代码序列和百分比序列长度不一致\n"
        return
    # 前端应该传来的用于构造基金组合的数据
    # codeList为用户所选的组合中所用基金的代码（列表类型），pencentage为组合中所用基金占组合的百分比（也为列表类型，与codeList通过下标对应，如pencentage[i]表示基金代码为codeList[i]的基金占组合的百分比）
    minEndDate = '9999-12-30'
    maxStartDate = '1000-01-01'
    for code in codeList:
        fundDict[code] = getFund(code)  # 获取组合中各个基金的信息
        # print code,fundDict[code].date[-1],fundDict[code].date[0]
        # print '!!!!!!!!\n'
        if (fundDict[code].date[-1] > maxStartDate):
            maxStartDate = fundDict[code].date[-1]  # 时间序列是按逆序存放的
        if (fundDict[code].date[0] < minEndDate):
            minEndDate = fundDict[code].date[0]
    myFundGroup = Fund("myFundGroup")  # 创建一个空的基金组合对象，加权平均后的数据可放到这个对象中
    maxStartTime = datetime.strptime(maxStartDate, '%Y-%m-%d')
    minEndTime = datetime.strptime(minEndDate, '%Y-%m-%d')
    # print maxStartTime, minEndTime
    days = (minEndTime - maxStartTime).days
    # print days
    index = []  # 各个基金的下标列表
    for i in range(len(codeList)):
        index.append(0)
    if (days <= 0):
        print '这些基金的数据没有交集\n'
        return
    breakFlag = 0
    curDays = 0
    while (curDays < days):

        curTime = minEndTime - timedelta(days=curDays)  # 从结束时间开始
        for i in range(len(codeList)):
            while (index[i] < len(fundDict[codeList[i]].date) and fundDict[codeList[i]].date[
                index[i]] > curTime.strftime('%Y-%m-%d')):
                index[i] += 1

        for i in range(len(codeList)):
            if (index[i] >= len(fundDict[codeList[i]].date)):
                breakFlag = 1
                break
        if (1 == breakFlag):
            break

        if (fundDict[code0].date[index[0]] != curTime.strftime('%Y-%m-%d')):  # 如果今天不是交易日
            curDays += 1
            continue

        myFundGroup.date.append(fundDict[codeList[0]].date[index[0]])
        curRate = 0
        curNAV = 0
        curAccNetValue = 0
        # for i in range(len(pencentage)):
        #     curRate += fundDict[codeList[i]].dailyRate[index[i]] * pencentage[i]
        #     curNAV += fundDict[codeList[i]].nav[index[i]] * pencentage[i]
        #     curAccNetValue += fundDict[codeList[i]].accNetValue[index[i]] * pencentage[i]
        for i in range(len(pencentage)):
            curRate += fundDict[codeList[i]].dailyRate[index[i]] * pencentage[i]
            curNAV += pencentage[i] * (fundDict[codeList[i]].nav[index[i]])  # 假设对组合投资1块钱，则curNAV即为买到的净值
            curAccNetValue += pencentage[i] * (fundDict[codeList[i]].accNetValue[index[i]])

        myFundGroup.dailyRate.append(curRate)
        myFundGroup.nav.append(curNAV)
        myFundGroup.accNetValue.append(curAccNetValue)

        curDays += 1

    # print myFundGroup.date,'\n\n\n',myFundGroup.nav,'\n\n\n',myFundGroup.accNetValue
    return myFundGroup


# 基金组合测试函数
def fundGroupTest(codeList, pencentage, startTime, endTime):
    code = 'myFundGroup'
    fundDict[code] = fundGroup(codeList, pencentage)

    temp = corrDate(fundDict[code].date, fundDict[code].dailyRate, rm.date, rm.dayRate, rf.date, rf.rfMonthly,
                    fundDict[code].nav, fundDict[code].accNetValue)

    # print len(temp.date), len(temp.nav), len(temp.accNetValue)
    temp.countByDate(startTime, endTime)
    # print len(temp.date), len(temp.nav), len(temp.accNetValue)

    for i in range(len(temp.date)):
        print "#", "日收益率=", temp.date[i], temp.fundRate[i]

    for i in range(len(temp.date)):
        print "#", "累计净值=", temp.date[i], temp.accNetValue[i]

    for i in range(len(temp.date)):
        # 每日回撤=（当前日之前出现的最大的净值-当日净值）/当日净值
        retracement = 0
        if (i + 1 == len(temp.nav)):
            retracement = 0
        else:
            preMaxNAV = max(temp.nav[i:-1])
            retracement = (preMaxNAV - temp.nav[i]) / temp.nav[i]
        print "#", "每日回撤=", temp.date[i], retracement

    print "# 最大跌幅=", min(temp.fundRate)
    print "# 期初净值=", temp.nav[-1]
    print "# 期末净值=", temp.nav[0]
    print "# 累计收益=", sum(temp.fundRate)

    y = ListSub(temp.fundRate, temp.rf)
    x1 = ListSub(temp.rm, temp.rf)
    x2 = ListSubSqare(temp.rm, temp.rf)
    obj_dict = {'y': y, 'x1': x1, 'x2': x2}
    data = pd.DataFrame(obj_dict)  # 通过字典创建dataframe
    x = data[['x1', 'x2']]
    y = data['y']
    X_train, X_test, y_train, y_test = train_test_split(x, y, random_state=1)
    linreg = LinearRegression()

    model = linreg.fit(X_train, y_train)

    rmSubSqareRfAvg = sum(x2) / len(x2)

    print "# 择股系数=", linreg.intercept_
    print "# 择时系数=", linreg.coef_[1] * rmSubSqareRfAvg

    beta = countBeta(temp.fundRate, temp.rm)
    print "# beta=", beta

    # startTime = datetime.strptime(startTime, '%Y-%m-%d')
    # endTime = datetime.strptime(endTime, '%Y-%m-%d')
    # days = (endTime - startTime).days
    # totalReturn = (temp.nav[0] - temp.nav[-1]) / temp.nav[-1]
    # startTime = datetime.strptime(temp.date[-1], '%Y-%m-%d')
    # endTime = datetime.strptime(temp.date[0], '%Y-%m-%d')
    # days = (endTime - startTime).days
    startTime = datetime.strptime(temp.date[-1], '%Y-%m-%d')
    endTime = datetime.strptime(temp.date[0], '%Y-%m-%d')
    days = (endTime - startTime).days
    print "# 年化收益率=", annualizedRate(temp.fundRate, days)

    print "# 年化波动率=", annualizedVolatility(temp.fundRate)

    print "# 在险价值=", countValue_at_risk(annualizedVolatility(temp.fundRate))

    print "# 下行标准差=", downsideStdDev(temp.fundRate, temp.rf)

    print "# 夏普比=", countSharpeRatio(temp.fundRate, temp.rf)

    print "# 特雷诺指数=", TreynorRatio(temp.fundRate, temp.rf, beta)


def countFundCorrelation(code0, code1):  # 计算相关系数的函数，参数：两个基金代码
    fund0 = fundDict[code0]
    fund0CorrDate = corrDate(fund0.date, fund0.dailyRate, rm.date, rm.dayRate, rf.date, rf.rfMonthly)
    fund1 = fundDict[code1]
    fund1CorrDate = corrDate(fund1.date, fund1.dailyRate, rm.date, rm.dayRate, rf.date, rf.rfMonthly)

    print "#", code0, code1, countCorrelation(fund0CorrDate.fundRate, fund1CorrDate.fundRate)


rm = Rm()  # 读取市场数据
rf = Rf()  # 读取无风险利率
codeList = []
percentage = []

sys_param_len = len(sys.argv)
for index in range(3, sys_param_len):
    if index % 2 == 1:
        codeList.append(sys.argv[index])
    else:
        percentage.append(float(sys.argv[index]))

# 计算指标
fundGroupTest(codeList, percentage, sys.argv[1], sys.argv[2])

# 计算相关系数
code_list_len = len(codeList)
for j in range(code_list_len):
    code0 = codeList[j]
    for k in range(j + 1, code_list_len):
        code1 = codeList[k]
        countFundCorrelation(code0, code1)

cur.close()
conn.close()
