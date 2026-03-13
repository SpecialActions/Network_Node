const fs = require('fs');

async function main() {
    // ==========================================
    // ⚙️ 自定义配置区
    // ==========================================
    const SUB_LIMIT = 30;     
    const NODE_LIMIT = 50;   
    const FETCH_TIMEOUT = 4000; 
    const CHANNELS = [
        'https://t.me/s/freeVPNjd',     
        'https://t.me/s/freekankan',  
        'https://t.me/s/v2ray_free_vpn'
    ];

    console.log("🚀 开始仿 Sub-Store 逻辑抓取...");

    // 1. 获取网页源码
    const contents = await Promise.all(CHANNELS.map(async url => {
        try {
            const res = await fetch(url, { signal: AbortSignal.timeout(FETCH_TIMEOUT) });
            return await res.text();
        } catch (e) {
            console.log(`❌ 无法访问频道: ${url}`);
            return '';
        }
    }));

    let globalSubLinks = [];
    let globalNodeLinks = [];

    contents.forEach(html => {
        if (!html) return;
        let channelLinks = [];

        // 策略 A: 提取 href
        const hrefRegex = /href=["'](https?:\/\/[^"']+)["']/g;
        let hMatch;
        while ((hMatch = hrefRegex.exec(html)) !== null) { channelLinks.push(hMatch[1]); }

        // 策略 B: 提取纯文本
        const cleanText = html.replace(/<[^>]+>/g, ' ').replace(/&amp;/g, '&');
        const wideRegex = /(https?|ss|ssr|vmess|vless|trojan|hysteria2|hy2):\/\/[^\s"<>]+/g;
        let wMatch;
        while ((wMatch = wideRegex.exec(cleanText)) !== null) {
            let link = wMatch[0].replace(/\s+/g, '').replace(/[.,!?;）)]+$/, '');
            channelLinks.push(link);
        }

        const ignoreRegex = /\/\/(t\.me|telegram\.org|google\.com|gstatic\.com|apple\.com|twitter\.com|facebook\.com)\//;
        const uniqueLinks = [...new Set(channelLinks)].filter(l => !ignoreRegex.test(l));

        globalSubLinks.push(...uniqueLinks.filter(l => l.startsWith('http')).slice(-SUB_LIMIT));
        globalNodeLinks.push(...uniqueLinks.filter(l => !l.startsWith('http')).slice(-NODE_LIMIT));
    });

    const finalSubLinks = [...new Set(globalSubLinks)];
    const finalNodeLinks = [...new Set(globalNodeLinks)];
    console.log(`🔗 订阅链接: ${finalSubLinks.length} 个, 单节点: ${finalNodeLinks.length} 个`);

    // 2. 下载订阅内容
    let proxiesFromSub = [];
    for (const url of finalSubLinks) {
        try {
            const res = await fetch(url, { 
                headers: { 'user-agent': 'ClashMeta/1.18.0' }, 
                signal: AbortSignal.timeout(FETCH_TIMEOUT) 
            });
            const body = await res.text();
            // 简单处理：如果是 base64 则解码，否则直接正则提节点
            let decoded = body;
            if (!body.includes('://')) {
                try { decoded = Buffer.from(body, 'base64').toString(); } catch(e) {}
            }
            const nodes = decoded.match(/(ss|vmess|vless|trojan|hysteria2|hy2):\/\/[^\s"<>|]+/g) || [];
            proxiesFromSub.push(...nodes);
        } catch (e) {}
    }

    // 3. 合并并去重
    const allProxies = [...proxiesFromSub, ...finalNodeLinks];
    
    // --- 防止重名覆盖的处理逻辑 ---
    // 因为是原始链接，我们需要保证如果有多个节点重名，给它们加上编号
    const nameMap = new Map();
    const result = [];

    allProxies.forEach(proxy => {
        try {
            if (proxy.startsWith('vmess://')) {
                let config = JSON.parse(Buffer.from(proxy.slice(8), 'base64').toString());
                let baseName = config.ps || "Untitled";
                let count = (nameMap.get(baseName) || 0) + 1;
                nameMap.set(baseName, count);
                config.ps = count > 1 ? `${baseName} ${count}` : baseName;
                result.push('vmess://' + Buffer.from(JSON.stringify(config)).toString('base64'));
            } else if (proxy.includes('#')) {
                let [uri, name] = proxy.split('#');
                let baseName = decodeURIComponent(name);
                let count = (nameMap.get(baseName) || 0) + 1;
                nameMap.set(baseName, count);
                let finalName = count > 1 ? `${baseName} ${count}` : baseName;
                result.push(`${uri}#${encodeURIComponent(finalName)}`);
            } else {
                result.push(proxy);
            }
        } catch (e) {
            result.push(proxy);
        }
    });

    // 4. 剔除 Surge 不支持协议（可选，如需纯净可保留）
    const surgeCompatible = result.filter(p => !p.startsWith('vless://') && !p.startsWith('ssr://'));

    // 5. 导出 Base64
    fs.writeFileSync('sub.txt', Buffer.from(surgeCompatible.join('\n')).toString('base64'));
    console.log(`✅ 抓取完成！总数: ${allProxies.length}, Surge 兼容: ${surgeCompatible.length}`);
}

main();
