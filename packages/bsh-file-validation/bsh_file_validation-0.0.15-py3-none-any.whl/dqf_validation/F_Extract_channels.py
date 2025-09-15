# Create a Class for loading specific Channel with samples and timestamp
from asammdf import MDF
import io


class ChannelExtractor:
    def __init__(self, channel):
        self.channel = channel

    # Extracts Timestamp
    def extract_channel_timestamp(self, val):
        print("val", val)
        file_stream = io.BytesIO(val)
        mdf = MDF(file_stream)
        mdf_one_channel = mdf.get(self.channel)

        return mdf_one_channel.timestamps

    # Extracts  Values/Samples
    def extract_channel_values(self, val):
        file_stream = io.BytesIO(val)
        mdf = MDF(file_stream)
        mdf_one_channel = mdf.get(self.channel)

        return mdf_one_channel.samples
