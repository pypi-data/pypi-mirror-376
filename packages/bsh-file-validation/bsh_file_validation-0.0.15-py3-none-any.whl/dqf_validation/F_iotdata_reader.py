from pyspark.sql import functions as f
from .F_iot_schema import iotschema


class datareader:
    def __init__(self, spark, iotdata, fnt_id, fileschema):
        self.spark = spark
        self.iotdata = iotdata
        self.sc = self.spark.sparkContext
        self.fnt_id = fnt_id
        self.fschema = fileschema
        self.iot_obj = iotschema(self.spark, self.fnt_id, self.fschema)
        self.EVENTHUBS_CONNECTION_STRING = "eventhubs.connectionString"
        self.EVENTHUBS_CONSUMER_GROUP = "eventhubs.consumerGroup"
        self.READING_ALL_COLUMNS = "reading.*"

    def streamreader(self):
        if self.fnt_id == "32":
            df = self.iotdatareader_32()
            return df
        elif self.fnt_id == "57":
            df = self.iotdatareader_57()
            return df
        elif self.fnt_id == "67" or self.fnt_id == "68":
            df = self.iotdatareader_67()
            return df
        elif self.fnt_id == "66":
            df = self.iotdatareader_66()
            return df

    @staticmethod
    def convert_case(encr_val):
        x = "".join(chr(i) for i in encr_val)
        return x

    def iotdatareader_32(self):
        self.dataset_schema, self.body_schema = self.iot_obj.get_iot_schema()
        eh_conf = {
            self.EVENTHUBS_CONNECTION_STRING: self.iotdata["connectionString"],
            "ehName": self.iotdata["eventhubname"],
        }
        eh_conf[self.EVENTHUBS_CONNECTION_STRING] = (
            self.sc._jvm.org.apache.spark.eventhubs.EventHubsUtils.encrypt(
                self.iotdata["connectionString"]
            )
        )
        eh_conf[self.EVENTHUBS_CONSUMER_GROUP] = self.iotdata["consumergroup"]
        df = (
            self.spark.readStream.format("eventhubs")
            .options(**eh_conf)
            .schema(self.dataset_schema)
            .option("rowsPerBatch", 10)
            .load()
            .withColumn(
                "Body", f.from_json(f.col("Body").cast("string"), self.body_schema)
            )
            .withColumn(
                "timestamp2",
                f.from_unixtime(
                    f.unix_timestamp(f.col("Body.timestamp"), "M/d/yyyy hh:mm:ss a"),
                    "yyyy-MM-dd'T'HH:mm:ss",
                ),
            )
            .select(
                f.col("Body.DMC"),
                f.col("Body.EventName"),
                f.col("Body.Eventid"),
                f.col("Body.Identifier"),
                f.col("Body.Result_State"),
                f.col("Body.batch_no"),
                f.col("Body.line_no"),
                f.col("Body.part_no"),
                f.col("Body.plant"),
                f.col("Body.process_no"),
                f.col("Body.product_family"),
                f.col("Body.station_no"),
                f.col("Body.timestamp"),
                f.col("Body.timezone"),
                f.col("SystemProperties.iothub-connection-device-id"),
            )
            .alias("leftpart")
            .filter(f.col("iothub-connection-device-id") == self.iotdata["DeviceId"])
            .drop(f.col("iothub-connection-device-id"))
        )

        return df

    def iotdatareader_57(self):
        eh_conf = {
            self.EVENTHUBS_CONNECTION_STRING: self.iotdata["connectionString"],
            "ehName": self.iotdata["eventhubname"],
        }
        eh_conf[self.EVENTHUBS_CONNECTION_STRING] = (
            self.sc._jvm.org.apache.spark.eventhubs.EventHubsUtils.encrypt(
                self.iotdata["connectionString"]
            )
        )
        eh_conf[self.EVENTHUBS_CONSUMER_GROUP] = self.iotdata["consumergroup"]
        schema = self.iot_obj.get_iot_schema()
        iot_stream = (
            self.spark.readStream.format("eventhubs")
            .options(**eh_conf)
            .load()
            .withColumn("reading", f.from_json(f.col("body").cast("string"), schema))
            .select("reading.deviceId", "reading.temperature", "reading.humidity")
        )
        print("Printing schema from IOT source  ")
        iot_stream.printSchema()
        return iot_stream

    def iotdatareader_67(self):
        eh_conf = {
            self.EVENTHUBS_CONNECTION_STRING: self.iotdata["connectionString"],
            "ehName": self.iotdata["eventhubname"],
        }
        eh_conf[self.EVENTHUBS_CONNECTION_STRING] = (
            self.sc._jvm.org.apache.spark.eventhubs.EventHubsUtils.encrypt(
                self.iotdata["connectionString"]
            )
        )
        eh_conf[self.EVENTHUBS_CONSUMER_GROUP] = self.iotdata["consumergroup"]
        schema = self.iot_obj.get_iot_schema()
        iot_stream = (
            self.spark.readStream.format("eventhubs")
            .options(**eh_conf)
            .option("rowsPerBatch", 500)
            .load()
            .withColumn("reading", f.from_json(f.col("body").cast("string"), schema))
            .select(READING_ALL_COLUMNS)
        )

        return iot_stream

    def iotdatareader_66(self):
        convert_udf = f.udf(lambda z: datareader.convert_case(z))
        eh_conf = {
            self.EVENTHUBS_CONNECTION_STRING: self.iotdata["connectionString"],
            "ehName": self.iotdata["eventhubname"],
        }
        eh_conf[self.EVENTHUBS_CONNECTION_STRING] = (
            self.sc._jvm.org.apache.spark.eventhubs.EventHubsUtils.encrypt(
                self.iotdata["connectionString"]
            )
        )
        eh_conf[self.EVENTHUBS_CONSUMER_GROUP] = self.iotdata["consumergroup"]
        schema = self.iot_obj.get_iot_schema()
        df_stream_in = (
            self.spark.readStream.format("eventhubs")
            .options(**eh_conf)
            .option("rowsPerBatch", 500)
            .load()
            .withColumn("convereted", convert_udf(f.col("Body")))
        )
        df = df_stream_in.withColumn(
            "reading", f.from_json(f.col("convereted").cast("string"), schema)
        )
        df1 = df.select(READING_ALL_COLUMNS)

        return df1
