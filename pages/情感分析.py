import streamlit as st
import pandas as pd
import streamlit_echarts as ste
from snownlp import SnowNLP
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import numpy as np
import io



# 数据处理函数
@st.cache_data
def process_data(data):
    # 删除含有 NaN 的行
    data = data.dropna(subset=["review"])
    
    # 筛选评论为字符串类型的数据
    data = data[data["review"].map(lambda x: isinstance(x, str))]
    
    # 删除空字符串和无效数据
    data["review"] = data["review"].apply(lambda x: x.strip())
    data = data[data["review"] != ""]  # 删除空字符串
    
    return data

# 情感分析函数
def calculate_sentiment(df):
    # 计算情感得分
    df["sentiment"] = df["review"].apply(handle_sentiment)
    
    # 修饰情感分数
    bins = [0, 0.4, 0.6, 1]
    labels = ["消极", "中性", "积极"]
    df["sentiment_label"] = pd.cut(
        df["sentiment"], bins=bins, labels=labels, include_lowest=True
    )
    return df

def handle_sentiment(x):
    try:
        return SnowNLP(x).sentiments
    except:
        return 0.5  # 自定义默认值

# 生成情感饼图
def build_pie_chart(df):
    sentiment_counts = (
        df["sentiment_label"].value_counts(normalize=True).mul(100).round(1)
    )

    # 动态生成数据
    data = []
    for label in ["积极", "中性", "消极"]:
        value = sentiment_counts.get(label, 0)
        item = {
            "value": value,
            "name": label,
            "itemStyle": {"color": "#ff0000" if label == "积极" else "#9E9E9E" if label == "中性" else "#0000ff"}
        }
        data.append(item)

    option = {
        "title": {
            "text": "舆情情感分布",
            "left": "center",
            "textStyle": {"fontSize": 18},
        },
        "tooltip": {"trigger": "item"},
        "legend": {
            "orient": "vertical",
            "left": "left",
            "top": "middle",
        },
        "series": [
            {
                "type": "pie",
                "radius": ["40%", "70%"],
                "avoidLabelOverlap": True,
                "itemStyle": {
                    "borderRadius": 5,
                    "borderColor": "#fff",
                    "borderWidth": 2,
                },
                "label": {
                    "formatter": "{b}: {d}%",
                    "rich": {"fontSize": 14},
                },
                "emphasis": {
                    "itemStyle": {"shadowBlur": 10},
                    "label": {"show": True},
                },
                "data": data,
            }
        ],
    }
    return option

# 生成情感趋势分析图
def build_line_chart(df):
    # 确保 "发布时间" 列存在
    if "发布时间" not in df.columns:
        st.warning("数据中没有发布时间列，无法生成情感趋势图。")
        return {}
    
    # 转换时间为日期格式
    df["发布时间"] = pd.to_datetime(df["发布时间"]).dt.date  # Ensure date type
    
    # 按天分组获取情感得分均值并填充缺失值
    grouped = df.groupby("发布时间")
    sentiment_trend = grouped["sentiment"].mean().reset_index()
    
    # 创建完整的日期范围
    start_date = df["发布时间"].min()
    end_date = df["发布时间"].max()
    date_range = pd.date_range(start=start_date, end=end_date)
    
    # 创建新的 DataFrame 用于合并
    sentiment_trend_display = pd.DataFrame({"时间": date_range.date})
    
    # 合并并填充缺失值
    sentiment_trend_display = pd.merge(
        sentiment_trend_display, 
        sentiment_trend.rename(columns={"发布时间": "时间"}),
        on="时间",
        how="left"
    ).fillna(0)  # 填充空缺值
    
    # 调整图表展示的时间间隔
    delta = (end_date - start_date).days
    if delta > 365:
        freq = "M"  # 每月
    elif delta > 30:
        freq = "W"  # 每周
    else:
        freq = "D"  # 每天
    
    # 动态调整 x 轴标签间隔
    interval = get_dynamic_interval(delta)
    
    option = {
        "title": {
            "text": "舆情情感趋势",
            "left": "center",
            "textStyle": {"fontSize": 18},
        },
        "tooltip": {"trigger": "axis"},
        "xAxis": {
            "type": "category",
            "data": sentiment_trend_display["时间"].astype(str).tolist(),
            "axisLabel": {
                "rotate": 45,
                "interval": interval,  # 动态间隔
                "formatter": "{value}",
            },
            "boundaryGap": False,
        },
        "yAxis": {
            "type": "value",
            "name": "情感得分",
            "min": 0,
            "max": 1,
        },
        "series": [
            {
                "name": "情感得分",
                "type": "line",
                "data": sentiment_trend_display["sentiment"].tolist(),
                "symbolSize": 8,
                "smooth": True,
                "itemStyle": {"color": "#4CAF50"},
            }
        ],
    }
    return option

# 动态计算 x 轴标签间隔
def get_dynamic_interval(delta):
    if delta > 365:
        return 30  # 每月显示一次
    elif delta > 30:
        return 7  # 每周显示一次
    elif delta > 14:
        return 3  # 每3天显示一次
    else:
        return 1  # 每天显示一次
    
def main():    
    # 权限验证
    if not st.session_state.get("logged_in"):
        st.error("请先登录")
        st.stop()

    # 数据上传与初始化
    if "data" not in st.session_state:
        st.warning("请先上传文件")
        st.stop()
    else:
        data = st.session_state.data.copy()

    # 数据处理管道
    data = process_data(data)
    df = calculate_sentiment(data)

    # 渲染图表
    st.write("### 舆情情感分布可视化")
    pie_chart_options = build_pie_chart(df)
    ste.st_echarts(options=pie_chart_options, height="500px")

    st.write("### 舆情情感趋势分析")
    line_chart_options = build_line_chart(df)
    ste.st_echarts(options=line_chart_options, height="500px")

if __name__ == "__main__":
    main()       
