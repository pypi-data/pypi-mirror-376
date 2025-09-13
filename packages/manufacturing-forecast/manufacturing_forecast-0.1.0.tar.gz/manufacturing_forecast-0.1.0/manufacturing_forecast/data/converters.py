"""
Data converters for transforming data structures.
"""

from typing import Dict, Any, List
import numpy as np


class AssetConverter:
    """Converter for Asset objects to dictionary representations"""

    VAR_TYPES = ["past_covariates", "future_covariates", "target", "status"]

    @classmethod
    def to_dict(cls, asset: Any) -> Dict:
        """
        Convert an Asset object to a dictionary representation.

        Args:
            asset: Asset object to convert (should have Metadata attribute)

        Returns:
            Dict: Dictionary containing asset metadata and stream references
        """
        result = {}

        # Extract metadata if available
        if hasattr(asset, 'Metadata'):
            for meta in asset.Metadata:
                if hasattr(meta, 'Id') and hasattr(meta, 'Value'):
                    result[meta.Id] = meta.Value

        return result


class DataConverter:
    """Converter for data results to numpy arrays"""

    @staticmethod
    def to_numpy(data: Any) -> np.ndarray:
        """
        Convert data results to a numpy array.

        Args:
            data: Data results object with Results attribute

        Returns:
            np.ndarray: Converted data array
        """
        result_data = []

        try:
            if hasattr(data, 'Results'):
                for key, ts in data.Results.items():
                    if len(ts) == 0:
                        continue
                    result_data.append([item.get("value", np.nan) if isinstance(item, dict) else item for item in ts])

            return np.array(result_data)

        except Exception as e:
            print(f"Error converting data results: {e}")
            return np.array([])

    @staticmethod
    def to_numpy_ordered(asset_dict: Dict, data: Any) -> Dict[str, np.ndarray]:
        """
        Convert data results to numpy array with specific ordering based on asset dictionary.

        Args:
            asset_dict: Dictionary containing variable type categorization
            data: Data results object with Results attribute

        Returns:
            Dict[str, np.ndarray]: Dictionary with ordered data arrays
        """
        result_data = {}

        try:
            for variable in ["target", "past", "future", "status"]:
                result_data[variable] = []
                tmp = str(asset_dict.get(variable)).split(",")
                if tmp[0] != "[]" and tmp[0] != "":
                    rows = []
                    for i in range(len(tmp)):
                        if hasattr(data, 'Results'):
                            ts = data.Results.get(tmp[i], [])
                            rows.append([item.get("value", np.nan) if isinstance(item, dict) else item for item in ts])
                        else:
                            rows.append([])
                    result_data[variable] = np.array(rows, dtype=object)
            return result_data
        except Exception as e:
            print(f"Error converting ordered data results: {e}")
            return result_data

    @staticmethod
    def from_dataframe(df, column_mapping: Dict[str, List[str]]) -> Dict[str, np.ndarray]:
        """
        Convert pandas DataFrame to numpy arrays based on column mapping.
        
        Args:
            df: pandas DataFrame
            column_mapping: Dict mapping variable types to column names
                          e.g. {'target': ['col1'], 'past': ['col2', 'col3']}
        
        Returns:
            Dict[str, np.ndarray]: Dictionary with variable type arrays
        """
        result_data = {}
        
        for var_type, columns in column_mapping.items():
            if columns:
                try:
                    data_subset = df[columns].values
                    if data_subset.shape[1] == 1:
                        result_data[var_type] = data_subset.flatten()
                    else:
                        result_data[var_type] = data_subset.T  # Transpose to match (n_features, n_timesteps)
                except KeyError as e:
                    print(f"Warning: Column {e} not found in DataFrame")
                    result_data[var_type] = np.array([])
            else:
                result_data[var_type] = np.array([])
                
        return result_data
