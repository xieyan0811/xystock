# XY Stock Streamlit UI

基于 Streamlit 构建的股票分析系统Web界面。

## 功能特性

- 🎯 支持多市场查询：A股、港股、指数、基金
- 💻 简洁直观的用户界面
- 📊 实时股票信息展示
- 🚀 快速响应的查询体验

## 界面结构

- **左侧边栏**: 功能菜单和系统信息
- **右侧主区域**: 
  - 市场类型选择下拉框
  - 股票代码输入框  
  - 查询结果显示区域

## 启动方式

### 方式1: 使用Python脚本启动
```bash
cd /exports/stock/mine/xystock
python ui/start_ui.py
```

### 方式2: 使用Shell脚本启动
```bash
cd /exports/stock/mine/xystock
./ui/start_ui.sh
```

### 方式3: 直接使用Streamlit命令
```bash
cd /exports/stock/mine/xystock
streamlit run ui/app.py --server.port 8811 --server.address 0.0.0.0
```

## 访问地址

启动成功后，在浏览器中访问：
- http://localhost:8811
- http://0.0.0.0:8811

## 支持的股票代码示例

### A股
- 000001 (平安银行)
- 000002 (万科A)  
- 600000 (浦发银行)
- 600036 (招商银行)

### 港股
- 00700 (腾讯控股)
- 00941 (中国移动)
- 02318 (中国平安)

### 指数
- 000001 (上证指数)
- 399001 (深证成指)
- 399006 (创业板指)

### 基金
- 159915 (创业板ETF)
- 510300 (沪深300ETF)
- 512100 (中证1000ETF)

## 注意事项

1. 当前使用模拟数据进行演示
2. 实际部署时需要连接真实的股票数据源
3. 确保系统已安装所需的Python依赖包

## 技术栈

- **前端框架**: Streamlit
- **后端语言**: Python 3.x
- **数据源**: 可配置多种股票数据API
- **部署端口**: 8811

## 目录结构

```
ui/
├── app.py              # 主应用文件
├── config.py          # 配置文件
├── stock_provider.py  # 股票数据提供者
├── start_ui.py        # Python启动脚本
├── start_ui.sh        # Shell启动脚本
└── README.md          # 说明文档
```
