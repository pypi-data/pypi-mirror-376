# taco-compression
This is the official implementation of the TACO compression algorithm for time series [1]. 

# Usage
There are two usage modes, one as a command line tool operating on files, the other as callables from within python.

## Command Line
```shell
python -m taco-compress "time_series"
```

```shell
python -m taco-compress "data/time_series_1.csv"
```

## As a Callable
```python
import taco-compress

taco-compress.
```

[1] Bauer, André. TACO: A Lightweight Tree-Based Approximate Compression Method for Time Series. In: Proceedings of the 
    14th International Conference on Data Science, Technology and Applications (DATA 2025), pages 182-190. 2025.