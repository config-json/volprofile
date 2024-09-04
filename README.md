# Custom Volume Profile Indicator

This is a simple script that generates an accurate volume profile based on Binance API

## Extracting Custom Data

Before starting to use the indicator, download your desired amount of data. The command below obtains the aggregate trades for July 2023

```python
python3 binance-data/download-aggTrade.py -s BTCUSDT -startDate 2023-07-01 -endDate 2023-07-31  -t spot -skip-monthly 1
```

## Getting Started

1. Go to `vol-profile/singleday.ipynb`
2. Replace the values from where the dataframe is created with your own. By default the path will be:

```python
df = pd.read_csvZipFile("../data/spot/daily/aggTrades/BTCUSDT/BTCUSDT-aggTrades-YYYY-MM-DD.zip".open("BTCUSDT-aggTrades-YYYY-MM-DD.csv"), names=["aggregated_id","price","quantity","first_trade_id","last_trade_id","last_timestamp","is_buyer_maker","is_best_match"])
```

3. Run will provide a volume profile for the day selected in step 2

## How the volume profile is calculated

Data for every trade is pulled from the Binance API. After that, the high and the low of the range are obtained in order to divide it in a certain amount of bins (set to 50 by default).

Next, the bin with the most volume is obtained, also called Point of Control (PoC). Lastly, to calculate the Value Area (or 1 STD parting from the PoC), values for the bins above and below the PoC are considered until the total volume reaches 68%.

## Multiple days volume profile

`vol-profile/multipledays.ipynb` provides a script that plots volume profile over an amount of consecutive days. Functionality for now is limited and all adjustments have to be made similarly to `singleday.ibynb` (last section of code). Relevant settings:

1. Date list: `date_list = ['','2023-07-01','2023-07-02','2023-07-03','2023-07-04','2023-07-05']` and `for i in range(amount_of_strings_in_date_list):`

2. Number of bins: `num_bins = 50`

3. Bin size: `bin_size = 12`

All bins are standarised and made equal.
