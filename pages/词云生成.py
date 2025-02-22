import streamlit as st
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import jieba
import jieba.analyse
from mk import check_permissions

# 使用 st.cache_resource 缓存 CampusWordFilter 类的实例，避免重复初始化
@st.cache_resource 
def get_campus_word_filter():
    return CampusWordFilter()

# 使用 st.cache_data 缓存加载停用词文件的操作，避免重复读取
@st.cache_data 
def load_stopwords(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return set(f.read().splitlines()) 
    except FileNotFoundError:
        st.warning(f"未找到停用词文件 {path}，启用基础过滤")
        return set(["的", "了", "是", "在"])

# 高校舆情专用过滤模块
class CampusWordFilter:
    def __init__(self):
        # 核心过滤配置
        self.base_stopwords = load_stopwords("stopwords.txt") 
        self.sensitive_words = ["广告"]  # 可扩展
        
        # 重点保留词从文件中读取
        self.education_keywords = self.load_custom_keywords("custom_dict.txt") 
                                        # 如果文件不存在，使用默认值
        if not self.education_keywords:  
            self.education_keywords = ["教学质量", "课程改革", "科研成果", "校园文化"]
            # 显示提示信息
            st.warning("未找到 `custom_dict.txt` 文件，启用默认的重点保留词。")

    def load_custom_keywords(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                # 去除空行和空白字符
                return [line.strip() for line in f.read().splitlines() 
                        if line.strip()]
        except FileNotFoundError:
            return []

    def load_custom_keywords(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f.read().splitlines() 
                        if line.strip()]
        except FileNotFoundError:
            return []

    def filter_text(self, text):
        # 使用TF-IDF提取教育领域关键词
        keywords = jieba.analyse.extract_tags(text, 
                                              topK=50,
                                              allowPOS=('n', 'ns', 'vn', 'nz'))

        # 双重过滤机制
        words = [word for word in jieba.cut(text) 
                 if len(word) > 1
                 and word not in self.base_stopwords 
                 and word not in self.sensitive_words 
                 and word in keywords + self.education_keywords] 

        return " ".join(words)

# 使用 st.cache_data 缓存生成词云的操作，避免重复生成
@st.cache_data 
def generate_campus_wordcloud(filtered_text, max_words):
    if not filtered_text:
        st.warning("有效文本内容为空")
        return None

    try:
        # 字体兼容方案（Windows/macOS）
        font_paths = [
            "C:/Windows/Fonts/msyh.ttc",   # Windows
            "/System/Library/Fonts/Supplemental/Songti.ttc"   # macOS
        ]

        for fp in font_paths:
            try:
                wc = WordCloud(
                    font_path=fp,
                    width=800,
                    height=400,
                    collocations=False,  # 禁用词组重复
                    background_color='white',
                    max_words=max_words
                ).generate(filtered_text)
                break
            except FileNotFoundError:
                continue
        else:
            st.warning("未找到系统字体，使用默认字体")
            wc = WordCloud().generate(filtered_text)

        # 生成专业可视化图形
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.imshow(wc, interpolation='bilinear')
        ax.axis('off') 
        plt.tight_layout() 
        return fig

    except Exception as e:
        st.error(f"生成失败：{str(e)}")
        return None

# 主程序
def main():
    check_permissions()

    # 界面布局优化
    st.header("词云生成")

    if 'data' not in st.session_state: 
        st.warning("请先上传数据文件")
        st.stop()
        return

    data = st.session_state.data 
    if data.empty: 
        st.error("数据集为空")
        return

    with st.expander("🔧 高级设置"):
        col1, col2 = st.columns(2) 
        with col1:
            min_word_length = st.radio( 
                "选择最小词长",
                options=[2, 3, 4],
                horizontal=True,  # 水平排列
                index=0,
                format_func=lambda x: f"{x}字符",
                help="过滤低于此长度的词语"
            )
        with col2:
            max_words = st.slider( 
                "最大显示词数",
                min_value=20, max_value=100, value=50,
                help="限制展示结果中最多显示的词语数量"
            )

    # 添加开始按钮
    if st.button("开始"):
        # 显示加载动画
        with st.spinner("正在生成词云集锦图，请稍等..."):
            try:
                processor = get_campus_word_filter()
                processed_text = processor.filter_text(" ".join(data['review'].dropna()))

                # 生成词云并显示
                wordcloud_fig = generate_campus_wordcloud(processed_text, max_words)

                if wordcloud_fig:
                    st.pyplot(wordcloud_fig)

            except KeyError:
                st.error("数据集中缺少'review'字段")

if __name__ == "__main__":
    main()