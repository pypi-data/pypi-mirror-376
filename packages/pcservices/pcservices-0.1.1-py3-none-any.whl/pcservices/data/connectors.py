from pyspark.sql import SparkSession

class BigQuerySparkConnector:
    def __init__(
        self,
        app_name: str,
        materialization_project: str,
        materialization_dataset: str,
        bigquery_connector_version: str = "0.36.1",
        extra_configs: dict = None,
        local_mode: bool = True,  # Flag to skip GCS in local
    ):
        self.app_name = app_name
        self.materialization_project = materialization_project
        self.materialization_dataset = materialization_dataset
        self.bigquery_connector_version = bigquery_connector_version
        self.extra_configs = extra_configs or {}
        self.local_mode = local_mode
        self.spark = self._create_spark_session()

    def _create_spark_session(self) -> SparkSession:
        """Create and configure SparkSession for BigQuery."""
        jars = f"com.google.cloud.spark:spark-bigquery-with-dependencies_2.12:{self.bigquery_connector_version}"
        builder = (
            SparkSession.builder
            .appName(self.app_name)
            .config("spark.jars.packages", jars)
            .config("viewsEnabled", "true")
            .config("materializationProject", self.materialization_project)
            .config("materializationDataset", self.materialization_dataset)
        )
        # Extra configs
        for k, v in self.extra_configs.items():
            builder = builder.config(k, v)

        spark = builder.getOrCreate()
        spark.sparkContext.setCheckpointDir("/tmp")
        spark.sparkContext.setLogLevel("WARN")
        return spark

    def read_table(self, table: str):
        """Read a BigQuery table into Spark DataFrame."""
        return self.spark.read.format("bigquery").option("table", table).load()

    def write_table(self, df, table: str, mode: str = "overwrite", temporary_gcs_bucket: str = None):
        """Write a Spark DataFrame to BigQuery."""
        if self.local_mode:
            print(f"Skipping write_table in local mode: would write to {table}")
            return
        writer = df.write.format("bigquery").option("table", table).mode(mode)
        if temporary_gcs_bucket:
            writer = writer.option("temporaryGcsBucket", temporary_gcs_bucket)
        writer.save()

    def stop(self):
        self.spark.stop()