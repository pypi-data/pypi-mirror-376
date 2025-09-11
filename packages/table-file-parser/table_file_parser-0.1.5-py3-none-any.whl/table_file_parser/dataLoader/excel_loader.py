import os
import tempfile

import pandas as pd
import re
from .base_file_loader import FileLoader
from ..utils.header_detector import detect_excel_sheet_header
from ..utils.thread_util import read_sheet_parallel_with_timeout, read_sheet_parallel_with_timeout_new


class ExcelLoader(FileLoader):
    def read_and_convert(self):
        """处理Excel文件"""
        output_file_path = []
        excel = None
        ext = os.path.splitext(self.input_path)[1].lower()
        engine = 'xlrd' if ext == '.xls' else 'openpyxl'
        try :
            if ext == '.xls':
                try:
                    excel = pd.ExcelFile(self.input_path, engine="xlrd")
                    engine = "xlrd"
                except Exception as e:
                    print(F"{self.input_path}不是xls格式，尝试通过xlsx格式进行读取 {e}")
                    excel = pd.ExcelFile(self.input_path, engine="openpyxl")
                    engine = "openpyxl"
            elif ext == '.xlsx':
                excel = pd.ExcelFile(self.input_path, engine="openpyxl")
                engine = "openpyxl"
        except Exception as e2:
            print(f"{self.input_path} 也无法用 openpyxl 读取，尝试转换为 CSV/TSV: {e2}")
            # 尝试转存为 CSV/TSV
            df = self._try_convert_to_csv_tsv(self.input_path)
            if df is not None:
                # 模拟只有一个 sheet 的 Excel
                sheet_name = base_name = os.path.splitext(os.path.basename(self.input_path))[0]
                sheet_output_dir = f'{self.output_prefix}{os.sep}{sheet_name}{os.sep}'
                os.makedirs(sheet_output_dir, exist_ok=True)
                sheet_prefix = f"{sheet_output_dir}{sheet_name}"

                chunks = [df]  # 直接作为 chunk 处理
                output_file_path += self.write_function(chunks, sheet_prefix, self.output_format, self.max_size)
                return output_file_path
            else:
                raise RuntimeError(f"无法解析文件 {self.input_path}，尝试了 xls、xlsx、csv、tsv 格式") from e2

        for sheet_name in excel.sheet_names:
            try:
                #df = excel.parse(sheet_name, data_only=True)
                # df = read_sheet_with_timeout(self.input_path, sheet_name, engine=engine)
                # 判断是否有列名行
                has_header = detect_excel_sheet_header(excel, sheet_name)
                df = read_sheet_parallel_with_timeout_new(self.input_path, sheet_name, engine=engine, has_header=has_header)
                if df is None:
                    continue
                # 处理sheet中的特殊字符，以免存储时出错
                invalid_chars = self.get_invalid_chars()
                clear_sheet_name = re.sub(f"[{re.escape(invalid_chars)}]", "", sheet_name)
                # sheet_prefix = os.path.join(output_prefix, f"{clear_sheet_name}")

                # 这里按照 文件名_sheet名 创建文件夹
                # sheet_output_dir = f'{output_prefix}{current_sep}{file_name}_{clear_sheet_name}{current_sep}'
                sheet_output_dir = f'{self.output_prefix}{os.sep}{clear_sheet_name}{os.sep}'
                os.makedirs(sheet_output_dir, exist_ok=True)
                # sheet_prefix = f"{sheet_output_dir}{file_name}_{clear_sheet_name}"
                sheet_prefix = f"{sheet_output_dir}{clear_sheet_name}"
                # 合并所有output_file_path
                chunks = self._split_dataframe_by_size(df, self.max_size, self.output_prefix)
                output_file_path += self.write_function(chunks, sheet_prefix, self.output_format,
                                                                      self.max_size)
            except Exception as e:
                print(f"处理Excel文件 {self.input_path} 的sheet {sheet_name} 失败: {str(e)}")
                self.logger_manager.output_log(f"处理Excel文件 {self.input_path} 的sheet {sheet_name} 失败: {str(e)}", self.output_prefix)
        return output_file_path

    def is_valid_xls(self, file_path):
        """检查文件是否为有效的 Excel BIFF (xls) 文件"""
        with open(file_path, "rb") as f:
            header = f.read(8)
            # Excel BIFF 文件头通常是 0x09 0x08 开头
            return header[:2] == b'\x09\x08'

    def _try_convert_to_csv_tsv(self, file_path):
        """尝试将文件转存为 CSV 和 TSV，并尝试读取"""
        temp_dir = self.output_prefix
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        csv_path = os.path.join(temp_dir, f"{base_name}.csv")
        tsv_path = os.path.join(temp_dir, f"{base_name}.tsv")

        # 检查是否为纯文本文件
        if not self.is_text_file(file_path):
            print(f"{file_path} 不是纯文本文件，无法转换为 CSV/TSV")
            return None

        try:
            # 直接尝试自动识别分隔符（不修改文件）
            # 如果自动识别失败，尝试读取为纯文本并保存为 CSV
            df = pd.read_csv(file_path, sep=None, engine='python')
            print(f"成功自动识别分隔符并读取文件: {file_path}")
            return df
        except Exception as e:
            print(f"无法自动识别分隔符: {e}")

        try:
            # 尝试读取为文本并保存为 CSV
            with open(file_path, 'r', encoding='utf-8') as fin:
                content = fin.read().replace(',', '\t')
            with open(csv_path, 'w', encoding='utf-8') as fout:
                fout.write(content)
            df = pd.read_csv(csv_path)
            print(f"成功通过 CSV 格式读取文件: {file_path}")
            return df
        except Exception as e1:
            print(f"无法将文件保存为 CSV 或读取 CSV: {e1}")

        try:
            # 尝试保存为 TSV 并读取
            with open(file_path, 'r', encoding='utf-8') as fin:
                content = fin.read().replace(',', '\t')
            with open(tsv_path, 'w', encoding='utf-8') as fout:
                fout.write(content)
            df = pd.read_csv(tsv_path, sep='\t')
            print(f"成功通过 TSV 格式读取文件: {file_path}")
            return df
        except Exception as e2:
            print(f"无法将文件保存为 TSV 或读取 TSV: {e2}")
            return None

    def is_text_file(self, file_path, chunk_size=1024, encoding='utf-8'):
        """检测文件是否为纯文本文件"""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read(chunk_size)
            return True
        except UnicodeDecodeError:
            return False