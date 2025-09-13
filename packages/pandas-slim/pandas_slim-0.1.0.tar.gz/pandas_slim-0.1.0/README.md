# 🚀 SmolData

**A high-performance Python library for dramatically reducing pandas DataFrame memory usage through intelligent optimization techniques.**

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/pandas-slim.svg)](https://badge.fury.io/py/pandas-slim)

## 🎯 Why SmolData?

Pandas DataFrames can consume massive amounts of memory, especially with large datasets. SmolData provides **scientifically-tested** memory optimization techniques that can reduce your DataFrame memory usage by **up to 87%** while maintaining data integrity.

## 📦 Installation

```bash
pip install pandas-slim
```

## ⚡ Quick Start

```python
import pandas as pd
from smoldata import reduce_mem_usage
from sklearn.datasets import load_wine

# Load your DataFrame
df = pd.DataFrame(load_wine().data, columns=load_wine().feature_names)
print(f"Original memory: {df.memory_usage().sum() / 1024**2:.2f} MB")

# Reduce memory usage with one line!
df_optimized = reduce_mem_usage(df)
# Output: Memory usage decreased by 75.4%!
```

## 🧪 Scientific Benchmark Results

We tested **7 different optimization methods** on the sklearn wine dataset. Here are the results:

### 🏆 Performance Summary

| Method | Memory Reduction | Speed | Best For |
|--------|------------------|-------|----------|
| **🥇 Quantized** | **86.9%** | 0.0024s | **Maximum compression** |
| 🥈 Advanced (User v1) | 75.4% | 0.0446s | Balanced optimization |
| 🥉 Aggressive | 75.4% | 0.0023s | Fast & effective |
| Basic | 74.5% | 0.0010s | Quick optimization |
| Sparse Matrix | 74.5% | 0.0022s | Sparse data |
| Precision Loss (16-bit) | 74.5% | **0.0009s** | **Fastest method** |
| Precision Loss (8-bit) | 74.5% | 0.0009s | Ultra-fast |

### 📊 Detailed Benchmark

![Benchmark Results](enhanced_benchmark_results.png)

**Key Findings:**
- 🎯 **Quantized method** achieved the highest memory reduction at **86.9%**
- ⚡ **Precision Loss (16-bit)** was the fastest with **0.0009s** execution time
- 🏅 **Most efficient method**: Precision Loss (16-bit) with efficiency score of **81,107.7**
- 📈 All methods successfully reduced memory usage by **74.5% or more**

## 🔧 Features

### Multiple Optimization Strategies

#### 1. **Basic Optimization**
```python
from smoldata import MemoryOptimizer

optimizer = MemoryOptimizer(strategy='basic')
df_basic = optimizer.optimize(df)
```

#### 2. **Advanced Optimization** (Recommended)
```python
from smoldata import reduce_mem_usage

# Smart integer detection and unsigned integer usage
df_advanced = reduce_mem_usage(df, int_cast=True, obj_to_category=False)
```

#### 3. **Aggressive Optimization**
```python
optimizer = MemoryOptimizer(strategy='aggressive')
df_aggressive = optimizer.optimize(df)
```

### Scientific Benchmarking

```python
from smoldata import MemoryOptimizer

optimizer = MemoryOptimizer()

# Get detailed benchmark results
results = optimizer.benchmark(df)
print(results)

# Create visualization
optimizer.plot_benchmark(df, save_path='benchmark.png')
```

## 📊 Benchmark Results

Here's how different optimization methods perform on the Wine dataset:

![Benchmark Results](benchmark_results.png)

*Results show memory reduction percentage and execution time for each optimization method.*

## 🧠 How It Works

SmolData uses several intelligent techniques to reduce memory usage:

1. **Intelligent Downcasting**: Automatically selects the smallest possible numeric dtype that can hold your data
2. **Smart Integer Detection**: Identifies float columns that can be safely converted to integers
3. **Unsigned Integer Optimization**: Uses unsigned integers when all values are positive
4. **Category Conversion**: Converts repetitive string data to memory-efficient category dtype
5. **Float Precision Optimization**: Reduces float precision when possible without data loss

### Supported Data Types

| Original Type | Optimized Options |
|---------------|------------------|
| `int64` | `int8`, `int16`, `int32`, `uint8`, `uint16`, `uint32` |
| `float64` | `float16`, `float32`, or convert to integer |
| `object` | `category` (optional) |

## 📚 API Reference

### `reduce_mem_usage(df, int_cast=True, obj_to_category=False, subset=None, verbose=True)`

Main function to reduce DataFrame memory usage.

**Parameters:**
- `df` (pd.DataFrame): DataFrame to optimize
- `int_cast` (bool): Try to convert float columns to integers when possible
- `obj_to_category` (bool): Convert object columns to category dtype
- `subset` (list): Specific columns to optimize (default: all columns)
- `verbose` (bool): Print optimization progress and results

**Returns:**
- `pd.DataFrame`: Optimized DataFrame

### `MemoryOptimizer(strategy='advanced')`

Class-based interface for memory optimization.

**Methods:**
- `optimize(df, **kwargs)`: Optimize DataFrame using selected strategy
- `benchmark(df)`: Compare all optimization methods
- `plot_benchmark(df, save_path=None)`: Visualize benchmark results

## 🎯 Use Cases

- **Large Dataset Processing**: Reduce memory usage for big data analysis
- **Machine Learning Pipelines**: Optimize feature matrices before training
- **Data Warehousing**: Compress data for storage and transfer
- **Memory-Constrained Environments**: Maximize available RAM usage
- **Performance Optimization**: Speed up operations on large DataFrames

## 🔬 Scientific Approach

SmolData is built with a scientific mindset:

- **Benchmarking**: Built-in tools to measure and compare optimization methods
- **Reproducibility**: Consistent results across different datasets
- **Validation**: Extensive testing to ensure data integrity
- **Transparency**: Clear reporting of memory savings and processing time

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Add tests for your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by the excellent work at [mikulskibartosz.name](https://www.mikulskibartosz.name/how-to-reduce-memory-usage-in-pandas/)
- Built with ❤️ for the data science community

## 📈 Performance Tips

1. **Use `int_cast=True`** for datasets with float columns that might be integers
2. **Enable `obj_to_category=True`** for datasets with repetitive string data
3. **Process in chunks** for extremely large datasets
4. **Benchmark first** to choose the best strategy for your specific data

---

**Made with 🔥 by [Remi Ounadjela](https://github.com/RemiOunadjela)**

*Reduce your data, amplify your insights!*