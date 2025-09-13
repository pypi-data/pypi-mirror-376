"""Unit tests for smoldata core functionality."""

import unittest
import pandas as pd
import numpy as np
from sklearn.datasets import load_wine
from pandas_slim.core import (
    reduce_mem_usage,
    check_if_integer,
    benchmark_methods,
    MemoryOptimizer,
    reduce_mem_basic,
    reduce_mem_aggressive
)


class TestSmolDataCore(unittest.TestCase):
    """Test cases for smoldata core functions."""
    
    def setUp(self):
        """Set up test data."""
        # Load wine dataset
        wine_data = load_wine()
        self.df = pd.DataFrame(wine_data.data, columns=wine_data.feature_names)
        
        # Create test DataFrame with different data types
        self.test_df = pd.DataFrame({
            'int_col': [1, 2, 3, 4, 5],
            'float_col': [1.1, 2.2, 3.3, 4.4, 5.5],
            'float_as_int': [1.0, 2.0, 3.0, 4.0, 5.0],
            'large_int': [1000, 2000, 3000, 4000, 5000],
            'small_int': [1, 2, 3, 4, 5],
            'string_col': ['a', 'b', 'c', 'a', 'b']
        })
    
    def test_check_if_integer(self):
        """Test integer detection function."""
        # Test with actual integers
        int_series = pd.Series([1.0, 2.0, 3.0, 4.0])
        self.assertTrue(check_if_integer(int_series))
        
        # Test with floats
        float_series = pd.Series([1.1, 2.2, 3.3, 4.4])
        self.assertFalse(check_if_integer(float_series))
        
        # Test with NaN values
        nan_series = pd.Series([1.0, 2.0, np.nan, 4.0])
        self.assertTrue(check_if_integer(nan_series))
    
    def test_reduce_mem_usage_basic(self):
        """Test basic memory reduction."""
        original_mem = self.df.memory_usage().sum()
        df_optimized = reduce_mem_usage(self.df.copy(), verbose=False)
        optimized_mem = df_optimized.memory_usage().sum()
        
        # Memory should be reduced
        self.assertLess(optimized_mem, original_mem)
        
        # Data should be preserved
        pd.testing.assert_frame_equal(
            self.df.astype(df_optimized.dtypes), 
            df_optimized, 
            check_dtype=False
        )
    
    def test_reduce_mem_usage_with_params(self):
        """Test memory reduction with different parameters."""
        # Test with int_cast=False
        df_no_int = reduce_mem_usage(
            self.test_df.copy(), 
            int_cast=False, 
            verbose=False
        )
        
        # float_as_int should remain float
        self.assertTrue(pd.api.types.is_float_dtype(df_no_int['float_as_int']))
        
        # Test with obj_to_category=True
        df_cat = reduce_mem_usage(
            self.test_df.copy(), 
            obj_to_category=True, 
            verbose=False
        )
        
        # string_col should be category
        self.assertEqual(df_cat['string_col'].dtype.name, 'category')
    
    def test_reduce_mem_usage_subset(self):
        """Test memory reduction on subset of columns."""
        subset_cols = ['int_col', 'float_col']
        df_subset = reduce_mem_usage(
            self.test_df.copy(), 
            subset=subset_cols, 
            verbose=False
        )
        
        # Only specified columns should be optimized
        # Other columns should remain unchanged
        self.assertEqual(
            self.test_df['string_col'].dtype, 
            df_subset['string_col'].dtype
        )
    
    def test_reduce_mem_basic(self):
        """Test basic reduction method."""
        original_mem = self.df.memory_usage().sum()
        df_basic = reduce_mem_basic(self.df.copy(), verbose=False)
        optimized_mem = df_basic.memory_usage().sum()
        
        self.assertLess(optimized_mem, original_mem)
    
    def test_reduce_mem_aggressive(self):
        """Test aggressive reduction method."""
        original_mem = self.df.memory_usage().sum()
        df_aggressive = reduce_mem_aggressive(self.df.copy(), verbose=False)
        optimized_mem = df_aggressive.memory_usage().sum()
        
        self.assertLess(optimized_mem, original_mem)
    
    def test_benchmark_methods(self):
        """Test benchmarking functionality."""
        results = benchmark_methods(self.df)
        
        # Should return results for all methods
        expected_methods = ['basic', 'advanced', 'aggressive']
        for method in expected_methods:
            self.assertIn(method, results)
            
            # Each result should have required keys
            required_keys = [
                'original_memory_mb', 'optimized_memory_mb', 
                'reduction_percentage', 'execution_time_seconds'
            ]
            for key in required_keys:
                self.assertIn(key, results[method])
    
    def test_memory_optimizer_class(self):
        """Test MemoryOptimizer class."""
        # Test initialization
        optimizer = MemoryOptimizer(strategy='advanced')
        self.assertEqual(optimizer.strategy, 'advanced')
        
        # Test optimization
        df_optimized = optimizer.optimize(self.df.copy(), verbose=False)
        self.assertLess(
            df_optimized.memory_usage().sum(), 
            self.df.memory_usage().sum()
        )
        
        # Test benchmark
        results = optimizer.benchmark(self.df)
        self.assertIsInstance(results, dict)
        
        # Test invalid strategy
        with self.assertRaises(ValueError):
            invalid_optimizer = MemoryOptimizer(strategy='invalid')
            invalid_optimizer.optimize(self.df)
    
    def test_data_integrity(self):
        """Test that data values are preserved after optimization."""
        df_original = self.test_df.copy()
        df_optimized = reduce_mem_usage(df_original.copy(), verbose=False)
        
        # Check that numeric values are preserved (with appropriate tolerance for float16)
        for col in ['int_col', 'float_col', 'float_as_int', 'large_int', 'small_int']:
            if df_optimized[col].dtype == np.float16:
                # Float16 has lower precision, use appropriate tolerance
                np.testing.assert_allclose(
                    df_original[col].values,
                    df_optimized[col].values,
                    rtol=1e-3, atol=1e-3
                )
            else:
                np.testing.assert_array_almost_equal(
                    df_original[col].values,
                    df_optimized[col].values,
                    decimal=5
                )
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Empty DataFrame
        empty_df = pd.DataFrame()
        result = reduce_mem_usage(empty_df, verbose=False)
        self.assertTrue(result.empty)
        
        # DataFrame with only object columns
        obj_df = pd.DataFrame({
            'col1': ['a', 'b', 'c'],
            'col2': ['x', 'y', 'z']
        })
        result = reduce_mem_usage(obj_df, verbose=False)
        self.assertEqual(len(result.columns), 2)
        
        # DataFrame with datetime columns
        date_df = pd.DataFrame({
            'date_col': pd.date_range('2023-01-01', periods=5),
            'num_col': [1, 2, 3, 4, 5]
        })
        result = reduce_mem_usage(date_df, verbose=False)
        # Datetime column should be preserved
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(result['date_col']))


if __name__ == '__main__':
    unittest.main()