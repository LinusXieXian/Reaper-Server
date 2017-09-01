package reaper.service.impl;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import reaper.bean.*;
import reaper.model.*;
import reaper.repository.*;
import reaper.service.FundService;
import reaper.util.FundModelToBean;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.List;

/**
 * Created by Sorumi on 17/8/21.
 */

@Service
public class FundServiceImpl implements FundService {
    @Autowired
    FundRepository fundRepository;

    @Autowired
    FundShortMessageRepository fundShortMessageRepository;

    @Autowired
    FundNetValueRepository fundNetValueRepository;

    @Autowired
    FundHistoryRepository fundHistoryRepository;

    @Autowired
    ManagerRepository managerRepository;

    @Autowired
    CompanyRepository companyRepository;

    @Autowired
    FundManagerRepository fundManagerRepository;

    @Autowired
    FundCompanyRepository fundCompanyRepository;

    @Autowired
    AssetAllocationRepository assetAllocationRepository;

    SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");

    @Override
    public reaper.util.Page<FundMiniBean> findFundByKeyword(String keyword, String order, int size, int page) {
        reaper.util.Page<FundMiniBean> res = new reaper.util.Page<>();
        res.setOrder(order);
        res.setSize(size);
        res.setPage(page);
        //默认以升序进行排列
        org.springframework.data.domain.Page<Fund> fundPage = fundRepository.findAllByNameLike("%" + keyword + "%", new PageRequest(page - 1, size, new Sort(Sort.Direction.ASC, order==null?"code":order)));
        List<FundMiniBean> miniBeans = new ArrayList<>();
        for (Fund fund : fundPage.getContent()) {
            //根据基金代码找到经理代码
            List<FundManager> fundManagers = fundManagerRepository.findByFundCode(fund.getCode());
            //根据经理代码找到经理名
            List<MiniBean> managerList = new ArrayList<>();
            for(FundManager fundManager:fundManagers){
                managerList.add(new MiniBean(fundManager.getManagerId(),managerRepository.findByManagerId(fundManager.getManagerId()).getName()));
            }
            miniBeans.add(new FundMiniBean(fund.getCode(), fund.getName(), fund.getAnnualProfit(), fund.getVolatility(), managerList));
        }
        res.setResult(miniBeans);
        res.setTotalCount((int) fundPage.getTotalElements());
        return res;
    }

    @Override
    public FundBean findFundByCode(String code) {
        FundModelToBean fundModelToBean = new FundModelToBean();
        Fund fund = fundRepository.findByCode(code);
        FundNetValue fundNetValue = fundNetValueRepository.findFirstByCodeOrderByDateDesc(code);
        RateBean rateBean = getFundRate(code);

        List<MiniBean> managers = new ArrayList<>();
        for(FundManager fundManager:fundManagerRepository.findByFundCode(code)){
            managers.add(new MiniBean(fundManager.getManagerId(), managerRepository.findByManagerId(fundManager.getManagerId()).getName()));
        }
        String id = fundCompanyRepository.findByFundId(code).getcompanyId();
        MiniBean company = new MiniBean(id, companyRepository.findByCompanyId(id).getName());
        return fundModelToBean.modelToBean(fund, fundNetValue, rateBean, managers, company);
    }

    @Override
    public List<NetValueDateBean> findUnitNetValueTrendByCode(String code) {
        List<NetValueDateBean> res = new ArrayList<>();

        for (FundNetValue fundNetValue : fundNetValueRepository.findAllByCodeOrderByDateAsc(code)) {
            res.add(new NetValueDateBean(sdf.format(fundNetValue.getDate()), fundNetValue.getUnitNetValue()));
        }
        return res;
    }

    @Override
    public List<NetValueDateBean> findCumulativeNetValueTrendByCode(String code) {
        List<NetValueDateBean> res = new ArrayList<>();

        for (FundNetValue fundNetValue : fundNetValueRepository.findAllByCodeOrderByDateAsc(code)) {
            res.add(new NetValueDateBean(sdf.format(fundNetValue.getDate()), fundNetValue.getCumulativeNetValue()));
        }
        return res;
    }

    @Override
    public List<NetValueDateBean> findCumulativeRateTrendByCode(String code, String month) {
        List<NetValueDateBean> res = new ArrayList<>();

        //累加结果
        double cumulativeValue = 0;

        List<FundNetValue> fundNetValues;

        if (month.equals("all")) {
            fundNetValues = fundNetValueRepository.findAllByCodeOrderByDateAsc(code);
        } else {
            //获得n月前的日期
            Calendar calendar = Calendar.getInstance();
            calendar.setTime(new Date());
            calendar.add(Calendar.MONTH, -Integer.valueOf(month));
            fundNetValues = fundNetValueRepository.findAllByCodeAndDateAfterOrderByDateAsc(code, calendar.getTime());
        }

        for (FundNetValue fundNetValue : fundNetValues) {
            cumulativeValue += fundNetValue.getDailyRate();
            res.add(new NetValueDateBean(sdf.format(fundNetValue.getDate()), cumulativeValue));
        }

        return res;
    }

    //TODO 没数据，还未测试
    @Override
    public List<HistoryManagerBean> findHistoryManagersByCode(String code) {
        List<HistoryManagerBean> res = new ArrayList<>();

        for (FundHistory fundHistory : fundHistoryRepository.findAllByFundCodeOrderByStartDateAsc(code)) {
            //计算相差的天数
            int difDays = (int) ((fundHistory.getEndDate().getTime() - fundHistory.getStartDate().getTime()) / (1000 * 3600 * 24));
            res.add(new HistoryManagerBean(fundHistory.getManagerId(), managerRepository.findByManagerId(fundHistory.getManagerId()).getName(), sdf.format(fundHistory.getStartDate()), sdf.format(fundHistory.getEndDate()), difDays, fundHistory.getPayback()));
        }
        return res;
    }

    @Override
    public CurrentAssetBean findCurrentAssetByCode(String code) {
        AssetAllocation assetAllocation = assetAllocationRepository.findByCode(code);
        return new CurrentAssetBean(assetAllocation.bond,assetAllocation.stock,assetAllocation.bank);
    }

    /**
     * 计算基金近1、3、6、12、36月和成立以来的累计收益率
     *
     * @param code 基金代码
     * @return 各个阶段累计收益率
     */
    private RateBean getFundRate(String code) {
        //记录5个时间段
        Date dates[] = new Date[5];
        Calendar calendar = Calendar.getInstance();
        calendar.setTime(new Date());
        //1
        calendar.add(Calendar.MONTH, -1);
        dates[0] = calendar.getTime();
        //3
        calendar.add(Calendar.MONTH, -2);
        dates[1] = calendar.getTime();
        //6
        calendar.add(Calendar.MONTH, -3);
        dates[2] = calendar.getTime();
        //12
        calendar.add(Calendar.MONTH, -6);
        dates[3] = calendar.getTime();
        //36
        calendar.add(Calendar.MONTH, -24);
        dates[4] = calendar.getTime();

        //从最后一天开始往前加，减少循环次数
        List<FundNetValue> netValues = fundNetValueRepository.findAllByCodeOrderByDateDesc(code);
        //记录已经到达的时间段
        int countDate = 0;
        //累计值
        double rate = 0;
        //各个阶段结果保存
        double rates[] = new double[6];

        for (FundNetValue netValue : netValues) {
            if (countDate != 5 && netValue.getDate().before(dates[countDate])) {
                rates[countDate] = rate;
                countDate++;
            }
            rate += netValue.getDailyRate();
        }
        //成立以来的收益率
        rates[5] = rate;

        return new RateBean(rates);
    }

}
