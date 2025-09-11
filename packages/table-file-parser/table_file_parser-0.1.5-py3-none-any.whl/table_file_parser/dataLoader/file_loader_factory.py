import os
from .hdf5_loader import HDF5Loader
from .excel_loader import ExcelLoader
from .single_table_loader import SingleTableLoader

# 文件读取器工厂
class FileReaderFactory:
    @staticmethod
    def create_reader(input_path, output_prefix, output_format, max_size, chunk_size, write_function):
        ext = os.path.splitext(input_path)[1].lower()
        if ext in ['.csv', '.sav', '.tsv', '.ods', '.parquet','.tab']:
            return SingleTableLoader(input_path, output_prefix, output_format, max_size, chunk_size, write_function)
        elif ext in ['.xls', '.xlsx']:
            return ExcelLoader(input_path, output_prefix, output_format, max_size, chunk_size, write_function)
        elif ext == '.h5':
            return HDF5Loader(input_path, output_prefix, output_format, max_size, chunk_size, write_function)
        else:
            raise ValueError(f"Unsupported file type: {ext}")