class DBConfigReaders:
    VOLUMES_PATH = "/Volumes/datanexus_dev_catalog/"

    def __init__(self, dbcon, fnt_id, source_dl_layer, dest_dl_layer, sourcename):
        self.con = dbcon
        self.fnt_id = fnt_id
        self.source_dl_layer = source_dl_layer
        self.dest_dl_layer = dest_dl_layer
        self.source_name = sourcename
        

    def fn_get_schema(self):
        statement = f"""CALL sp_get_schema_details(@fnt_id:='{self.fnt_id}')"""
        print(statement)
        stmt = self.con.createStatement()
        result_set = stmt.executeQuery(statement)
        # print(res)
        results = []
        while result_set.next():
            vals = {}
            vals["expected_columnname"] = result_set.getString("expected_columnname")
            vals["expected_datatype"] = result_set.getString("expected_datatype")
            vals["expected_length"] = result_set.getString("expected_length")
            vals["expected_precision"] = result_set.getInt("expected_precision")
            vals["expected_unit"] = result_set.getString("expected_unit")
            vals["expected_type"] = result_set.getString("expected_type")
            vals["expected_scale"] = result_set.getInt("expected_scale")
            vals["is_nullable"] = result_set.getString("is_nullable")
            vals["is_unique"] = result_set.getString("is_unique")
            vals["operation"] = result_set.getString("operation")
            vals["query"] = result_set.getString("query")
            vals["is_mandatory_column"] = result_set.getString("is_mandatory_column")
            vals["expected_datetimeformat"] = result_set.getString(
                "expected_datetimeformat"
            )
            vals["expected_regex"] = result_set.getString("expected_regex")
            vals["expected_startvalue"] = result_set.getString("expected_startvalue")
            vals["expected_endvalue"] = result_set.getString("expected_endvalue")
            vals["is_maskable"] = result_set.getString("is_maskable")
            vals["mask_value"] = result_set.getString("mask_value")
            vals["group_no"] = result_set.getString("group_no")
            results.append(vals)
        return results

    def fn_get_list_of_attributes(self):
        statement = (
            f"""CALL sp_get_mapped_schema_attributes(@fnt_id:= {self.fnt_id})"""
        )
        print(statement)
        stmt = self.con.createStatement()
        result_set = stmt.executeQuery(statement)
        result_dict = []
        while result_set.next():
            vals = {}
            vals["file_attribute_name"] = result_set.getString("file_attribute_name")
            vals["validation_needed"] = result_set.getBoolean("validation_needed")
            vals["validation_type"] = result_set.getString("validation_type")
            vals["value_data_type"] = result_set.getString("value_datatype")
            vals["columnnames"] = result_set.getString("columnnames")
            vals["fk_file_schema_attribute_Id"] = result_set.getString(
                "fk_file_schema_attribute_id"
            )
            vals["group_no"] = result_set.getString("group_no")
            result_dict.append(vals)

        print("result_set   :", result_dict)
        return result_dict

    def fn_get_fnt_info(self):
        statement = f"""CALL sp_get_fnt_info(@fnt_id:={self.fnt_id});"""
        print(statement)
        stmt = self.con.createStatement()
        result_set = stmt.executeQuery(statement)

        while result_set.next():
            vals = {}
            vals["total_columns"] = result_set.getInt("total_columns")
            vals["delimiter"] = result_set.getString("delimiter")
            vals["fnt_id"] = self.fnt_id
            vals["is_header_present"] = result_set.getBoolean("is_header_present")
            vals["file_type"] = result_set.getString("file_type")
            vals["xmlroottag"] = result_set.getString("xml_root_tag")
            vals["xmldetailstag"] = result_set.getString("xml_details_tag")
            vals["data_func"] = result_set.getString("data_func")
            vals["scd_enabled"] = result_set.getString("scd_enabled")
            vals["expected_schema"] = result_set.getString("expected_schema")
            vals["repartition"] = result_set.getInt("repartition")
            # vals["duplicatecheck_needed"] = result_set.getInt("duplicatecheck_needed")
            # vals["expected_timestamp_col"] = result_set.getString(
            #     "expected_timestamp_col"
            # )
            # result_dict.append(vals)
            # Close connections
        # exec_statement.close()
        # self.con.close()
        print("vals   :", vals)
        return vals

    def fn_dqf_needed(self):
        statement = f"""CALL sp_get_dqf_flag(@fnt_id:={self.fnt_id})"""
        print(statement)
        stmt = self.con.createStatement()
        result_set = stmt.executeQuery(statement)
        while result_set.next():
            vals = {}
            vals["dqf_needed"] = result_set.getBoolean("dqf_needed")
            vals["duplicate_check_needed"] = result_set.getBoolean(
                "duplicate_check_needed"
            )
            vals["date_column"] = result_set.getString("date_column")
            vals["del_duration_value"] = result_set.getString("del_duration_value")
            vals["del_duration_unit"] = result_set.getString("del_duration_unit")
        print("Vals    :", vals)
        return vals

    def fn_get_deltalake_configs(self):
        statement = f"""CALL sp_get_delta_table_configs(@fnt_id:={self.fnt_id})"""
        print(statement)
        stmt = self.con.createStatement()
        result_set = stmt.executeQuery(statement)

        while result_set.next():
            vals = {}
            vals["db_name"] = result_set.getString("db_name")
            vals["tabel_name"] = result_set.getString("tabel_name")
            vals["key_columns"] = result_set.getString("key_columns")
            vals["partition_columns"] = result_set.getString("partition_columns")
            vals["watermark_columns"] = result_set.getString("watermark_columns")
            vals["db_load_type"] = result_set.getString("db_load_type")
            vals["scd_column"] = result_set.getString("scd_column")
            # result_dict.append(vals)
            # Close connections
        # exec_statement.close()
        # self.con.close()
        print("deltalake configs vals   :", vals)
        return vals

    def clean_null_terms(self, d):
        return {k: v for k, v in d.items() if v is not None}

    def func_get_paths(self):
        vals1 = {}
        for i in [self.source_dl_layer, self.dest_dl_layer]:
            try:
                statement = f"""select * from T_MST_File_Path fp inner join T_MST_DL_Layer la on la.pk_dl_layer_id=fp.fk_dl_layer_id  
where la.pk_dl_layer_id = (select pk_dl_layer_id from T_MST_DL_Layer where dl_layer_name='{i}') """
                # print(statement)
                print(statement)
                stmt = self.con.createStatement()
                result_set = stmt.executeQuery(statement)

                while result_set.next():
                    vals = {}

                    vals[i + "-Success"] = result_set.getString("Success_File_Path")
                    vals[i + "-Error"] = result_set.getString("Error_File_Path")
                    vals[i + "-Suspense"] = result_set.getString("Suspense_File_Path")
                    vals[i + "-Cache"] = result_set.getString("Cache_File_path")

                    # print(vals)
                    x = self.clean_null_terms(vals)
                    vals1.update(x)
                # l.append(vals1)

            except Exception as e:
                print(e)
        # exec_statement.close()
        path = {}
        for value in vals1.keys():
            path[value] = (
                self.VOLUMES_PATH + vals1[value].replace("{sourcesystem}", self.source_name) + "/"
            )
        print("path     :", path)
        return path

    def group_info(self):
        statement = f"""CALL sp_get_group_configs(@fnt_id:={self.fnt_id})"""
        print(statement)
        stmt = self.con.createStatement()
        result_set = stmt.executeQuery(statement)
        dic = []
        while result_set.next():
            vals = {}
            vals["group_number"] = result_set.getString("group_number")
            vals["allchannels_needed"] = result_set.getString("allchannels_needed")
            dic.append(vals)
        # exec_statement.close()
        print("dict    :", dic)
        return dic

    def iot_data_configs(self):
        try:
            statement = f"""(select * from T_META_IoT_Data_Config where fk_fnt_id='{self.fnt_id}') """
            # print(statement)
            stmt = self.con.createStatement()
            result_set = stmt.executeQuery(statement)

            results = []  # List to collect multiple results

            while result_set.next():
                vals = {}
                vals["fnt_id"] = result_set.getString("FK_FNT_Id")
                vals["connectionString"] = result_set.getString("connectionString")
                vals["eventhubname"] = result_set.getString("eventhubname")
                vals["consumergroup"] = result_set.getString("consumergroup")
                vals["checkpointlocation"] = result_set.getString("checkpointlocation")
                vals["maxBytesPerTrigger"] = result_set.getString("maxBytesPerTrigger")
                vals["load_type"] = result_set.getString("load_type")
                vals["DeviceId"] = result_set.getString("DeviceId")
                vals["queryname"] = result_set.getString("queryname")
                vals["uniquecol"] = result_set.getString("uniquecol")
                vals["log_tablename"] = result_set.getString("log_tablename")
                vals["errcount"] = result_set.getString("errcount")
                vals["errrows"] = result_set.getString("errrows")

                results.append(vals)  # Add the current result to the list

            # exec_statement.close()
            return vals
        except Exception as e:
            print(e)

    def getall_configs(self):
        config_dict = {}
        columnnames = []
        fileinfo = self.fn_get_fnt_info()
        fileschema = self.fn_get_schema()
        filedelta = self.fn_get_deltalake_configs()
        fileatt = self.fn_get_list_of_attributes()
        filedqf = self.fn_dqf_needed()
        pat = self.func_get_paths()
        iot = self.iot_data_configs()
        group_data = self.group_info()
        for i in fileschema:
            columnnames.append(i["expected_columnname"])
        config_dict["file_read_configs"] = fileinfo
        config_dict["columns"] = columnnames
        config_dict["schema"] = fileschema
        config_dict["deltalake_configs"] = filedelta
        config_dict["list_of_attributes"] = fileatt
        config_dict["dqf_needed"] = filedqf
        config_dict["path"] = pat
        config_dict["iot"] = iot
        config_dict["group_data"] = group_data
        print("config_dict    :", config_dict)
        return config_dict
