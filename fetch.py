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
    # 匹配各类明文协议
    raw_pattern = re.compile(r'(vmess|vless|ss|ssr|trojan|hysteria2)://[^\s\'"<>]+')
    # 匹配潜在的订阅链接
    sub_pattern = re.compile(r'https?://[^\s\'"<>]+')
    
    for url in CHANNELS:
        try:
            print(f"正在抓取: {url}")
            res = requests.get(url, timeout=10).text
            
            # 1. 抓取明文节点
            for m in raw_pattern.finditer(res):
                nodes.append(m.group(0))
                
            # 2. 抓取订阅链接并尝试解析 Base64
            for m in sub_pattern.finditer(res):
                sub_url = m.group(0)
                if "t.me" in sub_url: continue # 跳过频道本身的链接
                try:
                    sub_res = requests.get(sub_url, timeout=5).text
                    # 尝试 base64 解码
                    decoded = base64.b64decode(sub_res).decode('utf-8', errors='ignore')
                    for rm in raw_pattern.finditer(decoded):
                        nodes.append(rm.group(0))
                except:
                    pass # 解析失败则跳过
        except Exception as e:
            print(f"抓取失败 {url}: {e}")
            
    return nodes

def process_nodes(nodes):
    unique_configs = {} # 记录配置 MD5
    name_count = {}     # 记录名称出现次数
    final_nodes = []

    for node in nodes:
        try:
            if node.startswith("vmess://"):
                # Vmess 处理逻辑：解析内部 Base64 JSON
                b64_str = node[8:]
                # 补齐 base64 结尾的等号防止报错
                b64_str += "=" * ((4 - len(b64_str) % 4) % 4)
                v_json = json.loads(base64.b64decode(b64_str).decode('utf-8'))
                
                original_name = v_json.get('ps', 'Unnamed')
                
                # 去重：剔除 'ps' (名称) 字段后计算配置的 MD5
                v_config = {k: v for k, v in v_json.items() if k != 'ps'}
                config_hash = hashlib.md5(str(v_config).encode()).hexdigest()
                
                if config_hash in unique_configs:
                    continue
                unique_configs[config_hash] = True
                
                # 重命名：同名加后缀 _01, _02
                if original_name in name_count:
                    name_count[original_name] += 1
                    new_name = f"{original_name}_{name_count[original_name]:02d}"
                else:
                    name_count[original_name] = 1
                    new_name = original_name
                    
                # 重新打包成 vmess 链接
                v_json['ps'] = new_name
                new_node = "vmess://" + base64.b64encode(json.dumps(v_json).encode('utf-8')).decode('utf-8')
                final_nodes.append(new_node)

            else:
                # 其他协议 (Vless, Trojan, Hysteria2 等) 处理逻辑
                parts = node.split('#')
                config_part = parts[0]
                original_name = urllib.parse.unquote(parts[1]) if len(parts) > 1 else "Unnamed"
                
                # 去重
                config_hash = hashlib.md5(config_part.encode()).hexdigest()
                if config_hash in unique_configs:
                    continue
                unique_configs[config_hash] = True
                
                # 重命名
                if original_name in name_count:
                    name_count[original_name] += 1
                    new_name = f"{original_name}_{name_count[original_name]:02d}"
                else:
                    name_count[original_name] = 1
                    new_name = original_name
                    
                # 重新组合 URL
                final_nodes.append(f"{config_part}#{urllib.parse.quote(new_name)}")

        except Exception as e:
            # 遇到脏数据跳过，防止阻断
            continue
            
    return final_nodes

if __name__ == "__main__":
    nodes = get_nodes()
    processed = process_nodes(nodes)
    with open("raw_nodes.txt", "w", encoding='utf-8') as f:
        f.write("\n".join(processed))
    print(f"抓取并处理完毕，共保留 {len(processed)} 个独立且安全的节点。")
