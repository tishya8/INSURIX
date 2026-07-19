# RAG Evaluation Summary

**Total test cases:** 31

## Overall Metrics

| Metric                  |   count |     mean |      std |   median |     min |       max |
|:------------------------|--------:|---------:|---------:|---------:|--------:|----------:|
| Faithfulness            |      31 |    0.785 |    0.346 |     1    |    0    |     1     |
| Answer Relevancy        |      31 |    0.386 |    0.342 |     0.5  |    0    |     1     |
| Contextual Relevancy    |      31 |    0.048 |    0.098 |     0    |    0    |     0.333 |
| Retrieval Time (ms)     |      31 |  965.112 |  557.411 |   840.85 |  342.99 |  2939.73  |
| Generation Time (ms)    |      31 | 3317.06  | 1174.56  |  2780.65 | 1746.48 |  6989.49  |
| Total Time (ms)         |      31 | 5389.03  | 2111.95  |  5095.7  | 2677.1  | 12992.3   |
| Response Length (words) |      31 |   21.355 |   26.531 |    14    |    1    |   130     |

## Score Distribution

| Metric               | Band               |   Count |   Percent |
|:---------------------|:-------------------|--------:|----------:|
| Faithfulness         | Low (0.0-0.5)      |       4 |      12.9 |
| Faithfulness         | Moderate (0.5-0.8) |       5 |      16.1 |
| Faithfulness         | High (0.8-1.0)     |      22 |      71   |
| Answer Relevancy     | Low (0.0-0.5)      |      14 |      45.2 |
| Answer Relevancy     | Moderate (0.5-0.8) |      13 |      41.9 |
| Answer Relevancy     | High (0.8-1.0)     |       4 |      12.9 |
| Contextual Relevancy | Low (0.0-0.5)      |      31 |     100   |
| Contextual Relevancy | Moderate (0.5-0.8) |       0 |       0   |
| Contextual Relevancy | High (0.8-1.0)     |       0 |       0   |

## Breakdown by Category

| Category            |   Faithfulness |   Answer Relevancy |   Contextual Relevancy |   Retrieval Time (ms) |   Generation Time (ms) |   Total Time (ms) |   Response Length (words) |   Count |
|:--------------------|---------------:|-------------------:|-----------------------:|----------------------:|-----------------------:|------------------:|--------------------------:|--------:|
| Coverage            |          0.552 |              0.426 |                  0.077 |              1052.4   |                3363.28 |           5760.89 |                    20.333 |       9 |
| Claims              |          0.955 |              0.549 |                  0.045 |               831.448 |                3840.67 |           5363.57 |                    42.167 |       6 |
| Vehicle Information |          0.88  |              0.5   |                  0     |              1128.37  |                2738.57 |           5115.61 |                     6.6   |       5 |
| Policy Information  |          0.75  |              0.458 |                  0     |               501.975 |                3575.85 |           4166.92 |                     8.25  |       4 |
| Add-on              |          0.833 |              0.167 |                  0.131 |               961.247 |                3134.38 |           5894.72 |                    27.333 |       3 |
| Add-on Covers       |          1     |              0     |                  0     |               654.35  |                3522.33 |           4252.84 |                    31     |       1 |
| Customer Support    |          0.75  |              0     |                  0.143 |              1106.18  |                3361.42 |           6590.49 |                    36     |       1 |
| Deductible          |          1     |              0     |                  0     |               772.54  |                2794.7  |           5961.08 |                    10     |       1 |
| Exclusion           |          1     |              0     |                  0     |              2391.65  |                2437.56 |           6296.14 |                     1     |       1 |

## Breakdown by Difficulty

| Difficulty   |   Faithfulness |   Answer Relevancy |   Contextual Relevancy |   Retrieval Time (ms) |   Generation Time (ms) |   Total Time (ms) |   Response Length (words) |   Count |
|:-------------|---------------:|-------------------:|-----------------------:|----------------------:|-----------------------:|------------------:|--------------------------:|--------:|
| Easy         |          0.836 |              0.5   |                  0     |              1001.92  |                3048.6  |           5183.96 |                    11     |      14 |
| Medium       |          0.847 |              0.278 |                  0.06  |              1041.7   |                3056.45 |           5453.47 |                    27.889 |       9 |
| Hard         |          0.628 |              0.307 |                  0.121 |               814.528 |                4080.07 |           5675.39 |                    32.125 |       8 |

## Correlation (Length / Timing)

|                         |   Response Length (words) |   Generation Time (ms) |   Total Time (ms) |
|:------------------------|--------------------------:|-----------------------:|------------------:|
| Response Length (words) |                     1     |                  0.716 |             0.539 |
| Generation Time (ms)    |                     0.716 |                  1     |             0.503 |
| Total Time (ms)         |                     0.539 |                  0.503 |             1     |