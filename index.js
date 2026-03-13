const fs = require('fs');

// ==========================================
// ⚙️ 核心配置
// ==========================================
const CHANNELS = [
    'https://t.me/s/freeVPNjd',     
    'https://t.me/s/freekankan',  
    'https://t.me/s/v2ray_free_vpn'
];
const SUB_LIMIT = 5;  // 每个频道抓取最近的 5 个订阅链接
const RENAME_PREFIX = "Telegram｜";

// ==========================================
// 🛠️ 你的重命名工具集
// ==========================================
const countryMap = [
    { keys: /香港|港|HK/i, flag: '🇭🇰', name: '香港' },
    { keys: /台湾|台|TW/i, flag: '🇨🇳', name: '台湾' },
    { keys: /日本|日|JP/i, flag: '🇯🇵', name: '日本' },
    { keys: /美国|美|US/i, flag: '🇺🇸', name: '美国' },
    { keys: /新加坡|新|SG/i, flag: '🇸🇬', name: '新加坡' }
];

// 解析并重命名（支持 VMESS 和其他格式的简单处理）
function renameAndFormat(node, region, seq) {
    let newName = `${RENAME_PREFIX}${node.flag} ${region} ${seq}`;
    if (node.uri.startsWith('vmess://')) {
        try {
            let config = JSON.parse(Buffer.from(node.uri.slice(8), 'base64').toString());
            config.ps = newName;
            return 'vmess://' + Buffer.from(JSON.stringify(config)).toString('base64');
        } catch (e) { return null; }
    } else if (node.uri.includes('#')) {
        return node.uri.split('#')[0] + '#' + encodeURIComponent(newName);
    }
    return null;
}

// ==========================================
// 🚀 核心逻辑
// ==========================================
async function main() {
    let allLinks = [];

    // 1. 抓取频道网页内容
    for (let url of CHANNELS) {
        try {
            console.log(`📡 正在读取频道: ${url}`);
            const res = await fetch(url);
            const html = await res.text();
            
            // 提取所有链接
            const linkRegex = /(https?|ss|vmess|vless|trojan):\/\/[^\s"<>|]+/g;
            const matches = html.match(linkRegex) || [];
            
            // 过滤掉 Telegram 官方域名和垃圾链接
            const ignore = /t\.me|telegram\.org|google\.com|gstatic\.com|apple\.com/;
            const filtered = matches.filter(l => !ignore.test(l));
            
            // 分别提取订阅链接(http)和单节点(protocol://)
            const subs = filtered.filter(l => l.startsWith('http')).slice(-SUB_LIMIT);
            const nodes = filtered.filter(l => !l.startsWith('http')).slice(-10); // 每个频道顺便带 10 个单节点
            
            allLinks.push(...subs, ...nodes);
        } catch (e) { console.log(`❌ 频道抓取失败: ${url}`); }
    }

    let finalUris = [];
    const uniqueLinks = [...new Set(allLinks)];
    console.log(`🔗 抓取到待处理链接共: ${uniqueLinks.length} 个`);

    // 2. 像 Sub-Store 一样下载订阅链接内容
    for (let link of uniqueLinks) {
        if (link.startsWith('http')) {
            try {
                const res = await fetch(link, { timeout: 3000 });
                const content = await res.text();
                // 尝试 base64 解码订阅内容
                let decoded = "";
                try {
                    decoded = Buffer.from(content, 'base64').toString('utf8');
                } catch(e) { decoded = content; }
                
                const subNodes = decoded.match(/(ss|vmess|vless|trojan):\/\/[^\s"<>|]+/g) || [];
                finalUris.push(...subNodes);
                console.log(`📥 从订阅链接下到 ${subNodes.length} 个节点`);
            } catch (e) {}
        } else {
            finalUris.push(link);
        }
    }

    // 3. 结构化重命名 (按照你的要求：不覆盖，且按你的格式)
    let nodesForRename = [];
    [...new Set(finalUris)].forEach(uri => {
        // 简单识别国家
        let flag = '🏴', name = '其他';
        for (let c of countryMap) {
            if (c.keys.test(uri)) { flag = c.flag; name = c.name; break; }
        }
        nodesForRename.push({ uri, flag, name });
    });

    // 分组排序并导出
    let grouped = {};
    nodesForRename.forEach(n => {
        if (!grouped[n.name]) grouped[n.name] = [];
        grouped[n.name].push(n);
    });

    let output = [];
    Object.keys(grouped).forEach(region => {
        grouped[region].forEach((item, index) => {
            let seq = (index + 1).toString().padStart(2, '0');
            let formatted = renameAndFormat(item, region, seq);
            if (formatted) output.push(formatted);
        });
    });

    // 4. 写入文件（Base64 编码，方便 Surge 订阅）
    fs.writeFileSync('sub.txt', Buffer.from(output.join('\n')).toString('base64'));
    console.log(`🎉 任务完成！总共生成了 ${output.length} 个节点，请在 GitHub 仓库查看 sub.txt`);
}

main();
