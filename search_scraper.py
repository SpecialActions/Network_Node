import requests
import re
import urllib.parse
import time
import base64
import random

# ==========================================
# 1. 爬虫引擎配置
# ==========================================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
}

# 🌟 全网搜索关键词 (加上 site: 语法精准打击)
QUERIES = [
    'site:v2rayse.com/fs/public yaml',
    'site:v2rayse.com/fs/public txt',
    '"vmess://" OR "vless://" 免费节点 2026',
    'clash subscribe url github.io 2026'
]

# 核心雷达：专门抓取各种节点协议的通用正则表达式
NODE_REGEX = re.compile(r'(vmess|vless|ss|ssr|trojan|hysteria2|tuic)://[^\s\'"<>]+')

# 🌟 幽灵矩阵：开源免反爬搜索引擎节点 (SearxNG)
SEARX_INSTANCES = [
    "https://searx.be",
    "https://searx.fi",
    "https://searx.tiekoetter.com",
    "https://search.mdosch.de",
    "https://paulgo.io",
    "https://priv.au"
]

# ==========================================
# 2. 核心功能函数
# ==========================================
def get_search_urls(query):
    print(f"\n🔍 [阶段 1] 正在通过幽灵矩阵搜索: {query}")
    target_urls = []
    
    # 每次随机打乱引擎顺序，实现负载均衡防封锁
    random.shuffle(SEARX_INSTANCES)
    
    for instance in SEARX_INSTANCES:
        try:
            url = f"{instance}/search"
            params = {
                'q': query,
                'format': 'json',    # 直接请求机器最爱吃的 JSON 格式！
                'language': 'zh-CN'
            }
            print(f"  --> 尝试接驳节点: {instance}")
            
            res = requests.get(url, headers=HEADERS, params=params, timeout=15)
            
            if res.status_code == 200:
                data = res.json()
                results = data.get('results', [])
                for r in results:
                    link = r.get('url')
                    if link:
                        target_urls.append(link)
                
                if target_urls:
                    print(f"  [🎯 突破成功] 从该节点挖出了 {len(target_urls)} 个目标网页！")
                    break # 只要在一个引擎里搜到了，就直接跳出，去搜下一个关键词
                else:
                    print(f"  [⚠️ 节点为空] 该引擎未收录相关内容，切换下一个...")
            else:
                print(f"  [❌ 节点熔断] 状态码: {res.status_code}，切换下一个...")
        except Exception as e:
            print(f"  [❌ 节点超时] 切换下一个...")
            
    return list(set(target_urls))

def scrape_nodes_from_url(url):
    print(f"  --> 🚀 正在突入目标网页: {url[:60]}...")
    found_nodes = []
    try:
        # 伪装请求，设置 10 秒超时
        res = requests.get(url, headers=HEADERS, timeout=10)
        raw_text = res.text
        
        # 1. 直接在明文源码中捞节点
        for m in NODE_REGEX.finditer(raw_text):
            found_nodes.append(m.group(0))
            
        # 2. 尝试将整个网页当做 base64 解码后再捞一遍
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
            
    except requests.exceptions.RequestException:
        print(f"      [❌ 拦截] 无法访问目标网页 (可能阵亡或被盾)。")
        
    return found_nodes

# ==========================================
# 3. 主程序执行
# ==========================================
if __name__ == "__main__":
    print("🛸 启动全网级无差别节点爬虫 (幽灵矩阵版) ...")
    
    global_nodes_pool = []
    
    for q in QUERIES:
        urls_to_scrape = get_search_urls(q)
        
        for target_url in urls_to_scrape:
            # 过滤掉一些明显没用的聚合大站，防止卡死
            if any(block in target_url for block in ['github.com', 'reddit.com', 'twitter.com']):
                continue
                
            nodes = scrape_nodes_from_url(target_url)
            global_nodes_pool.extend(nodes)
            time.sleep(1)
            
        time.sleep(2)
        
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
        print("\n😭 本次全网扫荡未能满载而归，可能是关键词太偏，或者节点全部失效。")
