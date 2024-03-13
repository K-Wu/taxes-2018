To obtain graphhql and trade_series data, do the following steps.
1. Click on an asset you own, e.g., "十年如一". The URL should be something like https://qieman.com/assets/XXXXXXXXXXXXXX
2. Monitor the network pane in developer mode.
3. Click the range you want to inspect, e.g., "近一年"
4. graphhql of the asset, graphhql of the benchmark, e.g., 沪深300, and trade_series will show up as network responses.
5. txnDay in entry of trade_series is UNIX epoch timestamp in milliseconds. Reference: https://www.epochconverter.com/

To convert UNIX epoch timestamp in milliseconds to human readable time, use the following Python code.
```
import pendulum
pendulum.from_timestamp(1236472051807/1000.0,tz='America/Toronto')
```
Reference: https://stackoverflow.com/a/67067503/5555077
