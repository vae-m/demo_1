import streamlit as st

def check_permissions():
    """检查用户权限，没有权限则阻止页面加载。"""
    if not st.session_state.get('logged_in'):
        st.error("请先登录")
        st.stop()  # 阻止继续加载

def display_data():
    """显示已上传的数据。"""
    if 'data' in st.session_state:
        data = st.session_state.data
        st.write("### 数据实时展示：")
        st.dataframe(data, use_container_width=True)
    else:
        st.warning("请先上传文件")