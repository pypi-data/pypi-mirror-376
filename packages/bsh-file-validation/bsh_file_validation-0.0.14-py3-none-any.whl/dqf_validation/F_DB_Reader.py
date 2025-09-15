class Dbreader:
    def __init__(self, dbcon):
        self.con = dbcon

    def fn_get_tags_xml(self, fnt_id):
        try:
            statement = f"""EXEC dbo.sp_get_xmltags @fntid={fnt_id}"""
            exec_statement = self.con.prepareCall(statement)
            exec_statement.execute()
            result_set = exec_statement.getResultSet()
            result_dict = []
            while result_set.next():
                vals = {}
                result_dict.append(vals)
                # Close connections
            exec_statement.close()
            # self.con.close()
            return result_dict
        except Exception as e:
            print(e)

    def fn_get_files_for_dqf(self, fnt_id):
        try:
            statement = f"""CALL sp_get_files_for_dqf(@fnt_id:='{fnt_id}')"""
            print("Statement is ", statement)
            stmt = self.con.createStatement()
            result_set = stmt.executeQuery(statement)
            result_dict = []
            while result_set.next():
                vals = {}
                vals["tracking_id"] = result_set.getString("tracking_id")
                vals["to_dl_layer"] = result_set.getString("to_dl_layer")
                vals["fnt_id"] = result_set.getString("fnt_id")
                vals["job_run_id"] = result_set.getString("job_run_id")
                vals["file_id"] = result_set.getString("fk_file_id")

                result_dict.append(vals)
            print("result_set from dbreader :", result_dict)
            return result_dict
        except Exception as e:
            print(e)

    def fn_get_no_columns_new(self, fntid):
        try:
            statement = f"""CALL sp_get_no_columns(@fnt_id:={fntid})"""
            print(statement)
            stmt = self.con.createStatement()
            result_set = stmt.executeQuery(statement)
            while result_set.next():
                result_dict = result_set.getInt("total_columns")
            print("result_dict     :", result_dict)
            return result_dict
        except Exception as e:
            print(e)

    def fn_get_no_rows(self, tracking_id, fnt_id):
        try:
            statement = f"""CALL sp_get_no_rows(@p_tracking_id:='{tracking_id}',@p_fnt_id:='{fnt_id}')"""
            print("fn_get_no_rows query is ", statement)
            stmt = self.con.createStatement()
            result_set = stmt.executeQuery(statement)
            # print(result_set)
            while result_set.next():
                result_dict = result_set.getInt("agg_row_cnt")

            print(f"fn_get_no_rows result_dict value: {result_dict}")
            return result_dict
        except Exception as e:
            print(e)
