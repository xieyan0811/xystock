import baostock as bs
import os
import argparse


OUTPUT = '/app/data/stockdata/'


def mkdir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


class Downloader(object):
    def __init__(self,
                 output_dir,
                 date_start='1990-01-01',
                 date_end='2025-09-05',
                 stock_code=None):
        self._bs = bs
        bs.login()
        self.date_start = date_start
        self.date_end = date_end
        self.output_dir = output_dir
        self.fields = "date,code,open,high,low,close,volume,amount," \
                      "adjustflag,turn,tradestatus,pctChg,peTTM," \
                      "pbMRQ,psTTM,pcfNcfTTM,isST"
        self.stock_code = stock_code

    def exit(self):
        bs.logout()

    def get_codes_by_date(self, date):
        print(date)
        stock_rs = bs.query_all_stock(date)
        stock_df = stock_rs.get_data()
        print(stock_df)
        return stock_df

    def run(self):
        if self.stock_code:
            # 只下载指定股票
            print(f'processing {self.stock_code}')
            # 获取股票名称
            stock_df = self.get_codes_by_date(self.date_end)
            row = stock_df[stock_df['code'] == self.stock_code]
            if row.empty:
                print(f"股票代码 {self.stock_code} 未找到")
            else:
                code_name = row.iloc[0]["code_name"]
                df_code = bs.query_history_k_data_plus(self.stock_code, self.fields,
                                                       start_date=self.date_start,
                                                       end_date=self.date_end).get_data()
                df_code.to_csv(f'{self.output_dir}/{self.stock_code}.{code_name}.csv', index=False)
        else:
            # 下载全部股票
            stock_df = self.get_codes_by_date(self.date_end)
            for index, row in stock_df.iterrows():
                print(f'processing {row["code"]} {row["code_name"]}')
                df_code = bs.query_history_k_data_plus(row["code"], self.fields,
                                                       start_date=self.date_start,
                                                       end_date=self.date_end).get_data()
                df_code.to_csv(f'{self.output_dir}/{row["code"]}.{row["code_name"]}.csv', index=False)
        self.exit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download stock data')
    parser.add_argument('--stock_code', type=str, default=None, help='指定股票代码，如 sh.600036')
    parser.add_argument('--date_start', type=str, default='1990-01-01', help='开始日期')
    parser.add_argument('--date_end', type=str, default='2025-09-05', help='结束日期') # 注意必须为开盘日
    parser.add_argument('--output_dir', type=str, default=OUTPUT, help='输出目录')
    args = parser.parse_args()

    mkdir(args.output_dir)
    downloader = Downloader(args.output_dir, date_start=args.date_start, date_end=args.date_end, stock_code=args.stock_code)
    downloader.run()

