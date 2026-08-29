import pandas as pd
import numpy as np
from typing import List, Dict, Any
from app.adapters.base import HistoricalDataAdapter
from app.ml.dataset_generator import HistoricalDatasetGenerator

class MockHistoricalDataAdapter(HistoricalDataAdapter):
    """
    Mock implementation of HistoricalDataAdapter.
    Uses synthetic realistic Indian Railways dataset generated on-the-fly or loaded from CSV.
    Can easily be replaced by OfficialHistoricalDataAdapter reading from CRIS/IR databases.
    """
    def __init__(self, sample_size: int = 5000):
        self.sample_size = sample_size
        self._generator = HistoricalDatasetGenerator()
        self.df = None

    def load_historical_runs(self) -> List[Dict[str, Any]]:
        if self.df is None:
            self.df = self._generator.generate_dataset(num_records=self.sample_size)
        return self.df.to_dict(orient="records")

    def get_dataframe(self) -> pd.DataFrame:
        if self.df is None:
            self.df = self._generator.generate_dataset(num_records=self.sample_size)
        return self.df
