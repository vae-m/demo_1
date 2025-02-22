import streamlit as st 
from pyecharts import options as opts 
from pyecharts.charts   import Bar, Pie 
import pandas as pd 
from streamlit_echarts import st_pyecharts  
# 配置中文环境 
def set_chinese(): 
    return opts.InitOpts( 
        theme="light",  # 内置主题支持中文 
        animation_opts=opts.AnimationOpts(animation_threshold=2000), 
        width="100%", 
        height="600px" 
    ) 
 
# 生成柱状图 
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
def create_pie(data) -> Pie: 
    pie = ( 
        Pie(init_opts=set_chinese()) 
       .add( 
            "", 
            [list(z) for z in zip(data.index.tolist(),   data.values.tolist())],  
            radius=["30%", "75%"],  # 环形饼图 
            rosetype="radius"  # 南丁格尔玫瑰图 
        ) 
       .set_global_opts( 
            title_opts=opts.TitleOpts(title="舆情各地占比"), 
            legend_opts=opts.LegendOpts(orient="vertical", pos_top="15%", pos_left="2%") 
        ) 
       .set_series_opts(label_opts=opts.LabelOpts(formatter="{{b}}: {{d}}%"))  # 百分比显示 
    ) 
    return pie 
 
# 主程序 
def main(): 
    # 权限验证（所有子页面都需要添加） 
    if not st.session_state.get('logged_in'):  
        st.error("  请先登录") 
        st.stop()    # 阻止继续加载 
 
    if 'data' in st.session_state:  
        data = st.session_state.data  
        st.title("  舆情地域分布") 
        data['ip'] = data['ip'].fillna('未知') 
        province_counts = data['ip'].value_counts() 
 
        # 移除双列布局 
        st.markdown("###   舆情地区分布柱状图") 
        st_pyecharts(create_bar(province_counts), height=500) 
 
        st.markdown("###   舆情地区占比饼图") 
        st_pyecharts(create_pie(province_counts), height=500) 
    
    else: 
        st.warning(" 请先上传文件。") 
 
if __name__ == "__main__": 
     
    main() 