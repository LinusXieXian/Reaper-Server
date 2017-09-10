package reaper.service.impl;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import reaper.bean.CompanyMiniBean;
import reaper.bean.FundHistoryBean;
import reaper.bean.ManagerAbilityBean;
import reaper.bean.ManagerBean;
import reaper.bean.*;
import reaper.model.*;
import reaper.repository.*;
import reaper.service.ManagerService;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

/**
 * Created by Feng on 2017/8/23.
 */

@Service
public class ManagerServiceImpl implements ManagerService {
    @Autowired
    ManagerRepository managerRepository;

    @Autowired
    ManagerCompanyRespository managerCompanyRespository;

    @Autowired
    CompanyRepository companyRepository;

    @Autowired
    FundHistoryRepository fundHistoryRepository;

    @Autowired
    FundRepository fundRepository;

    @Autowired
    ManagerRemarkRepository managerRemarkRepository;

    @Autowired
    FundNetValueRepository fundNetValueRepository;

    SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");

    /**
     * 根据经理id获得经理信息
     * @param id 经理id
     * @return 经理信息
     */
    @Override
    public ManagerBean findManagerById(String id) {
        Manager manager=managerRepository.findByManagerId(id);
        if(manager!=null){
            ManagerCompany managerCompany=managerCompanyRespository.findByManagerId(manager.getManagerId());
            if(managerCompany!=null){
                Company company=companyRepository.findByCompanyId(managerCompany.getCompanyId());
                if(company!=null){
                    return  new ManagerBean(manager.getManagerId(), manager.getName(), sdf.format(manager.getAppointedDate()),
                            String.valueOf((int)((new Date().getTime()-manager.getAppointedDate().getTime())/(1000*3600*24))),
                            new CompanyMiniBean(company.getCompanyId(), company.getName()), manager.getTotalScope(), manager.getBestReturns(), manager.getIntroduction());
                }
            }
        }
        return null;
    }

    /**
     * 根据经理id获得经理历史基金信息
     * @param id 经理id
     * @return 经理历史基金信息
     */
    @Override
    public List<FundHistoryBean> findFundHistoryById(String id) {
        List<FundHistoryBean> res=new ArrayList<>();
        List<FundHistory> fundHistories=fundHistoryRepository.findAllByManagerId(id);
        if(fundHistories!=null){
            for(FundHistory fundHistory:fundHistories){
                Fund fund=fundRepository.findByCode(fundHistory.getFundCode());
                if(fund!=null){
                    List<String> type=new ArrayList<>();
                    type.add(fund.getType1());
                    type.add(fund.getType2());
                    //若fundHistory没有endDate, 则默认endDate是now
                    res.add(new FundHistoryBean(fundHistory.getFundCode(),fund.getName(),type,
                            fund.getScope(), sdf.format(fundHistory.getStartDate()),
                            sdf.format((fundHistory.getEndDate()==null)?new Date():fundHistory.getEndDate()),
                            (int)((((fundHistory.getEndDate()==null)?new Date():fundHistory.getEndDate()).getTime()-fundHistory.getStartDate().getTime())/(1000*3600*24)),
                            fundHistory.getPayback()));
                }
            }
        }
        return res;
    }

    /**
     * 根据经理id获得经理任期中的基金收益
     * @param managerId 经理id
     * @return 经理任期中的基金收益
     */
    @Override
    public List<ReturnBean> findFundReturnsByManagerId(String managerId) {
        List<ReturnBean> res=new ArrayList<>();
        List<FundHistory> fundHistories=fundHistoryRepository.findAllByManagerId(managerId);
        if(fundHistories!=null){
            for(FundHistory fundHistory : fundHistories){
                res.add(new ReturnBean(fundHistory.getFundCode(), fundHistory.getFundName(), fundHistory.getPayback()));
            }
        }
        return res;
    }

    /**
     * 根据经理id获得经理现任基金排名
     * @param managerId 经理id
     * @return 经理现任基金排名
     */
    //TODO
    @Override
    public List<RankBean> findFundRankByManagerId(String managerId) {
        List<RankBean> res=new ArrayList<>();
        List<FundHistory> fundHistories = fundHistoryRepository.findAllByManagerId(managerId);
        for(FundHistory fundHistory : fundHistories){

        }
        return null;
    }

    /**
     * 根据经理id获得经理现任基金收益率走势
     * @param managerId 经理id
     * @return 经理现任基金收益率走势
     */
    @Override
    public List<RateTrendBean> findFundRateTrendByManagerId(String managerId) {
        List<RateTrendBean> res=new ArrayList<>();
        List<FundHistory> fundHistories=fundHistoryRepository.findAllByManagerId(managerId);
        if(fundHistories!=null){
            for(FundHistory fundHistory : fundHistories){
                List<RateTrendDataBean> data=new ArrayList<>();
                List<FundNetValue> fundNetValues=fundNetValueRepository.findAllByCodeOrderByDateAsc(fundHistory.getFundCode());
                if(fundNetValues!=null){
                    for (FundNetValue fundNetValue : fundNetValues){
                        data.add(new RateTrendDataBean(sdf.format(fundNetValue.getDate()), fundNetValue.getUnitNetValue()));
                    }
                }
                res.add(new RateTrendBean(fundHistory.getFundCode(),fundHistory.getFundName(),data));
            }
        }
        return res;
    }

    /**
     * 根据经理id获得经理现任基金排名走势
     * @param managerId 经理id
     * @return 经理现任基金排名走势
     */
    //TODO
    @Override
    public List<RankTrendBean> findFundRankTrendByManagerId(String managerId) {
        return null;
    }

    /**
     * 根据经理id获得经理历任基金表现
     * @param managerId 经理id
     * @return 经理历任基金表现
     */
    @Override
    public FundPerformanceBean findFundPerformanceByManagerId(String managerId) {
        return null;
    }

    /**
     * 根据经理id获得经理综合表现
     * @param managerId 经理id
     * @return 经理综合表现
     * @apiNote 第一个为当前经理，剩下的为其他经理
     */
    @Override
    public ManagerPerformanceBean findManagerPerformanceByManagerId(String managerId) {
        return null;
    }

    /**
     * 根据经理id获得经理综合能力
     * @param managerId 经理id
     * @return 经理综合能力
     */
    @Override
    public ManagerAbilityBean findManagerAbilityByManagerId(String managerId) {
        Manager manager=managerRepository.findByManagerId(managerId);
        if(manager!=null){
            ManagerRemark managerRemark=managerRemarkRepository.findByManagerId(Integer.parseInt(managerId));
            if(managerRemark!=null){
                return new ManagerAbilityBean(managerRemark);
            }

        }
        return null;
    }

    /**
     * 根据经理id获得经理社会关系网络图
     * @param managerId 经理id
     * @return 经理社会关系网络图
     */
    @Override
    public NetworkBean findSocialNetworkByManagerId(String managerId) {
        return null;
    }

}
