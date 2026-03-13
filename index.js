const fs = require('fs');

async function fetchWithTimeout(url, options = {}, timeout = 15000) {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);
    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal,
            headers: {
                'User-Agent': 'v2rayN/6.39',
                'Accept': '*/*',
                ...options.headers
            }
        });
        clearTimeout(id);
        return response;
    } catch (e) {
        clearTimeout(id);
        return null;
    }
}

async function main() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const datePath = `${year}/${month}/${year}${month}${day}.txt`;

    const STATIC_SOURCES = [
        // --- 你新提供的精准源 ---
        'https://sub.proxygo.org/v2ray.php?key=88ed88e55f8eb3b7e31bd47b2ecfb0f2',
        'https://free.cndyw.ggff.net/sub',
        'https://misaka.cndyw.ggff.net/sub',
        'https://suba.cndyw.ggff.net/suba?sub',
        'https://subb.cndyw.ggff.net/subb?sub',
        'https://raw.githubusercontent.com/gslege/CloudflareIP/refs/heads/main/Vless.txt',
        
        // --- 之前的优质聚合源 ---
        'https://proxy.v2gh.com/https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub',
        `https://raw.githubusercontent.com/free-nodes/v2rayfree/main/node_list/${datePath}`, 
        `https://raw.githubusercontent.com/free-nodes/clashfree/main/node_list/${datePath}`,
        'https://raw.githubusercontent.com/chengaopan/AutoMergePublicNodes/master/list.txt'
    ];
    
    const TELEGRAM_CHANNELS = [
        'https://t.me/s/proxygogogo',
        'https://t.me/s/freekankan',
        'https://t.me/s/freeVPNjd'
    ];

    // 🚫 深度去广告关键词（包含新源自带的推广词）
    const adKeywords = [
        '剩余流量', '套餐到期', '过期时间', '官方网站', '重置', '加入频道',
        'dh.221345.xyz', 'v2rayse', 'shop', 't.me', 'pao-fu', 'v2rayfree',
        'clashfree', 'free-nodes', '点我获取', 'Pawdroid', '关注微信',
        'cndyw', 'ggff', '免费订阅', '流量', '到期'
    ];

    console.log(`🚀 [${year}-${month}-${day}] 正在启动全能纯净抓取...`);
    let allRawNodes = [];

    // 1. 静态与新增源抓取
    for (const url of STATIC_SOURCES) {
        const res = await fetchWithTimeout(url);
        if (res && res.ok) {
            const text = await res.text();
            let decoded = text;
            try { if (!text.includes('://')) decoded = Buffer.from(text, 'base64').toString('utf-8'); } catch(e) {}
            const nodes = decoded.match(/(ss|ssr|vmess|vless|trojan|hysteria2|hy2):\/\/[^\s"<>|]+/g) || [];
            allRawNodes.push(...nodes);
            console.log(`✅ [源] ${url.substring(0, 30)}... 贡献了 ${nodes.length} 个节点`);
        }
    }

    // 2. 频道动态抓取
    for (const url of TELEGRAM_CHANNELS) {
        const res = await fetchWithTimeout(url);
        if (res && res.ok) {
            const html = await res.text();
            const matches = html.match(/(https?|ss|ssr|vmess|vless|trojan|hysteria2|hy2):\/\/[^\s"<>|]+(?<!\.)/g) || [];
            for (const item of matches) {
                if (item.startsWith('http') && !item.includes('t.me') && !item.includes('telegram.org')) {
                    const subRes = await fetchWithTimeout(item);
                    if (subRes && subRes.ok) {
                        const subText = await subRes.text();
                        const subNodes = subText.match(/(ss|ssr|vmess|vless|trojan|hysteria2|hy2):\/\/[^\s"<>|]+/g) || [];
                        allRawNodes.push(...subNodes);
                    }
                } else if (!item.startsWith('http')) {
                    allRawNodes.push(item);
                }
            }
            console.log(`✅ [频道] ${url.split('/').pop()} 处理完成`);
        }
    }

    // 3. 核心清洗与广告剔除
    const cleanNodes = [...new Set(allRawNodes)]
        .map(n => n.trim())
        .filter(n => {
            if (!n.includes('://')) return false;
            try {
                // 解码节点备注进行关键字扫描
                const decodedPart = decodeURIComponent(n).toLowerCase();
                return !adKeywords.some(kw => decodedPart.includes(kw.toLowerCase()));
            } catch (e) {
                return !adKeywords.some(kw => n.toLowerCase().includes(kw.toLowerCase()));
            }
        });

    // 4. 保存文件
    if (cleanNodes.length > 0) {
        fs.writeFileSync('sub.txt', Buffer.from(cleanNodes.join('\n')).toString('base64'));
        console.log(`\n--------------------------------`);
        console.log(`✨ 抓取任务完成！`);
        console.log(`📊 过滤广告后总计节点: ${cleanNodes.length} 个`);
        console.log(`💾 sub.txt 已更新`);
        console.log(`--------------------------------`);
    } else {
        console.log("❌ 未发现任何有效节点。");
    }
}

main();
