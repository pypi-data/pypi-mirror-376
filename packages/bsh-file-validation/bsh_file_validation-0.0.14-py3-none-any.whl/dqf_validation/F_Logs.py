import json


class CommonLogs:
    def __init__(
        self,
        dbcon,
        source_name,
        dest_dl_layer,
        key,
        fnt_id,
        job_run_id,
        hierarchy_flag,
        file_template,
        spark1,
    ):
        """The constructor for UpdatingLogs class.

        Parameters:
           source_name(string)  : source system name of file.
           source_dl_layer (string): source file path.
           dest_dl_layer(string):destination file path.
           suc_path(string):Success file path.
           err_path(string):Error file path.
           sus_path(string):Suspense file path.
           fnt_id(string):Filename Template Id.
           job_run_id(string):Job Run Id.
           file_template(string):Filename Template.
        """
        self.key = key
        self.source_name = source_name
        self.fnt_attributes_master = {}

        self.dest_dl_layer = dest_dl_layer

        self.fnt_id = fnt_id
        self.job_run_id = job_run_id
        self.hierarchy_flag = hierarchy_flag
        self.file_template = file_template
        self.a = dbcon

        self.con = self.a.fn_get_connection()

    def fn_insert_delta_logs(
        self, file, job_id, pipeline_run_id, from_dl_layer, ref_tracking_ids=None
    ):
        """The function to insert T_file_delta logs.

        Parameters:
            file_id: File Id.
            job_id: Job run Id.
            pipeline_run_id: Pipeline run Id.
            fnt_id: Filename Template Id.
            from_dl_layer: From delta layer.
            from_dl_layer_path: From delta layer path.
            ref_tracking_ids: Reference tracking Id.
        """
        print("insert logs functions")
        print("in func", file)
        print(self.key)
        statement = f"""CALL sp_insert_t_file_deltas(@json_input:='{json.dumps(file)}',
                    @job_run_id:='{job_id}', @pipeline_run_id:='{pipeline_run_id}',
                    @from_dl_layer:='{from_dl_layer}',
                    @key_value:='{self.key}', @ref_tracking_ids:='{ref_tracking_ids}');"""
        print(statement)
        stmt = self.con.createStatement()
        stmt.executeQuery(statement)
        stmt.close()

    def fn_update_delta_logs_new(
        self,
        file,
        job_id,
        to_dl_layer,
        to_dl_layer_path,
        validation_status=None,
        copy_activity_status=None,
        validation_result=None,
        ref_tracking_ids=None,
    ):
        """The function to update delta logs.
        Args:
            file_id: File Id.
            job_id: Job run Id.
            fnt_id: Filename Template Id.
            to_dl_layer: To delta layer.
            to_dl_layer_path: To delta layer path.
            validation_status
            copy_activity_status
            validation_result
            ref_tracking_ids: Reference tracking Id.


        Returns:
            Returns result dict contains filename,fnt_id,file_id,file_path.
        """

        statement = f"""CALL sp_update_log_t_file_deltas_dqf_validation(
                    @tracking_id:='{job_id}-{self.fnt_id}',
                    @json_data:= '{json.dumps(file)}',
                    @to_dl_layer:='{to_dl_layer}',
                    @to_dl_layer_path:='{to_dl_layer_path}',
                    @validation_status:='{validation_status}',
                    @copy_Activity_status:='{copy_activity_status}',
                    @Business_Logic_Status:='None',
                    @validation_result:='{validation_result}',
                    @key_value:='{self.key}',
                    @ref_tracking_ids:='{ref_tracking_ids}')
                    """
        print(statement)
        stmt = self.con.createStatement()
        res = stmt.executeQuery(statement)
        print("error-----", res)
        # Close connections
        stmt.close()

    def fn_update_delta_logs_newcopy(
        self,
        file,
        job_id,
        to_dl_layer,
        validation_status=None,
        copy_activity_status=None,
        ref_tracking_ids=None,
    ):
        statement = f"""CALL sp_update_log_t_file_deltas_file_validation(
                    @tracking_id:='{job_id}-{str(self.fnt_id)}',
                    @json_data:='{json.dumps(file)}',
                    @to_dl_layer:='{to_dl_layer}',
                    @validation_status:='{validation_status}',
                    @copy_Activity_status:='{copy_activity_status}',
                    @Business_Logic_Status:='None',
                    @key_value:='{self.key}',
                    @ref_tracking_ids:='{ref_tracking_ids}')
                    """
        print(statement)
        stmt = self.con.createStatement()
        stmt.executeQuery(statement)
        stmt.close()

    def fn_add_alerts(self, fnt_id, alert_type, remarks, tracking_id, file_id):
        """The function to add alerts.

        Parameters:

            fnt_id: Filename Template Id.
            alert_type: Type of alerts.
            remarks: remarks for alert
        """
        print("Printing to resolve unused variable issue")
        print(file_id)
        print(tracking_id)

        print("trying to insert  to alerts")
        print("alert type", alert_type)
        print("fnt_id", fnt_id)
        print("remarks", remarks)
        statement = f"""CALL sp_alert_handler(
                    @Alert_validation_Type:='{alert_type}',
                    @FilenameTemplate_id:='{fnt_id}',
                    @remarks:='{remarks}',
                    @jobrunid:='{self.job_run_id}')
                    """
        print("Statement is ", statement)
        stmt = self.con.createStatement()
        stmt.executeQuery(statement)
        stmt.close()
