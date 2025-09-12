from typing import Any, Dict

from databricks.connect import DatabricksSession

from calista.engines.spark import SparkEngine


class DatabricksEngine(SparkEngine):

    def __init__(self, config: Dict[str, Any] = None):
        self.spark = DatabricksSession.builder.remote(
            host=config["host"],
            token=config["token"],
            cluster_id=config["cluster_id"]
        ).getOrCreate()
        self.dataset = None
        self._config = config


if __name__ == "__main__":

    config = {
        "token": "dapi268c1cbb2386ec4e83e1e3ae9d91151e",
        "host": "https://adb-1130861814770890.10.azuredatabricks.net",
        "cluster_id": "0716-124431-zmhs5gnt"
    }

    spark = DatabricksEngine(config).spark
    spark.range(10).show()