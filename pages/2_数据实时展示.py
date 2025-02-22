import streamlit as st
import pandas as pd
from mk import display_data,check_permissions

def main():
    """主页面逻辑。"""
    check_permissions()  # 调用权限验证函数
    display_data()       # 调用数据展示函数

if __name__ == "__main__":
    main()