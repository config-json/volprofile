# py download-aggTrade.py -s BTCUSDT  -t spot -skip-daily 1 -y 2023 -m 7

import pandas as pd
import numpy as np
from zipfile import ZipFile
import math
import json
from itertools import chain
import sys
import os

def create_volume_profile_ticks_standard(data, num_bins=0, bin_size=0):
    # Calculate the price range for binning
    min_price = data['price'].min()
    max_price = data['price'].max()
    price_range = max_price - min_price

    # calculate bin size if not provided
    if num_bins != 0:
        bin_size = int(price_range/num_bins)

    # Calculate the number of bins
    if bin_size != 0:
        num_bins = int(price_range/bin_size)

    # calculate the bin size and number of bins dinamically if not provided
    if num_bins == 0 and bin_size == 0:
        # use two times the natural log of the price range to calculate the bin size
        bin_size = 2*round(math.log(price_range), 0)
        num_bins = int(price_range/bin_size)

    # Create the bins
    bins = [min_price + i * bin_size for i in range(num_bins + 1)]

    # Bin the data and calculate total volume for each bin
    volume_profile = []
    for i in range(num_bins):
        bin_data = data[(data['price'] >= bins[i]) &
                        (data['price'] < bins[i+1])]
        total_volume = bin_data['quantity'].sum()
        volume_profile.append(total_volume)

    return bins[:-1], volume_profile


def calculate_value_area_with_highest_dual_bins(bins, volume_profile, percentage):
    # Find the index of the bin with the greatest volume
    highest_volume_index = volume_profile.index(max(volume_profile))

    # Initialize variables to track the value area
    value_area_low = min(bins)
    value_area_high = max(bins)
    value_area_volume = volume_profile[highest_volume_index]
    high_index = 0
    low_index = 0

    # Calculate the total volume
    total_volume = sum(volume_profile)

    # Calculate the target volume for the Value Area (68% of the total volume)
    target_volume = total_volume * percentage / 100

    # Loop until the value area reaches 68% of the total volume or no more bins to check
    while value_area_volume <= target_volume:
        # Calculate the total volume of the dual bins above and below
        if highest_volume_index + 2 + high_index < len(bins):
            dual_bins_volume_above = volume_profile[highest_volume_index + 1 +
                                                    high_index] + volume_profile[highest_volume_index + 2 + high_index]
            dual_bins_volume_below = volume_profile[highest_volume_index - 1 -
                                                    low_index] + volume_profile[highest_volume_index - 2 - low_index]

            # Compare the dual bins volume and update the value area if needed
            if dual_bins_volume_above >= dual_bins_volume_below or highest_volume_index - 2 - low_index < 0:
                value_area_volume += dual_bins_volume_above
                value_area_high = bins[highest_volume_index + 2 + high_index]
                high_index += 2
            elif dual_bins_volume_above < dual_bins_volume_below or highest_volume_index + 2 + high_index >= len(bins):
                value_area_volume += dual_bins_volume_below
                value_area_low = bins[highest_volume_index - 2 - low_index]
                low_index += 2
        else:
            dual_bins_volume_below = volume_profile[highest_volume_index - 1 -
                                                    low_index] + volume_profile[highest_volume_index - 2 - low_index]
            value_area_volume += dual_bins_volume_below
            value_area_low = bins[highest_volume_index - 2 - low_index]
            low_index += 2

    return value_area_low, value_area_high


def create_point_of_control_from_dataframe(data):
    # Calculate the price range for binning
    min_price = data['price'].min()
    max_price = data['price'].max()
    price_range = max_price - min_price

    bin_size = 2*round(math.log(price_range), 0)
    num_bins = int(price_range/bin_size)

    # Create the bins
    bins = [min_price + i * bin_size for i in range(num_bins + 1)]

    # Bin the data and calculate total volume for each bin
    volume_profile = []
    for i in range(num_bins):
        bin_data = data[(data['price'] >= bins[i]) &
                        (data['price'] < bins[i+1])]
        total_volume = bin_data['quantity'].sum()
        volume_profile.append(total_volume)

    poc_index = np.argmax(volume_profile)
    point_of_control = bins[poc_index]

    return point_of_control


if __name__ == "__main__":
    
    in_arr = sys.argv
    if '-y' not in in_arr  or '-m' not in in_arr:
        print (__doc__)
        raise NameError('error: -y and -m are required. -y for year and -m for month')
    else:
        year = in_arr[in_arr.index('-y') + 1]
        month = in_arr[in_arr.index('-m') + 1].zfill(2)
    
    os.makedirs(os.path.dirname("../data/poclist/"),exist_ok=True)
    
    if not os.path.isfile(f'../data/poclist/poclist-{year}-{month}.json'):
        
        
        df = pd.read_csv(ZipFile(f"../data/spot/monthly/aggTrades/BTCUSDT/BTCUSDT-aggTrades-{year}-{month}.zip").open(f"BTCUSDT-aggTrades-{year}-{month}.csv"),
                         names=["aggregated_id", "price", "quantity", "first_trade_id", "last_trade_id", "last_timestamp", "is_buyer_maker", "is_best_match"])
        # convert to datetime object from int
        df["datetime_object"] = pd.to_datetime(df['last_timestamp'], unit='ms')
        # convert to date object
        df["date"] = df["datetime_object"].dt.date
        # take the unique dates
        dates = df["date"].unique()
        # create a list of dictionaries with date and poc
        poc_list = []
        for date in dates:

            print(date)

            bins, volume_profile = create_volume_profile_ticks_standard(df[df["date"] == date])

            # Calculate the Value Area (using the function with dual bins)
            percentage = 68

            value_area_low, value_area_high = calculate_value_area_with_highest_dual_bins(
                bins, volume_profile, percentage)

            poc_list.append({'date': date.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                            'npoc': create_point_of_control_from_dataframe(df[df["date"] == date]), 'vah': value_area_high, 'val': value_area_low})
            
        
        
        # save the list of dictionaries to a json file
        with open(f"../data/poclist/poclist-{year}-{month}.json", 'w') as f:
            json.dump(poc_list, f)
    else:
        print(f'file already exists! ../data/poclist/poclist-{year}-{month}.json')
