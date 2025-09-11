import os
from collections import defaultdict
import sys

# 获取当前脚本的绝对路径
#current_script_path = os.path.abspath(__file__)  # 结果类似: /home/project/hqr/python/faird-parser-sciencedb/huggingface/my_huggingface_descriptive_statistics.py

# 向上回溯两级目录，得到项目根目录（因为当前脚本在huggingface子目录下）
#project_root = os.path.dirname(os.path.dirname(current_script_path))  # 结果: /home/project/hqr/python/faird-parser-sciencedb

# 将项目根目录添加到Python搜索路径（优先搜索）
#if project_root not in sys.path:
#    sys.path.insert(0, project_root)  # insert(0) 确保项目路径优先级最高

import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
import numpy as np
import re
import json
from typing import Dict, Any, List, Tuple
from ..utils.my_pandas_type_confirming_utils import MyPandasTypeConfirmingUtils
from ..utils.FileLogger import FileErrorLogger
from pyarrow import Time32Type, Time64Type
from datetime import datetime

class DescriptiveStatisticsGenerator:
    """描述性统计类"""
    def __init__(self, MAX_NUM_STRING_LABELS = 1000, HISTOGRAM_NUM_BINS = 10, MAX_PROPORTION_STRING_LABELS = 0.2,
                NUM_BINS = 30):
        # 常量定义（与官方实现对齐）
        self.HISTOGRAM_NUM_BINS = HISTOGRAM_NUM_BINS
        self.MAX_NUM_STRING_LABELS = MAX_NUM_STRING_LABELS
        # 在文件开头定义常量
        self.MAX_PROPORTION_STRING_LABELS = MAX_PROPORTION_STRING_LABELS  # 唯一值比例阈值
        self.NUM_BINS = NUM_BINS  # 唯一值数量后备阈值
        # 新增文本长度直方图缓存
        self.text_length_cache = defaultdict(lambda: {
            "lengths": [],
            "nan_count": 0,
            "total_samples": 0
        })
        self.type_confirming_utils = MyPandasTypeConfirmingUtils()
        self.logger_manager = FileErrorLogger()

    def get_hf_data_type(self, field: pa.Field, data: pd.Series) -> str:
        """
        根据 Arrow 类型和实际数据推断 HuggingFace 数据类型
        参考：https://github.com/huggingface/dataset-viewer/blob/main/services/worker/src/descriptive_stats/type_inference.rs
        """
        # 处理 metadata 为 None 的情况
        metadata = field.metadata or {}
        # 检查 ClassLabel（优先通过 metadata 判断）
        class_label_meta = metadata.get(b'_type', b'{}')
        try:
            class_info = json.loads(class_label_meta.decode('utf-8'))
            if class_info.get("_type") == "ClassLabel" and "names" in class_info:
                return "class_label"
        except json.JSONDecodeError:
            pass

        def confirm_string_type(temp_data: pd.Series) -> str:
            # 计算有效数据（非空值）的统计量
            temp_clean_data = temp_data.dropna()
            temp_total_count = len(temp_clean_data)
            temp_unique_count = temp_clean_data.nunique()

            # 计算唯一值比例（防止除零）
            temp_unique_proportion = temp_unique_count / temp_total_count if temp_total_count > 0 else 0.0

            # 分类决策逻辑
            temp_condition_main = (temp_unique_count <= self.MAX_NUM_STRING_LABELS) and (
                    temp_unique_proportion <= self.MAX_PROPORTION_STRING_LABELS)
            temp_condition_fallback = temp_unique_count <= self.NUM_BINS

            return "string_label" if temp_condition_main or temp_condition_fallback else "string_text"

        # 检查 Arrow 类型
        if pa.types.is_integer(field.type):
            return "int"
        elif pa.types.is_floating(field.type):
            return "float"
        elif pa.types.is_boolean(field.type):
            return "bool"
        elif pa.types.is_string(field.type) or pa.types.is_large_string(field.type):
            return confirm_string_type(data)
        elif pa.types.is_temporal(field.type):
            # 2.1 检查是否为 Arrow 的「纯时间子类型」（仅时分秒）
            if isinstance(field.type, (Time32Type, Time64Type)):
                return confirm_string_type(data)  # 纯时间类型归为string

            timestamp = datetime
            # 2.2 若是日期时间类型（pa.timestamp），检查数据是否包含日期信息
            if isinstance(field.type, timestamp):
                # 抽样检查数据（取非空样本）
                non_empty = data.dropna().astype(str)
                if non_empty.empty:
                    return "datetime"  # 无数据时保持原判断

                # 取最多5个样本验证（平衡性能）
                samples = non_empty.sample(min(5, len(non_empty)), replace=True)

                # 正则：匹配「仅时分秒」的字符串（如 '10:04:07' 或 '09:59:59.123'）
                time_only_pattern = r"^\d{1,2}:\d{1,2}:\d{1,2}(?:\.\d+)?$"

                # 统计样本中「仅时分秒」的比例
                time_only_count = sum(1 for sample in samples if re.fullmatch(time_only_pattern, sample))
                if time_only_count / len(samples) > 0.5:  # 超半数样本是纯时间
                    return confirm_string_type(data)

            # 2.3 其他正常时间类型（含日期）保持原判断
            return "datetime"
        elif pa.types.is_list(field.type):
            return "list"
        # elif 'hf_audio' in field.metadata:
        #     return "audio"
        # elif 'hf_image' in field.metadata:
        #     return "image"
        return "unknown"

    def handle_numerical_stats(self, data: pd.Series, field: pa.Field) -> Dict[str, Any]:
        """处理数值型（int/float）统计"""
        """完全符合HuggingFace官方规范的float统计"""
        # 计算基础统计量
        total_samples = len(data)
        nan_count = int(data.isnull().sum())
        nan_proportion = round(nan_count / total_samples, 4) if total_samples > 0 else 0.0
        cleaned = data.dropna()
        numeric_type = cleaned.dtype
        column_type = None

        # 初始化统计值
        stats = {
            "nan_count": nan_count,
            "nan_proportion": nan_proportion,
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
            "std": None,
            "histogram": {"hist": [], "bin_edges": []}
        }

        if not cleaned.empty:
            # 基础统计计算
            if numeric_type == 'int64' or numeric_type == 'int32':
                # 整数类型
                stats["min"] = int(cleaned.min())
                stats["max"] = int(cleaned.max())
                stats["mean"] = round(float(cleaned.mean()), 6)
                stats["median"] = round(float(cleaned.median()), 6)
                stats["std"] = round(float(cleaned.std(ddof=0)), 6)
                column_type = 'int'
            elif numeric_type == 'float64' or numeric_type == 'float32':
                stats["min"] = round(float(cleaned.min()), 6)
                stats["max"] = round(float(cleaned.max()), 6)
                stats["mean"] = round(float(cleaned.mean()), 6)
                stats["median"] = round(float(cleaned.median()), 6)
                stats["std"] = round(float(cleaned.std(ddof=0)), 6)  # 使用总体标准差
                column_type = 'float'
            else:
                # 其他类型（如 object）
                stats["min"] = cleaned.min()
                stats["max"] = cleaned.max()
                stats["mean"] = cleaned.mean()
                stats["median"] = cleaned.median()
                stats["std"] = cleaned.std(ddof=0)
                column_type = 'unknown'
            # 中位数需要全量数据（分块模式下无法计算）
            # 若必须支持分块，需使用近似算法（此处保留空值）
            # 直方图生成
            # hist, bin_edges = np.histogram(
            #     cleaned,
            #     bins=self.HISTOGRAM_NUM_BINS,
            #     range=(stats["min"], stats["max"])
            # )
            #
            # stats["histogram"] = {
            #     "hist": hist.tolist(),
            #     "bin_edges": [int(edge) for edge in bin_edges.tolist()]
            # }

            stats["histogram"] = self.generate_histogram(cleaned, self.HISTOGRAM_NUM_BINS, stats["min"], stats["max"])

        # stats = {
        #     "nan_count": int(data.isnull().sum()),
        #     "min": float(data.min()),
        #     "max": float(data.max()),
        #     "mean": float(data.mean()),
        #     "median": float(data.median()),
        #     "std": float(data.std() if len(data) > 1 else 0),
        #     "histogram": self.generate_histogram(data, self.HISTOGRAM_NUM_BINS)
        # }
        # if data.dtype.kind == 'i':  # 整数类型额外统计
        #     stats.update({
        #         "unique_count": int(data.nunique()),
        #         "most_frequent": self.get_most_frequent(data)
        #     })
        # return {"numerical_statistics": stats}
        return {
            "column_name": field.name,
            "column_type": column_type,
            "column_statistics": stats
        }

    def handle_class_label(self, data: pd.Series, field: pa.Field) -> Dict[str, Any]:
        """修复键值类型转换问题"""
        metadata = field.metadata or {}
        class_label_meta = metadata.get(b'hf_class_label', b'{}')

        try:
            class_info = json.loads(class_label_meta.decode('utf-8'))
            class_names = class_info.get('names', [])
        except json.JSONDecodeError:
            class_names = []

        # 数据清洗和转换
        total_samples = len(data)
        clean_data = data.copy()

        # 特殊处理-1值（no label）
        no_label_mask = clean_data == -1
        no_label_count = int(no_label_mask.sum())
        clean_data[no_label_mask] = np.nan  # 将-1转换为nan统一处理

        # 计算基础统计量
        nan_count = int(clean_data.isnull().sum())
        valid_count = total_samples - nan_count
        valid_data = clean_data.dropna().astype(int)

        # 映射标签到名称（处理超出类名列表的情况）
        def map_label(x):
            try:
                return class_names[x] if 0 <= x < len(class_names) else f"__invalid_label_{x}__"
            except:
                return f"__invalid_label_{x}__"

        # 生成频率统计（排除no_label）
        freq_data = valid_data.apply(map_label)
        frequencies = freq_data.value_counts().to_dict()

        # 计算比例指标
        nan_proportion = nan_count / total_samples if total_samples > 0 else 0.0
        no_label_proportion = no_label_count / total_samples if total_samples > 0 else 0.0

        stats = {
            "column_name": field.name,
            "column_type": "class_label",
            "column_statistics": {
                "nan_count": nan_count,
                "nan_proportion": round(float(nan_proportion), 4),
                "no_label_count": no_label_count,
                "no_label_proportion": round(float(no_label_proportion), 4),
                "n_unique": len(frequencies),
                "frequencies": {str(k): int(v) for k, v in frequencies.items()}
            }
        }

        return stats
        # return {"class_label_statistics": stats}

    def handle_string_label(self, data: pd.Series, field: pa.Field) -> Dict[str, Any]:
        """处理低基数字符串统计"""
        """完全符合HuggingFace官方规范的string_label统计"""
        total_samples = len(data)
        nan_count = int(data.isnull().sum())
        nan_proportion = round(nan_count / total_samples, 4) if total_samples > 0 else 0.0

        # 清洗数据并统计频率
        clean_data = data.dropna()
        frequencies = clean_data.value_counts().to_dict()

        # value_counts = data.value_counts()
        # stats = {
        #     "nan_count": int(data.isnull().sum()),
        #     "unique_count": len(value_counts),
        #     "most_frequent": self.get_most_frequent(data),
        #     "distribution": {
        #         str(k): int(v) for k, v in value_counts.to_dict().items()
        #     }
        # }
        # return {"categorical_statistics": stats}
        return {
            "column_name": field.name,
            "column_type": "string_label",
            "column_statistics": {
                "nan_count": nan_count,
                "nan_proportion": nan_proportion,
                "n_unique": len(frequencies),
                "frequencies": {str(k): int(v) for k, v in frequencies.items()}
            }
        }

    def handle_string_text(self, data: pd.Series, field: pa.Field) -> Dict[str, Any]:
        """处理高基数文本统计"""
        """完全符合HuggingFace官方规范的string_text统计"""
        # 基础统计量
        total_samples = len(data)
        nan_count = int(data.isnull().sum())
        nan_proportion = round(nan_count / total_samples, 4) if total_samples > 0 else 0.0

        # 文本长度计算
        clean_data = data.dropna()
        text_lengths = clean_data.str.len()

        # 初始化统计结果
        stats = {
            "nan_count": nan_count,
            "nan_proportion": nan_proportion,
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
            "std": None,
            "histogram": {"hist": [], "bin_edges": []}
        }

        if not text_lengths.empty:
            # 基础统计计算
            stats["min"] = int(text_lengths.min())
            stats["max"] = int(text_lengths.max())
            stats["mean"] = round(float(text_lengths.mean()), 5)
            stats["std"] = round(float(text_lengths.std(ddof=0)), 5)
            stats["median"] = round(float(text_lengths.median()), 1)  # 保留1位小数与示例对齐

            stats["histogram"] = self.generate_histogram(text_lengths, self.HISTOGRAM_NUM_BINS, stats["min"], stats["max"])

        # stats = {
        #     "nan_count": int(data.isnull().sum()),
        #     "unique_count": int(data.nunique()),
        #     "most_frequent": self.get_most_frequent(data),
        #     "examples": data.dropna().sample(min(5, len(data))).tolist(),
        #     "text_length": self.handle_numerical_stats(data.str.len())
        # }
        # return {"text_statistics": stats}
        return {
            "column_name": field.name,
            "column_type": "string_text",
            "column_statistics": stats
        }

    def handle_bool(self, data: pd.Series, field: pa.Field) -> Dict[str, Any]:
        # 基础统计量
        total_samples = len(data)
        nan_count = int(data.isnull().sum())
        nan_proportion = round(nan_count / total_samples, 4) if total_samples > 0 else 0.0

        # 统计True/False频率（排除NaN）
        clean_data = data.dropna().astype(bool)

        # 统计True值
        freq_counts = clean_data.value_counts().reindex([True, False], fill_value=0)

        # 统计结果
        return {
            "column_name": field.name,
            "column_type": "bool",
            "column_statistics": {
                "nan_count": nan_count,
                "nan_proportion": nan_proportion,
                "frequencies": {
                    "True": int(freq_counts.get(True, 0)),
                    "False": int(freq_counts.get(False, 0))
                }
            }
        }

    def handle_list(self, data: pd.Series, field: pa.Field) -> Dict[str, Any]:
        """处理列表类型统计"""
        # 基础统计量
        total_samples = len(data)
        nan_count = int(data.isnull().sum())
        nan_proportion = round(nan_count / total_samples, 4) if total_samples > 0 else 0.0

        # 文本长度计算
        clean_data = data.dropna()
        list_lengths = clean_data.apply(len)

        # 初始化统计结果
        stats = {
            "nan_count": nan_count,
            "nan_proportion": nan_proportion,
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
            "std": None,
            "histogram": {"hist": [], "bin_edges": []}
        }

        if not list_lengths.empty:
            # 基础统计计算
            stats["min"] = int(list_lengths.min())
            stats["max"] = int(list_lengths.max())
            stats["mean"] = round(float(list_lengths.mean()), 5)
            stats["std"] = round(float(list_lengths.std(ddof=0)), 5)
            stats["median"] = round(float(list_lengths.median()), 1)  # 保留1位小数与示例对齐

            # 直方图生成
            stats["histogram"] = self.generate_histogram(list_lengths, self.HISTOGRAM_NUM_BINS, stats["min"], stats["max"])

        # lengths = data.apply(len if data.notnull() else 0)
        # stats = {
        #     "nan_count": int(data.isnull().sum()),
        #     "length_statistics": self.handle_numerical_stats(lengths),
        #     "type": str(data.iloc[0].dtype) if not data.empty else "unknown"
        # }
        # return {"list_statistics": stats}
        return {
            "column_name": field.name,
            "column_type": "string_text",
            "column_statistics": stats
        }

    def handle_audio(self, data: pd.Series, field: pa.Field) -> Dict[str, Any]:
        """处理音频类型统计（假设存储为文件路径）"""
        # 需要实际音频处理库（如 librosa）实现完整功能
        stats = {
            "nan_count": int(data.isnull().sum()),
            "duration_stats": None,  # 需解析音频文件
            "sample_rate_stats": None
        }
        return {"audio_statistics": stats}

    def handle_image(self, data: pd.Series, field: pa.Field) -> Dict[str, Any]:
        """处理图像类型统计（假设存储为文件路径）"""
        # 需要图像处理库（如 PIL）实现完整功能
        stats = {
            "nan_count": int(data.isnull().sum()),
            "width_stats": None,
            "height_stats": None,
            "mode_stats": None
        }
        return {"image_statistics": stats}

    def handle_datetime(self, data: pd.Series, field: pa.Field) -> Dict[str, Any]:
        """处理dateTime类型统计"""
        # 基础统计量
        total_samples = len(data)
        nan_count = int(data.isnull().sum())
        nan_proportion = round(nan_count / total_samples, 4) if total_samples > 0 else 0.0

        # 文本长度计算
        clean_data = data.dropna()

        # 初始化统计结果
        stats = {
            "nan_count": nan_count,
            "nan_proportion": nan_proportion,
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
            "std": None,
            "histogram": {"hist": [], "bin_edges": []}
        }

        if not clean_data.empty:
            # 基础统计计算
            # 转换为pandas datetime类型（确保类型统一）
            # 检测时间单位：如果原始数据为毫秒时间戳，需转换为纳秒
            if isinstance(clean_data.iloc[0], (int, float)) and clean_data.max() < 1e12:
                # 假设数据是毫秒时间戳（数值范围在 1e12 以下）
                datetime_series = pd.to_datetime(clean_data, unit='ms')
            else:
                if pd.__version__ >= "2.0.0":
                    datetime_series = pd.to_datetime(clean_data, format="mixed", errors="coerce")
                else:
                    datetime_series = pd.to_datetime(clean_data, errors="coerce")
                # datetime_series = pd.to_datetime(clean_data)

            # 2. 确保时间类型为 datetime64[ns]
            datetime_series = datetime_series.astype('datetime64[ns]')
            #再过滤一遍空值
            datetime_series = datetime_series.dropna()

            # 1. 时间戳转换策略优化
            if datetime_series.empty:
                min_date = pd.NaT
                max_date = pd.NaT
            else:
                min_date = datetime_series.min()
                max_date = datetime_series.max()

            # 2. 基于时间差的统计计算（避免数值溢出）
            time_deltas = datetime_series - min_date
            total_seconds = time_deltas.dt.total_seconds()

            # 3. 统计量计算
            stats.update({
                "min": min_date.strftime("%Y-%m-%d %H:%M:%S"),
                "max": max_date.strftime("%Y-%m-%d %H:%M:%S"),
                "mean": (min_date + pd.to_timedelta(total_seconds.mean(), unit='s')).strftime("%Y-%m-%d %H:%M:%S"),
                "median": datetime_series.median().strftime("%Y-%m-%d %H:%M:%S"),
                "std": str(pd.to_timedelta(total_seconds.std(), unit='s'))
            })

            # 4. 直方图生成策略（对齐官方分桶逻辑）
            # 生成分箱边界（确保时区一致）
            if datetime_series.dt.tz is not None:
                tz = datetime_series.dt.tz
                bin_edges = pd.date_range(
                    start=min_date,
                    end=max_date,
                    periods=self.HISTOGRAM_NUM_BINS + 1,
                    tz=tz
                )
            else:
                bin_edges = pd.date_range(
                    start=min_date,
                    end=max_date,
                    periods=self.HISTOGRAM_NUM_BINS + 1
                )

            # 转换为纳秒时间戳（直接使用 view 方法）
            data_int64 = datetime_series.astype("int64")  # datetime64[ns] -> int64 (纳秒)
            bin_edges_int64 = bin_edges.astype("int64")  # DatetimeIndex -> int64

            # 4. 验证分箱范围（防止数据落在分箱外）
            assert bin_edges_int64[0] <= data_int64.min(), f"分箱起始时间错误: {bin_edges_int64[0]} > {data_int64.min()}"
            assert bin_edges_int64[-1] >= data_int64.max(), f"分箱结束时间错误: {bin_edges_int64[-1]} < {data_int64.max()}"

            # 计算直方图
            hist, _ = np.histogram(data_int64, bins=bin_edges_int64)

            stats["histogram"] = {
                "hist": hist.tolist(),
                "bin_edges": [edge.strftime("%Y-%m-%d %H:%M:%S") for edge in bin_edges]
            }

        return {
            "column_name": field.name,
            "column_type": "datetime",
            "column_statistics": stats
        }

    def handle_unknown(self, data: pd.Series, field: pa.Field) -> Dict[str, Any]:
        total_samples = len(data)
        nan_count = int(data.isnull().sum())
        nan_proportion = round(nan_count / total_samples, 4) if total_samples > 0 else 0.0

        # 清洗数据并统计频率
        clean_data = data.dropna()
        frequencies = clean_data.value_counts().to_dict()

        return {
            "column_name": field.name,
            "column_type": "unkown",
            "column_statistics": {
                "nan_count": nan_count,
                "nan_proportion": nan_proportion,
                "n_unique": len(frequencies),
                "frequencies": {str(k): int(v) for k, v in frequencies.items()}
            }
        }

    def generate_dataset_statistics(self, file_path: str) -> Dict[str, Any]:
        print(f"开始处理文件: {file_path}")

        schema = None
        df = None
        num_rows = None

        ext = file_path.split('.')[-1]
        if ext == "arrow":
            # 读取 Arrow 文件为 pyarrow Table
            table = pa.ipc.RecordBatchFileReader(pa.memory_map(file_path, "r")).read_all()
            # 转换为 Pandas DataFrame
            schema = table.schema
            df = table.to_pandas()
            num_rows = table.num_rows
        elif ext == "parquet":
            parquet_file = pq.ParquetFile(file_path)
            # 获取文件的行组数和 schema
            num_row_groups = parquet_file.num_row_groups
            schema = parquet_file.schema_arrow
            df = parquet_file.read().to_pandas()
            num_rows = parquet_file.metadata.num_rows
        else:
            print(f"不支持的文件格式: {ext}")
            return None

        # 调试：打印所有字段名和 DataFrame 列名
        # print("Parquet 字段名:", [field.name for field in schema])
        # print("DataFrame 列名:", df.columns.tolist())

        if schema is None:
            print(f"错误：无法获取 {file_path} 的 schema")
            return None

        if df is None or df.empty:
            print(f"警告：{file_path} 数据为空")
            return {
                "num_rows": 0,
                "statistics": {"columns": []},
                "format": ext,
                "version": "2.0"
            }

        columns_meta = []
        for field in schema:
            # 强制字段名转换为字符串
            col_name = str(field.name)
            if col_name not in df.columns:
                # print(f"警告：列名 {col_name} 不存在于 DataFrame 中，尝试转为数字处理")
                try:
                    col_name = int(col_name)
                    if col_name not in df.columns:
                        # print(f"警告：列名 {col_name} 不存在于 DataFrame 中, 跳过处理")
                        continue
                except ValueError:
                    # print(f"错误：列名 {col_name} 无法转换为数字，跳过处理")
                    continue

            col_data = df[col_name]
            hf_type = self.get_hf_data_type(field, col_data)

            if hf_type == "unknown":
                print(f"警告：列 {col_name} 的类型无法识别")

            ## 这里新增一个对String类型进一步判断是不是dateTime类型判断的逻辑(不额外处理了，这里要保证3个地方的类型判别一致)
            # if (hf_type == 'string_label' or hf_type == 'string_text') and self.type_confirming_utils.string_is_datetime(df[col_name]):
            #     hf_type = "datetime"
            #     #对该列进行datetime类型的转换
            #     df[col_name] = self.type_confirming_utils.try_convert_to_datetime(df[col_name])

            # stats = {"_type": hf_type}
            handler_map = {
                "class_label": self.handle_class_label,
                "float": self.handle_numerical_stats,
                "int": self.handle_numerical_stats,  # 整数类型共用同一处理逻辑
                "string_label": self.handle_string_label,
                "string_text": self.handle_string_text,
                "bool": self.handle_bool,
                "list": self.handle_list,
                "audio": self.handle_audio,
                "image": self.handle_image,
                "datetime": self.handle_datetime,
                "unknown": self.handle_unknown
            }

            # stats.update(
            #     handler_map[hf_type](col_data, field) if hf_type == "class_label" else handler_map[hf_type](col_data))

            # 修改结果组装逻辑
            stats = handler_map[hf_type](col_data, field)  # 直接使用handler返回的完整结构
            columns_meta.append(stats)  # 直接附加结果

        print(f"{file_path} 处理完毕!")
        return {
            "num_rows": int(num_rows),
            "statistics": {"columns": columns_meta},
            "format": ext,
            "version": "2.0"  # 与官方版本对齐
        }

    # 辅助函数
    def generate_histogram(self, data: pd.Series, bins: int, min, max) -> Dict[str, list]:
        """生成直方图数据（与Hugging Face相同的分箱策略）"""
        # cleaned = data.dropna()
        if len(data) == 0:
            return {"hist": [], "bin_edges": []}

        # 判断数据类型是否为整数
        is_integer = pd.api.types.is_integer_dtype(data)

        counts, bin_edges = np.histogram(data, bins=bins + 1, range=(min, max))
        if is_integer:
            bin_edges = list(map(int, bin_edges))
        else:
            # 保留浮点精度，限制小数位数为 6 位（避免长浮点数）
            bin_edges = [round(float(edge), 6) for edge in bin_edges]
        bin_edges[-1] = max  # 确保最后一个边界等于最大值
        return {
            "hist": counts.tolist(),
            "bin_edges": bin_edges
        }

    def get_most_frequent(self, data: pd.Series) -> Dict[str, Any]:
        """获取最高频项"""
        counts = data.value_counts()
        if counts.empty:
            return {"value": None, "count": 0}
        return {
            "value": str(counts.index[0]),
            "count": int(counts.iloc[0])
        }

    def generate_and_save_json(self, file_path: str, output_json: str) -> int:
        """生成统计信息并保存为JSON文件"""
        try:
            if not os.path.exists(file_path):
                print(f"{file_path} 不存在，无法生成描述文件！")
                return 0
            stats = self.generate_dataset_statistics(file_path)
            with open(output_json, "w") as f:
                json.dump(stats, f, indent=2, default=str)
            print(f"统计信息已保存到 {output_json}")
            return 1
        except Exception as e:
            file_name = os.path.basename(file_path).split(".")[0]
            print(f"处理文件 {file_path}, 生成统计信息失败: {str(e)}")
            self.logger_manager.output_log(str(e), file_name)
            return 0

    def read_merged_column(self, file_paths: List[str], column_name: str) -> Tuple[pd.Series, pa.Field]:
        """
        合并多个Parquet文件的同名列数据（严格校验类型并返回Series）

        参数:
            file_paths: 待读取的Parquet文件路径列表
            column_name: 需合并的列名

        返回:
            (合并后的pd.Series, 字段描述pa.Field) 元组
        """
        column_data: List[pd.Series] = []  # 显式声明列表元素为Series
        expected_field: pa.Field = None

        for file_path in file_paths:
            # 读取Parquet文件的指定列（仅加载目标列）
            try:
                table = pq.read_table(file_path, columns=[column_name])
            except Exception as e:
                raise ValueError(f"读取文件 {file_path} 失败: {e}")

            # 校验列是否存在
            if column_name not in table.column_names:
                raise ValueError(f"文件 {file_path} 缺少列 {column_name}")

            # 获取字段描述并校验类型一致性
            current_field = table.schema.field(column_name)

            if expected_field is not None and current_field.type != expected_field.type and current_field.type != pa.null():
                if current_field.type != expected_field.type:
                    # 以非Null的current_field为主，转换之前的column_data
                    try:
                        # 以当前非空类型为准，转换之前所有数据
                        target_pd_type = self.pyarrow_type_to_pandas_type(current_field.type)
                        column_data = [series.astype(target_pd_type) for series in column_data]
                        expected_field = current_field  # 更新预期类型
                    except Exception as e:
                        raise ValueError(
                            f"文件 {file_path} 列类型不一致，转换失败: {e}"
                        )
            # 初始化预期类型（首次读取时）
            if expected_field is None:
                expected_field = current_field

            # 转换为Series并校验类型（防止意外得到DataFrame）
            series = table.to_pandas()[column_name]
            if not isinstance(series, pd.Series):
                raise TypeError(
                    f"文件 {file_path} 列 {column_name} 转换后应为pd.Series，实际得到 {type(series)}"
                )
            column_data.append(series)

        # 合并Series（ignore_index=True重置索引）
        merged_series = pd.concat(column_data, ignore_index=True)
        return merged_series, expected_field

    def generate_dataset_statistics_folder(self, file_paths: List[str]) -> Dict[str, Any]:
        print(f"开始处理文件: {file_paths}")

        if not file_paths:
            print("未提供文件路径列表")
            return {}
        schema = None
        num_rows = 0
        ext = None
        for file_path in file_paths:
            if not os.path.exists(file_path):
                print(f"文件 {file_path} 不存在，跳过处理")
                continue
            ext = file_path.split('.')[-1]
            parquet_file = pq.ParquetFile(file_path)
            if parquet_file is not None:
                num_rows += parquet_file.metadata.num_rows
                if schema is None:
                    schema = parquet_file.schema_arrow
        if schema is None:
            print("未找到有效的Parquet文件或其schema")
            return {}

        columns_meta = []
        for field in schema:
            # 强制字段名转换为字符串
            col_name = str(field.name)
            if col_name == '__index_level_0__':
                continue
            # 按列名读取所有文件的同名列
            merged_series,expected_field = self.read_merged_column(file_paths, col_name)

            hf_type = self.get_hf_data_type(expected_field, merged_series)

            if hf_type == "unknown":
                print(f"警告：列 {col_name} 的类型无法识别")

            handler_map = {
                "class_label": self.handle_class_label,
                "float": self.handle_numerical_stats,
                "int": self.handle_numerical_stats,  # 整数类型共用同一处理逻辑
                "string_label": self.handle_string_label,
                "string_text": self.handle_string_text,
                "bool": self.handle_bool,
                "list": self.handle_list,
                "audio": self.handle_audio,
                "image": self.handle_image,
                "datetime": self.handle_datetime,
                "unknown": self.handle_unknown
            }

            # 修改结果组装逻辑
            stats = handler_map[hf_type](merged_series, expected_field)  # 直接使用handler返回的完整结构
            columns_meta.append(stats)  # 直接附加结果

        print(f"{file_paths} 处理完毕!")
        return {
            "num_rows": int(num_rows),
            "statistics": {"columns": columns_meta},
            "format": ext,
            "version": "2.0"  # 与官方版本对齐
        }

    def generate_and_save_json_folder(self, file_paths: List[str], output_json: str) -> int:
        """生成统计信息并保存为JSON文件"""
        try:
            if not file_paths or not isinstance(file_paths, list):
                print("未提供有效的文件路径列表")
                print(f"{file_paths} 不存在，无法生成描述文件！")
                return 0
            stats = self.generate_dataset_statistics_folder(file_paths)
            with open(output_json, "w") as f:
                json.dump(stats, f, indent=2, default=str)
            print(f"统计信息已保存到 {output_json}")
            return 1
        except Exception as e:
            file_name = os.path.basename(file_paths[0]).split(".")[0]
            print(f"处理文件 {file_name}, 生成统计信息失败: {str(e)}")
            self.logger_manager.output_log(str(e), file_name)
            return 0

    def pyarrow_type_to_pandas_type(self, pa_type: pa.DataType) -> str:
        """
        将PyArrow类型映射到Pandas类型（支持用户指定的所有类型）
        覆盖类型：int/float/string/bool/list/datetime
        """
        # 整数类型（int8/int16/int32/int64/uint系列）
        if pa.types.is_integer(pa_type):
            return 'int64'  # 统一转换为Pandas的int64（兼容无符号整数）

        # 浮点类型（float32/float64）
        elif pa.types.is_floating(pa_type):
            return 'float64'  # 统一转换为Pandas的float64

        # 字符串类型（包括large_string）
        elif pa.types.is_string(pa_type) or pa.types.is_large_string(pa_type):
            return 'object'  # Pandas默认用object存储字符串（或可改为'string[python]'）

        # 布尔类型
        elif pa.types.is_boolean(pa_type):
            return 'bool'

        # 列表类型（list<...>）
        elif pa.types.is_list(pa_type):
            return 'object'  # Pandas用object存储列表（每个元素是Python列表）

        # 日期时间类型（timestamp[ns]/timestamp[ms]等）
        elif pa.types.is_timestamp(pa_type):
            # 保留时区信息（若有）
            tz = pa_type.tz if pa_type.tz is not None else ''
            return f'datetime64[ns, {tz}]' if tz else 'datetime64[ns]'

        # 其他未显式支持的类型（可根据需要扩展）
        else:
            raise ValueError(f"暂不支持的PyArrow类型: {pa_type}（请联系维护者扩展）")
#     def generate_multi_file_statistics(self, input_dir: str, output_json: str) -> int:
#         """处理目录下所有parquet文件，合并同名列统计"""
#         # 步骤1：获取所有parquet文件路径（按part排序）
#         parquet_files = sorted([os.path.join(input_dir, f)
#                                 for f in os.listdir(input_dir)
#                                 if f.endswith(".parquet")])
#         if not parquet_files:
#             print("未找到parquet文件")
#             return 0
#
#         # 步骤2：读取第一个文件获取元信息（列名、列类型、总样本数）
#         first_file = parquet_files[0]
#         first_pf = pq.ParquetFile(first_file)
#         schema = first_pf.schema_arrow
#         total_rows = sum(pq.ParquetFile(f).metadata.num_rows for f in parquet_files)  # 总样本数
#         columns = [field.name for field in schema]  # 所有列名
#
#         # 步骤3：初始化最终统计结果（与单文件结构一致）
#         final_stats = {
#             "num_rows": total_rows,
#             "statistics": {"columns": []},
#             "format": "parquet",
#             "version": "2.0"
#         }
#
#         # 步骤4：按列逐个处理所有文件
#         for col_name in columns:
#             print(f"正在处理列: {col_name}")
#             # 获取该列的全局类型（所有文件类型必须一致）
#             col_type = self._get_uniform_column_type(parquet_files, col_name)
#             if not col_type:
#                 print(f"列 {col_name} 类型不一致，跳过")
#                 continue
#
#             # 根据类型初始化统计累加器
#             accumulator = self._init_accumulator(col_type)
#
#             # 遍历所有文件，累加统计信息
#             for file in parquet_files:
#                 pf = pq.ParquetFile(file)
#                 col_data = pf.read_column(col_name).to_pandas()  # 仅读取当前列
#                 self._update_accumulator(accumulator, col_data, col_type)
#
#             # 将累加器转换为最终统计格式
#             col_stats = self._accumulator_to_stats(accumulator, col_name, col_type)
#             final_stats["statistics"]["columns"].append(col_stats)
#
#             # 增量写入（可选：每处理完一列就写入临时文件，避免崩溃丢失）
#             # 这里为简化示例，最终一次性写入，实际可根据需要调整
#
#         # 步骤5：保存最终统计结果
#         with open(output_json, "w") as f:
#             json.dump(final_stats, f, indent=2, default=str)
#         return 1
#
#     def _get_uniform_column_type(self, parquet_files: list, col_name: str) -> str:
#         """验证所有文件中该列的HuggingFace类型是否一致"""
#         expected_type = None
#         for file in parquet_files:
#             pf = pq.ParquetFile(file)
#             field = pf.schema_arrow.field(col_name)
#             data = pf.read_column(col_name).to_pandas()
#             current_type = self.get_hf_data_type(field, data)
#             if expected_type is None:
#                 expected_type = current_type
#             elif current_type != expected_type:
#                 self.logger_manager.output_log(f"列 {col_name} 类型不一致: {expected_type} vs {current_type}",
#                                                "type_error")
#                 return None
#         return expected_type
#
#     def _init_accumulator(self, col_type: str) -> Any:
#         """根据列类型初始化统计累加器"""
#         if col_type in ["int", "float"]:
#             return NumericalAccumulator()
#         elif col_type in ["string_label"]:
#             return StringLabelAccumulator()
#         elif col_type in ["string_text"]:
#             return StringTextAccumulator()
#         elif col_type in ["class_label"]:
#             return ClassLabelAccumulator()
#         elif col_type in ["bool"]:
#             return BooleanAccumulator()
#         elif col_type in ["list"]:
#             return ListAccumulator()
#         else:
#             return GenericAccumulator()
#
#     def _update_accumulator(self, accumulator: Any, data: pd.Series, col_type: str) -> None:
#         """更新累加器统计信息"""
#         accumulator.update(data)
#
#     def _accumulator_to_stats(self, accumulator: Any, col_name: str, col_type: str) -> Dict[str, Any]:
#         return {
#                 "column_name": col_name,
#                 "column_type": col_type,
#                 "column_statistics": accumulator.to_stats()
#         }
#
#
# class NumericalAccumulator:
#     """数值型数据统计累加器（支持中位数近似）"""
#
#     def __init__(self):
#         self.nan_count = 0
#         self.total_samples = 0
#         self.sum = 0.0
#         self.sq_sum = 0.0
#         self.min = None
#         self.max = None
#         self.tdigest = TDigest()  # TDigest分布摘要
#
#     def update(self, data: pd.Series) -> None:
#         self.total_samples += len(data)
#         self.nan_count += data.isnull().sum()
#         cleaned = data.dropna()
#         if cleaned.empty:
#             return
#
#         self.sum += cleaned.sum()
#         self.sq_sum += (cleaned ** 2).sum()
#
#         current_min = cleaned.min()
#         current_max = cleaned.max()
#         if self.min is None or current_min < self.min:
#             self.min = current_min
#         if self.max is None or current_max > self.max:
#             self.max = current_max
#
#         # 新增：将有效数据点添加到TDigest
#         self.tdigest.batch_update(cleaned.tolist())
#
#     def to_stats(self) -> Dict[str, Any]:
#         valid_count = self.total_samples - self.nan_count
#         stats = {
#             "nan_count": self.nan_count,
#             "nan_proportion": round(self.nan_count / self.total_samples, 4) if self.total_samples else 0.0,
#             "min": self.min,
#             "max": self.max,
#             "mean": None,
#             "median": None,  # 新增中位数字段
#             "std": None,
#             "histogram": {"hist": [], "bin_edges": []}
#         }
#
#         if valid_count > 0:
#             stats["mean"] = round(self.sum / valid_count, 6)
#             variance = (self.sq_sum - (self.sum ** 2) / valid_count) / valid_count
#             stats["std"] = round(np.sqrt(variance), 6)
#
#             # 新增：通过TDigest获取中位数（第50百分位数）
#             if self.tdigest.n > 0:
#                 stats["median"] = round(self.tdigest.percentile(50), 6)
#
#         return stats
#
# class ClassLabelAccumulator:
#     """处理class_label类型（预定义分类标签）"""
#     def __init__(self):
#         self.nan_count = 0
#         self.total_samples = 0
#         self.frequencies = defaultdict(int)  # 类别频率
#         self.classes = set()  # 所有出现过的类别（去重）
#
#     def update(self, data: pd.Series) -> None:
#         self.total_samples += len(data)
#         self.nan_count += data.isnull().sum()
#         cleaned = data.dropna()
#         for value in cleaned.astype(str):
#             self.frequencies[value] += 1
#             self.classes.add(value)
#
#     def to_stats(self) -> Dict[str, Any]:
#         return {
#             "nan_count": self.nan_count,
#             "nan_proportion": round(self.nan_count / self.total_samples, 4) if self.total_samples else 0.0,
#             "n_unique": len(self.classes),
#             "frequencies": dict(sorted(self.frequencies.items(), key=lambda x: -x[1])),  # 频率降序
#             "classes": sorted(self.classes)  # 类别列表（排序）
#         }
#
# class StringLabelAccumulator:
#     """处理string_label类型（短字符串标签）"""
#     def __init__(self):
#         self.nan_count = 0
#         self.total_samples = 0
#         self.frequencies = defaultdict(int)
#
#     def update(self, data: pd.Series) -> None:
#         self.total_samples += len(data)
#         self.nan_count += data.isnull().sum()
#         cleaned = data.dropna().astype(str)
#         for value in cleaned:
#             self.frequencies[value] += 1
#
#     def to_stats(self) -> Dict[str, Any]:
#         valid_count = self.total_samples - self.nan_count
#         return {
#             "nan_count": self.nan_count,
#             "nan_proportion": round(self.nan_count / self.total_samples, 4) if self.total_samples else 0.0,
#             "n_unique": len(self.frequencies),
#             "frequencies": dict(sorted(self.frequencies.items(), key=lambda x: -x[1]))
#         }
#
# class StringTextAccumulator:
#     """处理string_text类型（长文本内容，支持直方图）"""
#     def __init__(self, num_bins: int = 100):
#         self.nan_count = 0
#         self.total_samples = 0
#         self.num_bins = num_bins  # 直方图分桶数量
#         self.bins = defaultdict(int)  # 桶计数（键：桶索引，值：计数）
#         self.min = None  # 全局最小长度
#         self.max = None  # 全局最大长度
#         self.tdigest = TDigest()  # 用于中位数统计
#         self.total_length = 0.0   # 新增：所有有效长度的总和
#         self.total_sq_length = 0.0  # 新增：所有有效长度的平方和
#
#     def update(self, data: pd.Series) -> None:
#         self.total_samples += len(data)
#         self.nan_count += data.isnull().sum()
#         cleaned = data.dropna().astype(str)
#         if cleaned.empty:
#             return
#
#         # 计算当前文件数据的长度
#         lengths = cleaned.str.len()
#         current_lengths = lengths.tolist()  # 转换为列表以便遍历
#
#         # 更新全局最小/最大长度
#         current_min = min(current_lengths) if current_lengths else None
#         current_max = max(current_lengths) if current_lengths else None
#         if current_min is not None:
#             if self.min is None or current_min < self.min:
#                 self.min = current_min
#         if current_max is not None:
#             if self.max is None or current_max > self.max:
#                 self.max = current_max
#
#         # 更新TDigest（用于中位数统计）
#         for length in current_lengths:
#             self.tdigest.update(length)
#
#         # 新增：累加总长度和平方和
#         self.total_length += sum(current_lengths)
#         self.total_sq_length += sum(length**2 for length in current_lengths)
#
#         # 更新分桶计数（仅当全局min/max确定后）
#         if self.min is not None and self.max is not None and self.min != self.max:
#             bin_width = (self.max - self.min) / self.num_bins
#             for length in current_lengths:
#                 bin_idx = int((length - self.min) / bin_width)
#                 bin_idx = max(0, min(bin_idx, self.num_bins - 1))  # 确保索引在范围内
#                 self.bins[bin_idx] += 1
#
#     def to_stats(self) -> Dict[str, Any]:
#         valid_count = self.total_samples - self.nan_count
#         stats = {
#             "nan_count": self.nan_count,
#             "nan_proportion": round(self.nan_count / self.total_samples, 4) if self.total_samples else 0.0,
#             "min": self.min,
#             "max": self.max,
#             "mean": None,
#             "median": None,
#             "std": None,
#             "histogram": {"hist": [], "bin_edges": []}
#         }
#
#         if valid_count == 0:
#             return stats
#
#         # 计算中位数（使用TDigest）
#         if self.tdigest.n > 0:
#             stats["median"] = round(self.tdigest.percentile(50), 2)
#
#         # 计算均值和标准差（使用手动维护的累加值）
#         if valid_count > 0:
#             # 均值 = 总长度 / 有效数量
#             stats["mean"] = round(self.total_length / valid_count, 2)
#
#             # 方差 = (总平方和 - (总长度^2)/有效数量) / 有效数量
#             variance = (self.total_sq_length - (self.total_length ** 2) / valid_count) / valid_count
#             stats["std"] = round(np.sqrt(variance), 2)
#
#         # 生成直方图数据
#         if self.min is not None and self.max is not None and self.min != self.max:
#             bin_width = (self.max - self.min) / self.num_bins
#             hist = [self.bins.get(i, 0) for i in range(self.num_bins)]
#             bin_edges = [self.min + i * bin_width for i in range(self.num_bins + 1)]
#             stats["histogram"] = {
#                 "hist": hist,
#                 "bin_edges": bin_edges
#             }
#
#         return stats
#
# class BooleanAccumulator:
#     """处理布尔类型（bool）数据的统计"""
#
#     def __init__(self):
#         self.nan_count = 0  # 空值数量
#         self.total_samples = 0  # 总样本数
#         self.true_count = 0  # 真值（True）数量
#         self.false_count = 0  # 假值（False）数量
#
#     def update(self, data: pd.Series) -> None:
#         """更新统计信息（保持原有逻辑不变）"""
#         self.total_samples += len(data)
#         self.nan_count += data.isna().sum()
#
#         cleaned = data.dropna()
#         if cleaned.empty:
#             return
#
#         # 统计真值和假值数量（逻辑优化：直接通过value_counts）
#         counts = cleaned.value_counts().to_dict()
#         self.true_count += counts.get(True, 0)
#         self.false_count += counts.get(False, 0)
#
#     def to_stats(self) -> Dict[str, Any]:
#         """转换为要求的column_statistics结构"""
#         return {
#             "nan_count": self.nan_count,
#             "nan_proportion": round(self.nan_count / self.total_samples, 4) if self.total_samples else 0.0,
#             "frequencies": {
#                 "True": self.true_count,
#                 "False": self.false_count
#             }
#         }
#
# class ListAccumulator:
#     """
#     列表类型（list）数据的统计累加器
#     支持流式更新、多文件合并统计，仅基于列表长度计算指定stats结构
#     """
#
#     def __init__(self, num_bins: int = 100):
#         self.total_samples = 0  # 总样本数（所有文件/批次的总行数）
#         self.nan_count = 0  # 列表本身为缺失（None）的总数
#         self.lengths: List[int] = []  # 所有非缺失列表的长度（用于直方图和精确统计）
#         self.tdigest = TDigest()  # 用于近似计算中位数（内存友好）
#         self.num_bins = num_bins  # 直方图分桶数
#
#     def update(self, data: pd.Series, field: pa.Field) -> None:
#         """
#         流式更新统计信息（处理单个文件/批次的列表数据）
#
#         参数:
#             data: 当前文件/批次的列表数据（pd.Series，每个元素是list或None）
#             field: pyarrow字段描述（用于类型验证）
#         """
#         # 类型验证（确保是列表类型）
#         if not isinstance(field.type, pa.ListType):
#             raise ValueError(f"Field {field.name} expected to be pa.ListType, got {type(field.type)}")
#
#         # 更新总样本数和缺失数
#         current_samples = len(data)
#         current_nan = data.isna().sum()
#         self.total_samples += current_samples
#         self.nan_count += current_nan
#
#         # 处理非缺失的列表数据
#         non_missing = data.dropna()
#         if non_missing.empty:
#             return
#
#         # 提取列表长度并累加
#         current_lengths = non_missing.apply(len).tolist()
#         self.lengths.extend(current_lengths)  # 存储所有非缺失列表的长度（用于精确统计）
#
#         # 更新TDigest（用于中位数近似）
#         for length in current_lengths:
#             self.tdigest.update(length)
#
#     def to_stats(self) -> Dict[str, Any]:
#         """
#         合并所有统计信息，生成符合要求的stats结构
#         """
#         valid_count = self.total_samples - self.nan_count
#         stats = {
#             "nan_count": self.nan_count,
#             "nan_proportion": round(self.nan_count / self.total_samples, 4) if self.total_samples else 0.0,
#             "min": None,
#             "max": None,
#             "mean": None,
#             "median": None,
#             "std": None,
#             "histogram": {"hist": [], "bin_edges": []}
#         }
#
#         if valid_count == 0:
#             return stats
#
#         # 计算基础统计量（基于存储的长度数据）
#         stats["min"] = min(self.lengths)
#         stats["max"] = max(self.lengths)
#         stats["mean"] = round(sum(self.lengths) / valid_count, 2)
#         stats["median"] = round(self.tdigest.percentile(50), 2)  # 使用TDigest近似中位数
#         stats["std"] = round(np.std(self.lengths), 2)  # 标准差（基于完整数据）
#
#         # 计算长度直方图（基于存储的长度数据）
#         if len(self.lengths) > 0 and stats["min"] != stats["max"]:
#             hist, bin_edges = np.histogram(self.lengths, bins=self.num_bins)
#             stats["histogram"] = {
#                 "hist": hist.tolist(),
#                 "bin_edges": bin_edges.tolist()
#             }
#
#         return stats
#
# class GenericAccumulator:
#     """通用类型累加器（扩展用）"""
#
#     def __init__(self):
#         self.count = 0
#
#     def update(self, data: pd.Series) -> None:
#         self.count += len(data)
#
#     def to_stats(self) -> Dict[str, Any]:
#         return {"count": self.count}

def get_files_with_suffix(dir_path, target_suffix):
    """
    获取目录下指定后缀的文件列表（仅文件，不包含目录）

    :param dir_path: 目标目录路径
    :param target_suffix: 目标后缀（如'.txt'）
    :return: 符合条件的文件名列表
    """
    # 遍历目录下所有条目，并过滤出符合条件的文件
    return [
        filename
        for filename in os.listdir(dir_path)
        if filename.endswith(target_suffix)  # 检查后缀匹配
           and os.path.isfile(os.path.join(dir_path, filename))  # 确保是文件而非目录
    ]

if __name__ == "__main__":
    generator = DescriptiveStatisticsGenerator()
    # generator.generate_and_save_json("D:\hqr\workspace\csvfiles\output\csv\patents_detail_cs\patents_detail_cs_part000.parquet",
    #                                  "D:\hqr\workspace\csvfiles\output\csv\patents_detail_cs\patents_detail_cs_part000.json")
    dir_path = "D:\\hqr\\workspace\\csvfiles\\output\\bigparquet\\4mula_small"
    file_name_list = get_files_with_suffix(dir_path, "parquet")
    abs_paths = [
        os.path.abspath(os.path.join(dir_path, name))
        for name in file_name_list
    ]
    generator.generate_and_save_json_folder(abs_paths, "D:\\hqr\\workspace\\csvfiles\\output\\bigparquet\\4mula_small\\4mula_small.json")