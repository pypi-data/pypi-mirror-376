"""
This module contains a class for establishing a database connection using PySpark,
specifically for MySQL databases.

Author          : Keerthana Subramanian
Creation date   : Feb 13, 2024
Updated by      : Keerthana Subramanian
Updation date   : Mar 8, 2024
"""

from pyspark.sql import SparkSession


class DBConnection:
    """
    Class for MySQL database connection.
    Args:
        - database (str): Name of the database.
        - server (str): Database server address.
        - spark (pyspark.sql.SparkSession): PySpark SparkSession.
        - username (str): Database username.
        - password (str): Database password.
    """

    def __init__(self, spark_session, server, database, username, password):
        self.spark = spark_session
        self.server = server
        self.database = database
        self.username = username
        self.password = password

    def fn_get_connection(self):
        """
        Establish a connection to the MySQL database.
        Returns:
        - JDBC connection object of MySQL database.
        """
        # Form the JBDC URL string
        rds_jdbc_url = f"jdbc:mysql://{self.server}/{self.database}?useSSL=true&requireSSL=true&trustServerCertificate=true"

        # Set spark properties object
        rds_driver_class = "com.mysql.jdbc.Driver"
        properties = {
            "user": self.username,
            "password": self.password,
            "driver": rds_driver_class,
        }
        # Fetch the driver manager from your spark context and add properties
        driver_manager = self.spark._sc._gateway.jvm.java.sql.DriverManager
        props = self.spark._sc._gateway.jvm.java.util.Properties()
        props.putAll(properties)

        connection = driver_manager.getConnection(rds_jdbc_url, props)
        return connection


################ Use below to check the connection ####################
# spark = SparkSession.builder.getOrCreate()
# db = DBConnection(
#     database="eda_datastore_db_v2", server="eda-qa-db-instance-manual.cf3vqa3tx6pc.us-east-2.rds.amazonaws.com", spark_session=spark,
#     username="eda_master", password="xxxxxxxxxxxx"
# )
# # Get the database connection
# connection = db.fn_get_connection()
# print("Connection created successfully!")
# print(connection)
# stmt = connection.createStatement()
# rs = stmt.executeQuery("select * from T_MST_File_Type limit 10")
# print(rs)
# while rs.next():
#     print(f"{rs.getString('pk_file_type_id')}, {rs.getString('file_type')}")
