import json


class Dbwriters:
    def __init__(self, dbcon):
        self.con = dbcon

    def fn_update_error_status_new(self, final_json):
        statement = (
            f"""CALL sp_update_error_status_new (@json := '{json.dumps(final_json)}')"""
        )
        print("update statement for error is ", statement)
        stmt = self.con.createStatement()
        res = stmt.executeQuery(statement)
        print(res)
        print("Error file status updated")

    def fn_update_row_cnt_new(self, final_json):
        statement = (
            f"""CALL sp_update_row_count(@json := '{json.dumps(final_json)}')"""
        )
        exec_statement = self.con.prepareCall(statement)
        res = exec_statement.execute()
        print(res)

        exec_statement.close()

    def fn_update_error_row_cnt_new(self, final_json):
        statement = f"""CALL sp_insert_delta_summary_logs(@json:= '{json.dumps(final_json)}')"""
        print(statement)
        stmt = self.con.createStatement()
        res = stmt.executeQuery(statement)
        print(res)
        print("Error row count updated")

    def fn_update_error_row_cnt_mdf(self, final_json):
        statement = f"""CALL sp_insert_delta_summary_logs_mdf1(@json:= '{json.dumps(final_json)}')"""
        print(statement)
        stmt = self.con.createStatement()
        res = stmt.executeQuery(statement)
        print(res)

    def fn_file_info_mdf(self, final_json):
        statement = (
            f"""CALL sp_insert_T_file_info_mdf1(@json:= '{json.dumps(final_json)}')"""
        )
        print(statement)
        stmt = self.con.createStatement()
        res = stmt.executeQuery(statement)
        print(res)

    def fn_insert_delta_summary_logs_mdf(
        self, delta_tracking_id, expected_rows, gooddf_count, baddf_count, group_number
    ):
        statement = f"""CALL sp_update_delta_summary_logs_mdf(@delta_tracking_id:='{delta_tracking_id}',@expected_rows:='{expected_rows}',@gooddf_count:='{gooddf_count}',@baddf_count:='{baddf_count}',@group_number:='{group_number}')"""
        print(statement)
        stmt = self.con.createStatement()
        res = stmt.executeQuery(statement)
        print(res)
        print("Delta Summary logs updated")

    def fn_insert_delta_summary_logs(
        self, delta_tracking_id, expected_rows, gooddf_count, baddf_count, track_id
    ):
        statement = f"""CALL sp_update_delta_summary_logs(@expected_rows:='{expected_rows}',@baddf_count:='{baddf_count}', @gooddf_count:='{gooddf_count}', @p_delta_tracking_id:='{delta_tracking_id}', @tracking_id1:='{track_id}')"""
        print(f"fn_insert_delta_summary_logs query statement: {statement}")
        stmt = self.con.createStatement()
        res = stmt.executeQuery(statement)
        print(res)
        print("Delta Summary logs updated")
