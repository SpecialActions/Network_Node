import requests
import re
import urllib.parse
import time
import base64

# ==========================================
# 1. 爬虫引擎配置
# ==========================================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5"
}

# 🌟 全网搜索关键词 (你可以随便加，加上最新的年月保证时效性)
QUERIES = [
    '"vmess://" OR "vless://" 免费节点 2026',
    'clash subscribe url github.io 2026',
    'v2ray 订阅链接 每日更新 pastebin'
]

# 核心雷达：专门抓取各种节点协议的通用正则表达式
NODE_REGEX = re.compile(r'(vmess|vless|ss|ssr|trojan|hysteria2|tuic)://[^\s\'"<>]+')

# ==========================================
# 2. 核心功能函数
# ==========================================
def get_ddg_search_urls(query):
    print(f"\n🔍 [阶段 1] 正在搜索引擎中广撒网: {query}")
    url = "https://html.duckduckgo.com/html/"
    payload = {'q': query}
    
    target_urls = []
    try:
        res = requests.post(url, headers=HEADERS, data=payload, timeout=15)
        if res.status_code == 200:
            # 解析 DDG 搜索结果中的真实跳转链接
            # DDG 的搜索结果链接通常伪装在 //duckduckgo.com/l/?uddg= 后面
            raw_links = re.findall(r'href="//duckduckgo\.com/l/\?uddg=(.*?)&', res.text)
            for link in raw_links:
                real_url = urllib.parse.unquote(link)
                target_urls.append(real_url)
            print(f"  [🎯 索敌成功] 挖出了 {len(target_urls)} 个潜在的目标网页！")
        else:
            print(f"  [❌ 报错] 搜索引擎拒绝访问，状态码: {res.status_code}")
    except Exception as e:
        print(f"  [❌ 超时] 搜索请求失败: {e}")
        
    return target_urls

def scrape_nodes_from_url(url):
    print(f"  --> 🚀 正在突入目标网页: {url[:60]}...")
    found_nodes = []
    try:
        # 伪装请求，设置 10 秒超时防止卡死
        res = requests.get(url, headers=HEADERS, timeout=10)
        
        # 很多节点网站会用 base64 加密整个网页内容，所以我们需要双重解码
        raw_text = res.text
        
        # 1. 直接在明文源码中捞节点
        matches = NODE_REGEX.findall(raw_text)
        for m in NODE_REGEX.finditer(raw_text):
            found_nodes.append(m.group(0))
            
        # 2. 尝试将整个网页当做 base64 解码后再捞一遍 (专门对付纯 base64 订阅页)
        try:
            padded_text = raw_text.strip() + "=" * ((4 - len(raw_text.strip()) % 4) % 4)
            dec = base64.b64decode(padded_text).decode('utf-8', errors='ignore')
            for m in NODE_REGEX.finditer(dec):
                found_nodes.append(m.group(0))
        except:
            pass
            
        if found_nodes:
            # 去重
            found_nodes = list(set(found_nodes))
            print(f"      [💰 大丰收] 从该网页中榨出了 {len(found_nodes)} 个节点！")
        else:
            print(f"      [⚠️ 空军] 网页能打开，但没发现节点 (可能被隐藏或需输入密码)。")
            
    except requests.exceptions.RequestException:
        print(f"      [❌ 拦截] 无法访问 (该网站可能阵亡，或被 Cloudflare 盾拦截)。")
        
    return found_nodes

# ==========================================
# 3. 主程序执行
# ==========================================
if __name__ == "__main__":
    print("🛸 启动全网级无差别节点爬虫 (Web Crawler) ...")
    
    global_nodes_pool = []
    
    for q in QUERIES:
        # 第一步：去搜索引擎找网页
        urls_to_scrape = get_ddg_search_urls(q)
        
        # 第二步：挨个去网页里抓节点
        for target_url in urls_to_scrape:
            nodes = scrape_nodes_from_url(target_url)
            global_nodes_pool.extend(nodes)
            
            # 礼貌性延时，防止被目标网站 IP 封禁
            time.sleep(1)
            
        # 搜索不同关键词之间的延时，防止搜索引擎封锁
        print("  ⏳ 冷却 3 秒钟防封锁...")
        time.sleep(3)
        
    # 全局去重
    final_clean_nodes = list(set(global_nodes_pool))
    
    if final_clean_nodes:
        print("\n" + "="*50)
        print(f"🎉 扫荡结束！全网累计抓取到 {len(final_clean_nodes)} 个独立节点。")
        print("="*50)
        
        # 保存为 base64 格式的 txt 文件，方便你直接丢进 Nodes 文件夹里给 fetch.py 吃！
        final_string = "\n".join(final_clean_nodes)
        b64_content = base64.b64encode(final_string.encode('utf-8')).decode('utf-8')
        
        filename = f"hunted_nodes_{int(time.time())}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(b64_content)
        print(f"📁 战利品已打包编码，保存为: {filename}")
    else:
        print("\n😭 本次全网扫荡未能满载而归，可能是关键词失效，或者遭遇了强力反爬。")
