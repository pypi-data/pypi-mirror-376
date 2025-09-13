# taco-compression
This is the official implementation of the TACO compression algorithm for time series [1]. 

# Usage
There are two usage modes, one as a command line tool operating on files, the other as callables from within python.

## Command Line

You can pass the time series to compress in two ways, either by specifying a directory from which all csv files are read...
```shell
python -m tacocompression c time_series
python -m tacocompression d time_series
```

... or by passing the paths to the files directly.
```shell
python -m tacocompression data/time_series_1.csv data/time_series_2.csv
```

Each file must contain a single column interpreted as a univariate time series. We assume row 0 is the header.

## As a Callable
```python
from tacocompression import compress, decompress

# 2 univariate time series, length 10 and 8:
time_series = [[0.0, 1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8, 9.9], [8.8, 7.7, 6.6, 5.5, 4.4, 3.3, 2.2, 1.1]]

compressed = compress(time_series, "szudzik", 1)
reconstructed = decompress(compressed, "szudzik")

assert time_series == reconstructed
```

[1] Bauer, André. TACO: A Lightweight Tree-Based Approximate Compression Method for Time Series. In: Proceedings of the 
    14th International Conference on Data Science, Technology and Applications (DATA 2025), pages 182-190. 2025.