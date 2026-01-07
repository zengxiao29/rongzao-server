/**
 * 商品名称映射规则
 * 用于将相似的商品名称映射到统一的名称，实现商品去重
 */

/**
 * 商品名称映射规则配置
 * 按照优先级从高到低匹配，一旦匹配成功就返回对应的映射名称
 */
const PRODUCT_MAPPING_RULES = [
    // 规则1: 特定夹克商品保持原名（不做去重）
    {
        type: 'exact',
        exactName: '4代蓝色经典飞行夹克',
        mappedName: '4代蓝色经典飞行夹克'
    },
    {
        type: 'exact',
        exactName: '荣造王牌飞行系列35飞行夹克',
        mappedName: '荣造王牌飞行系列35飞行夹克'
    },
    {
        type: 'exact',
        exactName: '王牌飞行系列共和国天空飞行夹克',
        mappedName: '王牌飞行系列共和国天空飞行夹克'
    },
    {
        type: 'exact',
        exactName: '指挥员系列飞行夹克',
        mappedName: '指挥员系列飞行夹克'
    },

    // 规则2: 其他夹克商品合并为"其他夹克"
    {
        type: 'keyword',
        keyword: '夹克',
        mappedName: '其他夹克'
    },

    // 规则3: 弹射时代系列帽子合并
    {
        type: 'prefix',
        prefix: '弹射时代系列J15T帽子',
        mappedName: '弹射时代系列帽子'
    },
    {
        type: 'prefix',
        prefix: '弹射时代系列J35帽子',
        mappedName: '弹射时代系列帽子'
    },
    {
        type: 'prefix',
        prefix: '弹射时代系列KJ600帽子',
        mappedName: '弹射时代系列帽子'
    },

    // 规则4: 山东舰飞织舰帽颜色去重
    {
        type: 'prefix',
        prefix: '山东舰飞织舰帽',
        mappedName: '山东舰飞织舰帽'
    },

    // 规则5: 山东舰热熔款舰帽颜色去重
    {
        type: 'prefix',
        prefix: '山东舰热熔款舰帽',
        mappedName: '山东舰热熔款舰帽'
    },

    // 规则6: 特定前缀的商品归为一类
    {
        type: 'prefix',
        prefix: '航母岗位章',
        mappedName: '航母岗位章'
    },
    {
        type: 'prefix',
        prefix: '舰载熊猫公仔',
        mappedName: '舰载熊猫公仔'
    },
    {
        type: 'prefix',
        prefix: '舰载熊猫',
        mappedName: '舰载熊猫'
    },
    {
        type: 'prefix',
        prefix: '舰载',
        mappedName: '舰载公仔'
    },
    {
        type: 'prefix',
        prefix: '航空母舰',
        mappedName: '航空母舰'
    },
    {
        type: 'prefix',
        prefix: '航母',
        mappedName: '航母'
    },
    {
        type: 'prefix',
        prefix: '熊猫',
        mappedName: '熊猫'
    },
    {
        type: 'prefix',
        prefix: '公仔',
        mappedName: '公仔'
    },

    // 规则7: 去除颜色后缀（--开头）
    {
        type: 'suffix',
        pattern: /--.*$/,
        mappedName: null // null表示去除该后缀
    },

    // 规则8: 去除尺寸后缀（-开头，后跟数字）
    {
        type: 'suffix',
        pattern: /-\d+$/,
        mappedName: null
    },

    // 规则9: 去除尺寸后缀（-开头，后跟数字和字母组合，如-58, -XS, -61）
    {
        type: 'suffix',
        pattern: /-\d+[A-Za-z]*$/,
        mappedName: null
    },

    // 规则10: 去除尺寸后缀（-开头，后跟字母）
    {
        type: 'suffix',
        pattern: /-[A-Za-z]+$/,
        mappedName: null
    },

    // 规则11: 去除尺寸单位（数字+CM）
    {
        type: 'suffix',
        pattern: /\d+CM$/i,
        mappedName: null
    },

    // 规则12: 去除末尾纯数字
    {
        type: 'suffix',
        pattern: /\d+$/,
        mappedName: null
    }
];

/**
 * 商品名称映射函数
 * @param {string} productName - 原始商品名称
 * @returns {string} 映射后的商品名称
 */
function mapProductName(productName) {
    if (!productName || typeof productName !== 'string') {
        return productName;
    }

    let mappedName = productName.trim();

    // 按规则顺序处理
    for (const rule of PRODUCT_MAPPING_RULES) {
        if (rule.type === 'exact') {
            // 精确匹配规则
            if (mappedName === rule.exactName) {
                mappedName = rule.mappedName;
                break; // 匹配成功后立即返回
            }
        } else if (rule.type === 'keyword') {
            // 关键词匹配规则
            if (mappedName.includes(rule.keyword)) {
                mappedName = rule.mappedName;
                break; // 匹配成功后立即返回
            }
        } else if (rule.type === 'prefix') {
            // 前缀匹配规则
            if (mappedName.startsWith(rule.prefix)) {
                mappedName = rule.mappedName;
                break; // 匹配成功后立即返回
            }
        } else if (rule.type === 'suffix') {
            // 后缀去除规则
            mappedName = mappedName.replace(rule.pattern, '');
        }
    }

    // 去除首尾空格
    mappedName = mappedName.trim();

    return mappedName;
}

// 导出函数供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        PRODUCT_MAPPING_RULES,
        mapProductName
    };
}