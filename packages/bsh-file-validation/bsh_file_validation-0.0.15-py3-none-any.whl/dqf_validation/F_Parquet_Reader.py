from pyspark.sql.functions import explode_outer, col
import pyspark.sql.functions as sf


class ParquetReader:
    def __init__(self, header, spark):
        self.header = header
        self.spark = spark
        self.FILE_PATH_MESSAGE = "file path is"

    def flatten_df(self, nested_df):
        flat_cols = [c[0] for c in nested_df.dtypes if not c[1].startswith("struct")]
        nested_cols = [c[0] for c in nested_df.dtypes if c[1].startswith("struct")]
        flat_df = nested_df.select(
            flat_cols
            + [
                sf.col(nc + "." + c).alias(nc + "_" + c)
                for nc in nested_cols
                for c in nested_df.select(nc + ".*").columns
            ]
        )
        return flat_df

    def fn_read_parquet(self, filepath):
        header = "true" if self.header else "false"
        print("header is", header)
        print(self.FILE_PATH_MESSAGE, filepath)
        data = self.spark.read.parquet(*filepath)
        return data

    def api_1_109(self, filepath):
        print(self.FILE_PATH_MESSAGE, filepath)
        data = self.spark.read.parquet(*filepath)
        return data

    def api_3_112(self, filepath):
        print(self.FILE_PATH_MESSAGE, filepath)
        data = self.spark.read.parquet(*filepath)
        data1 = data.withColumn("counties", explode_outer(data.counties)).withColumn(
            "types", explode_outer(data.types)
        )
        return data1

    def api_6_114(self, filepath):
        print(self.FILE_PATH_MESSAGE, filepath)
        data = self.spark.read.parquet(*filepath)
        data1 = data.withColumn("exp", explode_outer(data.exp))
        return data1

    def api_9_116(self, filepath):
        print(self.FILE_PATH_MESSAGE, filepath)
        data = self.spark.read.parquet(*filepath)
        data1 = data.withColumn("images", explode_outer(data.images))
        data2 = self.flatten_df(data1)
        return data2

    def api_8_117(self, filepath):
        print(self.FILE_PATH_MESSAGE, filepath)
        data = self.spark.read.parquet(*filepath)
        data2 = (
            data.selectExpr("*", "explode(holidays)")
            .select("*", "col.*")
            .drop("holidays", "col")
        )
        data2 = data2.withColumn("type", explode_outer(col("type")))
        data2 = self.flatten_df(data2)
        data2 = self.flatten_df(data2)
        return data2
