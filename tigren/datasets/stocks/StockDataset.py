import os
import pickle
import datetime
from typing import List
from abc import ABC, abstractmethod
import pandas as pd

class StockDataset(ABC):
    @abstractmethod
    def __init__(self):
        pass
    
    @abstractmethod
    def min(self):
        '''Minimum date in the dataset'''
        pass
    
    @abstractmethod
    def max(self):
        '''Maximum date in the dataset'''
        pass

    @abstractmethod
    def get_tickers(self):
        '''List of stock tickers in the dataset'''
        pass

    def _str_to_date(self, date_str):
        date_str = date_str.split("/")
        or_str = []
        for ss in date_str:
            or_str = or_str + ss.split("-")
        Y, m, d = or_str
        return datetime.date(int(Y), int(m), int(d))
    
    def split_dataset(self, ratios=List[int]) -> List[pd.DataFrame]:
        """Splits the dataset *in order* in above ratios. For instance if the data had 10 trading days
        and ratios=(0.6, 0.2, 0.2), this will split the data as {first 6 days, the next 2 days, the next 2 days}.

        Args:
            ratios (List[int]): variable length list of ratios to split the data. 
        
        Returns:
            splits (List[pd.DataFrame])
        """
        date_range = self.data.index
        number_of_dates = len(date_range)
        for idx, ratio in enumerate(ratios):
            ratios[idx] = int(number_of_dates*ratio)

        splits = []
        prev_index = 0
        for idx, ratio in enumerate(ratios):
            data_split = self.data.loc[self.data.index[prev_index : prev_index + ratio]]
            splits.append(data_split)
            prev_index = ratio

        return splits
        
    def split_train_valid_test_random(self, ratios: tuple, random_state: int = 100):
        """Randomly generate split: train - valid - test. Ratios are supplied in that order.
        This is probably not useful for stock data, but included nevertheless for now. 
        Args:
            ratios       (tuple): ratio of train - valid - test, respectively.
            random_state (int): random seed for reproducibility
        Returns:
            train (pd.DataFrame): DataFrame object of the train data
            valid (pd.DataFrame)
            test  (pd.DataFrame)

        """
        summed = sum(ratios)
        if summed != 1.0:
            raise Exception("Ratios must add up to 1.0. EX: (0.6, 0.2, 0.2)")
        else:
            cache_exists = False
            if self.cache: # you want there to be a cache
                la = ["train", "valid", "test"]
                filenames = [f"cache/raw_{i}_split.pkl" for i in la]
                cache_exists = [os.path.isfile(fn) for fn in filenames]
                cache_exists = not (False in cache_exists)
                if cache_exists: # and you had the cache!
                    train = pickle.load(open(f"cache/raw_train_split.pkl", "rb"))
                    valid = pickle.load(open(f"cache/raw_valid_split.pkl", "rb"))
                    test = pickle.load(open(f"cache/raw_test_split.pkl", "rb"))
                    return train, valid, test

            if not cache_exists: # there is no cache 
                df = self.data
                train = df.sample(frac=ratios[0], random_state=random_state)
                rest = df.drop(train.index)
                valid_frac = ratios[1] / (ratios[1] + ratios[2])
                valid = rest.sample(frac=valid_frac, random_state=random_state)
                test = rest.drop(valid.index)        

                if self.cache: # but you wanted there to be cache. so make cache.
                    logger.warning("Cached train-valid-test split not found. Generating new split but <r>do reconfirm this is the intended consequence</r>.")
                    ll = [train, valid, test]
                    zipped = list(zip(ll, la))
                    for zipp in zipped:
                        with open(f"cache/raw_{zipp[1]}_split.pkl", "wb") as f:
                            pickle.dump(zipp[0], f)

                return train, valid, test

    