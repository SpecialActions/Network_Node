const fs = require('fs');

async function fetchWithTimeout(url, options = {}, timeout = 10000) {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);
    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal,
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': 'text/plain,text/html,application/xhtml+xml',
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
    const SUB_LIMIT = 50; 
    const CHANNELS = [
        'https://t.me/s/freeVPNjd',
        'https://t.me/s/freekankan',
        'https://t.me/s/v2ray_free_vpn',
        'https://t.me/s/V2ray_Free_VPN_Account' // 增加一个源
    ];

    console.log("🚀 WARP 已就绪，开始执行深度抓取...");

    // 1. 获取频道网页内容
    const contents = await Promise.all(CHANNELS.map(url => 
        fetchWithTimeout(url).then(res => res ? res.text() : '')
    ));

    let globalSubLinks = [];
    let globalNodeLinks = [];

    contents.forEach(html => {
        if (!html) return;
        // 改进后的正则：捕获 http 链接和各种协议头
        const wideRegex = /(https?|ss|ssr|vmess|vless|trojan|hysteria2|hy2):\/\/[^\s"<>|]+(?<!\.)/g;
        const matches = html.match(wideRegex) || [];
        
        const ignoreRegex = /\/\/(t\.me|telegram\.org|google\.com|gstatic\.com|apple\.com|twitter\.com|facebook\.com|github\.com)\//;
        const filtered = [...new Set(matches)].filter(l => !ignoreRegex.test(l));

        globalSubLinks.push(...filtered.filter(l => l.startsWith('http')).slice(-SUB_LIMIT));
        globalNodeLinks.push(...filtered.filter(l => !l.startsWith('http')));
    });

    const finalSubLinks = [...new Set(globalSubLinks)];
    console.log(`📡 发现疑似订阅源: ${finalSubLinks.length} 个。开始逐一解析...`);

    // 2. 递归下载订阅内容
    let proxiesFromSub = [];
    for (const [index, url] of finalSubLinks.entries()) {
        process.stdout.write(`进度: [${index + 1}/${finalSubLinks.length}] 正在尝试: ${url.substring(0, 40)}... `);
        
        const res = await fetchWithTimeout(url, { headers: { 'User-Agent': 'v2rayN/6.39' } });
        if (res && res.ok) {
            let body = await res.text();
            // 尝试 Base64 解码
            let decoded = body;
            if (!body.includes('://')) {
                try { decoded = Buffer.from(body, 'base64').toString(); } catch(e) {}
            }
            
            const nodes = decoded.match(/(ss|ssr|vmess|vless|trojan|hysteria2|hy2):\/\/[^\s"<>|]+/g) || [];
            if (nodes.length > 0) {
                proxiesFromSub.push(...nodes);
                console.log(`✅ 抓到 ${nodes.length} 个`);
            } else {
                console.log(`❌ 无效内容`);
            }
        } else {
            console.log(`❌ 请求失败`);
        }
    }

    // 3. 去重与合并
    const allNodes = [...new Set([...proxiesFromSub, ...globalNodeLinks])];
    
    // 基础清洗：移除结尾可能存在的冗余字符
    const cleanedNodes = allNodes.map(n => n.replace(/[ \t\r\n]+$/, ''));

    if (cleanedNodes.length === 0) {
        console.log("⚠️ 未发现有效节点，跳过写入。");
        return;
    }

    // 保存为 Base64
    fs.writeFileSync('sub.txt', Buffer.from(cleanedNodes.join('\n')).toString('base64'));
    console.log(`\n🎉 任务圆满完成！汇总节点总数: ${cleanedNodes.length}`);
}

main();
