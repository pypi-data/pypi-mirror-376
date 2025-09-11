import logging

import duckdb
from pathlib import Path
from typing import List, Union
import pyarrow.parquet as pq
from ..utils.FileLogger import FileErrorLogger

class DuckDBFTSIndexer:
    """
    DuckDB全文搜索引擎工具类
    功能：为Parquet文件创建全文搜索索引
    
    版本要求：DuckDB 1.0+
    文档：https://duckdb.org/docs/extensions/full_text_search
    """
    
    def __init__(self, default_index_colum = '__index__', overwrite = True, fts_params = None):
        self.supported_text_types = {
            'VARCHAR', 'TEXT', 'STRING', 
            'CHAR', 'BLOB', 'BPCHAR'
        }
        self.default_index_colum = default_index_colum
        self.overwrite = overwrite
        self.fts_params = {
            'overwrite': 1,
            'lower': 1
        } if fts_params is None else fts_params
        self.logger_manager = FileErrorLogger()

    def create_fts_index(
        self,
        parquet_path: Union[str, Path],
        index_name: str = None,
        columns: List[str] = None,
        fts_params: dict = None
    ) -> str:
        """
        创建全文搜索索引
        
        :param parquet_path: Parquet文件路径
        :param index_name: 索引名称（默认使用文件名）
        :param columns: 要索引的列（默认自动检测文本列）
        :param overwrite: 是否覆盖已有数据库
        :param fts_params: FTS参数配置字典
            支持参数：stopwords, stemmer, ignore, lower, strip_accents
            示例：{'stopwords': 'english', 'lower': True}
        :return: 生成的索引数据库路径
        """
        parquet_path = Path(parquet_path).resolve()
        self._validate_parquet(parquet_path)

        db_path = self._get_db_path(parquet_path)
        self._handle_existing_db(db_path, self.overwrite)

        conn = duckdb.connect(str(db_path))
        try:
            # 基础配置
            self._load_fts_extension(conn)
            
            # 创建基础表
            source_table = self._import_parquet(conn, parquet_path)
            
            # 解析索引列
            index_columns = self._get_text_columns(conn, source_table, columns)

            # 如果没有识别出的字符串属性列，则不生成duckdb索引
            if len(index_columns) < 1:
                print(f"{parquet_path.stem} 无法识别出字符串属性列，无法创建全文索引！ ")
                return None

            # 创建索引
            index_name = index_name or parquet_path.stem
            input_id = self.default_index_colum
            self._create_fts_core(
                conn,
                source_table=source_table,
                input_id=input_id,
                columns=index_columns,
                fts_params=fts_params or self.fts_params,
                index_name=index_name
            )
            
            return str(db_path.absolute())
        except Exception as e:
            print(f"{parquet_path}创建索引失败: {e}")
            self.logger_manager.output_log(str(e), parquet_path.name.split(".")[0])
        finally:
            conn.close()

    def search(self, db_path, search_term, limit=100):
        """修复后的搜索方法"""
        conn = duckdb.connect(str(db_path))
        try:
            # 获取实际索引表名
            index_table = self._get_fts_table_name(conn)

            return conn.execute(f"""
                SELECT 
                    {index_table}.score AS _relevance,
                    source.*
                FROM {index_table}
                JOIN parquet_source AS source
                ON {index_table}.__index__ = source.__index__
                WHERE {index_table}.match(?)
                ORDER BY _relevance DESC
                LIMIT ?
            """, [search_term, limit]).fetchall()
        finally:
            conn.close()

    # region 私有方法
    def _validate_parquet(self, path: Path):
        """验证Parquet文件有效性"""
        if not path.exists():
            raise FileNotFoundError(f"Parquet文件不存在: {path}")
        if path.suffix.lower() != '.parquet':
            raise ValueError("仅支持.parquet文件扩展名")

    def _get_db_path(self, parquet_path: Path) -> Path:
        """生成数据库路径"""
        return parquet_path.parent / f"{parquet_path.stem}_fts.duckdb"

    def _handle_existing_db(self, db_path: Path, overwrite: bool):
        """处理已存在数据库"""
        if db_path.exists():
            if overwrite:
                db_path.unlink(missing_ok=True)
            else:
                raise FileExistsError(
                    f"索引数据库已存在: {db_path}，请使用overwrite=True覆盖"
                )

    def _load_fts_extension(self, conn: duckdb.DuckDBPyConnection):
        """加载FTS扩展"""
        conn.execute("INSTALL fts")
        conn.execute("LOAD fts")

    def _import_parquet(self, conn: duckdb.DuckDBPyConnection, path: Path) -> str:
        """导入Parquet数据"""
        # 这里因为huggingface都是命名为data，且每个文件单独一个duckdb，所以这里直接使用data
        # table_name = f"parquet_{path.stem}"
        table_name = "data"
        conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM read_parquet('{path}')")
        # 添加索引标识列
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {self.default_index_colum} UINT64")
        conn.execute(f"UPDATE {table_name} SET {self.default_index_colum} = rowid")
        return table_name

    def _get_text_columns(self, conn: duckdb.DuckDBPyConnection, table: str, user_columns: List[str] = None) -> List[str]:
        """获取文本列列表"""
        if user_columns:
            return self._validate_columns(conn, table, user_columns)
        
        # 自动检测文本列
        columns = conn.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{table}'
              AND data_type IN {tuple(self.supported_text_types)}
        """).fetchall()
        
        if not columns:
            raise ValueError("未检测到支持的文本列，无法生成全文索引")

        # 过滤非中文列
        non_chinese_columns = []
        for col in columns:
            column_name = col[0]
            if not self._is_chinese_column(conn, table, column_name):
                non_chinese_columns.append(column_name)

        if not non_chinese_columns:
            raise ValueError("未检测到非中文文本列，无法生成全文索引")

        return non_chinese_columns

        # return [col[0] for col in columns]

    def _validate_columns(self, conn: duckdb.DuckDBPyConnection, table: str, columns: List[str]) -> List[str]:
        """验证用户指定列有效性"""
        valid_cols = [row[0] for row in conn.execute(f"DESCRIBE {table}").fetchall()]
        invalid = set(columns) - set(valid_cols)
        if invalid:
            raise ValueError(f"无效列名: {invalid}，可用列: {valid_cols}")
        return columns

    def _is_chinese_column(self, conn: duckdb.DuckDBPyConnection, table_name: str, origin_column_name: str, sample_size=10):
        """
        判断某列是否主要为中文内容
        :param conn: DuckDB 连接
        :param table_name: 表名
        :param column_name: 列名
        :param sample_size: 采样行数
        :return: True 表示是中文列，False 表示非中文列
        """
        column_name = _escape_column_name(origin_column_name)
        sql = f"SELECT '{column_name}' FROM {table_name} WHERE {column_name} IS NOT NULL AND {column_name} != '' LIMIT {sample_size}"
        rows = conn.execute(sql).fetchall()

        chinese_count = 0
        for row in rows:
            value = row[0]
            if not isinstance(value, str):
                continue
            # 判断字符串中是否包含中文字符
            if any('\u4e00' <= char <= '\u9fff' for char in value):
                chinese_count += 1

        return False if len(rows) == 0 else (chinese_count / len(rows) > 0.5)  # 超过一半含中文则认为是中文列

    def _create_fts_core(
        self,
        conn: duckdb.DuckDBPyConnection,
        source_table: str,
        input_id: str,
        columns: List[str],
        fts_params: dict,
        index_name: str
    ):
        """创建FTS索引核心逻辑"""
        # columns_array = f"[{colum_temp}]"

        # 构建参数列表（过滤None值）
        param_list = []
        for key, value in fts_params.items():
            if value is None:
                continue
            if isinstance(value, bool):
                param_list.append(f"{key} = {str(value).lower()}")
            elif isinstance(value, str):
                param_list.append(f"{key} = '{value}'")
            else:
                param_list.append(f"{key} = {value}")

        # 如果列数超过1000，DuckDB会报错，所以需要分批处理
        if len(columns) > 1000:
            print("表{index_name}的行数过长，超出1000行，只对前500有效字符行进行全文索引！")

        max_batch_size = 500
        # for i in range(0, len(columns), max_batch_size):
        batch_columns = columns[0: min(len(columns), max_batch_size)]
        colum_temp = ', '.join(f"'{c}'" for c in batch_columns)

        # 构建完整的PRAGMA语句
        pragma_sql = f"""
            PRAGMA create_fts_index(
                '{source_table}',
                '{input_id}',
                {colum_temp}
                {', ' + ', '.join(param_list) if param_list else ''}
            )
        """

        # 打印验证（实际使用时应移除）
        print("Executing SQL:\n", pragma_sql)

        # 执行语句
        conn.execute(pragma_sql)

        # 查看所有表（包括虚拟表）
        tables = conn.execute("SHOW ALL TABLES").fetchall()
        print(tables)

        # 检查虚拟表是否存在
        try:
            conn.execute("SELECT * FROM fts_main_data.docs LIMIT 1").fetchall()
            print(f"全文索引虚拟表 {index_name}_fts 存在且可查询！")
        except duckdb.BinderException as e:
            print(f"全文索引虚拟表 {index_name}_fts 查询失败:", e)

        # check_sql = f"""
        #     SELECT *
        #     FROM (
        #         SELECT *, fts_main_{source_table}.match_bm25(
        #             {input_id},
        #             'GRDC',
        #             fields := 'database'
        #         ) AS score
        #         FROM {source_table}
        #     ) sq
        #     WHERE score IS NOT NULL
        #       AND no > 1
        #     ORDER BY score DESC;
        # """
        #
        # print(check_sql)
        #
        # if not conn.execute(check_sql).fetchone():
        #     raise RuntimeError("FTS系统表未创建成功")
        # else:
        #     print("FTS系统表创建成功")

    def _format_param_value(self, value):
        """参数值格式化"""
        if isinstance(value, bool):
            return 'true' if value else 'false'
        if isinstance(value, str):
            return f"'{value}'"
        return str(value)

    def _get_fts_table_name(self, conn):
        """动态获取FTS表名"""
        tables = conn.execute("""
            SELECT table_name 
            FROM duckdb_tables 
            WHERE table_name LIKE 'fts_%'
        """).fetchall()

        if not tables:
            raise ValueError("找不到FTS系统表")
        return tables[0][0]

    def print_parquet_columns(self,file_path):
        """读取并打印Parquet文件的所有列名"""
        table = pq.read_table(file_path)
        print("列名：", table.column_names)


def _escape_column_name(column_name: str) -> str:
    """
    如果列名是纯数字，则用双引号包裹；否则保持原样。

    :param column_name: 原始列名
    :return: 转义后的列名
    """
    if column_name.isdigit():
        return f'"{column_name}"'
    # 如果列名包含非字母数字或下划线的字符，用双引号包裹
    if not column_name.replace('_', '').isalnum():
        return f'"{column_name}"'
    return column_name

# 使用示例
# if __name__ == "__main__":
#     # # 初始化索引器
#     # indexer = DuckDBFTSIndexer()
#     #
#     # input_path = "D:\hqr\workspace\csvfiles\output\csv\\2024-03-13-12-10-24\\2024-03-13-12-10-24.parquet"
#     #
#     # indexer.print_parquet_columns(input_path)
#     #
#     # # 创建索引（自动模式）
#     # db_path = indexer.create_fts_index(
#     #     input_path
#     # )
#     # print(f"索引已创建：{db_path}")
#
#     # indexer.search("{db_path}.duckdb", "search_term")
#     conn = duckdb.connect(str("D:\hqr\workspace\csvfiles\output\csv\paper\paper_fts.duckdb"))
#     sql = f"""
#     SELECT id, author, title, year, score, __index__
#     FROM (
#       SELECT *,
#         fts_main_data.match_bm25(
#           __index__,
#           '2012',
#           fields := 'year'
#         ) AS score
#       FROM data
#     ) WHERE score IS NOT NULL
#        """
#
#     # sql = f"""
#     #     SELECT id, author, title, year
#     #     from  data
#     #     where year = '2012'
#     #        """
#
#     # sql = """SELECT field FROM paper_fts.fts_main_data.fields;"""
#
#     sql = """WITH year_field AS (
#   SELECT fieldid
#   FROM paper_fts.fts_main_data.fields
#   WHERE field = 'year'
# ),
# year_term AS (
#   SELECT termid
#   FROM paper_fts.fts_main_data.dict
#   WHERE term = '2012'
# )
# SELECT COUNT(*)
# FROM paper_fts.fts_main_data.terms
# WHERE fieldid = (SELECT fieldid FROM year_field)
#   AND termid = (SELECT termid FROM year_term);"""
#
#     sql = """SELECT * FROM paper_fts.fts_main_data.dict;"""
#
#     with conn:
#         arrow_table = conn.sql(sql).arrow()
#         rows = arrow_table.to_pylist()
#         print(rows)

