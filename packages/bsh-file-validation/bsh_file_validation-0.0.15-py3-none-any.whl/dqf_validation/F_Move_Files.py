import json
from pyspark.sql import DataFrame
from pyspark.sql import functions as func
from functools import reduce


class MoveFiles:
    def __init__(
        self,
        dbasecon,
        uf,
        config,
        source_dl_layer,
        dest_dl_layer,
        path,
        file_template,
        spark,
        fnt_id,
        dbwriter,
        source_system,
    ):
        self.dbcon = dbasecon

        self.config = config
        self.source_system = source_system
        self.dbname = "silver." + self.config["deltalake_configs"]["db_name"]
        self.tablename = self.config["deltalake_configs"]["tabel_name"]
        self.spark = spark
        self.schema = config["schema"]
        self.sc = self.spark.sparkContext
        self.schema_df = self.spark.read.json(
            self.sc.parallelize([json.dumps(self.schema)])
        )
        self.columns = (
            self.schema_df.filter("operation='column'")
            .rdd.map(lambda a: a["expected_columnname"])
            .collect()
        )
        self.source_dl_layer = source_dl_layer
        self.dest_dl_layer = dest_dl_layer
        self.path = path
        self.fnt_id = fnt_id
        self.dbasecon = uf
        self.file_template = file_template
        self.dbw = dbwriter
        self.DBFS_PREFIX = "dbfs:"

    def get_dbutils(self):
        try:
            from pyspark.dbutils import DBUtils

            dbutils = DBUtils(self.spark)
        except ImportError:
            import IPython

            dbutils = IPython.get_ipython().user_ns["dbutils"]
        return dbutils

    def fn_move_file(self, src_path, dest_path):
        dbutils = self.get_dbutils()
        print("src and dest are", src_path, dest_path)

        if src_path.startswith("/dbfs/"):
            actual_src_path = src_path.replace("/dbfs/", "dbfs:/")
        else:
            actual_src_path = self.DBFS_PREFIX + src_path

        if dest_path.startswith(self.DBFS_PREFIX):
            actual_dest_path = dest_path
        else:
            actual_dest_path = self.DBFS_PREFIX + dest_path

        dbutils.fs.mv(actual_src_path, actual_dest_path)
        return src_path, dest_path

    def fn_move_error_files(self, filepath, ref_tracking_id, file_id):
        dict_mv = {}
        src_path = filepath
        file = filepath[1]

        x = file.split("/")
        print("x is", x)
        filename = x[len(x) - 1]
        hie_folder = self.dbasecon.fn_put_datepartition()
        dest_reqpath = self.path["Bronze-Error"]
        dest_path = dest_reqpath + self.file_template + hie_folder + filename
        print("src and dest path are", src_path, dest_path)
        src_path, dest_path = self.fn_move_file(src_path[1], dest_path)
        print("File moved to error path")
        dict_mv["filename"] = filename
        dict_mv["dest_path"] = dest_path
        dict_mv["ref_tracking_id"] = ref_tracking_id
        dict_mv["file_id"] = file_id

        self.dbw.fn_add_alerts(
            self.fnt_id,
            "DQF_FAILURE_RECORDS",
            "The tracking id is " + (ref_tracking_id),
        )
        print("Error alerts updated successfully")
        return dict_mv

    def fn_consolidate_errors(self, baddf):
        print("keys are", baddf.keys())
        allkeys = [a + "_success" for a in baddf.keys()]
        allkeys.append("Column_success")
        newbaddf = {}
        for k, v in baddf.items():
            print("key is", k)
            missed = set(allkeys) - set(v.columns)
            print("missed is", missed)
            for val in missed:
                v = v.withColumn(val, func.lit(True))

            newbaddf[k] = v
            # print(newbaddf.count())
            print("after adding", v.columns)
            add_col = ["source_file", "tracking_id"]
        return reduce(
            DataFrame.unionByName,
            [
                a.select(sorted(self.columns + allkeys + add_col))
                for a in newbaddf.values()
            ],
        )

    def fn_move_baddf_silver(self, badrows_df, path, file_template, uf):
        print(uf)
        errpath = self.path["Silver-Error"]
        folder_date = self.dbasecon.fn_put_datepartition()
        print(folder_date)

        path1 = errpath + file_template
        badrows_df = badrows_df.select(
            [func.col(column).cast("string") for column in badrows_df.columns]
        )
        badrows_df.repartition(100).write.format("delta").mode("append").option(
            "path", path1
        ).option("overwriteSchema", "true").saveAsTable(
            self.dbname + "." + self.tablename + "_baddfdata"
        )
