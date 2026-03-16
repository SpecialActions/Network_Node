import requests
import re
import urllib.parse
import time
import base64

# ==========================================
# 1. 爬虫引擎配置
# ==========================================
# 全网搜索关键词 (加上 site: 语法精准打击)
QUERIES = [
    'site:v2rayse.com/fs/public yaml',
    'site:v2rayse.com/fs/public txt',
    '"vmess://" 免费节点 每日更新 2026',
    '"vless://" 免费节点 每日更新 2026'
]

# 核心雷达：专门抓取各种节点协议的通用正则表达式
NODE_REGEX = re.compile(r'(vmess|vless|ss|ssr|trojan|hysteria2|tuic)://[^\s\'"<>]+')

# 🌟 核心穿透引擎：利用公益代理 API 隐藏微软机房 IP
def fetch_via_proxy(target_url):
    # 将目标网址进行 URL 编码
    encoded_url = urllib.parse.quote(target_url)
    proxy_url = f"https://api.allorigins.win/get?url={encoded_url}"
    
    try:
        # 给代理留足超时时间
        res = requests.get(proxy_url, timeout=20)
        if res.status_code == 200:
            # AllOrigins 会把网页源码包在 JSON 的 'contents' 字段里返回
            data = res.json()
            return data.get('contents', '')
        else:
            return ""
    except:
        return ""

# ==========================================
# 2. 核心功能函数
# ==========================================
def get_search_urls(query):
    print(f"\n🔍 [阶段 1] 正在通过代理 API 穿透搜索: {query}")
    
    # 构造鸭鸭搜的直达链接
    ddg_search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    
    # 使用代理引擎去访问鸭鸭搜
    html_content = fetch_via_proxy(ddg_search_url)
    
    target_urls = []
    if html_content:
        # 正则提取鸭鸭搜结果里的真实跳转链接
        raw_links = re.findall(r'href="//duckduckgo\.com/l/\?uddg=(.*?)&', html_content)
        for link in raw_links:
            real_url = urllib.parse.unquote(link)
            target_urls.append(real_url)
            
        if target_urls:
            print(f"  [🎯 突破成功] 绕过封锁，挖出了 {len(target_urls)} 个潜在网页！")
        else:
            print(f"  [⚠️ 搜索为空] 引擎未返回有效链接。")
    else:
        print(f"  [❌ 代理熔断] 代理服务器未能穿透该搜索请求。")
            
    return list(set(target_urls))

def scrape_nodes_from_url(url):
    print(f"  --> 🚀 正在突入目标网页: {url[:60]}...")
    found_nodes = []
    
    # 网站可能也有防爬虫盾，直接用代理穿透去抓取源码！
    raw_text = fetch_via_proxy(url)
    
    if not raw_text:
        print(f"      [❌ 拦截] 目标网页阵亡或代理穿透失败。")
        return found_nodes

    # 1. 直接在明文源码中捞节点
    for m in NODE_REGEX.finditer(raw_text):
        found_nodes.append(m.group(0))
        
    # 2. 尝试将整个网页当做 base64 解码后再捞一遍 (对付纯 Base64 的订阅页)
    try:
        padded_text = raw_text.strip() + "=" * ((4 - len(raw_text.strip()) % 4) % 4)
        dec = base64.b64decode(padded_text).decode('utf-8', errors='ignore')
        for m in NODE_REGEX.finditer(dec):
            found_nodes.append(m.group(0))
    except:
        pass
        
    if found_nodes:
        found_nodes = list(set(found_nodes))
        print(f"      [💰 大丰收] 从该网页中榨出了 {len(found_nodes)} 个节点！")
    else:
        print(f"      [⚠️ 空军] 网页能打开，但没发现可用节点。")
        
    return found_nodes

# ==========================================
# 3. 主程序执行
# ==========================================
if __name__ == "__main__":
    print("🛸 启动全网级无差别节点爬虫 (API 代理穿透版) ...")
    
    global_nodes_pool = []
    
    for q in QUERIES:
        urls_to_scrape = get_search_urls(q)
        
        for target_url in urls_to_scrape:
            # 过滤掉一些大站，防止抓到无效的教程代码
            if any(block in target_url for block in ['github.com', 'reddit.com', 'twitter.com']):
                continue
                
            nodes = scrape_nodes_from_url(target_url)
            global_nodes_pool.extend(nodes)
            # 延时防代理 API 封禁
            time.sleep(2)
            
        time.sleep(3)
        
    final_clean_nodes = list(set(global_nodes_pool))
    
    if final_clean_nodes:
        print("\n" + "="*50)
        print(f"🎉 扫荡结束！全网累计抓取到 {len(final_clean_nodes)} 个独立节点。")
        print("="*50)
        
        final_string = "\n".join(final_clean_nodes)
        b64_content = base64.b64encode(final_string.encode('utf-8')).decode('utf-8')
        
        filename = f"hunted_nodes_{int(time.time())}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(b64_content)
        print(f"📁 战利品已打包编码，保存为: {filename}")
    else:
        print("\n😭 本次全网扫荡未能满载而归，目标隐藏得太深了。")
