import os
import pandas as pd
from .base_file_loader import FileLoader
from ..utils.csv_chunk_read_util import CsvChunkReader
from ..utils.tab_chunk_read_util import is_table_tab, tab_has_header, find_data_start
import pyarrow.parquet as pq
import pyreadstat

class SingleTableLoader(FileLoader):
    def read_and_convert(self):
        """分块读取文件并返回迭代器"""
        output_file_path = []
        file_name = (os.path.basename(self.input_path)).split(".")[0]

        self.output_prefix += f'{os.sep}{file_name}{os.sep}'
        os.makedirs(self.output_prefix, exist_ok=True)
        self.output_prefix += file_name
        ext = os.path.splitext(self.input_path)[1].lower()
        chunks = self.read_file_chunked(self.input_path, ext)
        output_file_path += self.write_function(chunks, self.output_prefix, self.output_format, self.max_size)
        return output_file_path

    def read_file_chunked(self, input_path, ext):
        try:
            if ext == '.csv':
                csv_chunk_reader = CsvChunkReader()
                for chunk in csv_chunk_reader.read_csv_in_chunks(self.input_path, self.chunk_size):
                    yield chunk
            elif ext == '.tsv':
                for chunk in pd.read_csv(self.input_path, sep='\t', chunksize=self.chunk_size, on_bad_lines='skip',
                                         low_memory=False):
                    yield chunk
                    # 新增：处理.tab文件（区分表格类型和非表格类型）
            elif ext == '.tab':
                if is_table_tab(input_path):
                    # 表格类型.tab，按制表符分隔格式处理（同.tsv）
                    # 1. 跳过/* */注释块，找到数据起始行
                    data_start_row = find_data_start(input_path)
                    print(f"表格类型.tab文件{input_path}，已跳过注释块，数据从第{data_start_row + 1}行开始:")
                    # 检测是否有表头
                    has_header = tab_has_header(input_path, data_start_row)
                    print(f"检测到表格类型.tab文件，按制表符分隔格式读取: {input_path}")
                    print(f"表头存在: {has_header}")
                    for chunk in pd.read_csv(
                            input_path,
                            sep='\t',
                            chunksize=self.chunk_size,
                            on_bad_lines='skip',
                            low_memory=False,
                            skiprows=data_start_row,
                            header=0 if has_header else None
                    ):
                        yield chunk
                else:
                    # 非表格类型.tab（如GIS），抛出不支持异常
                    raise ValueError(f"Unsupported .tab file: {input_path} (non-table type, e.g., GIS data)")
            elif ext == '.parquet':
                # Parquet分块读取
                parquet_file = pq.ParquetFile(self.input_path)
                lines_processed = 0
                parquet_chunk_size = self.chunk_size / 100
                try:
                    for batch in parquet_file.iter_batches(batch_size=parquet_chunk_size):
                        chunk = batch.to_pandas()
                        lines_in_chunk = len(chunk)
                        lines_processed += lines_in_chunk
                        print(f"成功处理块: {lines_processed - lines_in_chunk} - {lines_processed - 1} 行")
                        yield chunk
                except Exception as e:
                    print(f"块解析错误: {str(e)}. 尝试逐行处理...")
                    # 这里对于Parquet文件逐行处理较复杂，可根据实际情况进一步实现
                    raise
            elif ext == '.sav':
                # pyreadstat暂不支持分块，改为分批读取
                try:
                    try:
                        df, meta = pyreadstat.read_sav(input_path, apply_value_formats=True)
                        print(f"成功读取 {input_path} 文件。")
                    except Exception as e :
                        print(f"[ERROR] 读取 .{input_path} 文件失败 (pyreadstat): {type(e).__name__}: {e}")
                        print("尝试使用 pandas.read_spss 读取文件...")
                        df = pd.read_spss(input_path)
                        print(f"成功使用 pandas.read_spss 读取 {input_path} 文件。")
                except Exception as e:
                    print(f"[ERROR] 读取 .{input_path} 文件失败: {type(e).__name__}: {e}")
                    print("尝试强制处理所有列为字符串...")
                    try:
                        df, meta = pyreadstat.read_sav(input_path, usecols=None, apply_value_formats=False)
                        for col in df.columns:
                            df[col] = df[col].astype(str)
                        print("成功将所有列转为字符串并完成读取。")
                    except Exception as inner_e:
                        print(f"第二次尝试失败: {inner_e}")
                        raise RuntimeError(f"无法解析 {input_path} 文件: {input_path}") from inner_e
                for i in range(0, len(df), self.chunk_size):
                    yield df.iloc[i:i + self.chunk_size]
            elif ext == '.ods':
                # 使用odf的流式读取
                with pd.ExcelFile(self.input_path, engine='odf') as excel:
                    for sheet_name in excel.sheet_names:
                        df = pd.read_excel(excel, sheet_name=sheet_name)
                        for i in range(0, len(df), self.chunk_size):
                            yield df.iloc[i:i + self.chunk_size]
            else:
                raise ValueError(f"Unsupported file type: {ext}")
        except Exception as e:
            raise RuntimeError(f"Error reading {self.input_path}: {str(e)}")
