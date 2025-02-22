# import streamlit as st
# import pandas as pd
# import datetime
# from mk import check_permissions

# check_permissions()

# def handle_file_upload(file):
#     """处理上传的文件并保存到 session_state """
#     try:
#         data = pd.read_csv(file)
#         st.session_state.data = data
#         return data
#     except Exception as e:
#         st.error(f"文件解析失败：{e}")
#         st.stop()

# # 上传 CSV 文件
# uploaded_file = st.file_uploader("选择一个CSV文件(请确定存在review列和ip列)", type=["csv"])

# if uploaded_file is not None:
#     # 处理上传的文件
#     data = handle_file_upload(uploaded_file)
#     st.success("文件上传成功！")
#     # 保存上传历史
#     if 'upload_history' not in st.session_state:
#         st.session_state.upload_history = []
#     # 保存文件名和上传时间
#     file_info = {
#         "文件名": uploaded_file.name,
#         "上传时间": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     }
#     st.session_state.upload_history.insert(0, file_info)  # 插入到历史记录开头
# else:
#     st.info("请上传一个 CSV 文件进行查看。")

# # 显示上传历史
# st.subheader("文件上传历史")
# if 'upload_history' in st.session_state:
#     for idx, file_info in enumerate(st.session_state.upload_history):
#         st.write(f"**文件 {idx + 1}**")
#         st.write(f"文件名：{file_info['文件名']}")
#         st.write(f"上传时间：{file_info['上传时间']}")
#         st.divider()
# else:
#     st.info("暂无历史记录")
import streamlit as st
import pandas as pd
import datetime
from mk import check_permissions

def handle_file_upload(file):
    """处理上传的文件并保存到 session_state """
    try:
        data = pd.read_csv(file)
        st.session_state.data = data
        return data
    except Exception as e:
        st.error(f"文件解析失败：{e}")
        st.stop()

def display_upload_history():
    """显示文件上传历史"""
    if 'upload_history' in st.session_state:
        upload_history = st.session_state.upload_history
        for idx, file_info in enumerate(upload_history):
            st.write(f"**文件 {idx + 1}**")
            st.write(f"文件名：{file_info['文件名']}")
            st.write(f"上传时间：{file_info['上传时间']}")
            st.divider()
    else:
        st.info("暂无历史记录")

def main():
    check_permissions()

    # 初始化 session_state
    if 'data' not in st.session_state:
        st.session_state.data = None
    if 'upload_history' not in st.session_state:
        st.session_state.upload_history = []

    # 上传 CSV 文件
    uploaded_file = st.file_uploader("选择一个CSV文件(请确保存在review列和ip列)", type=["csv"])
    
    if uploaded_file is not None:
        # 处理上传的文件
        data = handle_file_upload(uploaded_file)
        st.success("文件上传成功！")
        
        # 保存文件信息到上传历史
        file_info = {
            "文件名": uploaded_file.name,
            "上传时间": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        st.session_state.upload_history.insert(0, file_info)  # 插入到历史记录开头
    else:
        st.info("请上传一个 CSV 文件进行查看。")

    # 显示上传历史
    st.subheader("文件上传历史")
    display_upload_history()

if __name__ == "__main__":
    main()