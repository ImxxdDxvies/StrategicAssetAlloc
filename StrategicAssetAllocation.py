# Rebalance tool
# Imaad Davies

from numpy import ndarray, array, concatenate, zeros, ones, random
from pandas import DataFrame, Timestamp, ExcelWriter
from scipy.optimize import minimize

def RebalanceTool(FTotalIn : float, WIn : ndarray, WTarget : ndarray, Fee : float, 
                  Return : ndarray) -> ndarray:
    """Rebalance portfolio to target weights
    
    Args:
        FTotalIn: float
        :Portfolio starting value
        WIn: ndarray
        :Starting weights
        WTarget: ndarray
        :Target weights
        Fee: float
        :Brokerage fee
        Return: float
        :Asset return
    Returns:
        FOut: ndarray
        :Instrument end values"""
    WeightChange = (WTarget - WIn)
    TradeValue = (1 - Fee) * WeightChange
    Brokerage = Fee * abs(WeightChange)
    FOut = FTotalIn * (WIn + TradeValue - Brokerage) * (1 + Return)
    return FOut

def CreateResultsDataFrame(Returns : DataFrame) -> DataFrame:
    """Creates a DataFrame to store results
    
    Args:
        Returns: DataFrame
        :DataFrame of asset returns
    Returns:
        Results: DataFrame
        :DataFrame to store results"""
    Columns = list(Returns.columns)
    Assets = list(Returns.columns[1:])
    Columns += ['Total', 'Return', 'Benchmark']
    NoAssets = len(Assets)
    Dtypes = ['datetime64[ns]'] + ['float64'] * (NoAssets + 3) 
    Results = DataFrame({Column : [] for Column in Columns})
    Results = Results.astype(dtype = {Column : Dtype for Column, Dtype in zip(Columns, Dtypes)})
    return Results

def PortfolioRebalance(WTarget : ndarray, Returns : DataFrame, Results : DataFrame, Fee : float, 
                       RebalancePeriod : int, ReturnHurdle : float) -> DataFrame:
    """Simulation of portfolio rebalancing through time
    
    Args:
        WTarget: ndarray
        :Target weights
        Returns: DataFrame
        :DataFrame of asset returns
        Results: DataFrame
        :DataFrame to store results
        Fee: float
        :Brokerage fee
        RebalancePeriod: int
        :Number of days before rebalancing back to target weights
        ReturnHurdle: float
        :Return hurdle
    Returns:
        Results: DataFrame
        :DataFrame to store results"""
    FTotalIn = 100
    FIn = WTarget * FTotalIn
    WIn = FIn / FTotalIn
    Assets = list(Returns.columns[1:])
    Columns = list(Results.columns)
    for Idx in Returns.index:
        Return = Returns.loc[Idx, Assets].values
        if (Idx + 1) % RebalancePeriod == 0:
            FOut = RebalanceTool(FTotalIn, WIn, WTarget, Fee, Return)
        else:
            FOut = RebalanceTool(FTotalIn, WIn, WIn, Fee, Return)
        FTotalOut = sum(FOut)
        PortfolioReturn = FTotalOut / FTotalIn - 1
        FIn = FOut
        FTotalIn = FTotalOut
        WIn = FIn / FTotalIn
        Date = Timestamp(Returns.loc[Idx, 'Date'])
        Values = concatenate(([Date], FIn, [FTotalOut, PortfolioReturn, ReturnHurdle]))
        Results.loc[Idx, Columns] = Values
    return Results

def Objective(WTarget : ndarray, Returns : DataFrame, Results : DataFrame, Fee : float, 
              RebalancePeriod : int, ReturnHurdle : float) -> float:
    """Calculate target weights
    
        Args:
        WTarget: ndarray
        :Target weights
        Returns: DataFrame
        :DataFrame of asset returns
        Results: DataFrame
        :DataFrame to store results
        Fee: float
        :Brokerage fee
        RebalancePeriod: int
        :Number of days before rebalancing back to target weights
        ReturnHurdle: float
        :Return hurdle
    Returns:
        Freq: float
        :Frequency of outperformance"""
    Results = PortfolioRebalance(WTarget, Returns, Results, Fee, RebalancePeriod, ReturnHurdle)
    NoDataPts = len(Results.index)
    Freq = (Results['Return'] > Results['Benchmark']).sum() / NoDataPts
    return Freq * -1

def Constraints(WTarget : ndarray, LBound : ndarray, UBound : ndarray) -> ndarray:
    """Optimisation problem constraints
    
    Args:
        WTarget: ndarray
        :Target weights
        LBound: ndarray
        :Lower bound
        UBound: ndarray
        :Upper bound
    Returns:
        AllConstraints: ndarray
        :Optimisation problem constraints"""
    # Equality constraints
    Constraint1 = sum(WTarget) - 1
    Constraint2 = - Constraint1
    EqualityConstraints = array([Constraint1, Constraint2])
    # Inequality constraints
    Constraint3 = UBound - WTarget
    Constraint4 = WTarget - LBound
    InequalityConstraints = concatenate((Constraint3, Constraint4))
    # Combine equality and inequality constraints
    AllConstraints = concatenate((EqualityConstraints, InequalityConstraints))
    return AllConstraints

def CalcWeights(Returns : DataFrame, Fee : float, RebalancePeriod : int, ReturnHurdle : float) -> ndarray:
    """Calculates the weight of capital to allocate to each asset
    
    Args:
        Returns: DataFrame
        :DataFrame of asset returns
        Fee: float
        RebalancePeriod: int
        ReturnHurdle: float
        :Return hurdle
    Returns:
        Output: ndarray
        :Array containing asset weights and objective function value"""
    Assets = list(Returns.columns[1:])
    Results = CreateResultsDataFrame(Returns)
    NoAssets = len(Assets)
    LBound = zeros(NoAssets)
    UBound = ones(NoAssets)
    ConstraintInput = {'type': 'ineq', 'fun': Constraints, 'args': (LBound, UBound, )}
    Args = (Returns, Results, Fee, RebalancePeriod, ReturnHurdle, )
    WTargetGuess = 1 / NoAssets * ones(NoAssets)
    Res = minimize(Objective, WTargetGuess, args = Args, method = 'COBYLA', constraints = ConstraintInput)
    Output = concatenate((Res.x, [Res.fun * -100]))
    return Output

def Bootstrap(Returns : DataFrame, Fee : float, RebalancePeriod : int, ReturnHurdle : float, NoIter : int) -> DataFrame:
    """Resample return history and generate more robust allocations
    
    Args:
        Returns: DataFrame
        :DataFrame of asset returns
        Fee: float
        RebalancePeriod: int
        ReturnHurdle: float
        :Return hurdle
        NoIter: int
        :Number of iterations to do for resampling
    Returns:
        Allocation: DataFrame
        :Asset allocation"""
    NoDataPts = len(Returns.index)
    Assets = list(Returns.columns[1:])
    IterationRes = DataFrame({Column : [] for Column in (Assets + ['Frequency'])})
    for Idx in range(0, NoIter):
        print(f'Iteration number: {Idx + 1}')
        Rnd = random.default_rng().integers(low = 0, high = NoDataPts - 1, size = NoDataPts, endpoint = True)
        RndReturns = Returns.copy().loc[Rnd, :]
        RndReturns['Date'] = Returns['Date']
        RndReturns.reset_index(drop = True, inplace = True)
        Output = CalcWeights(RndReturns, Fee, RebalancePeriod, ReturnHurdle)
        IterationRes.loc[Idx, :] = Output
    Q50 = IterationRes['Frequency'].quantile(q = 0.5)
    WTarget = IterationRes[Assets][IterationRes['Frequency'] >= Q50].mean().values
    Allocation = DataFrame({'Asset': Assets, 'Weights (%)' : WTarget * 100}).set_index('Asset')
    return Allocation

def WriteToExcel(Df : DataFrame, FileName : str) -> None:
    """Write DataFrame contents to Excel
    
    Args:
        Df: DataFrame
        :DataFrame to write to Excel
    Returns:
        None"""
    with ExcelWriter(FileName) as Writer:
        Df.to_excel(Writer, sheet_name = 'Allocation')