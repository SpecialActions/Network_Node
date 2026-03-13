const fs = require('fs');

async function main() {
    const SUB_LIMIT = 30;     
    const NODE_LIMIT = 50;   
    const CHANNELS = [
        'https://t.me/s/freeVPNjd',     
        'https://t.me/s/freekankan',  
        'https://t.me/s/v2ray_free_vpn'
    ];

    console.log("🚀 WARP 环境启动，开始递归抓取...");

    // 1. 获取频道源码
    const contents = await Promise.all(CHANNELS.map(async url => {
        try {
            const res = await fetch(url);
            return await res.text();
        } catch (e) { return ''; }
    }));

    let globalSubLinks = [];
    let globalNodeLinks = [];

    contents.forEach(html => {
        if (!html) return;
        const wideRegex = /(https?|ss|ssr|vmess|vless|trojan|hysteria2|hy2):\/\/[^\s"<>]+/g;
        const matches = html.match(wideRegex) || [];
        const ignoreRegex = /\/\/(t\.me|telegram\.org|google\.com|gstatic\.com|apple\.com|twitter\.com|facebook\.com)\//;
        const filtered = [...new Set(matches)].filter(l => !ignoreRegex.test(l));

        globalSubLinks.push(...filtered.filter(l => l.startsWith('http')).slice(-SUB_LIMIT));
        globalNodeLinks.push(...filtered.filter(l => !l.startsWith('http')).slice(-NODE_LIMIT));
    });

    const finalSubLinks = [...new Set(globalSubLinks)];
    console.log(`📡 发现订阅链接: ${finalSubLinks.length} 个。正在通过 WARP 下载...`);

    // 2. 递归下载
    let proxiesFromSub = [];
    for (const url of finalSubLinks) {
        try {
            const res = await fetch(url, { headers: { 'user-agent': 'ClashMeta/1.18.0' } });
            if (res.ok) {
                const body = await res.text();
                let decoded = body;
                if (!body.includes('://')) {
                    try { decoded = Buffer.from(body, 'base64').toString(); } catch(e) {}
                }
                const nodes = decoded.match(/(ss|ssr|vmess|vless|trojan|hysteria2|hy2):\/\/[^\s"<>|]+/g) || [];
                proxiesFromSub.push(...nodes);
                if (nodes.length > 0) console.log(`✅ 成功抓取: ${nodes.length} 个节点`);
            }
        } catch (e) {}
    }

    // 3. 合并与重命名防止覆盖
    const allNodes = [...new Set([...proxiesFromSub, ...globalNodeLinks])];
    const nameMap = new Map();
    const finalResult = [];

    allNodes.forEach(proxy => {
        try {
            if (proxy.startsWith('vmess://')) {
                let config = JSON.parse(Buffer.from(proxy.slice(8), 'base64').toString());
                let baseName = config.ps || "Node";
                let count = (nameMap.get(baseName) || 0) + 1;
                nameMap.set(baseName, count);
                config.ps = count > 1 ? `${baseName} ${count}` : baseName;
                finalResult.push('vmess://' + Buffer.from(JSON.stringify(config)).toString('base64'));
            } else if (proxy.includes('#')) {
                let [uri, name] = proxy.split('#');
                let baseName = decodeURIComponent(name || "Node");
                let count = (nameMap.get(baseName) || 0) + 1;
                nameMap.set(baseName, count);
                let finalName = count > 1 ? `${baseName} ${count}` : baseName;
                finalResult.push(`${uri}#${encodeURIComponent(finalName)}`);
            } else {
                finalResult.push(proxy);
            }
        } catch (e) { finalResult.push(proxy); }
    });

    fs.writeFileSync('sub.txt', Buffer.from(finalResult.join('\n')).toString('base64'));
    console.log(`\n🎉 任务结束！最终节点总数: ${finalResult.length}`);
}

main();
