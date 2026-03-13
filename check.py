import yaml
import requests
import subprocess
import time
import urllib.parse
import sys

try:
    with open("clash_nodes.yaml", "r", encoding='utf-8') as f:
        data = yaml.safe_load(f)
except Exception as e:
    print(f"读取 YAML 失败: {e}")
    sys.exit(1)

if not isinstance(data, dict):
    print(f"❌ 严重错误: Subconverter 转换节点失败！返回内容为: {data}")
    sys.exit(1)

proxies = data.get("proxies", [])
if not proxies:
    print("没有找到任何可用代理节点，退出。")
    sys.exit(0)

# 恢复标准配置，取消 IPv6 禁用
mihomo_config = {
    "allow-lan": True,
    "bind-address": "*",
    "external-controller": "127.0.0.1:9090",
    "proxies": proxies
}
with open("mihomo_config.yaml", "w", encoding='utf-8') as f:
    yaml.dump(mihomo_config, f, allow_unicode=True)

print("启动 Mihomo 进行测速...")
process = subprocess.Popen(["./mihomo", "-d", ".", "-f", "mihomo_config.yaml"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(3) 

valid_proxies = []

def test_proxy(name):
    encoded_name = urllib.parse.quote(name)
    # 超时时间设为 2000ms
    test_url = f"http://127.0.0.1:9090/proxies/{encoded_name}/delay?timeout=2000&url=https://www.gstatic.com/generate_204"
    try:
        res = requests.get(test_url, timeout=3)
        if res.status_code == 200 and "delay" in res.json():
            return res.json()['delay']
    except:
        pass
    return 0

print("开始进行连通性测试...")
for p in proxies:
    original_name = p['name']
    
    delay = test_proxy(original_name)
    if delay > 0:
        print(f"[✅ 保留] {original_name} - 延迟: {delay}ms")
        valid_proxies.append(p)
    else:
        print(f"[❌ 删除] {original_name} - 测速不通")

# 测速完毕，关闭核心
process.terminate()

# ==========================================
# 测速通过的节点：统一重命名
# ==========================================
PREFIX = "Internet｜" # 这里可以修改为你想要的名字前缀
for index, p in enumerate(valid_proxies, start=1):
    new_name = f"{PREFIX}_{index:03d}"
    p['name'] = new_name

# 生成最终的订阅文件
final_output = {
    "proxies": valid_proxies,
    "proxy-groups": [
        {
            "name": "🚀 自动选择",
            "type": "url-test",
            "proxies": [p['name'] for p in valid_proxies],
            "url": "https://www.gstatic.com/generate_204",
            "interval": 3600
        }
    ]
}

with open("final_sub.yaml", "w", encoding='utf-8') as f:
    yaml.dump(final_output, f, allow_unicode=True, sort_keys=False)
    
print(f"\n测速与重命名完成！初始节点 {len(proxies)} 个，保留有效节点 {len(valid_proxies)} 个。")
