# Databricks notebook source
# MAGIC %reload_ext autoreload
# MAGIC %autoreload 2

# COMMAND ----------

# Use the below cell for manual testing
data = {
    "current_try": "1",
    "filename_template": "unity_file",
    "fnt_id": "1011",
    "hierarchy_flag": "None",
    "iot_flag": "None",
    "job_run_id": "dq-job-dec18-4",
    "pipeline_run_id": "dq-pipeline-dec18-4",
    "source_system_name": "ClientPortal",
}

job_run_id = data["job_run_id"]
pipeline_run_id = data["pipeline_run_id"]
source_system = data["source_system_name"]
hierarchy_flag = data["hierarchy_flag"]
iot_flag = data["iot_flag"]
fnt_id = data["fnt_id"]
file_template = data["filename_template"]
curr_try = data["current_try"]

print(job_run_id)
print(pipeline_run_id)

# COMMAND ----------

# # Use the below cell for pipeline testing
# job_run_id = dbutils.widgets.get("job_run_id")
# pipeline_run_id = dbutils.widgets.get("pipeline_run_id")
# source_system = dbutils.widgets.get("sourcesystem_name")
# file_template = dbutils.widgets.get("filename_template")
# fnt_id = dbutils.widgets.get("fnt_id")
# iot_flag = dbutils.widgets.get("iot_flag")
# hierarchy_flag = dbutils.widgets.get("hierarchy_flag")
# curr_try = dbutils.widgets.get("current_try")


# COMMAND ----------

# # # Use the below cell for workflow testing
# job_run_id = dbutils.jobs.taskValues.get(taskKey="FileValidationChecks", key="job_run_id")
# pipeline_run_id = dbutils.jobs.taskValues.get(taskKey="FileValidationChecks", key="pipeline_run_id")
# source_system = dbutils.jobs.taskValues.get(taskKey="FileValidationChecks", key="source_system")
# file_template = dbutils.jobs.taskValues.get(taskKey="FileValidationChecks", key="file_template")
# fnt_id = dbutils.jobs.taskValues.get(taskKey="FileValidationChecks", key="fnt_id")
# iot_flag = dbutils.jobs.taskValues.get(taskKey="FileValidationChecks", key="iot_flag")
# hierarchy_flag = dbutils.jobs.taskValues.get(taskKey="FileValidationChecks", key="hierarchy_flag")
# curr_try = dbutils.jobs.taskValues.get(taskKey="FileValidationChecks", key="current_try")


# COMMAND ----------

import pandas as pd
from pyspark.sql.functions import spark_partition_id, asc, desc
from pyspark.sql.types import (
    StringType,
    StructField,
    StructType,
    LongType,
    DecimalType,
    DateType,
    TimestampType,
    FloatType,
    BooleanType,
)
from pyspark.sql import functions as func
from functools import reduce  # For Python 3.x
from pyspark.sql import DataFrame, SparkSession
import operator

# COMMAND ----------

from F_Utility_Functions import UtilityFunction as utf
from F_DB_Reader import Dbreader
from F_DB_Writers import Dbwriters
from F_DB_Config_Reader import DBConfigReaders
from F_Delta_Table_Load import DeltaTableLoad
from F_Move_Files import MoveFiles
from F_Attribute_Validator4 import AttributeValidator
from F_File_Reader import MasterData
from F_Data_Masking import DataMasking
from common_functions.F_Database_Connect import DBConnection
from common_functions.F_Logs import CommonLogs
from common_functions import F_Scope_Util

# COMMAND ----------

# This part is specific to AWS
# Keeping same variable names "dbcon" and "spark1" to match with Azure code

spark1 = SparkSession.builder.appName("integrity-tests").getOrCreate()

# Get the values from databricks secrets
eda_scope = "eda-qa"
key_list = [
    "rds_mysql_host",
    "rds_mysql_db",
    "rds_mysql_username",
    "rds_mysql_password",
]
db_server, db_name, db_user, db_password = F_Scope_Util.get_values_from_secrets_scope(
    eda_scope, key_list
)

# Get MySQL connection object
dbasecon = DBConnection(spark1, db_server, db_name, db_user, db_password)
conn = dbasecon.fn_get_connection()

# COMMAND ----------

# # Added by Keerthana
# # These SPs are part of pipeline, moving it to notebook as it does the same thing, and comparatively more efficient.
# statement = f"""CALL sp_insert_job_statistics(
#                 @pipelinename:='Bronze_to_Silver',
#                 @status:='Started',
#                 @job_run_id:='{job_run_id}',
#                 @error_message:='Some error occurred',
#                 @fnt_id:='{fnt_id}',
#                 @curr_try:='{curr_try}');
#             """
# print(statement)
# stmt = conn.createStatement()
# stmt.executeQuery(statement)

# statement = f"""CALL sp_update_pipeline_run_id(
#                 @p_job_run_id:='{job_run_id}',
#                 @p_pipeline_run_id:='{pipeline_run_id}')
#             """
# print(statement)
# stmt = conn.createStatement()
# stmt.executeQuery(statement)

# COMMAND ----------

bbaddf = None
gooddf = None
attributes = None
spark.conf.set("spark.sql.legacy.timeParserPolicy", "EXCEPTION")
spark.conf.set("spark.sql.shuffle.partitions", "auto")

source_dl_layer = "Bronze"
dest_dl_layer = "Silver"
con = dbasecon.fn_get_connection()
dbread = Dbreader(con)
dbwrite = Dbwriters(con)

dbwriter = CommonLogs(
    dbasecon,
    source_name=source_system,
    dest_dl_layer=dest_dl_layer,
    key="DQFValidation",
    fnt_id=fnt_id,
    job_run_id=job_run_id,
    hierarchy_flag=hierarchy_flag,
    file_template=file_template,
    spark1=spark1,
)
print(dbwriter)

# COMMAND ----------

list_of_batches = dbread.fn_get_files_for_dqf(fnt_id)
print("list_of_batches ", list_of_batches)
configreader = DBConfigReaders(
    con, fnt_id, source_dl_layer, dest_dl_layer, source_system
)
config_dict = configreader.getall_configs()
uf = utf(con, source_dl_layer, dest_dl_layer, source_system)
path = config_dict["path"]
badrowscount = 0
print("configs are-----------------------", config_dict)
mv = MoveFiles(
    dbwrite,
    uf,
    config_dict,
    source_dl_layer,
    dest_dl_layer,
    path,
    file_template,
    spark1,
    fnt_id,
    dbwriter,
    source_system,
)

if len(list_of_batches) > 0:
    # Updated by Keerthana
    batches_files = (
        pd.DataFrame.from_records(list_of_batches)
        .groupby(["fnt_id"])[["file_id", "to_dl_layer"]]
        .apply(lambda g: g.values.tolist())
        .to_dict()
    )
    ref_tracking_ids_temp = (
        pd.DataFrame.from_records(list_of_batches)
        .groupby(["fnt_id"])["tracking_id"]
        .apply(lambda g: set(g.values.tolist()))
        .to_dict()
    )
    ref_tracking_ids = {
        a: "|".join([c for c in b]) for a, b in ref_tracking_ids_temp.items()
    }
    print("ref tracking ids are", ref_tracking_ids)
else:
    batches_files = {}
print("batches_files", batches_files)
for key, value in batches_files.items():
    print("key is", key)
    print("value is", value)
    check = config_dict["dqf_needed"]
    DQF_Check = check["dqf_needed"]
    duplicate_check = check["duplicate_check_needed"]
    act_from_dl_layer_path = path["Bronze-Success"]
    json1 = {"file_id": 0, "filepath": act_from_dl_layer_path, "fnt_id": key}

    dbwriter.fn_insert_delta_logs(
        file=json1,
        job_id=job_run_id,
        pipeline_run_id=pipeline_run_id,
        from_dl_layer=source_dl_layer,
        ref_tracking_ids=ref_tracking_ids[key],
    )

    print("DQF_Needed value is ", DQF_Check)
    fnt_info = config_dict["file_read_configs"]
    file_type = fnt_info["file_type"]
    print("file_type is", file_type)
    if (
        file_type == "csv"
        or file_type == "txt"
        or file_type == "json"
        or file_type == "xml"
        or file_type == "parquet"
    ):
        act_temp_file_path = path["Bronze-Cache"]
        print("temp_file_path ", act_temp_file_path)
        track_id = job_run_id + "-" + key
        print("DQF tracking id", track_id)
        av = AttributeValidator(
            config=config_dict,
            temp_file_path=act_temp_file_path,
            temp_file_name=job_run_id + "_" + key,
            spark=spark1,
            job_run_id=job_run_id,
        )
        msdata = MasterData(
            dbwrite,
            dbread,
            job_run_id,
            ref_tracking_ids[key],
            config_dict,
            value,
            iot_flag,
            spark1,
            mv,
            track_id,
        )
        data = msdata.fn_read_files()

        data.printSchema()
        display(data)
        print("final df in dqf notebook")
    if data is None:
        act_to_dl_layer_path = path["Bronze-Error"]

        json3 = {"file_id": 0, "filepath": act_to_dl_layer_path, "fnt_id": key}
        dbwriter.fn_update_delta_logs_new(
            file=json3,
            job_id=job_run_id,
            to_dl_layer=source_dl_layer,
            to_dl_layer_path=act_to_dl_layer_path,
            validation_status="completed",
            ref_tracking_ids=ref_tracking_ids[key],
        )
        print("Delta logs are updated for error file")
        gooddf_count = 0
        baddf_count = 0
        error_df_count = 0

    elif not DQF_Check:
        print("dqf not needed")
        print("after repartition")
        gooddf_count = data.count()
        print("good data count", gooddf_count)
        print("adding index column to df")
        data1 = uf.fn_addindex(data)
        gooddf = data1
        baddf_count = 0
        error_df_count = 0
        badrowscount = 0
        print("last stmt of elif loop")
    else:
        data = uf.fn_addindex(data)
        print("data")
        print("count of data")
        print("schema of data is", data.schema)
        baddf, gooddf, error_df = av.fn_getattributes_validation(data)
        gooddf.printSchema()
        gooddf_count = gooddf.count()
        print("count of gooddf is ", gooddf_count)

        baddf_count = baddf.count()
        error_df_count = error_df.count()
        print("count of badddf is ", baddf_count)

    if error_df_count > 0:
        print("error data count is greater than 0")
        error_df = error_df.withColumn("tracking_id", lit(job_run_id))
        error_df = error_df.withColumn("batchId", lit(-1))
        error_df = error_df.withColumn("curr_time", current_timestamp())
        error_df.write.format("jdbc").option("url", url).option(
            "dbtable", "T_LOG_error_reason_data"
        ).option("user", sqlusername).option("password", sqlPassword).mode(
            "append"
        ).save()
    if baddf_count > 0:
        print("baddf count is grrater than 0")
        display(baddf)
        mv.fn_move_baddf_silver(baddf, path, file_template, uf)
        keycolumn = config_dict["deltalake_configs"]["KeyColumns"]
        dbwriter.fn_add_alerts(
            key, "DQF_FAILURE_RECORDS", "", job_run_id + "-" + fnt_id, ""
        )
    if gooddf_count > 0:
        print("gooddf count is greater than 0")
        print(path)
        act_target_path = path["Silver-Success"]
        targetpath = act_target_path + file_template
        print("targetpath ", targetpath)
        print("calling the delta lake function here")
        masking = DataMasking(gooddf, config_dict, spark1)
        print("masking obj is created")
        maskdf = masking.data_mask()
        maskdf = gooddf
        print("masking completed")
        deltaload = DeltaTableLoad(config_dict, targetpath, maskdf, spark1)
        print("obj for deltaload created and calling table_load func")
        deltaload.table_load()
    act_to_dl_layer_path = path["Silver-Success"]
    json2 = {"file_id": 0, "filepath": act_to_dl_layer_path, "fnt_id": key}
    dbwriter.fn_update_delta_logs_new(
        file=json2,
        job_id=job_run_id,
        to_dl_layer=dest_dl_layer,
        to_dl_layer_path=act_to_dl_layer_path,
        validation_status="completed",
        copy_activity_status="completed",
        ref_tracking_ids=ref_tracking_ids[key],
    )
    print("updated status for good df")
    # For reconciliation logs
    expected_rows = dbread.fn_get_no_rows(ref_tracking_ids[key], key)
    print("expected_rows", expected_rows)
    print(badrowscount)
    dbwrite.fn_insert_delta_summary_logs(
        ref_tracking_ids[key], expected_rows, gooddf_count, baddf_count, track_id
    )

# COMMAND ----------

spark._jsparkSession.catalog().tableExists("datanexus_dev_catalog.silver"+'.'+"clientportal_t_unity_file")