import streamlit as st 
 
# 初始化会话状态 
if 'logged_in' not in st.session_state: 
    st.session_state.logged_in  = False 
    st.session_state.username  = None 
 
def check_login(username, password):
    """从secrets.toml 验证用户"""
    valid_users = st.secrets.users  
    return username in valid_users and valid_users[username] == password 
 
def login_page():
    """登录界面"""
    st.title("LOGIN")
    with st.form("login_form"): 
        username = st.text_input(" 用户名")
        password = st.text_input(" 密码", type="password")
        if st.form_submit_button(" 登录"):
            if check_login(username, password):
                st.session_state.logged_in  = True 
                st.session_state.username  = username 
                st.rerun()   # 刷新页面跳转 
            else:
                st.error(" 认证失败")
 
def main_page():
    """主功能界面"""
    # 设置页面配置
    st.set_page_config(page_title="社交网络舆情分析系统", page_icon=":guardsman:", layout="wide")

    # 显示背景图片
    st.image("assets/your_name.jpg", use_container_width=True)

    # 页面标题
    st.title("社交网络舆情分析系统")

    # 系统介绍
    st.markdown("""
    欢迎使用 **社交网络舆情分析系统**。该系统可以帮助您：
    - 上传社交网络数据文件（如 CSV 格式）
    - 查看数据并进行预处理
    - 生成词云，展示文本数据的关键词
    - 进行情感分析，了解数据中的情感倾向
    - 使用主题建模（LDA 或 KMeans）对数据进行深度分析
    - 查看舆情地域分布
    
    请选择左侧菜单中的功能，开始您的分析之旅！
""")
def main(): 
    # 主程序逻辑 
    if not st.session_state.logged_in: 
        login_page()
        st.stop()   # 阻止未登录访问 
    else:
        main_page()

if __name__ == "__main__":
    main()       

