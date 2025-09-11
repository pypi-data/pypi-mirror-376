import os
from datetime import datetime
from typing import List
from .huggingface.my_huggingface_descriptive_statistics import DescriptiveStatisticsGenerator
from .duckDBUtils.my_parquet_fts_indexer_upgrade import DuckDBFTSIndexer
from .utils.split_file_name_format_checker import FormatChecker
from .utils.FileLogger import FileErrorLogger, Timer
from .utils.sciencedb_output_info_generator import Process_Output_Info
import yaml
from .dataWriter.base_writer_utils import save_as_output_format_with_chunks as write_function
from .dataLoader.file_loader_factory import FileReaderFactory

current_sep = os.sep

class FormParser :
    def __init__(self, SUPPORTED_EXTENSIONS = [".h5", ".ods", ".parquet", ".sav", ".tsv", ".csv", ".xls", ".xlsx", ".tab"],
                 output_format = 'parquet',
                 max_size = 5*1024**3):
        self.SUPPORTED_EXTENSIONS = SUPPORTED_EXTENSIONS
        self.max_size = max_size
        self.output_format = output_format
        self.support_output_format = ['parquet', 'arrow']
        self.logger_manager = FileErrorLogger()

    def set_output_format(self, output_format):
        """设置输出格式"""
        if output_format not in ['parquet', 'arrow']:
            raise ValueError("Unsupported output format. Choose 'parquet' or 'arrow'.")
        self.output_format = output_format

    def get_supported_extensions(self):
        """获取支持的文件扩展名"""
        return self.SUPPORTED_EXTENSIONS

    def get_support_output_format(self):
        """获取支持的输出格式"""
        return self.support_output_format

    def convert_to_output_format(self, input_path, output_prefix, file_name) -> List[str]:
        try:
            if not os.path.isfile(input_path):
                raise FileNotFoundError(f"File not found: {input_path}")

            ext = os.path.splitext(input_path)[1].lower()
            if ext not in self.SUPPORTED_EXTENSIONS:
                raise ValueError(f"Unsupported file type: {ext}")

            if output_prefix is None:
                output_prefix = os.path.dirname(input_path)
            os.makedirs(output_prefix, exist_ok=True)
            # 这里把按文件名称再创建一级目录的逻辑去除，改为再各自类型中自己特殊处理
            # output_prefix += f'{current_sep}{file_name}{current_sep}'
            # os.makedirs(output_prefix, exist_ok=True)

            output_file_path = []

            try:
                # 初始化Reader工厂
                file_loader = FileReaderFactory.create_reader(input_path, output_prefix, self.output_format,
                                                              self.max_size, 10000, write_function)
                output_file_path += file_loader.read_and_convert()

                # if ext == '.h5':
                #     # h5Tool = H5UltimateConverter(input_path, output_prefix, self.output_format, self.max_size)
                #     # output_file_path += h5Tool.convert_all()
                #     output_file_path += self.process_h5(input_path, output_prefix, file_name, ext)
                # elif ext in ['.xls', '.xlsx']:
                #     #这里修改了，不按文件名创建目录，而是直接在output_prefix下按 "文件名_sheet名" 创建文件夹
                #     # output_prefix += file_name
                #     output_file_path += self.process_excel(input_path, output_prefix, file_name, ext)
                # else:
                #     output_prefix += f'{current_sep}{file_name}{current_sep}'
                #     os.makedirs(output_prefix, exist_ok=True)
                #     output_prefix += file_name
                #     chunks = self.read_file_chunked(input_path, ext)
                #     output_file_path += save_as_output_format_with_chunks(chunks, output_prefix, self.output_format, self.max_size)
            except Exception as e:
                self.logger_manager.output_log(str(e), file_name)
                print(f"Error processing {input_path}: {str(e)}")

            return output_file_path

        except Exception as eo :
            self.logger_manager.output_log(str(eo), file_name)
            print(f"处理文件 {input_path} 时发生错误: {str(eo)}")

def load_config(config_path=f".{current_sep}configs{current_sep}config.yaml"):
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"配置文件 {config_path} 不存在！")
        return {}


def replace_last(s, old, new, n=1):
    parts = s.rsplit(old, n)
    return new.join(parts)

def processing_single_file(input_file_path : str, output_dir_path : str, output_format = 'parquet', max_size = 1 * 1024 ** 3) -> list[dict] :
    is_generating_dec = True
    is_generating_duckdb_index = True
    form_parser = FormParser(output_format=output_format, max_size=max_size)
    indexer = DuckDBFTSIndexer()
    format_checker = FormatChecker()

    if not os.path.isfile(input_file_path):
        print(f"'{input_file_path}' 不是文件或不存在")
        return []

    #处理结果存储列表
    result_json_list = []

    logger = FileErrorLogger()
    file_log_dir = logger.get_file_log_dir()

    # 初始化生成描述文件的工具类对象
    dec_generator = DescriptiveStatisticsGenerator()
    file_name = os.path.basename(input_file_path)
    with Timer() as timer:
        ext = os.path.splitext(file_name)[1].lower()

        if ext not in form_parser.SUPPORTED_EXTENSIONS:
            print(f"跳过不支持的文件类型: {file_name}")
            return result_json_list
        elif ext == '.h5' or ext == '.xls' or ext == '.xlsx':
            # 对于Excel文件，直接使用处理Excel的方法
            # 初始化处理结果
            parquet_list = []
            json_list = []
            fts_index_list = []
            fail_result_info = Process_Output_Info(output_format)
            is_parquet_proceed = False
            is_statistics_proceed = False
            is_fts_index_proceed = False
            try:
                try:
                    # 记录处理开始时间
                    fail_result_info.processing_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # file_path = data_root + f'{current_sep}' + file_name
                    file_path = input_file_path
                    print('正在添加 : ' + file_path)

                    # 获得table_id
                    fail_result_info.table_id = file_name.split(".")[0]

                    output_file_path_list = form_parser.convert_to_output_format(file_path, output_dir_path,
                                                                                 file_name.split(".")[0])
                    parquet_list = output_file_path_list
                    output_file_path_len = len(output_file_path_list)
                    # parquet成功生成
                    if output_file_path_list is not None and len(output_file_path_list) > 0:
                        is_parquet_proceed = True
                        parquet_list = output_file_path_list
                except Exception as e:
                    print(f'转换{output_format}出错 : {file_name}, 错误信息: {str(e)}')
                    fail_result_info.is_parquet_proceed = False
                    return result_json_list
                # 生成描述文件
                if is_generating_dec:
                    try:
                        json_count = 0
                        # excel一个sheet文件一般不会太大，这里还是每个文件生成一个json的逻辑
                        for output_file in output_file_path_list:
                            # 在同文件下生成描述文件
                            last_index = output_file.rfind('.')  # 找到最后一个 '.' 的索引位置
                            json_prefix = output_file[:last_index]  # 取 '.' 之前的所有字符
                            json_output_path = json_prefix + "_des" + ".json"
                            json_count += dec_generator.generate_and_save_json(output_file, json_output_path)
                            json_list.append(json_output_path)
                            # 生成描述文件成功
                            if json_count > 0:
                                is_statistics_proceed = True
                            # 获得描述文件路径
                            statistics_file_path = json_output_path
                    except Exception as e:
                        print(f'生成描述文件出错 : {file_name}, 错误信息: {str(e)}')
                        # 生成描述文件失败
                        fail_result_info.is_statistics_proceed = False
                        return result_json_list

                if is_generating_duckdb_index:
                    try:
                        # 生成duckdb索引
                        for output_file in output_file_path_list:
                            # 在同文件下生成描述文件
                            # 如果遇到分块文件，则只对第一个文件进行索引；未分块则直接创建
                            if format_checker.check_index_generate_format(output_file, output_format):
                                db_index_path = indexer.create_fts_index(output_file)
                                if db_index_path is not None:
                                    # 生成duckdb索引成功
                                    is_fts_index_proceed = True
                                    fts_index_file_path = db_index_path
                                    fts_index_list.append(db_index_path)
                    except Exception as e:
                        print(f'生成duckdb索引出错 : {file_name}, 错误信息: {str(e)}')
                        # 生成duckdb索引失败
                        fail_result_info.is_fts_index_proceed = False
                        return result_json_list

                if not is_parquet_proceed or not is_statistics_proceed or not is_fts_index_proceed:
                    # 如果有一个没成功，则说明有错误日志生成
                    log_file_path = file_log_dir + f"{current_sep}" + file_name + "_error.log"
                    fail_result_info.log_file_path = os.path.abspath(log_file_path)
                print('转换完成 : ' + file_name)
            except Exception as e:
                print(f'转换时出错 : {file_name}, 错误信息: {str(e)}')
            finally:
                # 进行输出结果组装
                # 记录处理结束时间
                fail_result_info.processing_end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # 如果parquet就没生成成功，则返回失败info
                if len(parquet_list) < 1:
                    final_file_processing_result = fail_result_info.generate_output_info()
                    print(f"{ext}文件处理失败 : {final_file_processing_result}")
                    result_json_list.append(final_file_processing_result)
                else:
                    # 这里要把每个结果按sheet再组装起来
                    current_sheet = ""
                    temp_info = None
                    for parquet_file_path in parquet_list:
                        sheet_name = parquet_file_path.split(f"{current_sep}")[-2]
                        if current_sheet != sheet_name:
                            # 如果当前sheet和上一个sheet不同，则需要结算上一个sheet，并重新初始化处理结果
                            if temp_info is not None:
                                result_json_list.append(temp_info.generate_output_info())
                            temp_info = Process_Output_Info()
                            # temp_info.table_id = file_name.split(".")[0] + "_" + sheet_name
                            temp_info.table_id = sheet_name
                            temp_info.is_parquet_proceed = True
                            temp_info.parquet_file_path = replace_last(parquet_file_path,
                                                             parquet_file_path.split(f"{current_sep}")[-1],
                                                             f"*.{output_format}", 1)
                            # 这里需要找到对应的描述文件和索引文件
                            for json_file in json_list:
                                if sheet_name in json_file:
                                    temp_info.statistics_file_path = json_file
                                    temp_info.is_statistics_proceed = True
                                    break
                            for index_file in fts_index_list:
                                if sheet_name in index_file:
                                    temp_info.fts_index_file_path = index_file
                                    temp_info.is_fts_index_proceed = True
                                    break
                            temp_info.processing_start_time = fail_result_info.processing_start_time
                            temp_info.processing_end_time = fail_result_info.processing_end_time
                            current_sheet = sheet_name
                        else:
                            # 如果与上一个sheet相同，则说明进行了分块，需要对split参数进行更新
                            temp_info.is_splited = True
                            temp_info.split_num += 1
                            temp_info.split_size = max_size
                    if temp_info is not None:
                        # 将当前sheet的处理结果添加到结果列表中
                        final_file_processing_result = temp_info.generate_output_info()
                        print(final_file_processing_result)
                        result_json_list.append(final_file_processing_result)
        else:
            # 初始化处理结果
            result_info = Process_Output_Info(output_format)
            try:
                try:
                    # 记录处理开始时间
                    result_info.processing_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    #file_path = input_file_path + f'{current_sep}' + file_name
                    file_path = input_file_path
                    print('正在添加 : ' + file_path)

                    # 获得table_id
                    result_info.table_id = file_name.split(".")[0]

                    output_file_path_list = form_parser.convert_to_output_format(file_path, output_dir_path, file_name.split(".")[0])
                    output_file_path_len = len(output_file_path_list)
                    # parquet成功生成
                    if output_file_path_list is not None and len(output_file_path_list) > 0:
                        result_info.is_parquet_proceed = True
                        # 获得parquet文件路径，*.parquet
                        result_info.parquet_file_path = replace_last(output_file_path_list[0], output_file_path_list[0].split(f"{current_sep}")[-1], f"*.{output_format}", 1)
                        if output_file_path_len > 1:
                            # 如果有多个文件，则记录分块信息
                            result_info.is_splited = True
                            result_info.split_num = output_file_path_len
                            result_info.split_size = max_size
                except Exception as e:
                    print(f'转换{output_format}出错 : {file_name}, 错误信息: {str(e)}')
                    result_info.is_parquet_proceed = False
                    return result_json_list
                # 生成描述文件
                if is_generating_dec:
                    try:
                        json_count = 0
                        #这里改为只生成一个描述文件
                        json_output_path = output_dir_path + current_sep + file_name.split(".")[0] + current_sep + file_name.split(".")[0] + "_des" + ".json"
                        json_count += dec_generator.generate_and_save_json_folder(output_file_path_list, json_output_path)
                        # for output_file in output_file_path_list:
                        #     # 在同文件下生成描述文件
                        #     json_output_path = output_file.split(".")[0] + "_des" + ".json"
                        #     json_count += dec_generator.generate_and_save_json(output_file, json_output_path)
                        # 生成描述文件成功
                        if json_count > 0:
                            result_info.is_statistics_proceed = True
                        # 获得描述文件路径
                        result_info.statistics_file_path = json_output_path
                    except Exception as e:
                        print(f'生成描述文件出错 : {file_name}, 错误信息: {str(e)}')
                        # 生成描述文件失败
                        result_info.is_statistics_proceed = False
                        return result_json_list

                if is_generating_duckdb_index:
                    try:
                        # 生成duckdb索引
                        for output_file in output_file_path_list:
                            # 在同文件下生成描述文件
                            # 如果遇到分块文件，则只对第一个文件进行索引；未分块则直接创建
                            if format_checker.check_index_generate_format(output_file, output_format):
                                db_index_path = indexer.create_fts_index(output_file)
                                if db_index_path is not None:
                                    # 生成duckdb索引成功
                                    result_info.is_fts_index_proceed = True
                                    result_info.fts_index_file_path = db_index_path
                    except Exception as e:
                        print(f'生成duckdb索引出错 : {file_name}, 错误信息: {str(e)}')
                        # 生成duckdb索引失败
                        result_info.is_fts_index_proceed = False
                        return []

                if not result_info.is_parquet_proceed or not result_info.is_statistics_proceed or not result_info.is_fts_index_proceed:
                    # 如果有一个没成功，则说明有错误日志生成
                    log_file_path = file_log_dir+ f"{current_sep}" + file_name + "_error.log"
                    result_info.log_file_path = os.path.abspath(log_file_path)
                print('转换完成 : ' + file_name)
            except Exception as e:
                print(f'转换时出错 : {file_name}, 错误信息: {str(e)}')
            finally:
                # 进行输出结果组装
                # 记录处理结束时间
                result_info.processing_end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                final_file_processing_result = result_info.generate_output_info()
                print(final_file_processing_result)
                result_json_list.append(final_file_processing_result)

    elapsed = timer.get_elapsed_time()
    print(f"文件 : {file_name}  转换耗时 : {elapsed}")

    print('转换完毕！')
    return result_json_list


# if __name__ == "__main__":

    # is_testing_generate = True
    # #is_generating_dec = True
    # #is_generating_duckdb_index = True
    # index = 0
    # index_min = 8
    # index_max = 8
    #
    # # 使用配置
    # config = load_config()
    # output_root = config.get('paths', {}).get('output_root', f'{current_sep}default{current_sep}data')
    # data_root = config.get('paths', {}).get('data_root', f'{current_sep}default{current_sep}data')
    #
    # form_type_list = [".h5", ".ods", ".parquet", ".sav", ".tsv", ".csv", ".xls", ".xlsx", ".tab"]
    # form_folder_list = ["h5", "ods", "parquet", "sav", "tsv", "csv", "xls", "xlsx", "tab", "bigcsv", "bigparquet"]
    # # output_root = 'D:\hqr\workspace\csvfiles\output'
    #
    # # form_parser = FormParser( form_type_list, output_format='parquet', max_size=1*1024**3)
    # # indexer = DuckDBFTSIndexer()
    # # format_checker = FormatChecker()
    #
    # for i in range(index_min, index_max + 1):
    #     index = i
    #     # if not is_testing_generate:
    #     output_root += form_folder_list[index]
    #
    #     # data_root = 'D:\hqr\workspace\csvfiles\样例数据'
    #     # data_root = 'D:\hqr\workspace\csvfiles\\'
    #     data_root = data_root + form_folder_list[index]
    #
    #     #file_name_list = os.listdir(data_root)
    #     file_name_list = os.listdir(data_root)
    #     absolute_paths = [os.path.join(data_root, fname) for fname in file_name_list]
    #     if absolute_paths is None or len(absolute_paths) == 0:
    #         print(f"输入目录 {data_root} 中没有文件！")
    #
    #     for file_name in absolute_paths:
    #         processing_single_file(file_name, output_root, "parquet", 1 * 1024 ** 3)
    #
    #     # processing_file(data_root, output_root)
    #
    #     data_root = config.get('paths', {}).get('data_root', f'{current_sep}default{current_sep}data')
    #     output_root = config.get('paths', {}).get('output_root', f'{current_sep}default{current_sep}data')

