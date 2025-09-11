import pandas as pd
import pyarrow as pa
import re
import hashlib
from collections import defaultdict
from typing import List
from io import BytesIO, StringIO
from ..utils.FileLogger import FileErrorLogger
from .parquet_writer import ParquetWriter
from .pyarrow_writer import PyArrowWriter
import pyarrow.parquet as pq

logger_manager = FileErrorLogger()
def _analyze_all_schemas(df, chunk_size):
    """
    预分析所有数据块的schema，返回一个能兼容所有数据块的最终schema
    """
    num_chunks = (len(df) + chunk_size - 1) // chunk_size
    final_fields = {}  # 存储最终的字段信息

    for i in range(num_chunks):
        start = i * chunk_size
        end = min(start + chunk_size, len(df))
        chunk_df = df.iloc[start:end]

        # 跳过空块
        if chunk_df.empty:
            continue

        # 转换 DataFrame 到 Arrow Table
        try:
            table = pa.Table.from_pandas(chunk_df)
        except Exception as e:
            print(f"预分析时Arrow转换异常：{str(e)}")
            clean_df = clean_dataframe(chunk_df, "schema_analysis")
            table = pa.Table.from_pandas(clean_df)

        # 分析当前数据块的schema
        for field in table.schema:
            field_name = field.name
            field_type = field.type

            # 如果字段不在最终schema中，添加它
            if field_name not in final_fields:
                final_fields[field_name] = field_type
            else:
                current_type = final_fields[field_name]

                # 如果当前类型是null，更新为新类型
                if _is_null_type(current_type):
                    # print(f"更新字段 '{field_name}' 的类型从 null 到 {field_type}")
                    final_fields[field_name] = field_type
                # 如果新类型不是null且与当前类型不同，发出警告
                elif not _is_null_type(field_type) and current_type != field_type:
                    print(f"警告: 字段 '{field_name}' 在不同数据块中有不兼容的类型: {current_type} vs {field_type}")
                    final_fields[field_name] = field_type if get_write_weight(field_type) > get_write_weight(current_type) else current_type
                    print(f"选择更通用的类型: {final_fields[field_name]}")
                    # 这里可以添加更复杂的类型合并逻辑，例如选择更通用的类型

    # 创建最终schema
    fields = [pa.field(name, dtype) for name, dtype in final_fields.items()]
    return pa.schema(fields)

def auto_convert_column(series: pd.Series) -> pd.Series:
    """更安全的类型转换逻辑"""
    # 1. 优先尝试数值转换
    try:
        # 仅当值看起来像数字时才尝试转换
        if series.apply(lambda x: str(x).replace('.', '', 1).isdigit()).mean() > 0.5:
            return pd.to_numeric(series, errors='coerce').astype('double[pyarrow]')
    except:
        pass

    # 2. 尝试日期时间转换
    try:
        if series.apply(lambda x: isinstance(x, str) and re.match(r'\d{4}-\d{2}-\d{2}', x)).mean() > 0.3:
            return pd.to_datetime(series, errors='coerce')
    except:
        pass

    # 3. 处理类 JSON 数据
    if series.apply(lambda x: isinstance(x, str) and x.startswith('{') and x.endswith('}')).mean() > 0.5:
        return series.astype('string[pyarrow]')

    # 4. 最终回退到字符串
    return (
        series.astype(str)
        .str.replace(r'\s+', ' ', regex=True)
        .astype('string[pyarrow]')
    )

def clean_dataframe(df: pd.DataFrame, output_prefix) -> pd.DataFrame:
    """增强型数据清洗"""
    print(f"{output_prefix}进行数据清洗...")
    cleaned_df = df.copy()

    # 列名处理增强
    def safe_column_name(col, idx):
        # 替换所有非字母数字字符为下划线
        clean_col = re.sub(r'[^a-zA-Z0-9]', '_', str(col))
        # 移除连续下划线并截断
        clean_col = re.sub(r'_+', '_', clean_col).strip('_')
        # 动态截断长度（保留20字符基础+5字符哈希）
        base_col = clean_col[:20] if clean_col else f'col_{idx}'
        hash_suffix = hashlib.md5(str(col).encode()).hexdigest()[:5]
        return f"{base_col}_{hash_suffix}"

    df.columns = [safe_column_name(col, idx) for idx, col in enumerate(df.columns)]

    # 确保列名唯一性
    seen = defaultdict(int)
    new_columns = []
    for col in df.columns:
        while col in seen:
            seen[col] += 1
            col = f"{col}_v{seen[col]}"
        seen[col] = 0
        new_columns.append(col)
    df.columns = new_columns

    # 分列处理（强制统一列类型）
    for col in cleaned_df.columns:
        try:
            # 尝试智能转换
            converted_series = auto_convert_column(cleaned_df[col])

            # 检查类型一致性
            if converted_series.dtype != object:
                cleaned_df[col] = converted_series
            else:
                # 如果转换失败，强制清理为字符串
                cleaned_df[col] = (
                    converted_series
                    .astype(str)
                    .str.replace(r'[\x00-\x1F\x7F-\x9F]', '', regex=True)
                )

        except Exception as e:
            print(f"列 [{col}] 转换失败，强制转为字符串 | 错误类型：{type(e).__name__}")
            print(f"问题数据示例：{cleaned_df[col].head(3).tolist()}")
            cleaned_df[col] = cleaned_df[col].astype(str)

    # 强制所有列转换为字符串作为最终保障
    for col in cleaned_df.columns:
        if cleaned_df[col].dtype == object:
            cleaned_df[col] = cleaned_df[col].astype(str)

    return cleaned_df

def _is_null_type(arrow_type):
    """检查 Arrow 类型是否为 null 类型"""
    return arrow_type == pa.null()

def write_dataframe_in_chunks(df, output_path_prefix, output_list, output_format, chunk_size=1000):
    if df is None or df.empty:
        raise ValueError("输入DataFrame不能为空")

    # 计算需要的分块数量
    num_chunks = (len(df) + chunk_size - 1) // chunk_size  # 向上取整
    output_path = f"{output_path_prefix}.{output_format}"
    final_schema = None
    data_writer = None
    written_rows = 0  # 记录已写入的行数

    try:
        # 步骤1: 预分析所有数据块的schema
        print("开始预分析所有数据块的schema...")
        final_schema = _analyze_all_schemas(df, chunk_size)
        print(f"最终确定的schema: {final_schema}")

        # 步骤2: 使用最终schema写入数据
        for i in range(num_chunks):
            start = i * chunk_size
            end = min(start + chunk_size, len(df))
            # chunk_df = df[start:end]  # 当前 chunk 的 DataFrame
            chunk_df = df.iloc[start:end]  # 当前 chunk 的 DataFrame

            # 数据块完整性校验
            if chunk_df.empty:
                continue  # 空块直接跳过

            # 转换 DataFrame 到 Arrow Table（异常时清洗当前 chunk）
            try:
                table = pa.Table.from_pandas(chunk_df)
            except Exception as e:
                print(f"Arrow转换异常：{str(e)}")
                clean_df = clean_dataframe(chunk_df, output_path_prefix)  # 清洗当前 chunk 而非全量 df
                table = pa.Table.from_pandas(clean_df)

            # 将表转换为最终 schema
            if table.schema != final_schema:
                # print(f"将第{i + 1}个chunk的schema从 {table.schema} 转换为 {final_schema}")
                table = table.cast(final_schema)
                # print("Schema转换完成")

            if output_format == 'parquet':
                # ---------------------- Parquet 写入逻辑 ----------------------
                # 首次写入时初始化 writer
                if i == 0 and data_writer is None:
                    data_writer  = (ParquetWriter(output_path, final_schema)).get_writer()

                data_writer.write_table(table)
            elif output_format == 'arrow':
                # ---------------------- Arrow IPC 写入逻辑 ----------------------
                if i == 0 and data_writer is None:
                    data_writer = (PyArrowWriter(output_path, final_schema)).get_writer()

                data_writer.write_table(table)

            # 记录已写入行数
            written_rows += len(chunk_df)
        # 验证总写入行数
        if written_rows != len(df):
            print(f"数据写入不完整，预期{len(df)}行，实际写入{written_rows}行")
            raise RuntimeError(f"数据写入不完整，预期{len(df)}行，实际写入{written_rows}行")
        output_list.append(output_path)
    except Exception as e:
        print(f"写入数据块时发生错误: {str(e)}")
        logger_manager.output_log(str(e), output_path_prefix)
        raise
    finally:
        # 强制资源释放（双重保障）
        if data_writer is not None:
            try:
                data_writer.close()
            except Exception as close_err:
                print(f"关闭写入器时发生错误: {close_err}")
                logger_manager.output_log(close_err, output_path_prefix)

def save_as_output_format_with_chunks(chunks, output_prefix, output_format, max_size) -> List[str]:
    """根据 max_size 动态分块保存"""
    output_file_path = []
    current_chunks = []  # 累积当前块的 DataFrame
    current_size = 0     # 当前累积块的大小（字节）
    part_num = 0         # 分块编号
    chunk_count = 1

    for chunk in chunks:
        if chunk is None or (len(chunk.columns) == 0):
            # 仅在既没有行也没有列时，才认为是无效数据
            print("跳过空数据块")
            continue
        # 如果只有列名没有数据行，添加一行空数据以保留列结构
        if chunk.empty:
            print("检测到 chunk 为空，正在添加一行空数据以保留列结构...")
            empty_row = pd.DataFrame({col: [None] for col in chunk.columns}, index=[0])
            chunk = pd.concat([empty_row], ignore_index=True)
        # 如果 index 为空，手动重置 index
        if len(chunk.index) == 0:
            print("检测到 chunk.index 为空，正在重置索引...")
            chunk.reset_index(drop=True, inplace=True)
        try:
            # 估算当前 chunk 转换为 PyArrow Table 后的大小
            chunk_table = pa.Table.from_pandas(chunk)
            # print("列名：", chunk_table.column_names)
            buf = BytesIO()
            pq.write_table(chunk_table, buf, compression='snappy')
            chunk_size = buf.tell()
        except Exception as e:
            print(f"块大小估算错误: {str(e)}，使用默认大小")
            chunk_size = max_size // 2  # 使用一半最大大小作为默认

        # 判断是否需要分块
        if current_size + chunk_size > max_size * 1.02:
            chunk_count += 1
            # 写入当前累积的块
            if current_chunks:
                combined_df = pd.concat(current_chunks)
                write_dataframe_in_chunks(combined_df, f"{output_prefix}_part{part_num:03d}", output_file_path, output_format)
                part_num += 1
                current_chunks = []
                current_size = 0

            # 如果单个 chunk 就超过 max_size，强制拆分
            if chunk_size > max_size:
                rows_per_part = max(1, int(len(chunk) * (max_size / chunk_size)))
                for i in range(0, len(chunk), rows_per_part):
                    sub_chunk = chunk.iloc[i:i+rows_per_part]
                    write_dataframe_in_chunks(sub_chunk, f"{output_prefix}_part{part_num:03d}", output_file_path, output_format)
                    part_num += 1
            else:
                current_chunks.append(chunk)
                current_size += chunk_size
        else:
            current_chunks.append(chunk)
            current_size += chunk_size

    # 写入剩余的数据
    if current_chunks:
        combined_df = pd.concat(current_chunks)
        if chunk_count <= 1:
            # 如果只有一个块，直接使用 output_prefix
            path = f"{output_prefix}"
        else :
            path = f"{output_prefix}_part{part_num:03d}"
        write_dataframe_in_chunks(combined_df, path, output_file_path, output_format)

    return output_file_path

def get_write_weight(field_type) -> int:
    """获取字段类型的写入权重"""
    if field_type == pa.string():
        return 8
    elif field_type == pa.large_string():
        return 9
    elif field_type == pa.int64():
        return 5
    elif field_type == pa.float64():
        return 6
    elif field_type == pa.bool_():
        return 4
    elif field_type == pa.timestamp('ns'):
        return 10
    elif field_type == pa.null()():
        return -1
    else:
        return 0  # 未知类型权重为0