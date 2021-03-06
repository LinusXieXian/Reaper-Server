package reaper.bean;

import java.util.List;

/**
 * 资产配置-基金+组合
 *
 * @author keenan on 09/09/2017
 */
public class FundCombinationBean {
    /**
     * 1-10
     */
    public Integer profitRiskTarget;

    /**
     * 1=资产间分散, 2=因子间分散
     */
    public Integer path;

    /**
     * 如果选择资产间分散 则 weight 有效
     */
    public AssetWeightBean weight;

    /**
     * 如果选择因子间分散，则factor有效
     */
    public List<String> factor;

    /**
     * 组合的名称
     */
    public String name;

    /**
     * 选择的基金，需要分类
     */
    public List<FundCategoryBean> funds;

    /**
     * 如果选择barra，则barraFactor有效
     */
    public List<BarraFactorBean> barraFactor;

    /**
     * 分散化方法 1 2 3
     */
    public Integer method;

    /**
     * 如果分散化方法为均值方差 6，则 profitRate 有效
     */
    public Double profitRate;

    public FundCombinationBean() {
    }

    public FundCombinationBean(Integer profitRiskTarget, Integer path, AssetWeightBean weight, List<String> factor,
                               String name, List<FundCategoryBean> funds, Integer method, Double profitRate) {
        this.profitRiskTarget = profitRiskTarget;
        this.path = path;
        this.weight = weight;
        this.factor = factor;
        this.name = name;
        this.funds = funds;
        this.method = method;
        this.profitRate = profitRate;
    }

    @Override
    public String toString() {
        return "FundCombinationBean{" +
                "profitRiskTarget=" + profitRiskTarget +
                ", path=" + path +
                ", weight=" + weight +
                ", factor=" + factor +
                ", name='" + name + '\'' +
                ", funds=" + funds +
                ", method=" + method +
                ", profitRate=" + profitRate +
                '}';
    }
}
