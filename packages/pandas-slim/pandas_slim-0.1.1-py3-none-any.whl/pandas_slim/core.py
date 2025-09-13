"""Core memory optimization functions for pandas DataFrames."""

import numpy as np
import pandas as pd
from tqdm import tqdm
import gc
import time
import matplotlib.pyplot as plt
from typing import Optional, List, Dict, Tuple
from scipy import sparse
import warnings
warnings.filterwarnings('ignore')


def check_if_integer(column: pd.Series, tolerance: float = 0.01) -> bool:
    """
    Checks if a column can be converted to integer.
    
    :param column: numeric column (pd.Series)
    :param tolerance: tolerance for the float-int casting (float)
    :return: True if column can be converted to integer (bool)
    """
    casted = column.fillna(0).astype(np.int64)
    result = (column - casted)
    result = result.sum()
    if result > -0.01 and result < 0.01:
        return True
    else:
        return False


def reduce_mem_usage(df: pd.DataFrame, int_cast: bool = True, 
                    obj_to_category: bool = False, 
                    subset: Optional[List[str]] = None,
                    verbose: bool = True) -> pd.DataFrame:
    """
    Iterate through all the columns of a dataframe and modify the data type to reduce memory usage.
    
    :param df: dataframe to reduce (pd.DataFrame)
    :param int_cast: indicate if columns should be tried to be casted to int (bool)
    :param obj_to_category: convert non-datetime related objects to category dtype (bool)
    :param subset: subset of columns to analyse (list)
    :param verbose: print memory usage information (bool)
    :return: dataset with the column dtypes adjusted (pd.DataFrame)
    """
    start_mem = df.memory_usage().sum() / 1024**2
    gc.collect()
    if verbose:
        print('Memory usage of dataframe is {:.2f} MB'.format(start_mem))
    
    cols = subset if subset is not None else df.columns.tolist()

    for col in tqdm(cols, disable=not verbose):
        col_type = df[col].dtype
        
        if col_type != object and col_type.name != 'category' and 'datetime' not in col_type.name:
            c_min = df[col].min()
            c_max = df[col].max()

            # test if column can be converted to an integer
            treat_as_int = str(col_type)[:3] == 'int'
            if int_cast and not treat_as_int:
                treat_as_int = check_if_integer(df[col])

            if treat_as_int:
                if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                    df[col] = df[col].astype(np.int8)
                elif c_min > np.iinfo(np.uint8).min and c_max < np.iinfo(np.uint8).max:
                    df[col] = df[col].astype(np.uint8)
                elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                    df[col] = df[col].astype(np.int16)
                elif c_min > np.iinfo(np.uint16).min and c_max < np.iinfo(np.uint16).max:
                    df[col] = df[col].astype(np.uint16)
                elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                    df[col] = df[col].astype(np.int32)
                elif c_min > np.iinfo(np.uint32).min and c_max < np.iinfo(np.uint32).max:
                    df[col] = df[col].astype(np.uint32)
                elif c_min > np.iinfo(np.int64).min and c_max < np.iinfo(np.int64).max:
                    df[col] = df[col].astype(np.int64)
                elif c_min > np.iinfo(np.uint64).min and c_max < np.iinfo(np.uint64).max:
                    df[col] = df[col].astype(np.uint64)
            else:
                if c_min > np.finfo(np.float16).min and c_max < np.finfo(np.float16).max:
                    df[col] = df[col].astype(np.float16)
                elif c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                    df[col] = df[col].astype(np.float32)
                else:
                    df[col] = df[col].astype(np.float64)
        elif 'datetime' not in col_type.name and obj_to_category:
            df[col] = df[col].astype('category')
    
    gc.collect()
    end_mem = df.memory_usage().sum() / 1024**2
    if verbose:
        print('Memory usage after optimization is: {:.3f} MB'.format(end_mem))
        print('Decreased by {:.1f}%'.format(100 * (start_mem - end_mem) / start_mem))
    
    return df


def reduce_mem_basic(df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """
    Basic memory reduction using simple downcasting.
    
    :param df: dataframe to reduce (pd.DataFrame)
    :param verbose: print memory usage information (bool)
    :return: dataset with optimized dtypes (pd.DataFrame)
    """
    start_mem = df.memory_usage().sum() / 1024**2
    if verbose:
        print('Memory usage of dataframe is {:.2f} MB'.format(start_mem))
    
    for col in df.columns:
        col_type = df[col].dtype
        
        if col_type != object:
            c_min = df[col].min()
            c_max = df[col].max()
            
            if str(col_type)[:3] == 'int':
                if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                    df[col] = df[col].astype(np.int8)
                elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                    df[col] = df[col].astype(np.int16)
                elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                    df[col] = df[col].astype(np.int32)
                elif c_min > np.iinfo(np.int64).min and c_max < np.iinfo(np.int64).max:
                    df[col] = df[col].astype(np.int64)
            else:
                if c_min > np.finfo(np.float16).min and c_max < np.finfo(np.float16).max:
                    df[col] = df[col].astype(np.float16)
                elif c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                    df[col] = df[col].astype(np.float32)
                else:
                    df[col] = df[col].astype(np.float64)
        else:
            df[col] = df[col].astype('category')
    
    end_mem = df.memory_usage().sum() / 1024**2
    if verbose:
        print('Memory usage after optimization is: {:.3f} MB'.format(end_mem))
        print('Decreased by {:.1f}%'.format(100 * (start_mem - end_mem) / start_mem))
    
    return df


def reduce_mem_aggressive(df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """
    Aggressive memory reduction with unsigned integers and category conversion.
    
    :param df: dataframe to reduce (pd.DataFrame)
    :param verbose: print memory usage information (bool)
    :return: dataset with optimized dtypes (pd.DataFrame)
    """
    start_mem = df.memory_usage().sum() / 1024**2
    if verbose:
        print('Memory usage of dataframe is {:.2f} MB'.format(start_mem))
    
    for col in df.columns:
        col_type = df[col].dtype
        
        if col_type != object and col_type.name != 'category':
            c_min = df[col].min()
            c_max = df[col].max()
            
            # Check if can be converted to integer
            if pd.api.types.is_float_dtype(df[col]):
                if df[col].fillna(0).apply(lambda x: x.is_integer()).all():
                    df[col] = df[col].astype('Int64')
                    col_type = df[col].dtype
                    c_min = df[col].min()
                    c_max = df[col].max()
            
            if str(col_type)[:3] == 'int' or 'Int' in str(col_type):
                # Try unsigned first if all values are positive
                if c_min >= 0:
                    if c_max < np.iinfo(np.uint8).max:
                        df[col] = df[col].astype(np.uint8)
                    elif c_max < np.iinfo(np.uint16).max:
                        df[col] = df[col].astype(np.uint16)
                    elif c_max < np.iinfo(np.uint32).max:
                        df[col] = df[col].astype(np.uint32)
                    else:
                        df[col] = df[col].astype(np.uint64)
                else:
                    # Use signed integers
                    if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                        df[col] = df[col].astype(np.int8)
                    elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                        df[col] = df[col].astype(np.int16)
                    elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                        df[col] = df[col].astype(np.int32)
                    else:
                        df[col] = df[col].astype(np.int64)
            else:
                # Float optimization
                if c_min > np.finfo(np.float16).min and c_max < np.finfo(np.float16).max:
                    df[col] = df[col].astype(np.float16)
                elif c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                    df[col] = df[col].astype(np.float32)
                else:
                    df[col] = df[col].astype(np.float64)
        else:
            # Convert objects to category
            df[col] = df[col].astype('category')
    
    end_mem = df.memory_usage().sum() / 1024**2
    if verbose:
        print('Memory usage after optimization is: {:.3f} MB'.format(end_mem))
        print('Decreased by {:.1f}%'.format(100 * (start_mem - end_mem) / start_mem))
    
    return df


def reduce_mem_sparse(df: pd.DataFrame, sparsity_threshold: float = 0.95, verbose: bool = True) -> pd.DataFrame:
    """
    Memory reduction using sparse matrices for columns with high sparsity.
    
    :param df: dataframe to reduce (pd.DataFrame)
    :param sparsity_threshold: minimum sparsity ratio to convert to sparse (float)
    :param verbose: print memory usage information (bool)
    :return: dataset with sparse columns where applicable (pd.DataFrame)
    """
    start_mem = df.memory_usage().sum() / 1024**2
    if verbose:
        print('Memory usage of dataframe is {:.2f} MB'.format(start_mem))
    
    df_optimized = df.copy()
    
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            # Calculate sparsity (percentage of zeros)
            zero_count = (df[col] == 0).sum()
            sparsity = zero_count / len(df[col])
            
            if sparsity >= sparsity_threshold:
                if verbose:
                    print(f"Converting {col} to sparse (sparsity: {sparsity:.2%})")
                # Convert to sparse array and back to maintain DataFrame structure
                sparse_array = sparse.csr_matrix(df[col].values.reshape(-1, 1))
                df_optimized[col] = pd.arrays.SparseArray(df[col].values, dtype=df[col].dtype)
    
    # Apply basic optimization to non-sparse columns
    df_optimized = reduce_mem_basic(df_optimized, verbose=False)
    
    end_mem = df_optimized.memory_usage().sum() / 1024**2
    if verbose:
        print('Memory usage after sparse optimization is: {:.3f} MB'.format(end_mem))
        print('Decreased by {:.1f}%'.format(100 * (start_mem - end_mem) / start_mem))
    
    return df_optimized


def reduce_mem_quantized(df: pd.DataFrame, n_bins: int = 256, verbose: bool = True) -> pd.DataFrame:
    """
    Memory reduction using quantization for float columns.
    
    :param df: dataframe to reduce (pd.DataFrame)
    :param n_bins: number of bins for quantization (int)
    :param verbose: print memory usage information (bool)
    :return: dataset with quantized float columns (pd.DataFrame)
    """
    start_mem = df.memory_usage().sum() / 1024**2
    if verbose:
        print('Memory usage of dataframe is {:.2f} MB'.format(start_mem))
    
    df_optimized = df.copy()
    
    for col in df.columns:
        if pd.api.types.is_float_dtype(df[col]):
            # Quantize float values
            try:
                df_optimized[col] = pd.cut(df[col], bins=n_bins, labels=False, duplicates='drop')
                df_optimized[col] = df_optimized[col].astype('uint8')
                if verbose:
                    print(f"Quantized {col} to {n_bins} bins")
            except Exception:
                # If quantization fails, apply regular optimization
                if verbose:
                    print(f"Quantization failed for {col}, applying regular optimization")
                continue
    
    # Apply basic optimization to remaining columns
    for col in df_optimized.columns:
        if pd.api.types.is_integer_dtype(df_optimized[col]) and df_optimized[col].dtype != 'uint8':
            c_min = df_optimized[col].min()
            c_max = df_optimized[col].max()
            
            if c_min >= 0:
                if c_max < np.iinfo(np.uint8).max:
                    df_optimized[col] = df_optimized[col].astype(np.uint8)
                elif c_max < np.iinfo(np.uint16).max:
                    df_optimized[col] = df_optimized[col].astype(np.uint16)
    
    end_mem = df_optimized.memory_usage().sum() / 1024**2
    if verbose:
        print('Memory usage after quantization is: {:.3f} MB'.format(end_mem))
        print('Decreased by {:.1f}%'.format(100 * (start_mem - end_mem) / start_mem))
    
    return df_optimized


def reduce_mem_precision_loss(df: pd.DataFrame, precision_bits: int = 16, verbose: bool = True) -> pd.DataFrame:
    """
    Aggressive memory reduction with controlled precision loss.
    
    :param df: dataframe to reduce (pd.DataFrame)
    :param precision_bits: target precision in bits (8, 16, 32) (int)
    :param verbose: print memory usage information (bool)
    :return: dataset with reduced precision (pd.DataFrame)
    """
    start_mem = df.memory_usage().sum() / 1024**2
    if verbose:
        print('Memory usage of dataframe is {:.2f} MB'.format(start_mem))
    
    df_optimized = df.copy()
    
    target_dtype = {
        8: np.float16,
        16: np.float16,
        32: np.float32
    }.get(precision_bits, np.float32)
    
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            try:
                if pd.api.types.is_float_dtype(df[col]):
                    df_optimized[col] = df_optimized[col].astype(target_dtype)
                elif pd.api.types.is_integer_dtype(df[col]):
                    # Convert integers to smaller types
                    c_min = df[col].min()
                    c_max = df[col].max()
                    
                    if precision_bits <= 8:
                        if c_min >= 0 and c_max < 256:
                            df_optimized[col] = df_optimized[col].astype(np.uint8)
                        elif c_min >= -128 and c_max < 128:
                            df_optimized[col] = df_optimized[col].astype(np.int8)
                    elif precision_bits <= 16:
                        if c_min >= 0 and c_max < 65536:
                            df_optimized[col] = df_optimized[col].astype(np.uint16)
                        elif c_min >= -32768 and c_max < 32768:
                            df_optimized[col] = df_optimized[col].astype(np.int16)
            except Exception as e:
                if verbose:
                    print(f"Could not reduce precision for {col}: {e}")
                continue
    
    end_mem = df_optimized.memory_usage().sum() / 1024**2
    if verbose:
        print('Memory usage after precision reduction is: {:.3f} MB'.format(end_mem))
        print('Decreased by {:.1f}%'.format(100 * (start_mem - end_mem) / start_mem))
    
    return df_optimized


def benchmark_methods(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """
    Benchmark different memory reduction methods.
    
    :param df: dataframe to benchmark (pd.DataFrame)
    :return: dictionary with method names and their performance metrics (dict)
    """
    results = {}
    original_mem = df.memory_usage().sum() / 1024**2
    
    methods = {
        'basic': lambda x: reduce_mem_basic(x, verbose=False),
        'advanced': lambda x: reduce_mem_usage(x, verbose=False),
        'aggressive': lambda x: reduce_mem_aggressive(x, verbose=False),
        'sparse': lambda x: reduce_mem_sparse(x, verbose=False),
        'quantized': lambda x: reduce_mem_quantized(x, verbose=False),
        'precision_loss_16': lambda x: reduce_mem_precision_loss(x, precision_bits=16, verbose=False),
        'precision_loss_8': lambda x: reduce_mem_precision_loss(x, precision_bits=8, verbose=False)
    }
    
    for method_name, method_func in methods.items():
        try:
            start_time = time.time()
            optimized_df = method_func(df.copy())
            end_time = time.time()
            
            optimized_mem = optimized_df.memory_usage().sum() / 1024**2
            reduction_pct = 100 * (original_mem - optimized_mem) / original_mem
            
            results[method_name] = {
                'original_memory_mb': original_mem,
                'optimized_memory_mb': optimized_mem,
                'reduction_percentage': reduction_pct,
                'execution_time_seconds': end_time - start_time
            }
        except Exception as e:
            print(f"Method {method_name} failed: {e}")
            results[method_name] = {
                'original_memory_mb': original_mem,
                'optimized_memory_mb': original_mem,
                'reduction_percentage': 0.0,
                'execution_time_seconds': 0.0,
                'error': str(e)
            }
    
    return results


class MemoryOptimizer:
    """
    A class to handle memory optimization with different strategies.
    """
    
    def __init__(self, strategy: str = 'advanced'):
        """
        Initialize the optimizer with a specific strategy.
        
        :param strategy: optimization strategy ('basic', 'advanced', 'aggressive')
        """
        self.strategy = strategy
        self.methods = {
            'basic': reduce_mem_basic,
            'advanced': reduce_mem_usage,
            'aggressive': reduce_mem_aggressive
        }
    
    def optimize(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        Optimize DataFrame memory usage using the selected strategy.
        
        :param df: dataframe to optimize
        :param kwargs: additional arguments for the optimization method
        :return: optimized dataframe
        """
        if self.strategy not in self.methods:
            raise ValueError(f"Unknown strategy: {self.strategy}")
        
        return self.methods[self.strategy](df, **kwargs)
    
    def benchmark(self, df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """
        Benchmark all available methods on the given DataFrame.
        
        :param df: dataframe to benchmark
        :return: benchmark results
        """
        return benchmark_methods(df)
    
    def plot_benchmark(self, df: pd.DataFrame, save_path: Optional[str] = None) -> None:
        """
        Create a visualization of benchmark results.
        
        :param df: dataframe to benchmark
        :param save_path: path to save the plot (optional)
        """
        results = self.benchmark(df)
        
        methods = list(results.keys())
        reductions = [results[method]['reduction_percent'] for method in methods]
        times = [results[method]['time_seconds'] for method in methods]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Memory reduction plot
        bars1 = ax1.bar(methods, reductions, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        ax1.set_ylabel('Memory Reduction (%)')
        ax1.set_title('Memory Reduction by Method')
        ax1.set_ylim(0, max(reductions) * 1.1)
        
        # Add value labels on bars
        for bar, reduction in zip(bars1, reductions):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{reduction:.1f}%', ha='center', va='bottom')
        
        # Execution time plot
        bars2 = ax2.bar(methods, times, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        ax2.set_ylabel('Execution Time (seconds)')
        ax2.set_title('Execution Time by Method')
        
        # Add value labels on bars
        for bar, time_val in zip(bars2, times):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.001,
                    f'{time_val:.3f}s', ha='center', va='bottom')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()