import json
from .F_Csv_Txt_Reader import CsvTxtDataReader
from .F_Json_Reader import JsonReader
from .F_Xml_Reader import XmlDataReader
from .F_Parquet_Reader import ParquetReader
from pyspark.sql.types import StringType, StructField, StructType
from pyspark.sql import functions as func
from .F_json_2reader import json2reader
from pyspark.sql.functions import input_file_name, col, concat, lit
from pyspark.sql.window import Window


class MasterData:
    def __init__(
        self,
        dbwrite,
        dbread,
        tracking_id,
        ref_tracking_ids,
        config,
        list_of_files,
        iot_flag,
        spark,
        mvfl,
        track_id,
    ):
        self.dbwrite = dbwrite
        self.dbread = dbread
        self.spark = spark
        self.track_id = track_id
        self.fnt_id = config["file_read_configs"]["fnt_id"]
        self.file_schema = config["file_read_configs"]["expected_schema"]
        self.mov = mvfl
        self.job_run_id = tracking_id
        self.ref_tracking_ids = ref_tracking_ids
        self.header = config["file_read_configs"]["is_header_present"]
        self.delimiter = config["file_read_configs"]["delimiter"]
        self.schema = config["schema"]
        self.repartition = config["file_read_configs"]["repartition"]
        self.iot_flag = iot_flag
        self.sc = self.spark.sparkContext
        self.schema_df = self.spark.read.json(
            self.sc.parallelize([json.dumps(self.schema)])
        )
        self.xmlroottag = config["file_read_configs"]["xmlroottag"]
        self.xmldetailstag = config["file_read_configs"]["xmldetailstag"]
        # print("schema_df is ",self.schema_df)
        self.list_of_files = list_of_files
        # print("list_of_files ",list_of_files)
        self.columns = (
            self.schema_df.filter("operation='column'")
            .rdd.map(lambda a: a["expected_columnname"])
            .collect()
        )
        print(self.columns)
        self.file_type = config["file_read_configs"]["file_type"]
        self.file_read_configs = config["file_read_configs"]
        self.csv_obj = CsvTxtDataReader(self.header, self.delimiter, self.spark)
        self.json_obj = JsonReader(self.schema_df, self.iot_flag)
        self.json_obj2 = json2reader(self.spark, self.sc)
        self.xml_obj = XmlDataReader(
            self.xmlroottag,
            self.xmldetailstag,
            self.file_schema,
            self.fnt_id,
            self.spark,
        )
        self.parquet_obj = ParquetReader(self.header, self.spark)
        self.function_mapper = {
            "jsondata_32": self.json_obj2.jsondata_32,
            "jsondata_55": self.json_obj2.jsondata_55,
            "jsondata_96": self.json_obj2.jsondata_96,
        }
        self.schema1 = StructType(
            [
                StructField("file_id", StringType(), True),
                StructField("filepath", StringType(), True),
            ]
        )
        self.id_path = self.spark.sparkContext.parallelize(self.list_of_files)

    def fn_read_files(self):
        dataframe = None
        print(dataframe)
        data = self.fn_masterdata()
        return data

    def fn_masterdata(self):
        expected_length = self.dbread.fn_get_no_columns_new(self.fnt_id)
        all_files = []
        dict_error = {}
        json_data = []
        error_data = []
        for file in self.list_of_files:
            all_files.append(file[1])
        print("all file paths are---", all_files)
        if self.file_type == "json":
            print("inside filereader at json function")
            tempdat = self.function_mapper[self.file_read_configs["data_func"]](
                all_files
            )
            print("data in temp data")
        elif self.file_type == "csv" or self.file_type == "txt":
            tempdat = self.csv_obj.fn_readcsv_txt(all_files)
        elif self.file_type == "xml":
            tempdat = self.xml_obj.fn_readxml(all_files)
        elif self.file_type == "parquet":
            tempdat = self.function_mapper_parq[self.file_read_configs["data_func"]](
                all_files
            )
        print("data in tempdata")

        # add source filename for each row
        print("temp dataframe is")
        tempdata1 = tempdat.withColumn("source_file", input_file_name())
        # replacing dbfs: with ''
        # tempdata1.show()
        tempdata1 = tempdata1.withColumn(
            "source_file", func.regexp_replace(col("source_file"), "dbfs:", "")
        )
        row_cnt = tempdata1.count()
        print("total rows", row_cnt)
        # aggregating row count for each source file
        tempdata2 = tempdata1.groupBy("source_file").agg(
            func.count("*").alias("row_cnt")
        )
        # extracting file name
        tempdata2 = tempdata2.withColumn(
            "filename", func.expr("reverse(split(source_file,'/'))[0]")
        )
        # creating new df based on file id and filepath
        id_path_df = self.spark.createDataFrame(self.id_path, self.schema1)
        # id_path_df.show()
        # tempdata2.show()
        # joining 2 dfs based on filepaths
        joined_df = tempdata2.join(
            id_path_df, tempdata2["source_file"] == id_path_df["filepath"], "inner"
        )
        print(joined_df)
        print("df is")
        print(self.list_of_files)
        # tempdata2.show()
        # id_path_df.show()
        # joined_df.show()
        # adding tracking id column for final dataframe
        final_tempdata = tempdata1.withColumn("Tracking_Id", lit(str(self.job_run_id)))
        final_df = final_tempdata
        rows = joined_df.collect()
        list_of_dicts = []
        for row in rows:
            dict_row = row.asDict()
            list_of_dicts.append(dict_row)
        print("list_of_dicts info:", list_of_dicts)
        for i in list_of_dicts:
            dict_data = {}
            dict_data["filename"] = i["filename"]
            dict_data["row_cnt"] = i["row_cnt"]
            dict_data["file_id"] = i["file_id"]
            json_data.append(dict_data)
        print("json_data", json_data)
        self.dbwrite.fn_update_row_cnt_new(json_data)
        dict_error["ref_tracking_ids"] = self.ref_tracking_ids
        dict_error["error_row_cnt"] = 0
        dict_error["expected_length"] = expected_length
        dict_error["tracking_id"] = self.track_id
        error_data.append(dict_error)
        print("error_data", error_data)
        self.dbwrite.fn_update_error_row_cnt_new(error_data)
        final_df.persist()
        return final_df
