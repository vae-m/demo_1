import time
import random
import pandas as pd
import requests
import streamlit as st
from datetime import datetime, timedelta
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, InvalidCookieDomainException, WebDriverException

# IP获取相关配置
API_RETRY = 3
IP_API_DELAY = (1, 3)
IP_API_TIMEOUT = 10

def configure_chrome_options():
    """配置Chrome浏览器选项"""
    options = Options()
    
    # 基础配置
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    
    # 反爬虫规避设置
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # 用户代理池
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
    ]
    options.add_argument(f"user-agent={random.choice(user_agents)}")
    
    # 性能优化
    options.add_argument("--disable-images")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_experimental_option("prefs", {
        "profile.managed_default_content_settings.images": 2,
        "profile.default_content_setting_values.notifications": 2,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    })
    
    # 语言设置
    options.add_argument("--lang=zh-CN")
    options.add_argument("--accept-language=zh-CN,zh;q=0.9")
    
    return options

def init_webdriver():
    """初始化浏览器实例"""
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(executable_path=ChromeDriverManager().install())
        options = configure_chrome_options()
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        st.error(f"浏览器初始化失败: {str(e)}")
        raise RuntimeError("无法启动浏览器，请检查ChromeDriver配置")

def load_cookies(driver):
    """加载微博Cookie"""
    cookies = [
        {
            "name": "SUB",
            "value": "_2A25Kvql6DeRhGeFM7lQQ-SzEzz-IHXVptaSyrDV8PUNbmtAYLVaskW9NQN2BkAvhupcrROysKhyF-f1eCou5SZ7u",
            "domain": ".weibo.com",
            "path": "/",
            "expires": datetime.now().timestamp() + 86400,
            "httpOnly": True,
            "secure": True
        },
        {
            "name": "SUBP",
            "value": "0033WrSXqPxfM725Ws9jqgMF55529P9D9WFEJijQVlllSysUmdzKHGR65JpX5KzhUgL.FoMESKqp1KzRShe2dJLoIp7LxKML1KBLBKnLxKqL1hnLBoMNeo-ceK.E1hB0",
            "domain": ".weibo.com",
            "path": "/",
            "expires": datetime.now().timestamp() + 86400,
            "httpOnly": True,
            "secure": True
        }
    ]
    
    driver.get("https://weibo.com")
    time.sleep(2)
    
    for cookie in cookies:
        try:
            formatted_cookie = {
                'name': cookie['name'],
                'value': cookie['value'],
                'domain': ".weibo.com",
                'path': '/',
                'httpOnly': True,
                'secure': True
            }
            driver.add_cookie(formatted_cookie)
        except Exception as e:
            print(f"添加Cookie失败: {cookie['name']} - {str(e)}")
    
    driver.refresh()
    time.sleep(3)
    return driver

def get_ip_location(bid, driver):
    """通过微博API获取IP属地"""
    api_url = f"https://weibo.com/ajax/statuses/show?id={bid}"
    
    try:
        cookies = {c['name']: c['value'] for c in driver.get_cookies()}
    except Exception as e:
        print(f"获取Cookies失败: {str(e)}")
        return "未知"
    
    headers = {
        'User-Agent': driver.execute_script("return navigator.userAgent;"),
        'Referer': 'https://weibo.com/',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    for attempt in range(API_RETRY):
        try:
            time.sleep(random.uniform(*IP_API_DELAY))
            response = requests.get(
                api_url,
                headers=headers,
                cookies=cookies,
                timeout=IP_API_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                region = data.get("region_name", "")
                return region.split()[-1] if region else "未知"
                
            elif response.status_code == 404:
                return "已删除"
                
            response.raise_for_status()
            
        except requests.exceptions.RequestException as e:
            print(f"API请求失败（尝试{attempt+1}/{API_RETRY}）: {str(e)}")
            if attempt == API_RETRY - 1:
                return "未知"
            
        except KeyError as e:
            print(f"JSON解析失败: {str(e)}")
            return "未知"
    
    return "未知"

def parse_weibo_post(post_element, driver):
    """解析单条微博内容"""
    try:
        # 基础信息
        content = post_element.find_element(By.CSS_SELECTOR, '.txt').text.strip()
        
        # 发布时间
        publish_time_element = post_element.find_element(By.CSS_SELECTOR, '.from a')
        publish_time = parse_time(publish_time_element.text.strip())
        
        # 获取bid
        try:
            href = post_element.find_element(By.CSS_SELECTOR, '.from a').get_attribute('href')
            bid = href.split('/')[-1].split('?')[0]
        except Exception as e:
            print(f"获取bid失败: {str(e)}")
            bid = None
        
        # IP属地获取
        ip_location = "未知"
        if bid:
            ip_location = get_ip_location(bid, driver)
        
        # 页面回退方案
        if ip_location == "未知":
            try:
                ip_element = post_element.find_element(By.XPATH, ".//span[contains(text(), 'IP属地')]")
                ip_location = ip_element.text.split('：')[-1].strip()
            except NoSuchElementException:
                pass

        # 互动数据
        repost_btn = post_element.find_element(By.CSS_SELECTOR, '.card-act li:nth-child(1)').text
        comment_btn = post_element.find_element(By.CSS_SELECTOR, '.card-act li:nth-child(2)').text
        like_btn = post_element.find_element(By.CSS_SELECTOR, '.card-act li:nth-child(3)').text
        
        # 用户信息
        user_element = post_element.find_element(By.CSS_SELECTOR, '.name')
        # user_id = user_element.get_attribute('href').split('/')[-1]
        user_name = user_element.text
        
        return {
            "review": content,
            "发布时间": publish_time,
            "ip": ip_location,
            "转发数": extract_count(repost_btn),
            "评论数": extract_count(comment_btn),
            "点赞数": extract_count(like_btn),
            # "用户ID": user_id,
            "用户名": user_name,
            "采集时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        print(f"解析异常: {str(e)}")
        return None

def parse_time(time_str):
    """处理时间格式"""
    now = datetime.now()
    if "刚刚" in time_str:
        return now.strftime("%Y-%m-%d %H:%M")
    elif "分钟前" in time_str:
        mins = int(time_str.replace("分钟前", ""))
        return (now - timedelta(minutes=mins)).strftime("%Y-%m-%d %H:%M")
    elif "今天" in time_str:
        return now.strftime(f"%Y-%m-%d {time_str.split()[-1]}")
    elif "-" in time_str:
        return f"{now.year}-{time_str}"
    else:
        return time_str

def extract_count(text):
    """提取互动数量"""
    try:
        return int(''.join(filter(str.isdigit, text)))
    except:
        return 0

def weibo_crawler(driver, keyword, start_date, end_date, max_posts):
    """核心爬取逻辑"""
    base_url = "https://s.weibo.com/weibo?q={}"
    search_url = base_url.format(quote(keyword)) + f"&timescope=custom:{start_date}:{end_date}"
    
    collected_data = []
    page = 1
    
    try:
        while len(collected_data) < max_posts:
            current_url = f"{search_url}&page={page}"
            driver.get(current_url)
            time.sleep(random.uniform(3, 5))
            
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".card-wrap"))
                )
            except TimeoutException:
                print(f"页面 {page} 加载超时")
                page += 1
                continue
            
            posts = driver.find_elements(By.CSS_SELECTOR, ".card-wrap")
            if not posts:
                print("无更多内容")
                break
            
            for post in posts:
                if len(collected_data) >= max_posts:
                    break
                
                parsed = parse_weibo_post(post, driver)
                if parsed and parsed not in collected_data:
                    collected_data.append(parsed)
            
            page += 1
        
        return collected_data[:max_posts]
    except Exception as e:
        print(f"爬取异常: {str(e)}")
        return collected_data

def main():
    """Streamlit界面"""
    st.set_page_config(
        page_title="微博数据采集系统",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed"  # 默认折叠侧边栏
    )
    
    st.title("📈 微博舆情数据采集系统")
    
    # 原侧边栏内容整合到主界面
    config_col1, config_col2 = st.columns([3, 2])
    
    with config_col1:
        st.header("配置参数")
        keyword = st.text_input("搜索关键词", "海南自贸港")
        
        date_col1, date_col2 = st.columns(2)
        with date_col1:
            start_date = st.date_input("开始日期", datetime.now() - timedelta(days=7))
        with date_col2:
            end_date = st.date_input("结束日期", datetime.now())
        
        max_posts = st.slider("最大采集数量", 10, 1000, 100, 10)
    
    with config_col2:
        with st.expander("📖 使用说明", expanded=True):
            st.markdown("""
            **数据采集流程：**
            1. 输入搜索关键词（支持复杂搜索语法）
            2. 设置日期范围（建议跨度≤30天）
            3. 调整需要采集的最大数量
            4. 点击下方【开始采集】按钮
            
            **注意事项：**
            - 首次使用需要配置有效Cookie
            - 大规模采集建议分时段进行
            - 结果文件请及时下载保存
            """)
    
    st.markdown("---")
    
    if st.button("🚀 开始采集", use_container_width=True):
        with st.spinner("数据采集中..."):
            try:
                driver = init_webdriver()
                load_cookies(driver)
                
                start_time = time.time()
                data = weibo_crawler(
                    driver=driver,
                    keyword=keyword,
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d"),
                    max_posts=max_posts
                )
                
                if data:
                    df = pd.DataFrame(data)
                    st.success(f"成功采集 {len(df)} 条数据（耗时：{time.time()-start_time:.1f}秒）")
                    
                    with st.expander("📊 数据预览", expanded=True):
                        st.dataframe(df, use_container_width=True)
                    
                    csv = df.to_csv(index=False, encoding="utf_8_sig")
                    st.download_button(
                        label="💾 下载CSV",
                        data=csv,
                        file_name=f"weibo_{keyword}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    st.warning("未采集到有效数据")
                
            except Exception as e:
                st.error(f"采集失败: {str(e)}")
            finally:
                if 'driver' in locals():
                    driver.quit()

if __name__ == "__main__":
    main()