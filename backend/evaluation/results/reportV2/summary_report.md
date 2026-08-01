# RAG Evaluation Summary

**Total test cases:** 23

## Overall Metrics

| Metric                  |   count |     mean |      std |   median |     min |       max |
|:------------------------|--------:|---------:|---------:|---------:|--------:|----------:|
| Faithfulness            |      23 |    0.758 |    0.384 |     1    |    0    |     1     |
| Answer Relevancy        |      23 |    0.52  |    0.294 |     0.5  |    0    |     1     |
| Contextual Relevancy    |      23 |    0.048 |    0.108 |     0    |    0    |     0.333 |
| Retrieval Time (ms)     |      23 |  925.191 |  565.907 |   840.85 |  342.99 |  2939.73  |
| Generation Time (ms)    |      23 | 3425.58  | 1305.05  |  2780.65 | 1746.48 |  6989.49  |
| Total Time (ms)         |      23 | 5378.11  | 2285.54  |  5095.7  | 2677.1  | 12992.3   |
| Response Length (words) |      23 |   20.087 |   28.27  |    13    |    1    |   130     |

## Score Distribution

| Metric               | Band               |   Count |   Percent |
|:---------------------|:-------------------|--------:|----------:|
| Faithfulness         | Low (0.0-0.5)      |       4 |      17.4 |
| Faithfulness         | Moderate (0.5-0.8) |       2 |       8.7 |
| Faithfulness         | High (0.8-1.0)     |      17 |      73.9 |
| Answer Relevancy     | Low (0.0-0.5)      |       6 |      26.1 |
| Answer Relevancy     | Moderate (0.5-0.8) |      13 |      56.5 |
| Answer Relevancy     | High (0.8-1.0)     |       4 |      17.4 |
| Contextual Relevancy | Low (0.0-0.5)      |      23 |     100   |
| Contextual Relevancy | Moderate (0.5-0.8) |       0 |       0   |
| Contextual Relevancy | High (0.8-1.0)     |       0 |       0   |

## Breakdown by Category

| Category            |   Faithfulness |   Answer Relevancy |   Contextual Relevancy |   Retrieval Time (ms) |   Generation Time (ms) |   Total Time (ms) |   Response Length (words) |   Count |
|:--------------------|---------------:|-------------------:|-----------------------:|----------------------:|-----------------------:|------------------:|--------------------------:|--------:|
| Coverage            |          0.538 |              0.479 |                  0.073 |              1082.36  |                3455.95 |           5924.32 |                    19.75  |       8 |
| Claims              |          0.955 |              0.549 |                  0.045 |               831.448 |                3840.67 |           5363.57 |                    42.167 |       6 |
| Policy Information  |          0.75  |              0.458 |                  0     |               501.975 |                3575.85 |           4166.92 |                     8.25  |       4 |
| Vehicle Information |          0.85  |              0.625 |                  0     |              1147.28  |                2790.59 |           5498.49 |                     2.75  |       4 |
| Add-on              |          1     |              0.5   |                  0.25  |              1034.83  |                2630.87 |           5458.85 |                     7     |       1 |

## Breakdown by Difficulty

| Difficulty   |   Faithfulness |   Answer Relevancy |   Contextual Relevancy |   Retrieval Time (ms) |   Generation Time (ms) |   Total Time (ms) |   Response Length (words) |   Count |
|:-------------|---------------:|-------------------:|-----------------------:|----------------------:|-----------------------:|------------------:|--------------------------:|--------:|
| Easy         |          0.823 |              0.538 |                  0     |               998.017 |                3088.45 |           5307.02 |                    10.154 |      13 |
| Medium       |          0.775 |              0.5   |                  0.05  |               841.698 |                2790.1  |           4722.63 |                    22.6   |       5 |
| Hard         |          0.571 |              0.492 |                  0.171 |               819.338 |                4937.57 |           6218.39 |                    43.4   |       5 |

## Correlation (Length / Timing)

|                         |   Response Length (words) |   Generation Time (ms) |   Total Time (ms) |
|:------------------------|--------------------------:|-----------------------:|------------------:|
| Response Length (words) |                     1     |                  0.729 |             0.535 |
| Generation Time (ms)    |                     0.729 |                  1     |             0.5   |
| Total Time (ms)         |                     0.535 |                  0.5   |             1     |