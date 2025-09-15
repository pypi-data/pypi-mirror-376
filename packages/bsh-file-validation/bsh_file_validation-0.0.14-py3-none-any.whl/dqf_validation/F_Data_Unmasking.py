from pyspark.sql.types import StringType
from cryptography.fernet import Fernet
import json


class DataUnmasking:
    def __init__(self, config, spark1):
        self.config = config
        self.schema = self.config["schema"]
        self.spark = spark1
        self.sc = self.spark.sparkContext
        self.fnt_id = self.config["file_read_configs"]["fnt_id"]
        self.schema_df = self.spark.read.json(
            self.sc.parallelize([json.dumps(self.schema)])
        )
        self.dbutils = self.get_dbutils()
        self.databasename = config["deltalake_configs"]["dbname"]
        print(self.databasename)
        self.tablename = config["deltalake_configs"]["tablename"]
        print(self.tablename)

    def get_dbutils(self):
        try:
            from pyspark.dbutils import DBUtils

            dbutils = DBUtils(self.spark)
        except ImportError:
            import IPython

            dbutils = IPython.get_ipython().user_ns["dbutils"]
        return dbutils

    @staticmethod
    def decrypt_val(cipher_text, master_key):
        f = Fernet(master_key)
        clear_val = f.decrypt(cipher_text.encode()).decode()
        return clear_val

    def data_mask(self):
        mask_dict = (
            self.schema_df.filter("is_maskable=1")
            .select("expected_columnname", "mask_value")
            .rdd.collectAsMap()
        )
        column = (
            self.schema_df.filter("is_maskable=1")
            .select("expected_columnname")
            .rdd.flatMap(lambda x: x)
            .collect()
        )
        print(column)

        for columns, maskval in mask_dict.items():
            if maskval == "Encryption":
                fernetkey = "fernet-key-" + self.fnt_id
                encryption_key = self.dbutils.preview.secret.get(
                    scope="fof-prd-scope", key=fernetkey
                )
                print(encryption_key)

                sqlContext.udf.register(  # noqa: F821
                    "decrypt", DataUnmasking.decrypt_val, StringType()
                )
                decrypt_df = spark.sql(  # noqa: F821
                    "select m.*,decrypt(df['columns'], '"
                    + encryption_key
                    + "')as '"
                    + columns
                    + "' from  '"
                    + self.databasename
                    + "'.'"
                    + self.tablename
                    + "' m"
                )
                decrypt_df.createOrReplaceTempView("decryptedtable")

        return decrypt_df
