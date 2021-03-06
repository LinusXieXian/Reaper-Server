package reaper.bean;

import java.util.List;

/**
 * @author keenan on 09/09/2017
 */
public class CombinationMiniBean {
    /**
     * 组合id
     */
    public Integer id;

    /**
     * 组合名字
     */
    public String name;

    /**
     * 最新收益率
     */
    public Double newProfit;

    /**
     * 年化收益
     */
    public Double annualProfit;

    /**
     * 波动率
     */
    public Double volatility;

    /**
     * 基金组成
     */
    public List<FundRatioNameBean> combination;

    /**
     * 是否有风险产生
     */
    public Boolean hasRisk = false;

    public CombinationMiniBean(Integer id, String name, Double newProfit, Double annualProfit, Double volatility, List<FundRatioNameBean> combination, Boolean hasRisk) {
        this.id = id;
        this.name = name;
        this.newProfit = newProfit;
        this.annualProfit = annualProfit;
        this.volatility = volatility;
        this.combination = combination;
        this.hasRisk = hasRisk;
    }

    public CombinationMiniBean() {
    }
}
