import uuid
import json
import pandas as pd
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import lit, current_timestamp

# from .f_utility_functions import UtilityFunction as utf
# from .f_db_reader import Dbreader
# from .f_db_writers import Dbwriters
# from .f_db_config_reader import DBConfigReaders
# from .f_delta_table_load import DeltaTableLoad
# from .f_move_files import MoveFiles
# from .f_attribute_validator4 import AttributeValidator
# from .f_file_reader import MasterData
# from .f_data_masking import DataMasking
# from .f_database_connect import DBConnection
# from .f_logs import CommonLogs
# from . import f_scope_util

from .F_Utility_Functions import UtilityFunction as utf
from .F_DB_Reader import Dbreader
from .F_DB_Writers import Dbwriters
from .F_DB_Config_Reader import DBConfigReaders
from .F_Delta_Table_Load import DeltaTableLoad
from .F_Move_Files import MoveFiles
from .F_Attribute_Validator4 import AttributeValidator
from .F_File_Reader import MasterData
from .F_Data_Masking import DataMasking
from .F_Database_Connect import DBConnection
from .F_Logs import CommonLogs
from . import F_Scope_Util




class DQFValidation:

    def __init__(self, SourceSystem, HierarchyFlag, IOTFlag, FNT_ID, FileTemplate) -> None:
        self.SourceSystem = SourceSystem
        self.HierarchyFlag = HierarchyFlag
        self.IOTFlag = IOTFlag
        self.FNT_ID = FNT_ID
        self.FileTemplate = FileTemplate

    def validate(self):
        job_run_id = str(uuid.uuid4())
        pipeline_run_id = str(uuid.uuid4())
        curr_try = "1"

        # Start Spark session
        spark1 = SparkSession.builder.appName("dqf-validation").getOrCreate()

        # Get DB connection details from secrets
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
        con = dbasecon.fn_get_connection()

        source_dl_layer = "Bronze"
        dest_dl_layer = "Silver"
        dbread = Dbreader(con)
        dbwrite = Dbwriters(con)

        dbwriter = CommonLogs(
            dbasecon,
            source_name=self.SourceSystem,
            dest_dl_layer=dest_dl_layer,
            key="DQFValidation",
            fnt_id=self.FNT_ID,
            job_run_id=job_run_id,
            hierarchy_flag=self.HierarchyFlag,
            file_template=self.FileTemplate,
            spark1=spark1,
        )

        # Get list of files for DQF validation
        list_of_batches = dbread.fn_get_files_for_dqf(self.FNT_ID)
        configreader = DBConfigReaders(
            con, self.FNT_ID, source_dl_layer, dest_dl_layer, self.SourceSystem
        )
        config_dict = configreader.getall_configs()
        uf = utf(con, source_dl_layer, dest_dl_layer, self.SourceSystem)
        path = config_dict["path"]

        mv = MoveFiles(
            dbwrite,
            uf,
            config_dict,
            source_dl_layer,
            dest_dl_layer,
            path,
            self.FileTemplate,
            spark1,
            self.FNT_ID,
            dbwriter,
            self.SourceSystem,
        )

        if len(list_of_batches) > 0:
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
        else:
            batches_files = {}

        for key, value in batches_files.items():
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

            fnt_info = config_dict["file_read_configs"]
            file_type = fnt_info["file_type"]

            if file_type in ["csv", "txt", "json", "xml", "parquet"]:
                act_temp_file_path = path["Bronze-Cache"]
                track_id = job_run_id + "-" + key
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
                    self.IOTFlag,
                    spark1,
                    mv,
                    track_id,
                )
                data = msdata.fn_read_files()
            else:
                data = None

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
                gooddf_count = baddf_count = error_df_count = 0

            elif not DQF_Check:
                gooddf_count = data.count()
                data1 = uf.fn_addindex(data)
                gooddf = data1
                baddf_count = error_df_count = 0

            else:
                data = uf.fn_addindex(data)
                baddf, gooddf, error_df = av.fn_getattributes_validation(data)
                gooddf_count = gooddf.count()
                baddf_count = baddf.count()
                error_df_count = error_df.count()

            if error_df_count > 0:
                error_df = error_df.withColumn("tracking_id", lit(job_run_id))
                error_df = error_df.withColumn("batchId", lit(-1))
                error_df = error_df.withColumn("curr_time", current_timestamp())
                error_df.write.format("jdbc").option("url", con.url).option(
                    "dbtable", "T_LOG_error_reason_data"
                ).option("user", con.username).option("password", con.password).mode(
                    "append"
                ).save()

            if baddf_count > 0:
                mv.fn_move_baddf_silver(baddf, path, self.FileTemplate, uf)
                keycolumn = config_dict["deltalake_configs"]["KeyColumns"]
                dbwriter.fn_add_alerts(
                    key, "DQF_FAILURE_RECORDS", "", job_run_id + "-" + self.FNT_ID, ""
                )

            if gooddf_count > 0:
                act_target_path = path["Silver-Success"]
                targetpath = act_target_path + self.FileTemplate
                masking = DataMasking(gooddf, config_dict, spark1)
                maskdf = masking.data_mask()
                deltaload = DeltaTableLoad(config_dict, targetpath, maskdf, spark1)
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

            expected_rows = dbread.fn_get_no_rows(ref_tracking_ids[key], key)
            dbwrite.fn_insert_delta_summary_logs(
                ref_tracking_ids[key], expected_rows, gooddf_count, baddf_count, job_run_id + "-" + key
            )
