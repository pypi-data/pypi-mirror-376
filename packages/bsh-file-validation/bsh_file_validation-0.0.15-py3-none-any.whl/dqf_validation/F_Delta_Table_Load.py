from delta.tables import DeltaTable
import pyspark.sql.functions as F
from pyspark.sql import Window
from pyspark.sql.functions import spark_partition_id, asc, desc
from pyspark.sql import SparkSession


class DeltaTableLoad:
    def __init__(self, config, targetpath, gooddf, spark):
        self.targetpath = targetpath
        self.databasename = "datanexus_dev_catalog.silver"
        print(self.databasename)
        self.tablename = config["deltalake_configs"]["db_name"] + "_" + config["deltalake_configs"]["tabel_name"]
        print(self.tablename)

        # print ("self.partition is ",self.partition)
        self.mod_df = gooddf.withColumn("current_time", F.current_timestamp())
        self.db_load_type = config["deltalake_configs"]["db_load_type"]
        self.duplicate_check = config["dqf_needed"]["duplicate_check_needed"]
        print("Duplicate check value ", self.duplicate_check)
        self.spark = spark
        self.configs = config["deltalake_configs"]
        self.fnt_id = config["file_read_configs"]["fnt_id"]
        self.scd_enabled = config["file_read_configs"]["scd_enabled"]
        if (
            self.configs["key_columns"] is not None
            and self.configs["key_columns"] != ""
        ):
            self.key = self.configs["key_columns"].split(",")
        else:
            self.key = None
        if (
            self.configs["partition_columns"] is not None
            and self.configs["partition_columns"] != ""
        ):
            self.partitioncolumn = self.configs["partition_columns"].split(",")
        else:
            self.partitioncolumn = None
            print("partitioncolumn is ", self.partitioncolumn)
        if (
            self.configs["watermark_columns"] is not None
            and self.configs["watermark_columns"] != ""
        ):
            self.watermark_columns = self.configs["watermark_columns"].split(",")
        else:
            self.watermark_columns = None
        if self.configs["scd_column"] is not None and self.configs["scd_column"] != "":
            self.scdcolumn = self.configs["scd_column"].split(",")
        else:
            self.scdcolumn = None

    def fn_get_key(self):
        key = ""
        for i in range(len(self.key)):
            if len(self.key) == 1 or i == len(self.key) - 1:
                key += "d." + self.key[i] + " = " + "dt." + self.key[i]
            else:
                key += "d." + self.key[i] + " = " + "dt." + self.key[i] + " and "
        print(key)
        return key

    def fn_get_scd_key(self):
        key = ""
        for i in range(len(self.scdcolumn)):
            if len(self.scdcolumn) == 1 or i == len(self.scdcolumn) - 1:
                key += "d." + self.scdcolumn[i] + " != " + "dt." + self.scdcolumn[i]
            else:
                key += (
                    "d."
                    + self.scdcolumn[i]
                    + " != "
                    + "dt."
                    + self.scdcolumn[i]
                    + " or "
                )
        print(key)
        return "(" + key + ")"

    def fn_delta_load_append(self):
        cols = ["Source_file", "Tracking_Id", "Id", "column_success", "current_time"]
        self.mod_df = self.mod_df.drop(*cols)
        if self.partitioncolumn is None:
            print("append load without partioning is to be done")
            print("insde  append load")
            self.mod_df.show()
            self.mod_df.printSchema()
            print(self.targetpath)
            print(self.databasename + "." + self.tablename)
            self.mod_df.write.format("delta").mode("append").option(
                "path", self.targetpath
            ).saveAsTable(self.databasename + "." + self.tablename)
        else:
            print("append load with partioning is to be done")

            self.mod_df.repartition(*self.partitioncolumn).write.format(
                "delta"
            ).partitionBy(self.partitioncolumn).mode("append").option(
                "path", self.targetpath
            ).saveAsTable(
                self.databasename + "." + self.tablename
            )

        # print("delta table appended successfully")
        load_stats = self.fn_get_stats()
        return load_stats

    def fn_delta_load_full(self):
        cols = ["Source_file", "Tracking_Id", "id", "column_success", "current_time"]
        self.mod_df = self.mod_df.drop(*cols)
        print("insde full load")
        if self.partitioncolumn is None:
            print("Full load without partioning is to be done")
            self.mod_df.write.format("delta").mode("overwrite").saveAsTable(
                self.databasename + "." + self.tablename
            )
        else:
            print("Full load with partioning is to be done")
            self.mod_df.repartition(*self.partitioncolumn).write.format(
                "delta"
            ).partitionBy(self.partitioncolumn).mode("overwrite").saveAsTable(
                self.databasename + "." + self.tablename
            )
        """
        self.mod_df.repartition('state','currency_code').write.format("delta").partitionBy('state','currency_code').mode("overwrite")\
                            .option("path",self.targetpath).saveAsTable(self.databasename+'.'+self.tablename)
        """
        load_stats = self.fn_get_stats()
        return load_stats

    def fn_delta_load_merge(self):
        key = self.fn_get_key()

        temp_table = "newtesttable" + self.fnt_id
        self.mod_df.createOrReplaceGlobalTempView(temp_table)
        app = SparkSession.builder.getOrCreate()  # noqa: F821
        print(app.__dict__)
        # self.mod_df.show()
        self.spark.sql("show tables in  default").show()

        # df.show()
        col_query = f"show columns from {self.databasename}.{self.tablename}"
        df_cols = self.spark.sql(col_query)
        py_list = df_cols.select("col_name").toPandas()["col_name"].tolist()
        print("py_list is ", py_list)
        # py_list.remove('current_time')
        update_qry = ",".join(
            [
                f"d.{a}=dt.{a}"
                for a in py_list
                if a
                not in [
                    "created_time",
                    "modified_time",
                    "start_date",
                    "end_date",
                    "current_status",
                ]
            ]
        )

        print("update_qry ", update_qry)
        insert_qry_colpart = ",".join(
            [
                f"{a}"
                for a in py_list
                if a
                not in [
                    "created_time",
                    "modified_time",
                    "start_date",
                    "end_date",
                    "current_status",
                ]
            ]
        )
        insert_qry_colpart = (
            insert_qry_colpart
            + ","
            + "start_date"
            + ","
            + "end_date"
            + ","
            + "current_status"
        )
        insert_qry_valpart = ",".join(
            [
                f"dt.{a}"
                for a in py_list
                if a
                not in [
                    "created_time",
                    "modified_time",
                    "start_date",
                    "end_date",
                    "current_status",
                ]
            ]
        )
        insert_qry_valpart = (
            insert_qry_valpart + "," + "current_timestamp()" + "," + "null" + "," + "1"
        )
        update_scd_qry = "d.end_date=current_timestamp(),current_status=0"

        unique_key = self.key[0]
        print(self.scd_enabled)
        if self.scd_enabled == 1:
            scd_key = self.fn_get_scd_key()
            full_qry = f"MERGE INTO {self.databasename}.{self.tablename} d USING \
                ( select {unique_key} as mergekey,* from global_temp.{temp_table} \
                     union all\
                     select null as mergekey,d.* from  global_temp.{temp_table} d \
                        join {self.databasename}.{self.tablename} dt on {key} and {scd_key} and\
                     current_status=1)dt \
                        ON d.{unique_key}=dt.mergekey \
                        WHEN MATCHED AND {scd_key} then\
                        update set {update_scd_qry}\
                        WHEN MATCHED AND CURRENT_STATUS=1 THEN \
                          UPDATE SET {update_qry} \
                        WHEN NOT MATCHED \
                          THEN INSERT ({insert_qry_colpart}) VALUES ({insert_qry_valpart}) \
                        "
        else:
            full_qry = f"MERGE INTO {self.databasename}.{self.tablename} d USING global_temp.{temp_table} dt \
                        ON {key} \
                        WHEN MATCHED THEN \
                          UPDATE SET {update_qry} \
                        WHEN NOT MATCHED \
                          THEN INSERT ({insert_qry_colpart}) VALUES ({insert_qry_valpart}) \
                        "

        print("complete qry is", full_qry)
        self.spark.sql(full_qry)
        load_stats = self.fn_get_stats()
        return load_stats

    def fn_delta_load(self):
        print("inside inc load")
        self.spark.sql("SET spark.databricks.delta.schema.autoMerge.enabled=true")

        if self.db_load_type == "append":
            print("calliing append function")
            deltaload_append = self.fn_delta_load_append()
            print("completed append load type")
            print(deltaload_append)
        elif self.db_load_type == "full":
            deltaload_full = self.fn_delta_load_full()
            print(deltaload_full)
        else:
            deltaload_merge = self.fn_delta_load_merge()
            print(deltaload_merge)
            print("Delta table incremental load completed")

    def table_load(self):
        # self.fn_retain_latest_of_duplicates()
        print(
            "does table exist",
            self.spark._jsparkSession.catalog().tableExists(
                f"{self.databasename}.{self.tablename}"
            ),
        )
        if self.spark._jsparkSession.catalog().tableExists(
            f"{self.databasename}.{self.tablename}"
        ):
            self.fn_delta_load()
        else:
            print("Delta Table does not exist")

    def fn_get_stats(self):
        print(f"inside merge stats {self.databasename}.{self.tablename}")

        deltatable = DeltaTable.forName(
            self.spark, f"{self.databasename}.{self.tablename}"
        )

        stats = deltatable.history(1)
        ls = stats.select(F.col("operationMetrics")).collect()

        # print(s)
        print("listrr-----", ls)
        return {
            a: b.strip()
            for a, b in ls[0][0].items()
            if a
            in [
                "numOutputRows",
                "numTargetRowsInserted",
                "numTargetRowsUpdated",
                "numTargetRowsDeleted",
            ]
        }
        # self.fn_one_time_load()
