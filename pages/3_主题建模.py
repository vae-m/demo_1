import streamlit as st
import streamlit_echarts as st_echarts
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE
import jieba
import pandas as pd
from mk import check_permissions

def do_data():
    jieba.load_userdict("custom_dict.txt") 

    data = st.session_state.data
    # 加载中文停用词 
    with open("stopwords.txt",  "r", encoding="utf-8") as f:
        stopwords = [line.strip() for line in f.readlines()] 
    data['processed'] = data['review'].fillna('').apply(
        lambda x: " ".join([word for word in jieba.cut(x) if word not in stopwords and len(word) > 1])
    )
    return data

def vectorize_text(data, max_df=0.95, min_df=2):
    """特征向量化"""
    vectorizer = TfidfVectorizer(max_df=max_df, min_df=min_df)
    X = vectorizer.fit_transform(data['processed'])
    return X.astype(np.float32), vectorizer.get_feature_names_out()

def train_lda(X, num_topics):
    """训练 LDA 模型"""
    lda = LatentDirichletAllocation(n_components=num_topics, random_state=42)
    lda.fit(X)
    return lda

def train_kmeans(X, num_clusters):
    """训练 KMeans 模型"""
    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    cluster_labels = kmeans.fit_predict(X)
    return kmeans, cluster_labels

def generate_lda_visualization(lda, features, num_topics):
    """生成 LDA 主题可视化图表"""
    topic_options = []
    for idx in range(num_topics):
        topic = lda.components_[idx]
        top_indices = topic.argsort()[-10:][::-1]
        top_words = [features[i] for i in top_indices]
        weights = [round(float(topic[i]), 3) for i in top_indices]
        weights = np.array(weights) / np.sum(weights)
        weights = [round(w, 3) for w in weights]
        
        option = {
            "title": {"text": f"主题 {idx + 1}"},
            "tooltip": {
                "trigger": "axis",
                "formatter": "{b}: {c}"
            },
            "xAxis": {"type": "value"},
            "yAxis": {
                "type": "category",
                "data": top_words,
                "axisLabel": {"interval": 0, "fontSize": 12}
            },
            "series": [{
                "type": "bar",
                "data": weights,
                "label": {"show": True, "position": 'right', "formatter": "{@[1]}"}
            }],
            "grid": {"left": "25%", "right": "15%", "bottom": "3%", "containLabel": True}
        }
        topic_options.append(option)
    
    return topic_options

def generate_kmeans_visualization(kmeans, features, cluster_labels, X, use_tsne, num_clusters):
    """生成 KMeans 聚类可视化图表"""
    cluster_keywords = []
    for idx in range(num_clusters):
        cluster = kmeans.cluster_centers_[idx]
        top_indices = cluster.argsort()[-10:][::-1]
        top_words = [features[i] for i in top_indices]
        cluster_keywords.append(f"** 聚类 {idx + 1} 关键词**：{', '.join(top_words)}")
    
    tsne_option = None
    if use_tsne and X.shape[0] > 10:
        tsne = TSNE(n_components=2, random_state=42)
        embeddings = tsne.fit_transform(X.toarray())
        scatter_data = []
        for i in range(len(embeddings)):
            scatter_data.append({
                "value": [float(embeddings[i, 0]), float(embeddings[i, 1])],
                "itemStyle": {"color": f"hsl({(cluster_labels[i] * 360) // num_clusters}, 60%, 60%)"}
            })
        tsne_option = {
            "title": {"text": "t-SNE 聚类分布图"},
            "xAxis": {"type": "value"},
            "yAxis": {"type": "value"},
            "series": [{
                "type": "scatter",
                "data": scatter_data,
                "itemStyle": {"opacity": 0.6},
                "symbolSize": 10
            }]
        }
    return cluster_keywords, tsne_option

def main():
    check_permissions()
    
    # 初始化 session_state
    if 'data' not in st.session_state:
        st.session_state.data = None
    
    if 'data' in st.session_state:
        data = st.session_state.data
        st.write("### 主题建模分析系统")
        
        # 数据预处理
        data = do_data()
        
        # 方法选择
        method = st.radio("选择分析方法", ["LDA主题模型", "KMeans聚类分析"])
        
        # 高级参数配置
        with st.expander("高级参数配置"):
            max_df = st.slider("最大文档频率", 0.7, 1.0, 0.95)
            min_df = st.slider("最小文档频率", 1, 10, 2)
            use_tsne = st.checkbox("启用t-SNE降维可视化(仅k-means时可选)")
            
            if method == "LDA主题模型":
                num_topics = st.slider("主题数量", 2, 10, 5)
            else:
                num_clusters = st.slider("聚类数量", 2, 10, 5)
        
        # 特征向量化
        X, features = vectorize_text(data, max_df, min_df)
        
        if method == "LDA主题模型":
            with st.spinner('主题建模中...'):
                lda = train_lda(X, num_topics)
                topic_options = generate_lda_visualization(lda, features, num_topics)
                
                st.write("### 主题关键词分布")
                # 分列显示主题
                cols = st.columns(2)
                for idx, option in enumerate(topic_options):
                    with cols[idx % 2]:
                        st_echarts.st_echarts(
                            options=option,
                            height=f"{len(option['yAxis']['data'])*30 + 100}px",
                            key=f"topic{idx}"
                        )
        
        elif method == "KMeans聚类分析":
            with st.spinner('聚类分析中...'):
                kmeans, cluster_labels = train_kmeans(X, num_clusters)
                cluster_keywords, tsne_option = generate_kmeans_visualization(
                    kmeans, features, cluster_labels, X, use_tsne, num_clusters
                )
                
                # 显示聚类关键词
                with st.expander("查看聚类关键词"):
                    cols = st.columns(2)
                    for idx in range(num_clusters):
                        with cols[idx % 2]:
                            st.markdown(cluster_keywords[idx])
                
                # 显示 t-SNE 可视化
                if tsne_option is not None:
                    st.write("### 聚类分布可视化")
                    st_echarts.st_echarts(options=tsne_option, height="600px")
    else:
        st.warning("请先上传文件。")
        st.stop()

if __name__ == "__main__":
    main()


# import streamlit as st 
# import streamlit_echarts as st_echarts 
# import numpy as np 
# from sklearn.feature_extraction.text  import TfidfVectorizer 
# from sklearn.decomposition  import LatentDirichletAllocation 
# from sklearn.cluster  import KMeans 
# from sklearn.manifold  import TSNE 
# import jieba 
# import pandas as pd 
 
# # 权限验证 
# if not st.session_state.get('logged_in'): 
#     st.error(" 请先登录")
#     st.stop() 
 
# # 加载自定义词典 
# jieba.load_userdict("custom_dict.txt") 
 
# if 'data' in st.session_state: 
#     data = st.session_state.data  
#     st.write("###  主题建模分析系统")
 
#     # 加载中文停用词 
#     with open("stopwords.txt",  "r", encoding="utf-8") as f:
#         stopwords = [line.strip() for line in f.readlines()] 
 
#     # 中文分词预处理 
#     data['processed'] = data['review'].fillna('').apply(
#         lambda x: " ".join([word for word in jieba.cut(x)  if word not in stopwords and len(word) > 1])
#     )
 
#     # 特征向量化函数 
#     def vectorize_text(data, max_df=0.95, min_df=2):
#         vectorizer = TfidfVectorizer(max_df=max_df, min_df=min_df)
#         X = vectorizer.fit_transform(data['processed']) 
#         return X.astype(np.float32),  vectorizer.get_feature_names_out() 
 
#     method = st.radio(" 选择分析方法", ["LDA主题模型", "KMeans聚类分析"])
 
#     # 高级参数配置 
#     with st.expander(" 高级参数配置"):
#         max_df = st.slider(" 最大文档频率", 0.7, 1.0, 0.95)
#         min_df = st.slider(" 最小文档频率", 1, 10, 2)
#         use_tsne = st.checkbox(" 启用t-SNE降维可视化(仅k-means时可选)")
#         if method == "LDA主题模型":
#             num_topics = st.slider(" 主题数量", 2, 10, 5)
#         else:
#             num_clusters = st.slider(" 聚类数量", 2, 10, 5)
#         # 修改后的LDA主题可视化部分 
#     if method == "LDA主题模型":
#         with st.spinner(' 主题建模中...'):
#             X, features = vectorize_text(data, max_df, min_df)
#             lda = LatentDirichletAllocation(n_components=num_topics, random_state=42)
#             lda.fit(X) 
    
#             st.write("###  主题关键词分布")
#             topic_options = []
#             for idx, topic in enumerate(lda.components_): 
#                 top_indices = topic.argsort()[-10:][::-1] 
#                 top_words = [features[i] for i in top_indices]
#                 # 关键修改点：添加round函数处理小数位数 
#                 weights = [round(float(topic[i]), 3) for i in top_indices]  # 三位小数处理 
    
#                 # 归一化处理 
#                 weights = np.array(weights)  / np.sum(weights) 
#                 weights = [round(w, 3) for w in weights]  # 再次四舍五入
                
#                 option = {
#                     "title": {"text": f"主题 {idx + 1}"},
#                     "tooltip": {
#                         "trigger": "axis",
#                         "formatter": "{b}: {c}"  # 提示框显示原始值 
#                     },
#                     "xAxis": {"type": "value"},
#                     "yAxis": {
#                         "type": "category",
#                         "data": top_words,
#                         "axisLabel": {
#                             "interval": 0,
#                             "formatter": "{value}",
#                             "fontSize": 12 
#                         }
#                     },
#                     "series": [{
#                         "type": "bar",
#                         "data": weights,
#                         "label": {
#                             "show": True,
#                             "position": 'right',
#                             "formatter": "{@[1]}"  # 显示三位小数 
#                         }
#                     }],
#                     "grid": {
#                         "left": "25%",
#                         "right": "15%",  # 增加右侧空间 
#                         "bottom": "3%",
#                         "containLabel": True 
#                     }
#                 }
#                 topic_options.append(option) 
    
#             # 分列显示主题 
#             cols = st.columns(2) 
#             for idx, option in enumerate(topic_options):
#                 with cols[idx % 2]:
#                     st_echarts.st_echarts( 
#                         options=option,
#                         height=f"{len(option['yAxis']['data'])*30 + 100}px",
#                         key=f"topic{idx}"
#                     )
 
#     elif method == "KMeans聚类分析":
#         with st.spinner(' 聚类分析中...'):
#             X, features = vectorize_text(data, max_df, min_df)
#             kmeans = KMeans(n_clusters=num_clusters, random_state=42)
#             cluster_labels = kmeans.fit_predict(X) 
 
#             # 聚类关键词展示 
#             cluster_keywords = []
#             for idx in range(num_clusters):
#                 cluster_words = [features[i] for i in kmeans.cluster_centers_[idx].argsort()[-10:][::-1]] 
#                 cluster_keywords.append(f"** 聚类 {idx + 1} 关键词**：{', '.join(cluster_words)}")
 
#             with st.expander(" 查看聚类关键词"):
#                 cols = st.columns(2) 
#                 for idx in range(num_clusters):
#                     with cols[idx % 2]:
#                         st.markdown(cluster_keywords[idx]) 
 
#             # t-SNE 可视化 
#             if use_tsne and X.shape[0]  > 10:
#                 st.write("###  聚类分布可视化")
#                 tsne = TSNE(n_components=2, random_state=42)
#                 embeddings = tsne.fit_transform(X.toarray()) 
 
#                 scatter_data = []
#                 for i in range(len(embeddings)):
#                     scatter_data.append({ 
#                         "value": [
#                             float(embeddings[i, 0]),  # 显式转换类型 
#                             float(embeddings[i, 1])
#                         ],
#                         "itemStyle": {"color": f"hsl({(cluster_labels[i] * 360) // num_clusters}, 60%, 60%)"}
#                     })
 
#                 tsne_option = {
#                     "title": {"text": "t-SNE 聚类分布图"},
#                     "xAxis": {"type": "value"},
#                     "yAxis": {"type": "value"},
#                     "series": [{
#                         "type": "scatter",
#                         "data": scatter_data,
#                         "itemStyle": {"opacity": 0.6},
#                         "symbolSize": 10 
#                     }]
#                 }
#                 st_echarts.st_echarts(options=tsne_option,  height="600px")
# else:
#     st.warning("请先上传文件。")
#     st.stop()
