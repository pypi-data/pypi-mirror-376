import pyarrow as pa
import os
import pyarrow.parquet as pq

class PyArrowWriter:
    def __init__(self, output_path, schema):
        self.output_path = output_path
        self.schema = schema
        self.output_format = 'arrow'
        if os.path.exists(self.output_path):
            os.remove(self.output_path)
        # 初始化 Arrow writer
        self.writer = pa.RecordBatchFileWriter(self.output_path, self.schema)

    def get_writer(self):
        return self.writer

    def write_dataframe(self, table):
        if self.writer is None:
            raise ValueError("请先初始化writer")
        # 写入当前数据块
        self.writer.write_table(table)

    # def write_dataframe_in_chunks(self, df, output_path_prefix, output_list, output_format, chunk_size=1000):
    #     if df is None or df.empty:
    #         raise ValueError("输入DataFrame不能为空")
    #     # 计算需要的分块数量
    #     num_chunks = (len(df) + chunk_size - 1) // chunk_size  # 向上取整
    #     output_path = f"{output_path_prefix}.{self.output_format}"
    #     final_schema = None
    #     arrow_writer = None
    #     parquet_writer = None
    #     written_rows = 0  # 记录已写入的行数
    #
    #     try:
    #         # 步骤1: 预分析所有数据块的schema
    #         print("开始预分析所有数据块的schema...")
    #         final_schema = self._analyze_all_schemas(df, chunk_size)
    #         print(f"最终确定的schema: {final_schema}")
    #
    #         # 步骤2: 使用最终schema写入数据
    #         for i in range(num_chunks):
    #             start = i * chunk_size
    #             end = min(start + chunk_size, len(df))
    #             # chunk_df = df[start:end]  # 当前 chunk 的 DataFrame
    #             chunk_df = df.iloc[start:end]  # 当前 chunk 的 DataFrame
    #
    #             # 数据块完整性校验
    #             if chunk_df.empty:
    #                 continue  # 空块直接跳过
    #
    #             # 转换 DataFrame 到 Arrow Table（异常时清洗当前 chunk）
    #             try:
    #                 table = pa.Table.from_pandas(chunk_df)
    #             except Exception as e:
    #                 print(f"Arrow转换异常：{str(e)}")
    #                 clean_df = self.clean_dataframe(chunk_df, output_path_prefix)  # 清洗当前 chunk 而非全量 df
    #                 table = pa.Table.from_pandas(clean_df)
    #
    #             # 将表转换为最终 schema
    #             if table.schema != final_schema:
    #                 # print(f"将第{i + 1}个chunk的schema从 {table.schema} 转换为 {final_schema}")
    #                 table = table.cast(final_schema)
    #                 # print("Schema转换完成")
    #
    #             if output_format == 'arrow':
    #                 # ---------------------- Arrow IPC 写入逻辑 ----------------------
    #                 # 首次写入时初始化 writer
    #                 if i == 0:
    #                     # 检查文件是否已存在，存在则删除
    #                     if os.path.exists(output_path):
    #                         os.remove(output_path)
    #
    #                     # 初始化 Arrow writer
    #                     arrow_writer = pa.RecordBatchFileWriter(output_path, final_schema)
    #                 # 写入当前数据块
    #                 arrow_writer.write_table(table)
    #             # 记录已写入行数
    #             written_rows += len(chunk_df)
    #         # 验证总写入行数
    #         if written_rows != len(df):
    #             print(f"数据写入不完整，预期{len(df)}行，实际写入{written_rows}行")
    #             raise RuntimeError(f"数据写入不完整，预期{len(df)}行，实际写入{written_rows}行")
    #         output_list.append(output_path)
    #     except Exception as e:
    #         print(f"写入数据块时发生错误: {str(e)}")
    #         self.logger_manager.output_log(str(e), output_path_prefix)
    #         raise
    #     finally:
    #         # 强制资源释放（双重保障）
    #         if parquet_writer is not None:
    #             try:
    #                 parquet_writer.close()
    #             except Exception as close_err:
    #                 print(f"关闭写入器时发生错误: {close_err}")
    #                 self.logger_manager.output_log(close_err, output_path_prefix)
    #         # 释放资源
    #         if arrow_writer is not None:
    #             try:
    #                 arrow_writer.close()
    #             except Exception as close_err:
    #                 print(f"关闭Arrow写入器时发生错误: {close_err}")
    #                 self.logger_manager.output_log(close_err, output_path_prefix)
