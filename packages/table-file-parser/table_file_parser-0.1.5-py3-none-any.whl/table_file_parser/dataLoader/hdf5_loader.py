import os
import numpy as np
import pandas as pd
import h5py
import re
from .base_file_loader import FileLoader

class HDF5Loader(FileLoader):
    def read_and_convert(self):
        output_file_path = []
        try:
            if not self.input_path or not os.path.isfile(self.input_path):
                print(f"[ERROR] 无效的 HDF5 文件路径: {self.input_path}")
                return []

            with h5py.File(self.input_path, 'r') as f:
                def recursively_collect_datasets(group, path=""):
                    """递归收集所有 Dataset 的路径"""
                    datasets = []
                    for name, item in group.items():
                        full_path = f"{path}/{name}" if path else name
                        if isinstance(item, h5py.Dataset):
                            datasets.append(full_path)
                        elif isinstance(item, h5py.Group):
                            datasets.extend(recursively_collect_datasets(item, full_path))
                    return datasets

                # 获取所有真正的 Dataset 路径（支持嵌套）
                dataset_paths = recursively_collect_datasets(f)

                if not dataset_paths or len(dataset_paths) == 0:
                    raise ValueError("HDF5 file contains no datasets")

                # 遍历每一个数据集
                for dataset_path in dataset_paths:
                    try:
                        dset = f[dataset_path]
                        data_array = dset[()]
                    except Exception as e:
                        print(f"读取数据集 {dataset_path} 失败: {e}")
                        continue

                    if data_array is None:
                        print(f"警告: 数据集 {dataset_path} 返回空数据")
                        continue

                    # 如果是结构化数组（如表格数据），尝试转换为 Pandas DataFrame
                    if isinstance(data_array, np.ndarray) and data_array.dtype.names:
                        df = pd.DataFrame(data_array)
                    else:
                        # 对于非结构化数组，尝试转换为二维 DataFrame
                        try:
                            df = pd.DataFrame(data_array)
                        except ValueError:
                            # 多维数组无法直接转为 DataFrame，展平后作为单列处理
                            df = pd.DataFrame({'data': data_array.flatten()})

                    invalid_chars = self.get_invalid_chars()
                    clear_dataset_name = re.sub(f"[{re.escape(invalid_chars)}]", "_", dataset_path)

                    # 这里按照 dataset名 创建文件夹
                    dataset_output_dir = f'{self.output_prefix}{os.sep}{clear_dataset_name}{os.sep}'
                    os.makedirs(dataset_output_dir, exist_ok=True)
                    dataset_prefix = f"{dataset_output_dir}{clear_dataset_name}"

                    chunks = self._split_dataframe_by_size(df, self.max_size, self.output_prefix)
                    output_file_path += self.write_function(chunks, dataset_prefix,self.output_format, self.max_size)

        except Exception as e:
            print(f"处理HDF5文件 {self.input_path} 失败: {str(e)}")
            self.logger_manager.output_log(f"处理HDF5文件 {self.input_path} 错误: {str(e)}", self.output_prefix)

        return output_file_path