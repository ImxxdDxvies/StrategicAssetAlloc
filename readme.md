# Strategic Asset Allocation
This toolset generates the strategic asset allocation (SAA) which maximises the frequency of outperformance relative to a return hurdle. 

The only inputs are an asset return history, specification of brokerage fees when rebalancing to SAA, the return hurdle, how often to rebalance to SAA and the number of bootstrap iterations.

Across all bootstrap iterations, the SAA and frequency of outperformance are stored. The optimal SAA is the average of all asset allocations corresponding to greater than or equal to the median frequency of outperformance.

For sample usage, see Main.py using the simulated asset returns in Returns.txt