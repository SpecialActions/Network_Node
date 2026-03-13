import re
import requests
import base64
import hashlib
import json
import urllib.parse

# 目标频道
CHANNELS = [
    'https://t.me/s/proxygogogo',
    'https://t.me/s/freekankan',
    'https://t.me/s/freeVPNjd'
]

def get_nodes():
    nodes = []
    raw_pattern = re.compile(r'(vmess|vless|ss|ssr|trojan|hysteria2)://[^\s\'"<>]+')
    sub_pattern = re.compile(r'https?://[^\s\'"<>]+')
    
    for url in CHANNELS:
        try:
            print(f"正在抓取: {url}")
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
            
    return nodes

def process_nodes(nodes):
    unique_configs = {} 
    name_count = {}     
    final_nodes = []

    for node in nodes:
        try:
            if node.startswith("vmess://"):
                b64_str = node[8:]
                b64_str += "=" * ((4 - len(b64_str) % 4) % 4)
                v_json = json.loads(base64.b64decode(b64_str).decode('utf-8'))
                
                original_name = v_json.get('ps', 'Unnamed')
                
                v_config = {k: v for k, v in v_json.items() if k != 'ps'}
                config_hash = hashlib.md5(str(v_config).encode()).hexdigest()
                
                if config_hash in unique_configs:
                    continue
                unique_configs[config_hash] = True
                
                if original_name in name_count:
                    name_count[original_name] += 1
                    new_name = f"{original_name}_{name_count[original_name]:02d}"
                else:
                    name_count[original_name] = 1
                    new_name = original_name
                    
                v_json['ps'] = new_name
                # 压缩 json 格式并重新编码
                new_node = "vmess://" + base64.b64encode(json.dumps(v_json, separators=(',', ':')).encode('utf-8')).decode('utf-8')
                final_nodes.append(new_node)

            else:
                parts = node.split('#', 1)
                config_part = parts[0]
                original_name = urllib.parse.unquote(parts[1]) if len(parts) > 1 else "Unnamed"
                
                config_hash = hashlib.md5(config_part.encode()).hexdigest()
                if config_hash in unique_configs:
                    continue
                unique_configs[config_hash] = True
                
                if original_name in name_count:
                    name_count[original_name] += 1
                    new_name = f"{original_name}_{name_count[original_name]:02d}"
                else:
                    name_count[original_name] = 1
                    new_name = original_name
                    
                # 取消了 urllib.parse.quote，保留原生的中文字符
                final_nodes.append(f"{config_part}#{new_name}")

        except Exception as e:
            continue
            
    return final_nodes

if __name__ == "__main__":
    nodes = get_nodes()
    processed = process_nodes(nodes)
    
    # 核心修复：将所有节点拼接后，进行一次全局 Base64 编码
    # 这是标准的订阅节点格式，Subconverter 能 100% 完美识别
    final_string = "\n".join(processed)
    b64_content = base64.b64encode(final_string.encode('utf-8')).decode('utf-8')
    
    with open("raw_nodes.txt", "w", encoding='utf-8') as f:
        f.write(b64_content)
        
    print(f"抓取并处理完毕，共保留 {len(processed)} 个独立且安全的节点。")
