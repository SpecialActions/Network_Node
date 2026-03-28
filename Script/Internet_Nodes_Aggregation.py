import os
import yaml
import requests
import subprocess
import time
import urllib.parse
import sys
import hashlib
import json
import re
import concurrent.futures
import base64
import urllib3

# 屏蔽不验证 SSL 证书时弹出的烦人警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# 👑 核心配置与参数 (全局控制中心)
# ==========================================

# ⏱️ 测速超时阈值 (单位：毫秒)
MAX_DELAY = 2500

# 🚀 并发测速线程数
MAX_WORKERS = 20

# 🏷️ 节点名称统一前缀
CUSTOM_PREFIX = "Internet｜" 

# 📄 输出的核心文件名称
OUTPUT_FILENAME = "Internet_Nodes_Aggregation.yaml"

# 📂 原始订阅链接库的本地路径
LINK_FILE_PATH = "Config/Internet_Nodes_Aggregation.txt"

# ☁️ Gist 目标仓库 ID (从 GitHub Secrets 安全读取)
GIST_ID_IN = os.environ.get("GIST_ID_IN", "")

# 🔑 GitHub 修改权限钥匙 (从 GitHub Secrets 安全读取)
REPO_TOKEN = os.environ.get("REPO_TOKEN", "")

# 🔄 订阅转换 API 容灾集群 (防宕机备用列表，按可靠性排序)
SUBCONVERTER_APIS = [
    "https://api.v1.mk", 
    "https://subapi.cmliussss.net",   
    "https://url.v1.mk",            
    "https://sub.xeton.dev",          
    "https://api.tsutsu.cc",          
    "https://sub.bonds.id",           
    "https://api.wcc.best"         
]

# ==========================================
# 🌍 地区映射与探测词库 (史诗级豪华增强版)
# ==========================================
FLAG_MAP = {
    "香港": "🇭🇰", "台湾": "🇹🇼", "澳门": "🇲🇴", "日本": "🇯🇵", "韩国": "🇰🇷", "新加坡": "🇸🇬",
    "印度": "🇮🇳", "马来西亚": "🇲🇾", "泰国": "🇹🇭", "越南": "🇻🇳", "菲律宾": "🇵🇭", "印度尼西亚": "🇮🇩",
    "澳大利亚": "🇦🇺", "新西兰": "🇳🇿",
    "英国": "🇬🇧", "德国": "🇩🇪", "法国": "🇫🇷", "荷兰": "🇳🇱", "俄罗斯": "🇷🇺",
    "瑞典": "🇸🇪", "芬兰": "🇫🇮", "丹麦": "🇩🇰", "挪威": "🇳🇴", "冰岛": "🇮🇸",
    "瑞士": "🇨🇭", "意大利": "🇮🇹", "西班牙": "🇪🇸", "葡萄牙": "🇵🇹", "爱尔兰": "🇮🇪", 
    "波兰": "🇵🇱", "奥地利": "🇦🇹", "比利时": "🇧🇪", "土耳其": "🇹🇷", "希腊": "🇬🇷",
    "美国": "🇺🇸", "加拿大": "🇨🇦", "墨西哥": "🇲🇽", "巴西": "🇧🇷", "阿根廷": "🇦🇷",
    "阿联酋": "🇦🇪", "沙特阿拉伯": "🇸🇦", "以色列": "🇮🇱", "南非": "🇿🇦",
    "未知地区": "🌍", "🚩": "🚩" 
}

REGION_KEYWORDS = {
    "香港": ["香港", "hk", "hkg", "hongkong", "xianggang"],
    "台湾": ["台湾", "tw", "tpe", "taiwan", "taipei"],
    "日本": ["日本", "jp", "jpn", "nrt", "tyo", "japan", "tokyo", "osaka", "riben"],
    "韩国": ["韩国", "kr", "kor", "icn", "sel", "korea", "seoul", "hanguo"],
    "新加坡": ["新加坡", "sg", "sgp", "sin", "singapore", "xinjiap"],
    "美国": ["美国", "us", "usa", "lax", "sjc", "sfo", "nyc", "america", "meiguo"],
    "印度": ["印度", "in", "ind", "bom", "del", "india", "mumbai", "delhi", "yindu"],
    "马来西亚": ["马来西亚", "马来", "my", "mys", "kul", "malaysia", "kuala lumpur", "malai"],
    "泰国": ["泰国", "th", "tha", "bkk", "thailand", "bangkok", "taiguo"],
    "越南": ["越南", "vn", "vnm", "sgn", "vietnam", "ho chi minh", "yuenan"],
    "菲律宾": ["菲律宾", "ph", "phl", "mnl", "philippines", "manila", "feilvbin"],
    "印度尼西亚": ["印度尼西亚", "印尼", "id", "idn", "cgk", "indonesia", "jakarta", "yinni"],
    "澳大利亚": ["澳大利亚", "澳洲", "au", "aus", "syd", "mel", "australia", "sydney", "aodaliya"],
    "新西兰": ["新西兰", "nz", "nzl", "akl", "new zealand", "auckland", "xinxilan"],
    "英国": ["英国", "uk", "gbr", "lon", "london", "england", "yingguo"],
    "德国": ["德国", "de", "ger", "fra", "germany", "frankfurt", "deguo"],
    "法国": ["法国", "fr", "fra", "par", "france", "paris", "faguo"],
    "荷兰": ["荷兰", "nl", "nld", "ams", "netherlands", "amsterdam", "helan"],
    "俄罗斯": ["俄罗斯", "俄国", "ru", "rus", "mows", "russia", "moscow", "eluosi"],
    "瑞典": ["瑞典", "se", "swe", "sto", "sweden", "stockholm", "ruidian"],
    "芬兰": ["芬兰", "fi", "fin", "hel", "finland", "helsinki", "fenlan"],
    "丹麦": ["丹麦", "dk", "dnk", "cph", "denmark", "copenhagen", "danmai"],
    "挪威": ["挪威", "no", "nor", "osl", "norway", "oslo", "nuowei"],
    "瑞士": ["瑞士", "ch", "che", "zrh", "switzerland", "zurich", "ruishi"],
    "意大利": ["意大利", "it", "ita", "mil", "italy", "milan", "yidali"],
    "西班牙": ["西班牙", "es", "esp", "mad", "spain", "madrid", "xibanya"],
    "葡萄牙": ["葡萄牙", "pt", "prt", "lis", "portugal", "lisbon", "putaoya"],
    "爱尔兰": ["爱尔兰", "ie", "irl", "dub", "ireland", "dublin", "aierlan"],
    "波兰": ["波兰", "pl", "pol", "waw", "poland", "warsaw", "bolan"],
    "奥地利": ["奥地利", "at", "aut", "vie", "austria", "vienna", "aodili"],
    "比利时": ["比利时", "be", "bel", "bru", "belgium", "brussels", "bilishi"],
    "土耳其": ["土耳其", "tr", "tur", "ist", "turkey", "istanbul", "tuerqi"],
    "加拿大": ["加拿大", "ca", "can", "yto", "canada", "toronto", "jianada"],
    "墨西哥": ["墨西哥", "mx", "mex", "mexico", "moxige"],
    "巴西": ["巴西", "br", "bra", "gru", "brazil", "sao paulo", "baxi"],
    "阿根廷": ["阿根廷", "ar", "arg", "eze", "argentina", "buenos aires", "agenting"],
    "阿联酋": ["阿联酋", "迪拜", "ae", "are", "dxb", "uae", "dubai", "emirates", "alianqiu", "dibai"],
    "沙特阿拉伯": ["沙特阿拉伯", "沙特", "sa", "sau", "ruh", "saudi arabia", "riyadh", "shate"],
    "以色列": ["以色列", "il", "isr", "tlv", "israel", "tel aviv", "yiselie"],
    "南非": ["南非", "za", "zaf", "jnb", "south africa", "johannesburg", "nanfei"]
}

# ==========================================
# 0. 聚合订阅链接 (✨ 支持 API 自动容灾切换)
# ==========================================
raw_proxies = []
print(f"🔄 开始从本地文件 [{LINK_FILE_PATH}] 拉取节点...")

if not os.path.exists(LINK_FILE_PATH):
    print(f"❌ 未找到 {LINK_FILE_PATH}。")
    sys.exit(1)

sub_urls = []
with open(LINK_FILE_PATH, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            parts = line.split('#', 1)
            url = parts[0].strip()
            forced_region = parts[1].strip() if len(parts) > 1 else None
            if url: sub_urls.append({'url': url, 'region': forced_region})

for sub in sub_urls:
    url = sub['url']
    forced_region = sub['region']
    try:
        print(f"  📥 获取: {url}")
        if forced_region:
            print(f"     📌 用户指定归属地: [{forced_region}]")
            
        resp = requests.get(url, timeout=15, verify=False)
        resp.raise_for_status()
        fetched_nodes = []
        
        try:
            data = yaml.safe_load(resp.text)
            if isinstance(data, dict) and "proxies" in data:
                fetched_nodes = data["proxies"]
        except: pass
            
        if not fetched_nodes:
            print(f"    ⚠️ 非 Clash 格式，启动 API 自动转换集群...")
            encoded_url = urllib.parse.quote(url)
            
            for api_base in SUBCONVERTER_APIS:
                try:
                    print(f"      -> 尝试接口: {api_base}")
                    sub_api = f"{api_base}/sub?target=clash&url={encoded_url}&insert=false&emoji=false"
                    sub_resp = requests.get(sub_api, timeout=10, verify=False)
                    sub_resp.raise_for_status()
                    
                    sub_data = yaml.safe_load(sub_resp.text)
                    if isinstance(sub_data, dict) and "proxies" in sub_data:
                        fetched_nodes = sub_data["proxies"]
                        print(f"      ✅ 转换成功！")
                        break 
                    else:
                        print(f"      ❌ 解析失败，内容格式不匹配")
                except Exception as e:
                    print(f"      ❌ 接口失效或超时，无缝切换下一个...")
                    continue
        
        for node in fetched_nodes:
            if forced_region: node['_forced_region'] = forced_region
            raw_proxies.append(node)
            
    except Exception as e: 
        print(f"    ❌ 获取订阅彻底失败: {e}")

if not raw_proxies: 
    print("❌ 所有链接均未找到可用节点，退出。")
    sys.exit(0)

# ==========================================
# 1. 结构过滤 & 防连坐去重
# ==========================================
proxies, seen_hashes, seen_names = [], set(), set()
VALID_TYPES = {'ss', 'ssr', 'vmess', 'vless', 'trojan', 'hysteria', 'hysteria2', 'tuic', 'wireguard', 'http', 'https', 'socks5', 'snell'}

for p in raw_proxies:
    try:
        if 'server' not in p or not str(p['server']).strip(): continue
        if 'port' not in p or not str(p['port']).strip(): continue
        ptype = str(p.get('type', '')).lower()
        if ptype not in VALID_TYPES: continue
    except: continue

    p_config = {k: v for k, v in p.items() if k not in ['name', '_forced_region', '_original_name']}
    config_hash = hashlib.md5(json.dumps(p_config, sort_keys=True).encode('utf-8')).hexdigest()
    
    if config_hash not in seen_hashes:
        seen_hashes.add(config_hash)
        orig_name = str(p.get('name', 'Unnamed'))
        new_name, counter = orig_name, 1
        while new_name in seen_names:
            new_name = f"{orig_name} {counter}"
            counter += 1
        seen_names.add(new_name)
        p['_original_name'], p['name'] = orig_name, new_name
        proxies.append(p)

# ==========================================
# 2. 内核级预检
# ==========================================
print("\n🛡️ 启动内核预检，剔除毒瘤节点...")
mihomo_config = {"allow-lan": True, "bind-address": "*", "external-controller": "127.0.0.1:9090", "proxies": proxies}
for attempt in range(30):
    mihomo_config["proxies"] = proxies
    with open("mihomo_config.yaml", "w", encoding='utf-8') as f: yaml.dump(mihomo_config, f, allow_unicode=True)
    result = subprocess.run(["./mihomo", "-d", ".", "-f", "mihomo_config.yaml", "-t"], capture_output=True, text=True)
    if result.returncode == 0: break
    
    error_log = result.stdout + result.stderr
    culprit = next((m for m in re.findall(r'\[([^\]]+)\]', error_log) if any(p['name'] == m for p in proxies)), None)
    if culprit: 
        print(f"  [⚠️ 预检拦截] 剔除损坏节点 [{culprit}]")
        proxies = [p for p in proxies if p['name'] != culprit]
    else: 
        proxies = proxies[:100]; break

# ==========================================
# 3. 并发真实测速
# ==========================================
print(f"\n🚀 {MAX_WORKERS} 线程测速中 (限时 {MAX_DELAY}ms)...")
process = subprocess.Popen(["./mihomo", "-d", ".", "-f", "mihomo_config.yaml"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(4) 

def test_proxy(p):
    test_url = f"http://127.0.0.1:9090/proxies/{urllib.parse.quote(p['name'])}/delay?timeout={MAX_DELAY}&url=https://www.gstatic.com/generate_204"
    for _ in range(2):
        try:
            res = requests.get(test_url, timeout=(MAX_DELAY/1000) + 1.5)
            if res.status_code == 200 and res.json().get('delay', 0) > 0: return p, res.json()['delay']
        except: time.sleep(0.5)
    return None, 0

valid_proxies = []
with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    future_to_proxy = {executor.submit(test_proxy, p): p for p in proxies}
    for future in concurrent.futures.as_completed(future_to_proxy):
        p, delay = future.result()
        if p and delay > 0:
            orig_name = p.get('_original_name', p.get('name', '未知节点'))
            print(f"  ✅ [测速通过] {orig_name} | 延迟: {delay}ms")
            valid_proxies.append(p)
process.terminate()

# ==========================================
# 4. 四级漏斗智能重命名
# ==========================================
print("\n🌍 正在应用命名规则...")
country_counters, ip_cache = {}, {}

def get_country_from_text(text):
    if not text: return None
    text_lower = text.lower()
    for c, kws in REGION_KEYWORDS.items():
        for kw in kws:
            if len(kw) <= 2:
                if re.search(rf'\b{kw}\b', text_lower) or re.search(rf'[-_\[\]\(\)]{kw}[-_\[\]\(\)]', f"-{text_lower}-"): return c
            elif kw in text_lower: return c
    return None

def get_country_from_ip(server):
    if server in ip_cache: return ip_cache[server]
    try:
        res = requests.get(f"http://ip-api.com/json/{server}?lang=zh-CN", timeout=3).json()
        if res.get('status') == 'success':
            c = res.get('country', '未知地区').replace("中国香港", "香港").replace("中国台湾", "台湾").replace("中国澳门", "澳门").replace("美利坚合众国", "美国")
            ip_cache[server] = c; time.sleep(1.2); return c
    except: pass
    ip_cache[server] = '未知地区'; return '未知地区'

for p in valid_proxies:
    orig_name = p.get('_original_name', p.get('name', '未知节点'))
    server = p.get('server', '')
    
    c = p.get('_forced_region') or get_country_from_text(orig_name) or get_country_from_text(server) or get_country_from_ip(server)
    country_counters[c] = country_counters.get(c, 0) + 1
    
    new_name = f"{CUSTOM_PREFIX}{FLAG_MAP.get(c, '🚩')} {c} {country_counters[c]:02d}"
    p['name'] = new_name
    p.pop('_forced_region', None); p.pop('_original_name', None)
    
    print(f"  🏷️ 命名成功: [{orig_name}] -> {new_name}")

valid_proxies.sort(key=lambda x: x['name'])

# ==========================================
# 5. 三通道分发 (YAML, Surge .list, Base64)
# ==========================================
final_yaml_str = yaml.dump({
    "proxies": valid_proxies,
    "proxy-groups": [{"name": "🚀 自动选择", "type": "url-test", "proxies": [p['name'] for p in valid_proxies], "url": "https://www.gstatic.com/generate_204", "interval": 3600}]
}, allow_unicode=True, sort_keys=False)

def clash_to_surge(p):
    try:
        ptype, name, server, port = str(p.get('type', '')).lower(), p['name'], p['server'], p['port']
        tls = 'true' if p.get('tls') else 'false'
        sni = f", sni={p.get('sni', p.get('servername', ''))}" if p.get('sni') or p.get('servername') else ""
        skip_cert = ", skip-cert-verify=true" if p.get('skip-cert-verify') else ", skip-cert-verify=false"
        
        ws_str = ""
        if p.get('network') == 'ws':
            ws_path = p.get('ws-opts', {}).get('path', '')
            ws_headers = p.get('ws-opts', {}).get('headers', {}).get('Host', '')
            ws_str = f", ws=true, ws-path={ws_path}" + (f", ws-headers=Host:{ws_headers}" if ws_headers else "")

        if ptype == 'trojan':
            return f"{name} = trojan, {server}, {port}, password={p.get('password', '')}{sni}{ws_str}{skip_cert}"
        elif ptype == 'vmess':
            return f"{name} = vmess, {server}, {port}, username={p.get('uuid', '')}, encrypt-method={p.get('cipher', 'auto')}, tls={tls}{sni}{ws_str}{skip_cert}"
        elif ptype == 'vless':
            return f"{name} = vless, {server}, {port}, username={p.get('uuid', '')}, tls={tls}{sni}{ws_str}{skip_cert}"
        elif ptype in ['ss', 'shadowsocks']:
            return f"{name} = ss, {server}, {port}, encrypt-method={p.get('cipher', '')}, password={p.get('password', '')}"
        elif ptype == 'hysteria2':
            return f"{name} = hysteria2, {server}, {port}, password={p.get('password', '')}{sni}{skip_cert}"
    except: pass
    return ""

final_surge_str = '\n'.join([clash_to_surge(p) for p in valid_proxies if clash_to_surge(p)])

def clash_to_url(p):
    try:
        ptype, name, server, port = str(p.get('type', '')).lower(), urllib.parse.quote(p.get('name', '')), p.get('server', ''), p.get('port', '')
        tls, sni, network = 'tls' if p.get('tls') else '', p.get('sni', p.get('servername', '')), p.get('network', 'tcp')
        if ptype == 'trojan':
            pw, path, host = p.get('password', ''), urllib.parse.quote(p.get('ws-opts', {}).get('path', '')), p.get('ws-opts', {}).get('headers', {}).get('Host', '')
            return f"trojan://{pw}@{server}:{port}?security={tls}&sni={sni}&type={network}&path={path}&host={host}#{name}"
        elif ptype == 'vless':
            uuid, path, host = p.get('uuid', ''), urllib.parse.quote(p.get('ws-opts', {}).get('path', '')), p.get('ws-opts', {}).get('headers', {}).get('Host', '')
            return f"vless://{uuid}@{server}:{port}?encryption=none&security={tls}&sni={sni}&type={network}&path={path}&host={host}#{name}"
        elif ptype == 'vmess':
            v_dict = {"v": "2", "ps": p.get('name', ''), "add": server, "port": str(port), "id": p.get('uuid', ''), "aid": str(p.get('alterId', 0)), "scy": p.get('cipher', 'auto'), "net": network, "type": "none", "tls": tls, "sni": sni, "path": p.get('ws-opts', {}).get('path', ''), "host": p.get('ws-opts', {}).get('headers', {}).get('Host', '')}
            return f"vmess://{base64.b64encode(json.dumps(v_dict).encode('utf-8')).decode('utf-8')}"
        elif ptype in ['ss', 'shadowsocks']:
            userpass = base64.b64encode(f"{p.get('cipher', '')}:{p.get('password', '')}".encode('utf-8')).decode('utf-8')
            return f"ss://{userpass}@{server}:{port}#{name}"
        elif ptype == 'hysteria2':
            return f"hysteria2://{p.get('password', '')}@{server}:{port}?sni={sni}&insecure=1#{name}"
    except: pass
    return ""

final_b64_str = base64.b64encode('\n'.join([url for url in (clash_to_url(p) for p in valid_proxies) if url]).encode('utf-8')).decode('utf-8')

surge_filename = OUTPUT_FILENAME.replace(".yaml", ".list") if ".yaml" in OUTPUT_FILENAME else f"{OUTPUT_FILENAME}.list"
b64_filename = OUTPUT_FILENAME.replace(".yaml", ".txt") if ".yaml" in OUTPUT_FILENAME else f"{OUTPUT_FILENAME}.txt"

print(f"\n🎉 处理完成！保留极品节点 {len(valid_proxies)} 个。")

if GIST_ID_IN and REPO_TOKEN:
    payload = {
        "description": f"Internet Nodes Auto-Sync - {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "files": {
            OUTPUT_FILENAME: {"content": final_yaml_str},
            surge_filename: {"content": final_surge_str},
            b64_filename: {"content": final_b64_str}
        }
    }
    try:
        requests.patch(f"https://api.github.com/gists/{GIST_ID_IN}", headers={"Authorization": f"token {REPO_TOKEN}"}, json=payload).raise_for_status()
        print(f"✅ Gist 已更新！\n  - Clash: {OUTPUT_FILENAME}\n  - Surge: {surge_filename}\n  - Base64: {b64_filename}")
    except Exception as e: print(f"❌ 上传失败: {e}")
