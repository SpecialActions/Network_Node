import re
import requests
import base64
import urllib.parse
import json
import hashlib
from datetime import datetime, timedelta, timezone

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

def get_and_heal_tg_nodes():
    """
    抓取并净化野生 TG 节点
    """
    raw_nodes = []
    raw_pattern = re.compile(r'(vmess|vless|ss|ssr|trojan|hysteria2)://[^\s\'"<>]+')
    sub_pattern = re.compile(r'https?://[^\s\'"<>]+')
    
    for url in CHANNELS:
        try:
            print(f"正在抓取 TG频道: {url}")
            res = requests.get(url, timeout=10).text
            for m in raw_pattern.finditer(res):
                raw_nodes.append(m.group(0))
            for m in sub_pattern.finditer(res):
                sub_url = m.group(0)
                if "t.me" in sub_url: continue 
                try:
                    sub_res = requests.get(sub_url, timeout=5).text
                    decoded = base64.b64decode(sub_res).decode('utf-8', errors='ignore')
                    for rm in raw_pattern.finditer(decoded):
                        raw_nodes.append(rm.group(0))
                except:
                    pass 
        except Exception as e:
            print(f"抓取失败 {url}: {e}")

    # ==========================================
    # 核心修复：野生节点净化中心
    # ==========================================
    clean_nodes = []
    seen_configs = set()

    for node in raw_nodes:
        try:
            if node.startswith("vmess://"):
                # 修复 Vmess：强行砍掉违规的 # 备注，补齐 Base64 等号
                b64_str = node[8:].split('#')[0] 
                b64_str += "=" * ((4 - len(b64_str) % 4) % 4)
                v_json = json.loads(base64.b64decode(b64_str).decode('utf-8'))
                
                # 提前进行 TG 节点间的去重，减轻后续压力
                v_config = {k: v for k, v in v_json.items() if k != 'ps'}
                config_hash = hashlib.md5(str(v_config).encode()).hexdigest()
                if config_hash in seen_configs: continue
                seen_configs.add(config_hash)
                
                # 重新打包成完全合规的 vmess 链接
                clean_node = "vmess://" + base64.b64encode(json.dumps(v_json, separators=(',', ':')).encode('utf-8')).decode('utf-8')
                clean_nodes.append(clean_node)
            else:
                # 修复其他协议：确保名字部分经过标准 URL 编码，防止 Subconverter 读断
                parts = node.split('#', 1)
                config_part = parts[0]
                
                config_hash = hashlib.md5(config_part.encode()).hexdigest()
                if config_hash in seen_configs: continue
                seen_configs.add(config_hash)
                
                if len(parts) > 1:
                    safe_name = urllib.parse.quote(urllib.parse.unquote(parts[1]))
                    clean_nodes.append(f"{config_part}#{safe_name}")
                else:
                    clean_nodes.append(config_part)
        except Exception:
            # 遇到彻底损坏无法抢救的节点，静默丢弃
            continue
            
    return clean_nodes

def get_dynamic_links():
    """
    主动出击探测：基于当前日期生成 datePath 探测动态节点文件
    """
    dynamic_urls = []
    tz = timezone(timedelta(hours=8)) # 东八区时间
    today = datetime.now(tz)
    yesterday = today - timedelta(days=1)

    REPOS = ["free-nodes/v2rayfree", "free-nodes/clashfree"]
    
    print("开始根据日期 ${datePath} 探测动态节点文件...")
    for date_obj in [today, yesterday]:
        date_path = date_obj.strftime("%Y/%m/%Y%m%d")
        
        for repo in REPOS:
            possible_paths = [
                f"node_list/{date_path}.yaml",
                f"node_list/{date_path}.txt",
                f"{date_path}.yaml",
                f"{date_path}.txt"
            ]
            for path in possible_paths:
                test_url = f"https://raw.githubusercontent.com/{repo}/main/{path}"
                try:
                    if requests.head(test_url, timeout=3).status_code == 200:
                        dynamic_urls.append(test_url)
                        print(f"  -> ✅ 成功锁定文件: {test_url}")
                        break 
                except:
                    pass
    return list(set(dynamic_urls))

if __name__ == "__main__":
    # 1. 抓取并【净化】TG 节点
    tg_nodes = get_and_heal_tg_nodes()
    if tg_nodes:
        final_string = "\n".join(tg_nodes)
        b64_content = base64.b64encode(final_string.encode('utf-8')).decode('utf-8')
        with open("tg_nodes.txt", "w", encoding='utf-8') as f:
            f.write(b64_content)
        print(f"✅ TG 频道抓取与修复完毕，提取了 {len(tg_nodes)} 个合规节点。")
    else:
        with open("tg_nodes.txt", "w") as f: f.write("")
        print("⚠️ 未抓取到任何有效的 TG 节点。")
    
    # 2. 探测动态仓库链接
    dynamic_urls = get_dynamic_links()
    
    # 3. 合并所有订阅源 (本地净化 TG + 固定源 + 动态解析源)
    all_urls = ["http://127.0.0.1:8000/tg_nodes.txt"] + EXTERNAL_URLS + dynamic_urls
    
    # 组合为 Subconverter 专用指令
    encoded_url = urllib.parse.quote("|".join(all_urls))
    sub_api = f"http://127.0.0.1:25500/sub?target=clash&url={encoded_url}&insert=false"
    
    with open("sub_api_url.txt", "w") as f:
        f.write(sub_api)
    print(f"\n🎉 资源聚合完毕！总计包含 {len(all_urls)} 个订阅入口，API指令已生成。")
