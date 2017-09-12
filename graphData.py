# -*- coding: utf-8 -*-
#!/usr/bin/env python
#@author: xiexian

import csv
import pymysql
import xlrd
import time
from datetime import datetime, timedelta
from xlrd import xldate_as_tuple
from xlutils.copy import copy
import numpy
import pandas as pd
import math
from sklearn.cross_validation import train_test_split  #���ý�����֤
from sklearn.linear_model import LinearRegression
import sys


Number_Of_Trading_Days=245#һ��Ľ����ո���



#�����׼��,�������ͣ��б�
def standardDeviation(rate):
     return numpy.std(rate)

#�������б�׼��������ͣ��б�
def downsideStdDev(rate,rf):   #rf:risk-free rate
     rateLen=len(rate)
     smallerRate=[]
     smallerLen=0
     squareSum=0
     for i in range(rateLen):
          if (rate[i]<rf[i]):
               smallerRate.append(rate[i])
               squareSum +=(rate[i]-rf[i])*(rate[i]-rf[i])
               smallerLen+=1
     if(smallerLen<=1):
          return 0
     else:
          return math.sqrt(squareSum/(float)(smallerLen-1))



#����Э����������ͣ��б�
def countCovariance(x,y):
     xy=[]
     xyLen=min(len(x),len(y))
     for i in range(xyLen):
          xy.append(x[i]*y[i])
     xAvg=(float)(sum((x)))/len(x)
     yAvg=(float)(sum(y))/len(y)
     xyAvg=(float)(sum(xy))/len(xy)
     #Cov(x,y)=E[xy]-E[x]E[y]
     cov=xyAvg-xAvg*yAvg
     return cov




#����Betaֵ���������ͣ��б�
def countBeta(resultRate,marketRate):
     x=resultRate
     y=marketRate   
     cov=countCovariance(x,y)
     var=numpy.var(marketRate)
     if(0==var):
          return 0
     beta=(float)(cov)/var
     return beta


#����Alpha���������ͣ�ǰ����Ϊ�б�betaΪ��ֵ
def countAlpha(resultRate,marketRate,rf,beta):
     alpha=[]
     alphaLen=min(len(resultRate),len(marketRate))
     for i in range(alphaLen):
          alpha.append((resultRate[i]-rf[i])-beta*(marketRate[i]-rf[i]))
     return alpha



#�������ձȣ��������ͣ��б�
def countSharpeRatio(resultRate,rf):
     Erp=sum(resultRate)/len(resultRate)
     Erf=sum(rf)/len(rf)
     std=standardDeviation(resultRate)
     if(0==std):
          return 0
     else:
          return (Erp-Erf)/std
     


#�����������е����ϵ�����������ͣ��б�
def countCorrelation(r1,r2):
     return countCovariance(r1,r2)/(numpy.std(r1)*numpy.std(r2))




#�������ռ�ֵ���������ͣ���ֵ
def countValue_at_risk(yearlySigam):
     return 2.33*yearlySigam/math.sqrt(52)




#�����껯�����ʣ��������ͣ��б�
def annualizedVolatility(r):
     return standardDeviation(r)*math.sqrt(Number_Of_Trading_Days)



#�����껯�����ʣ��������ͣ��б�
def annualizedRate(dailyRate):
     result=0
     countLen=0
     while(countLen<len(dailyRate) and countLen<Number_Of_Trading_Days):
          result+=dailyRate[countLen]
          countLen+=1
     return result/countLen*Number_Of_Trading_Days



#��������ŵ���ʣ��������ͣ�ǰ����Ϊ�б�betaΪ��ֵ
def TreynorRatio(resultRate,rf,beta):
     Erp=sum(resultRate)/len(resultRate)
     Erf=sum(rf)/len(rf)
     return (Erp-Erf)/beta





#�������б�Ĳ�
def ListSub(l1,l2):
     rtn=[]
     length=min(len(l1),len(l2))
     for i in range(length):
          rtn.append(l1[i]-l2[i])
     return rtn


def ListSubSqare(l1,l2):
     rtn=[]
     length=min(len(l1),len(l2))
     for i in range(length):
          rtn.append((l1[i]-l2[i])*(l1[i]-l2[i]))
     return rtn



#��ȡ���ݿ����������д���
def getCode():
    try:
        conn=pymysql.connect(host='106.15.203.173',user='reaper',passwd='reaper112233',db='reaper',port=3306,charset='utf8')
        cur=conn.cursor()#��ȡһ���α�
        cur.execute('SELECT  distinct code FROM reaper.fund_netValue')
        data=cur.fetchall()
        code=[]    
        for d in data :
            code.append(str(d[0]))        
    except Exception :print("��ѯʧ��")
    return code

#������
class Fund:
     def __init__(self,code):
          self.code=code   #�������
          self.date=[]
          self.nav=[]   #��λ��ֵ
          self.dailyRate=[]   #��������       

#���ݻ����������ݿ����ȡĳ���������Ϣ
def getFund(code):
    fund=Fund(code)
    try:
        conn=pymysql.connect(host='106.15.203.173',user='reaper',passwd='reaper112233',db='reaper',port=3306,charset='utf8')
        cur=conn.cursor()
        cur.execute('SELECT  date,unitNetValue,dailyRate FROM reaper.fund_netValue WHERE code='+code)
        data=cur.fetchall()               
        for d in data :          
            fund.date.append((str(d[0]))[:10]) #ȥ��ʱ����
            nav=filter(lambda ch: ch in '0123456789.',str(d[1]))
            if(''==nav):
                appNav=sum(fund.nav[-11:-1])/10
                fund.nav.append(appNav)
            else:
                fund.nav.append(float(nav))
                 
            dailyRate=filter(lambda ch: ch in '-0123456789.',str(d[2]))
            if(''==dailyRate):
                dIndex=data.index(d)
                appDailyRate=0
                if(dIndex+1<len(data)):
                    yesterdayNav=filter(lambda ch: ch in '-0123456789.',str(data[dIndex+1][1]))
                    if(yesterdayNav!=''):
                        yesterdayNav=float(yesterdayNav)
                        appDailyRate=(fund.nav[-1]-yesterdayNav)/yesterdayNav
                    else:
                         pass                
                else:
                    appDailyRate=sum(fund.dailyRate[-11:-1])/10
                
                fund.dailyRate.append(appDailyRate)
            else:       
                fund.dailyRate.append((float(dailyRate))/100) #���ݿ��������ʡ���˰ٷֺŵģ�������
            #print (float(d[2]))/100
    except Exception :print(code+"��ѯʧ��")
    return fund
    


#����������������Լ���ֵ�Ķ�Ӧ���⣬���صĶ�������԰�����
#�����������еĲ�ֵ���Լ���ʱ�����ж�Ӧ�Ļ��������ʣ��г������ʺ��޷�������(ͨ����ͬ���±��Ӧ����fundRate[i],rm[i],rf[i]ͬΪdate[i]��һ������ݣ�
class corrDate:   
    def __init__(self,date1,l1,date2,l2,date3=0,l3=0):    
          self.date=[]  #date1��date2��date3�������������еĲ�ֵ
          self.fundRate=[]
          self.rm=[]
          self.rf=[]    
          if(0==date3): #ֻ������ʱ�����е����
               i1=0
               i2=0
               while(i1<len(date1) and i2<len(date2)):
                   if(date1[i1]>date2[i2]):
                        while(i1<len(date1) and  date1[i1]>date2[i2]):
                             i1+=1
                   else:
                        while(i2<len(date2)  and date2[i2]>date1[i1]):
                             i2+=1
                    
                   if(i1<len(date1) and i2<len(date2)):
                        #�˴���date1[i1]=date2[i2]
                        self.date.append(date1[i1])
                        self.fundRate.append(l1[i1])
                        self.rm.append(l2[i2])
                        i1+=1
                        i2+=1
          else:#����ʱ������
               i1=0
               i2=0
               i3=0
               while(i1<len(date1) and i2<len(date2) and i3<len(date3)):
                   if((date1[i1]<date2[i2] or date1[i1]==date2[i2]) and (date1[i1]<date3[i3] or date1[i1]==date3[i3])):
                        while(i2<len(date2) and date1[i1]<date2[i2] ):
                             i2+=1
                        while(i3<len(date3) and date1[i1]<date3[i3]):
                             i3+=1
                        
                   elif((date2[i2]<date1[i1] or date2[i2]==date1[i1]) and (date2[i2]<date3[i3] or date2[i2]==date3[i3])):
                        while(i1<len(date1)  and date2[i2]<date1[i1]):
                             i1+=1
                        while(i3<len(date3) and date2[i2]<date3[i3] ):
                             i3+=1
                        
                   else:
                        while(i1<len(date1)  and date3[i3]<date1[i1]):
                             i1+=1
                        while(i2<len(date2) and date3[i3]<date2[i2]):
                             i2+=1
                             
                   if(i1<len(date1) and i2<len(date2) and i3<len(date3)):
                        self.date.append(date1[i1])
                        self.fundRate.append(l1[i1])
                        self.rm.append(l2[i2])
                        self.rf.append(l3[i3])
                        i1+=1
                        i2+=1
                        i3+=1
     #����ʼʱ�����(���û�Ҫ�����ĳһ��ʱ��Ĳ����ʣ�
    def countByDate(self,startTime,endTime):
        i=0
        tempDate=[]
        tempFundRate=[]
        tempRm=[]
        tempRf=[]
        while(i<len(self.date) and self.date[i]>endTime):
            i+=1
        while(i<len(self.date) and self.date[i]>=startTime):
            tempDate.append(self.date[i])
            tempFundRate.append(self.fundRate[i])
            tempRm.append(self.rm[i])
            tempRf.append(self.rf[i])
            i+=1
            
        self.date=tempDate
        self.fundRate=tempFundRate
        self.rm=tempRm
        self.rf=tempRf
          

          


#�г������ʶ�����ʱ�Ǵ�csv�ļ���ȡ���ݣ����ݿ����и����ݿ��޸ĳɴ����ݿ����ȡ
class Rm:
     def __init__(self,fileName):
          self.date=[]   
          self.closingPrice=[]
          self.dayRate=[]
          self.monthRate=[]

          csv_reader = csv.reader(open(fileName))
          firstRow=1
          fundData=[]
          for row in csv_reader:
               if(1==firstRow):
                         firstRow=0
                         continue    
               fundData.append(row)#����ÿһ������
               
          dataLen=len(fundData)
          i=0
          while(i+20<dataLen):     
             self.date.append((filter(lambda ch: ch in '-0123456789',fundData[i][0])))
             curPrice=(float)(filter(lambda ch: ch in '0123456789.', fundData[i][3]))
             monthAgoPrice=(float)(filter(lambda ch: ch in '0123456789.', fundData[i+20][3]))#��ÿ��20��������
             self.closingPrice.append(curPrice)
             dateRate=(filter(lambda ch: ch in '-0123456789.',fundData[i][4]))
             if(''==dateRate):
                 dateRate='0'
             #print dateRate,self.date[-1]
             self.dayRate.append(float(dateRate)/100)
             self.monthRate.append((curPrice-monthAgoPrice)/monthAgoPrice/100)
             i+=1


#�޷��������ʶ�����ʱ�Ǵ�csv�ļ���ȡ����
class Rf:
     def __init__(self,fileName,Treasury=''):
          self.date=[]   
          self.rfDaily=[]
          self.rfWeekly=[]
          self.rfMonthly=[]
          self.rfYearly=[]
          
          if(Treasury!=''):
              data = xlrd.open_workbook(Treasury)

              table=data.sheets()[0]          
              rm=[]
              r=1
              date=datetime(*xldate_as_tuple(table.row_values(r,0)[0],0)).strftime('%Y-%m-%d')
              while (date>'2016-12-30'):  #�ù�ծ���ݼ���2016/12/30�Ժ���޷��������ʣ���ΪFund_RiskFree.csv��û�У�
                  self.date.append(date)
                  self.rfDaily.append(table.row_values(r,4)[0])
                  self.rfWeekly.append((table.row_values(r,3)[0]-table.row_values(r+5,3)[0])/table.row_values(r+5,3)[0])
                  self.rfMonthly.append((table.row_values(r,3)[0]-table.row_values(r+20,3)[0])/table.row_values(r+20,3)[0])
                  self.rfYearly.append((table.row_values(r,3)[0]-table.row_values(r+246,3)[0])/table.row_values(r+246,3)[0])
                  r+=1
                  date=datetime(*xldate_as_tuple(table.row_values(r,0)[0],0)).strftime('%Y-%m-%d')
                  #print date
                  

          with open(fileName, 'r') as f:
               lines=f.readlines()
               isFirstLine=1
               lastLine=lines[-1]

               lineLen=len(lines)
               i=lineLen-1-1 #���һ��Ϊ���У���ȥ
               
               while i>0:
                    line=lines[i]
                    i-=1
                    if(1==isFirstLine):
                         isFirstLine=0
                         continue
                    if(line==lastLine):
                         break
                    date=line[39:58]
                    rfYearly = line[61:76]
                    rfDaily = line[79:92]              
                    rfWeekly = line[95:108]
                    rfMonthly = line[111:125]
                    
                    self.date.append(filter(lambda ch: ch in '0123456789-', date))
                    #print rfYearly
                    self.rfYearly.append(((float)(filter(lambda ch: ch in '-0123456789.', rfYearly)))/100)
                    self.rfDaily.append(((float)(filter(lambda ch: ch in '-0123456789.', rfDaily)))/100)
                    self.rfWeekly.append( ((float)(filter(lambda ch: ch in '-0123456789.', rfWeekly)))/100)
                    self.rfMonthly.append(((float)(filter(lambda ch: ch in '-0123456789.', rfMonthly)))/100)
                 












#���������ϣ�����
def fundGroup():
     fundDict={}
     codeList=[]    #ǰ��Ӧ�ô��������ڹ��������ϵ�����
     pencentage=[]  #codeListΪ�û���ѡ����������û���Ĵ��루�б����ͣ���pencentageΪ��������û���ռ��ϵİٷֱȣ�ҲΪ�б����ͣ���codeListͨ���±��Ӧ����pencentage[i]��ʾ�������ΪcodeList[i]�Ļ���ռ��ϵİٷֱȣ�
     for code in codeList:
        fundDict[code]=getFund(code) #��ȡ����и����������Ϣ
        
     myFundGroup=Fund("myFundGroup")#����һ���յĻ�����϶��󣬼�Ȩƽ��������ݿɷŵ����������
     #������
     




#���Ժ���
def test():
     rm=Rm('000001.csv')#��ȡ�г�����
     #print rm.monthRate
     rf=Rf('Fund_RiskFree.csv','Treasury.xlsx')
     #print rf.date
     fundDict={} #�����ֵ䣬���ڲ�ѯ��������keyΪ������룬valueΪFund����    
     #codeList=getCode()   
     #for code in codeList:
     #    fundDict[code]=getFund(code)
         
     code='000003' #ǰ�˵���鿴ĳֻ�������Ϣ�󣬴����û���Ĵ��룬��ֵ�������ɻ�ȡ�û������Ϣ��������ַ�������
     fundDict[code]=getFund(code)
     
     temp=corrDate(fundDict[code].date,fundDict[code].dailyRate,rm.date,rm.dayRate,rf.date,rf.rfMonthly) 
        #ͳһ���ڣ�������ͳһ����������к͸��������ж�Ӧ�Ļ�������������/�г�����������/�޷�����������,�г������õ����������ʣ��޷��������õ�����������

     
     beta=countBeta(temp.fundRate,temp.rm)
     alpha=countAlpha(temp.fundRate,temp.rm,temp.rf,beta)
     
      
     print "Ŀ������껯������=",annualizedRate(fundDict[code].dailyRate)
     print "Ŀ������껯������=",annualizedVolatility(temp.fundRate)
     print "Ŀ��������ռ�ֵ=",countValue_at_risk(annualizedVolatility(temp.fundRate))
     print "Ŀ��������������е����б�׼��=",downsideStdDev(temp.fundRate,temp.rf)
     print "Ŀ��������ձ�=",countSharpeRatio(temp.fundRate,temp.rf)
     print "beta=",beta
     #for i in range(len(alpha)):
     #    print temp.date[i]+"��Ӧ��alphaֵΪ",alpha[i]   
     print "Ŀ���������ŵָ��=",TreynorRatio(temp.fundRate,temp.rf,beta)

     
     
     #T-M�ع�ģ�ͣ������ָ�����ݹ���.pdf)
     y=ListSub(temp.fundRate,temp.rf)
     x1=ListSub(temp.rm,temp.rf)
     x2=ListSubSqare(temp.rm,temp.rf)
     obj_dict={'y':y,'x1':x1,'x2':x2}
     data=pd.DataFrame(obj_dict)#ͨ���ֵ䴴��dataframe
     #data.to_csv("testfoo.csv")
     x=data[['x1','x2']]
     y=data['y']
     X_train,X_test, y_train, y_test = train_test_split(x, y, random_state=1)
     linreg = LinearRegression()  
     model=linreg.fit(X_train, y_train)  
     #print model    
     print '���ϵ����',linreg.intercept_
     print '��ʱϵ����',linreg.coef_[1]



     #����ĳ��ʱ���ڵĸ��ֻ���ָ��
     code='000003' #ǰ�˵���鿴ĳֻ�������Ϣ�󣬴����û���Ĵ��룬��ֵ�������ɻ�ȡ�û������Ϣ��������ַ�������
     fundDict[code]=getFund(code)    
     temp=corrDate(fundDict[code].date,fundDict[code].dailyRate,rm.date,rm.dayRate,rf.date,rf.rfMonthly) 
     temp.countByDate('2016-05-06','2017-08-01') #��Ҫ���� ĳ��ʱ���� �Ĳ����ʣ���Ҫ�ȵ����������������Ϊ��ʼ�ͽ������ڣ�����Ϊ�ַ�������ʽΪ'yyyy-mm-dd'(�������ŵ�5��6ǰ��0����ʡ�ԣ�
     #Ȼ����temp�����Լ�������Ĳ����ʾ������ʱ���ڵ��ˣ�ǰ����Ŀ�����/�г�������/�޷������������ʱ���ڵ����ݣ�
     #���㷽��ͬ��
     beta=countBeta(temp.fundRate,temp.rm)
     alpha=countAlpha(temp.fundRate,temp.rm,temp.rf,beta)
     print "Ŀ���������������2016-05-06��2017-08-01���껯������=",annualizedRate(fundDict[code].dailyRate)
     print "Ŀ���������������2016-05-06��2017-08-01���껯������=",annualizedVolatility(temp.fundRate)
     print "Ŀ���������������2016-05-06��2017-08-01�����ռ�ֵ=",countValue_at_risk(annualizedVolatility(temp.fundRate))
     print "Ŀ���������������2016-05-06��2017-08-01�����������е����б�׼��=",downsideStdDev(temp.fundRate,temp.rf)
     print "Ŀ���������������2016-05-06��2017-08-01�����ձ�=",countSharpeRatio(temp.fundRate,temp.rf)
     print "Ŀ���������������2016-05-06��2017-08-01��beta=",beta
     #for i in range(len(alpha)):
     #    print temp.date[i]+"��Ӧ��alphaֵΪ",alpha[i]
     print "Ŀ���������������2016-05-06��2017-08-01������ŵָ��=",TreynorRatio(temp.fundRate,temp.rf,beta)

     
     #T-M�ع�ģ�͵ļ���Ҳͬ��
     y=ListSub(temp.fundRate,temp.rf)
     x1=ListSub(temp.rm,temp.rf)
     x2=ListSubSqare(temp.rm,temp.rf)
     obj_dict={'y':y,'x1':x1,'x2':x2}
     data=pd.DataFrame(obj_dict)#ͨ���ֵ䴴��dataframe
     #data.to_csv("testfoo.csv")
     x=data[['x1','x2']]
     y=data['y']
     X_train,X_test, y_train, y_test = train_test_split(x, y, random_state=1)
     linreg = LinearRegression()  
     model=linreg.fit(X_train, y_train)  
     #print model    
     print '���ϵ����',linreg.intercept_
     print '��ʱϵ����',linreg.coef_[1]






def test2(code,startTime,endTime,option):   #����������Ĵ��룬��ѯ����ʼ�ͽ������ڣ�'yyyy-mm-dd'���ַ�������,optionΪ�ַ�����ѡ��鿴��һ������
     rm=Rm('000001.csv')#��ȡ�г�����
     #print rm.monthRate
     rf=Rf('Fund_RiskFree.csv','Treasury.xlsx')
     #print rf.date
     fundDict={}

     #����ĳ��ʱ���ڵĸ��ֻ���ָ��

     fundDict[code]=getFund(code)
     temp=corrDate(fundDict[code].date,fundDict[code].dailyRate,rm.date,rm.dayRate,rf.date,rf.rfMonthly)
     
     
     startTime = datetime.strptime(startTime,'%Y-%m-%d')
     endTime = datetime.strptime(endTime,'%Y-%m-%d')
     days=(endTime-startTime).days

     alpha=[]
     beta=[]
     AnnualizedRate=[]
     AnnualizedVolatility=[]
     CountValue_at_risk=[]
     DownsideStdDev=[]
     sharpeRatio=[]
     treynorRatio=[]
     stockSelectionCoefficient=[]
     timeSelectionCoefficient=[]

     if('alpha'==option):
          temp.countByDate(startTime.strftime('%Y-%m-%d'),endTime.strftime('%Y-%m-%d'))
          alpha=countAlpha(temp.fundRate,temp.rm,temp.rf,countBeta(temp.fundRate,temp.rm))
          for i in range(len(alpha)):
               print temp.date[i],alpha[i]
     
     i=0
     while(i<=days):      
          temp=corrDate(fundDict[code].date,fundDict[code].dailyRate,rm.date,rm.dayRate,rf.date,rf.rfMonthly)  
          curEndTime = startTime + timedelta(days=i)
          curStartTime=curEndTime - timedelta(days=365) #��ÿһ���һ��ǰ����������
          #print curStartTime
          temp.countByDate(curStartTime.strftime('%Y-%m-%d'),curEndTime.strftime('%Y-%m-%d'))
          
          if('beta'==option):              
               beta.append(countBeta(temp.fundRate,temp.rm))
               print curEndTime.strftime('%Y-%m-%d'),beta[-1]
               
          elif('annualizedRate'==option):
               AnnualizedRate.append(annualizedRate(temp.fundRate))
               print curEndTime.strftime('%Y-%m-%d'),AnnualizedRate[-1]
               
          elif('annualizedVolatility'==option):
               AnnualizedVolatility.append(annualizedVolatility(temp.fundRate))
               print curEndTime.strftime('%Y-%m-%d'),AnnualizedVolatility[-1]
               
          elif('countValue_at_risk'==option):
               CountValue_at_risk.append(countValue_at_risk(annualizedVolatility(temp.fundRate)))
               print curEndTime.strftime('%Y-%m-%d'),CountValue_at_risk[-1]
               
          elif('downsideStdDev'==option):
               DownsideStdDev.append(downsideStdDev(temp.fundRate,temp.rf))
               print curEndTime.strftime('%Y-%m-%d'),DownsideStdDev[-1]
               
          elif('sharpeRatio'==option):
               sharpeRatio.append(countSharpeRatio(temp.fundRate,temp.rf))
               print curEndTime.strftime('%Y-%m-%d'),sharpeRatio[-1]
               
          elif('treynorRatio'==option):
               tempBeta=countBeta(temp.fundRate,temp.rm)
               treynorRatio.append(TreynorRatio(temp.fundRate,temp.rf,tempBeta))
               print curEndTime.strftime('%Y-%m-%d'),treynorRatio[-1]
               
          elif('stockSelectionCoefficient'==option or 'timeSelectionCoefficient'==option):
               y=ListSub(temp.fundRate,temp.rf)
               x1=ListSub(temp.rm,temp.rf)
               x2=ListSubSqare(temp.rm,temp.rf)
               obj_dict={'y':y,'x1':x1,'x2':x2}
               data=pd.DataFrame(obj_dict)#ͨ���ֵ䴴��dataframe
               x=data[['x1','x2']]
               y=data['y']
               X_train,X_test, y_train, y_test = train_test_split(x, y, random_state=1)
               linreg = LinearRegression()  
               model=linreg.fit(X_train, y_train)
               
               stockSelectionCoefficient.append(linreg.intercept_)
               timeSelectionCoefficient.append(linreg.coef_[1])
               if('stockSelectionCoefficient'==option):
                    print curEndTime.strftime('%Y-%m-%d'),linreg.intercept_
               else:
                    print curEndTime.strftime('%Y-%m-%d'),linreg.coef_[1]
               
          i+=1


         
                    
optionList=['alpha','beta','annualizedRate','annualizedVolatility','countValue_at_risk','downsideStdDev','sharpeRatio','treynorRatio','stockSelectionCoefficient','timeSelectionCoefficient']
test2(str(sys.argv[1]),'2013-03-22','2017-09-08',optionList[int(sys.argv[2])])


   
