from typing import List, Dict

from pandas import DataFrame
from pyspark.sql import DataFrame as PySparkDataFrame

from seshat.data_class import SFrame
from seshat.transformer import Transformer
from seshat.utils import pandas_func, pyspark_func


class Imputer(Transformer):
    def impute(self):
        pass


class SFrameImputer(Transformer):
    HANDLER_NAME = "impute"


class NaNImputer(SFrameImputer):
    """
    A transformer that replaces NaN values in specified columns with a specific value.

    Parameters
    ----------
    cols : list of str, optional
        Columns that should be imputed. If None, all columns will be considered.
    value : any, optional
        The value to impute. If None, a default zero-like value based on the column's data type will be used.
    """

    def __init__(
        self, cols: List[str] = None, value=None, group_keys=None, *args, **kwargs
    ):
        super().__init__(group_keys)

        self.cols = cols
        self.value = value

    def validate(self, sf: SFrame):
        super().validate(sf)
        if self.cols:
            self._validate_columns(sf, self.default_sf_key, *self.cols)

    def impute_df(self, default: DataFrame, *args, **kwargs) -> Dict[str, DataFrame]:
        for col in self.cols or default.columns.tolist():
            value = self.value or pandas_func.get_zero_value(default[col])
            default = default.fillna({col: value})
        return {"default": default}

    def impute_spf(
        self, default: PySparkDataFrame, *args, **kwargs
    ) -> Dict[str, PySparkDataFrame]:
        for col in self.cols or default.columns:
            value = self.value or pyspark_func.get_zero_value(default, col)
            default = default.fillna({col: value})
        return {"default": default}
