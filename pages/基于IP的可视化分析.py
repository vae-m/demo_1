import streamlit as st
from pyecharts import options as opts
from pyecharts.charts  import Map,Bar, Pie
import pandas as pd 
from streamlit_echarts import st_pyecharts 
from mk import check_permissions  

# 配置中文环境 
def set_chinese(): 
    return opts.InitOpts( 
        theme="light",  # 内置主题支持中文 
        animation_opts=opts.AnimationOpts(animation_threshold=2000), 
        width="100%", 
        height="600px" 
    ) 

# 生成柱状图 
@st.cache_data 
def create_bar(data) -> Bar: 
    provinces = data.index.tolist()   
    counts = data.values.tolist()   
    
    bar = ( 
        Bar(init_opts=set_chinese()) 
      .add_xaxis(provinces) 
      .add_yaxis("舆情数量", counts) 
      .set_global_opts( 
            title_opts=opts.TitleOpts(title="各地舆情数量分布"), 
            xaxis_opts=opts.AxisOpts( 
                name="省份", 
                axislabel_opts=opts.LabelOpts(rotate=45)  # 倾斜标签 
            ), 
            datazoom_opts=[opts.DataZoomOpts()]  # 添加滚动条 
        ) 
    ) 
    return bar 

# 生成饼图 
@st.cache_data 
def create_pie(data) -> Pie: 
    pie = ( 
        Pie(init_opts=set_chinese()) 
      .add( 
            "", 
            [list(z) for z in zip(data.index.tolist(),    data.values.tolist())],   
            radius=["30%", "75%"],  # 环形饼图 
            rosetype="radius"  # 南丁格尔玫瑰图 
        ) 
      .set_global_opts( 
            title_opts=opts.TitleOpts(title="舆情各地占比"), 
            legend_opts=opts.LegendOpts(orient="vertical", pos_top="15%", pos_left="2%") 
        ) 
      .set_series_opts(label_opts=opts.LabelOpts(formatter="{{{{b}}}}: {{{{d}}}}%"))  # 百分比显示 
    ) 
    return pie 

@st.cache_data 
def count_provinces(df):
    province_map = {
        "江苏": "江苏省",
        "浙江": "浙江省",
        "安徽": "安徽省",
        "福建": "福建省",
        "江西": "江西省",
        "山东": "山东省",
        "河南": "河南省",
        "湖北": "湖北省",
        "湖南": "湖南省",
        "广东": "广东省",
        "广西": "广西壮族自治区",
        "海南": "海南省",
        "四川": "四川省",
        "贵州": "贵州省",
        "云南": "云南省",
        "西藏": "西藏自治区",
        "陕西": "陕西省",
        "甘肃": "甘肃省",
        "青海": "青海省",
        "宁夏": "宁夏回族自治区",
        "新疆": "新疆维吾尔自治区",
        "北京": "北京市",
        "天津": "天津市",
        "上海": "上海市",
        "重庆": "重庆市",
        "香港": "香港特别行政区",
        "澳门": "澳门特别行政区",
        "台湾": "台湾省"
    }

    if 'ip' not in df.columns: 
        st.error("CSV  文件中没有名为 'ip' 的列。")
        return []
    
    # 使用.loc 确保操作在原始数据框上进行
    df.loc[df['ip'].notna(),  'ip'] = df.loc[df['ip'].notna(),  'ip'].map(province_map)
    
    # 统计省份 IP 出现次数
    province_counts = df['ip'].value_counts().reset_index()
    province_counts.columns  = ['省份', '次数']
    
    data = list(zip(province_counts['省份'], province_counts['次数']))
    
    if not data:
        data = [["未记录", 0]]
    
    return data

# 创建地图
@st.cache_data 
def create_china_map(data):
    c = Map()
    c.add("IP 分布", data, "china")
    c.set_global_opts( 
        title_opts=opts.TitleOpts(title="中国省份 IP 分布地图"),
        visualmap_opts=opts.VisualMapOpts(max_=max([x[1] for x in data]) or 1)
    )
    c.set_series_opts( 
        label_opts=opts.LabelOpts(
            is_show=True,
            color="blue",
            formatter="{{b}}: {{c}}"  # 显示省份名称和次数
        )
    )
    return c

# 主函数
def main():
    check_permissions()
    if 'data' in st.session_state:   
        data1 = st.session_state.data 
        data2 = st.session_state.data   
        st.title("   舆情地域分布") 
        data1['ip'] = data1['ip'].fillna('未知') 
        province_counts = data1['ip'].value_counts() 

        # 移除双列布局 
        st.markdown("###    舆情地区分布柱状图") 
        st_pyecharts(create_bar(province_counts), height=500) 

        st.markdown("###    舆情地区占比饼图") 
        st_pyecharts(create_pie(province_counts), height=500)

        # 统计省份 IP 数据
        province_data = count_provinces(data2)
        
        # 创建地图
        map_chart = create_china_map(province_data)
        
        # 显示地图
        st.title(" 中国省份 IP 分布地图")
        st.info(" 推荐使用夸克浏览器，其他浏览器打开可能存在显示问题")
        st.components.v1.html(map_chart.render_embed(),  height=800)
        st.stop() 
    
    else: 
        st.warning("  请先上传文件。")
        st.stop()   # 停止页面加载

if __name__ == "__main__":
    main()