# Main file
# Imaad Davies

from StrategicAssetAllocation import Bootstrap, WriteToExcel
from pandas import read_csv, Timestamp

def Main() -> None:
    """Main function
    
    Args:
        None
    Returns:
        None"""
    Fee = 30 / 1e4 # Brokerage fee
    RebalancePeriod = 30 # Number of days before rebalancing
    AnnualRet = 10 # Return target % to beat
    ReturnHurdle = (1 + AnnualRet / 100) ** (1 / 365) - 1
    NoIter = 10 # Number of bootstrap iterations
    Returns = read_csv('Returns.txt') # Read in return history
    Returns['Date'] = Returns['Date'].astype('datetime64[ns]')
    # Calculate asset allocation
    Allocation = Bootstrap(Returns, Fee, RebalancePeriod, ReturnHurdle, NoIter)
    # Write results to Excel
    Today = str(Timestamp('today'))[0:10].replace('-', '')
    FileName = f'Strategic Allocation {Today}.xlsx'
    WriteToExcel(Allocation, FileName)

if __name__ == '__main__':
    Main()