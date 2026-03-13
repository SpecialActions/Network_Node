import re
import requests
import base64
import urllib.parse
import json

# 1. TG 频道源
CHANNELS = [
    'https://t.me/s/proxygogogo',
    'https://t.me/s/freekankan',
    'https://t.me/s/freeVPNjd'
]

# 2. 固定的外部订阅源
EXTERNAL_URLS = [
    "https://nodesfree.github.io/v2raynode/subscribe/v2ray.txt",
    "https://nodesfree.github.io/v2raynode/v2ray.txt",
    "https://raw.githubusercontent.com/ovmvo/FreeSub/refs/heads/main/sub/permanent/mihomo.yaml",
    "https://raw.githubusercontent.com/clashv2ray-hub/v2rayfree/refs/heads/main/v2ray.txt",
    "https://raw.githubusercontent.com/shaoyouvip/free/refs/heads/main/all.yaml",
    "https://proxy.v2gh.com/https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
    "https://mirror.v2gh.com/https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub"
]

# 3. 动态变化的 Github 仓库
DYNAMIC_REPOS = [
    "free-nodes/clashfree",
    "free-nodes/v2rayfree"
]

def get_tg_nodes():
    nodes = []
    raw_pattern = re.compile(r'(vmess|vless|ss|ssr|trojan|hysteria2)://[^\s\'"<>]+')
    sub_pattern = re.compile(r'https?://[^\s\'"<>]+')
    
    for url in CHANNELS:
        try:
            print(f"正在抓取 TG频道: {url}")
            res = requests.get(url, timeout=10).text
            
            for m in raw_pattern.finditer(res):
                nodes.append(m.group(0))
                
            for m in sub_pattern.finditer(res):
                sub_url = m.group(0)
                if "t.me" in sub_url: continue 
                try:
                    sub_res = requests.get(sub_url, timeout=5).text
                    decoded = base64.b64decode(sub_res).decode('utf-8', errors='ignore')
                    for rm in raw_pattern.finditer(decoded):
                        nodes.append(rm.group(0))
                except:
                    pass 
        except Exception as e:
            print(f"抓取失败 {url}: {e}")
            
    return list(set(nodes)) # 初步简单去重

def get_dynamic_links():
    """
    智能解析会变动文件名的 GitHub 仓库
    通过读取 README.md，用正则提取最新的原始链接
    """
    dynamic_urls = []
    # 正则匹配形如 https://raw.githubusercontent.com/free-nodes/.../xxx.yaml 的链接
    # 排除括号和引号等 Markdown 干扰字符
    pattern = re.compile(r"https://raw\.githubusercontent\.com/free-nodes/[^\s\"'<>()]+(?:\.yaml|\.txt)")
    
    for repo in DYNAMIC_REPOS:
        try:
            print(f"正在智能解析动态仓库: {repo}")
            # 尝试访问 main 和 master 分支的 README
            for branch in ["main", "master"]:
                readme_url = f"https://raw.githubusercontent.com/{repo}/{branch}/README.md"
                res = requests.get(readme_url, timeout=5)
                if res.status_code == 200:
                    matches = pattern.findall(res.text)
                    if matches:
                        # 去重并取前 2 个最新的链接（防止抓到太老的历史文件）
                        unique_matches = list(dict.fromkeys(matches))
                        latest_links = unique_matches[:2]
                        dynamic_urls.extend(latest_links)
                        print(f"  -> 成功提取到最新节点文件: {latest_links}")
                        break # 找到了就跳出 branch 循环
        except Exception as e:
            print(f"解析仓库 {repo} 失败: {e}")
            
    return dynamic_urls

if __name__ == "__main__":
    # 第一步：获取 TG 节点并保存为本地 Base64 订阅源
    tg_nodes = get_tg_nodes()
    if tg_nodes:
        final_string = "\n".join(tg_nodes)
        b64_content = base64.b64encode(final_string.encode('utf-8')).decode('utf-8')
        with open("tg_nodes.txt", "w", encoding='utf-8') as f:
            f.write(b64_content)
        print(f"✅ TG 频道抓取完毕，提取了 {len(tg_nodes)} 个节点。")
    else:
        # 容错：如果TG没抓到，创建一个空的防止后续步骤报错
        with open("tg_nodes.txt", "w") as f: f.write("")
        print("⚠️ 未抓取到任何 TG 节点。")
    
    # 第二步：获取动态仓库的最新链接
    dynamic_urls = get_dynamic_links()
    
    # 第三步：合并所有订阅源 (本地 TG + 固定源 + 动态解析源)
    all_urls = ["http://127.0.0.1:8000/tg_nodes.txt"] + EXTERNAL_URLS + dynamic_urls
    
    # 将多个 URL 用 | 拼接，并进行 URL 编码
    encoded_url = urllib.parse.quote("|".join(all_urls))
    
    # 生成 Subconverter 专用的 URL 指令
    sub_api = f"http://127.0.0.1:25500/sub?target=clash&url={encoded_url}&insert=false"
    
    # 保存 API 指令供 Github Action 调用
    with open("sub_api_url.txt", "w") as f:
        f.write(sub_api)
        
    print(f"\n🎉 资源聚合完毕！总计包含 {len(all_urls)} 个订阅入口。API指令已生成。")
