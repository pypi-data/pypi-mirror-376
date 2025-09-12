import traceback
from kaq_quant_common.kaq_quant_common.resources.kaq_mysql_resources import KaqBtcMysqlRepository
from kaq_quant_common.utils import yml_utils
from sqlalchemy import text

engine = KaqBtcMysqlRepository().get_conn_engine()

time_idx_dict = {
    'kaq_binance_perpetual_commission_rate_now' :  'ctimestamp',
}

def mysql_table_init(project_dir=None):
    for table_name, timestamp in time_idx_dict.items():
        file_name = table_name + '.sql'
        try:
            file_path = yml_utils.get_mysql_script(project_dir, file_name)
            if file_path is None:
                continue
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # 创建数据库
            with engine.connect() as conn:
                conn.execute(text(content))
            # 设置分区,只创建索引应该够了
            # partition_list = [f'PARTITION p{symbol}{_date} VALUES LESS THAN (\'{symbol}\', \'{_date}\'),' for _date in date_list for symbol in symbol_names]
            # partition_list = [f'PARTITION p{symbol} VALUES IN (\'{symbol}\')' for symbol in symbol_names]
            # partition_list_str = ', '.join(partition_list)
            # partition_script = f"ALTER TABLE {table_name} PARTITION BY LIST COLUMNS(symbol) ( {partition_list_str});"
            # with engine.connect() as conn:
            #     conn.execute(text(partition_script))
        except Exception as e:
            print(f'【创建{table_name} - 表】失败, {str(e)} - {str(traceback.format_exc())}')
            

if __name__ == '__main__':
    pass
        