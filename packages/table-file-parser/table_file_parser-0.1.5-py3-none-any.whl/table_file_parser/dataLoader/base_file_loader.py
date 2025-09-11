from ..utils.Invaild_Chars import get_invalid_chars
import pyarrow as pa
import pyarrow.parquet as pq
from io import BytesIO
import math
from ..utils.FileLogger import FileErrorLogger
# 抽象基类
class FileLoader:
    def __init__(self, input_path, output_prefix, output_format, max_size, chunk_size, write_function):
        self.input_path = input_path
        self.output_prefix = output_prefix
        self.output_format = output_format
        self.max_size = max_size
        self.chunk_size = 10000 if chunk_size is None else chunk_size
        self.write_function = write_function
        self.logger_manager = FileErrorLogger()

    def read_and_convert(self):
        pass

    def get_invalid_chars(self):
        return get_invalid_chars()

    def _split_dataframe_by_size(self, df, max_size, output_prefix):
        """按预估大小拆分 DataFrame"""
        try :
            table = pa.Table.from_pandas(df)
        except Exception as e:
            print(f"df转换table出错，进行数据清洗 {str(e)}")
            clean_df = self.clean_dataframe(df, output_prefix)
            table = pa.Table.from_pandas(clean_df)
        buf = BytesIO()
        pq.write_table(table, buf, compression='snappy')
        full_size = buf.tell()
        n_chunks = math.ceil(full_size / max_size)
        rows_per_chunk = math.ceil(len(df) / n_chunks)
        return [df.iloc[i * rows_per_chunk: (i + 1) * rows_per_chunk] for i in range(n_chunks)]
