package reaper.util;

import org.junit.*;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;
import reaper.bean.CompanyMiniBean;
import reaper.bean.FundHistoryBean;
import reaper.bean.ManagerBean;
import reaper.model.*;
import reaper.repository.*;
import reaper.service.ManagerService;
import reaper.service.impl.ManagerServiceImpl;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

/**
 * Created by Feng on 2017/8/24.
 */

@RunWith(SpringJUnit4ClassRunner.class)
@SpringBootTest()
public class ManagerTest {
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

    //managers
    String[] managerIds={"m1","m2","m3"};
    String[] managerNames={"name1","name2","name3"};
    String[] genders={"w","w","m"};
    Date[] dates={new Date(), new Date(), new Date()};
    String[] introductions={"intro1", "intro2", "intro3"};
    Double[] totalScopes={1.1, 2.2, 3.3};
    Double[] bestReturnss={11.11, 22.22, 33.33};

    //managerCompany
    String[] managerCompanyIds={"c1", "c2", "c1"};

    //company
    String[] companyIds={"c1","c2"};
    String[] companyName={"cname1", "cname2"};

    //fund
    String[] fundCodes={"f1","f2","f3","f4"};
    String[] fundNames={"fname1","fname2","fname3","fname4"};
    String[] fundTypes={"t1","t2","t3","t4"};
    Date[] esDates={new Date(), new Date(), new Date(),new Date()};
    Double[] scopes={1.0, 2.0, 3.0, 4.0};

    //fundHistory
    String[] hManagerIds={"h1","h2","h2","h1","h2"};
    String[] hFundCodes={"f1","f1","f3","f2","f1"};
    String[] hFundNames={"fname1","fname1","fname3","fname2","fname1"};
    String[] hFundTypes={"t1","t1","t3","t2","t1"};
    Double[] hSizes={10.1, 20.2, 30.3, 50.5, 40.4};
    Date[] hStartDates={new Date(),new Date(),new Date(),new Date(),new Date()};
    Date[] hEndDates={new Date(),new Date(),new Date(),new Date(),new Date()};
    String[] hTimes={"11","22","33","44","55"};
    Double[] hPayBacks={1.11, 2.22, 3.33, 5.55, 4.44};

    SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");

    @Before
    public void prepare() throws Exception{
        System.out.println(fundHistoryRepository.getClass());
        for (int i = 0; i < managerIds.length; i++) {
            Manager manager=new Manager();
            manager.setManagerId(managerIds[i]);
            manager.setName(managerNames[i]);
            manager.setGender(genders[i]);
            manager.setAppointedDate(dates[i]);
            manager.setIntroduction(introductions[i]);
            manager.setTotalScope(totalScopes[i]);
            manager.setBestReturns(bestReturnss[i]);
            managerRepository.save(manager);

            ManagerCompany managerCompany=new ManagerCompany();
            managerCompany.setManagerId(managerIds[i]);
            managerCompany.setCompanyId(managerCompanyIds[i]);
            managerCompanyRespository.save(managerCompany);
        }

        for (int i = 0; i < companyIds.length; i++) {
            Company company=new Company();
            company.setCompanyId(companyIds[i]);
            company.setName(companyName[i]);
            companyRepository.save(company);
        }

        for (int i = 0; i < fundCodes.length; i++) {
            Fund fund=new Fund();
            fund.setFundCode(fundCodes[i]);
            fund.setName(fundNames[i]);
            fund.setType(fundTypes[i]);
            fund.setEstablishmentDate(esDates[i]);
            fund.setScope(scopes[i]);
            fundRepository.save(fund);
        }

//        for (int i = 0; i < hManagerIds.length; i++) {
//            FundHistory fundHistory=new FundHistory();
//            fundHistory.setManagerId(hManagerIds[i]);
//            fundHistory.setFundCode(hFundCodes[i]);
//            fundHistory.setFundName(hFundNames[i]);
//            fundHistory.setFundType(hFundTypes[i]);
//            fundHistory.setSize(hSizes[i]);
//            fundHistory.setStartDate(hStartDates[i]);
//            fundHistory.setEndDate(hEndDates[i]);
//            fundHistory.setTime(hTimes[i]);
//            fundHistory.setPayback(hPayBacks[i]);
//            fundHistoryRepository.save(fundHistory);
//        }

    }

    @Test
    public void findManagerByIdTest(){
//        ManagerService managerService=new ManagerServiceImpl();
//        ManagerBean managerBean =managerService.findManagerById("m1");
        List<Manager> managers=managerRepository.findByManagerId("m1");
        if(managers!=null){
            Manager manager=managers.get(0);
            List<ManagerCompany> managerCompanys=managerCompanyRespository.findByManagerId(manager.getManagerId());
            if(managerCompanys!=null){
                List<Company> companys=companyRepository.findByCompanyId(managerCompanys.get(0).getCompanyId());
                if(companys!=null){
                    ManagerBean managerBean=new ManagerBean(manager.getManagerId(), manager.getName(), manager.getGender(), sdf.format(manager.getAppointedDate()),
                            new CompanyMiniBean(companys.get(0).getCompanyId(), companys.get(0).getName()), manager.getTotalScope(), manager.getBestReturns(), manager.getIntroduction());
                    System.out.println();
                    System.out.println();
                    System.out.println();

                }
            }
        }
        System.out.println();
        System.out.println();
        System.out.println();

    }

    @Test
    public void findFundHistoryByIdTest(){
//        List<FundHistoryBean> res=new ArrayList<>();
//        List<FundHistory> fundHistories=fundHistoryRepository.findAllByManagerId("m1");
//        if(fundHistories!=null){
//            for(FundHistory fundHistory:fundHistories){
//                List<String> type=null;
//                type.add(fundHistory.getFundType());
//                res.add(new FundHistoryBean(fundHistory.getFundCode(),fundHistory.getFundName(),type,
//                        fundRepository.findByFundCode(fundHistory.getFundCode()).get(0).getScope(), sdf.format(fundHistory.getStartDate()), sdf.format(fundHistory.getEndDate()),
//                        (int)((fundHistory.getEndDate().getTime()-fundHistory.getStartDate().getTime())/(1000*3600*24)),
//                        fundHistory.getPayback()));
//            }
//        }
        System.out.println();
        System.out.println();
    }

    @After
    public void tearDown(){
        managerRepository.deleteAll();
        managerCompanyRespository.deleteAll();
        companyRepository.deleteAll();
//        fundHistoryRepository.deleteAll();
        fundRepository.deleteAll();
    }
}
