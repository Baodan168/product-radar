const FESTIVALS = [

// ===== 2027年1月（4个）=====
{
  id: "new-year-2027",
  name: "新年/新年新气象", nameEn: "New Year 2027", icon: "🎆",
  date: "2027-01-01", month: 1, importance: "A", category: "festival",
  themeColor: "#f59e0b",
  products: [
    { sku: "2027新年日历/挂历", skuEn: "2027 Calendar Wall Planner", category: "gift", costRange: "¥3-8", priceRange: "£5.99-8.99", margin: "约55-65%", matchScore: 5, riskLevel: "低", riskNote: "新年刚需；12月备货1月上架", keywords: ["2027 calendar","wall planner","new year calendar"], sourcing: "1688: 2027日历挂历" },
    { sku: "新年目标规划本", skuEn: "New Year Goal Planner Notebook", category: "gift", costRange: "¥5-12", priceRange: "£6.99-9.99", margin: "约50-60%", matchScore: 5, riskLevel: "低", riskNote: "新年Resolution季；可定制封面", keywords: ["goal planner","new year resolution","journal 2027"], sourcing: "1688: 新年规划本" },
    { sku: "新年装饰灯串(LED)", skuEn: "New Year LED String Lights", category: "decor", costRange: "¥5-10", priceRange: "£6.49-8.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "注意UK插头/电压；UKCA认证", keywords: ["led lights","new year decorations","string lights"], sourcing: "1688: LED灯串装饰" },
    { sku: "新年派对用品套装", skuEn: "New Year Party Supplies Kit", category: "decor", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "含气球/横幅/帽子等；常规品类", keywords: ["new year party","party supplies","celebration kit"], sourcing: "1688: 新年派对用品" },
    { sku: "收纳整理标签贴(新年大扫除)", skuEn: "Home Organization Label Stickers", category: "home", costRange: "¥3-6", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "新年大扫除季；轻小件", keywords: ["organization labels","home storage","declutter"], sourcing: "1688: 收纳标签贴" },
    { sku: "香薰蜡烛礼盒(新年款)", skuEn: "Scented Candle Gift Set New Year", category: "home", costRange: "¥10-20", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "中", riskNote: "蜡烛运输注意安全；需MSDS", keywords: ["scented candle","gift set","new year gift","aromatherapy"], sourcing: "1688: 香薰蜡烛礼盒" }
  ],
  validation: {
    googleTrends: ["new year 2027","new year party supplies uk","calendar 2027"],
    amazonCheck: "BSR < 8000；日历/规划本12-1月峰值",
    sourcing: "1688搜索：新年用品/日历/派对装饰",
    riskFlags: ["电子产品注意UKCA","日历类时效性强需提前备货"]
  }
},
{
  id: "january-sales-2027",
  name: "1月大促/清仓季", nameEn: "January Sales", icon: "🏷️",
  date: "2027-01-05", month: 1, importance: "A", category: "activity",
  themeColor: "#ef4444",
  products: [
    { sku: "家居收纳箱(折叠)", skuEn: "Foldable Storage Box", category: "home", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-50%", matchScore: 5, riskLevel: "低", riskNote: "新年收纳季；注意FBA体积费", keywords: ["storage box","foldable organizer","home storage"], sourcing: "1688: 折叠收纳箱" },
    { sku: "瑜伽垫(初学者)", skuEn: "Beginner Yoga Mat", category: "home", costRange: "¥15-25", priceRange: "£8.99-9.99", margin: "约35-45%", matchScore: 4, riskLevel: "低", riskNote: "新年健身季；体积大注意物流", keywords: ["yoga mat","exercise mat","fitness equipment"], sourcing: "1688: 瑜伽垫" },
    { sku: "运动水壶(刻度)", skuEn: "Motivational Water Bottle with Time Markers", category: "home", costRange: "¥6-12", priceRange: "£6.99-9.99", margin: "约50-60%", matchScore: 5, riskLevel: "低", riskNote: "Tritan材质BPA-Free；新年健身必备", keywords: ["water bottle","motivational bottle","fitness bottle"], sourcing: "1688: 刻度运动水壶" },
    { sku: "厨房调料收纳架", skuEn: "Kitchen Spice Rack Organizer", category: "home", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "新年厨房整理；常规品类", keywords: ["spice rack","kitchen organizer","storage rack"], sourcing: "1688: 调料收纳架" },
    { sku: "手机支架(桌面)", skuEn: "Desktop Phone Stand Holder", category: "gift", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 5, riskLevel: "低", riskNote: "轻小件高毛利；刚需品", keywords: ["phone stand","desktop holder","phone holder"], sourcing: "1688: 手机支架" }
  ],
  validation: {
    googleTrends: ["january sales uk","new year deals","home organization"],
    amazonCheck: "BSR < 6000；收纳/健身类1月峰值",
    sourcing: "1688搜索：收纳用品/健身器材/厨房用品",
    riskFlags: ["大件商品注意FBA仓储费","电子类产品UKCA"]
  }
},
{
  id: "burns-night-2027",
  name: "彭斯之夜", nameEn: "Burns Night", icon: "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
  date: "2027-01-25", month: 1, importance: "B", category: "festival",
  themeColor: "#1e40af",
  products: [
    { sku: "苏格兰格纹装饰品", skuEn: "Tartan Scottish Decorations", category: "decor", costRange: "¥5-12", priceRange: "£6.99-9.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "苏格兰小众市场；格纹经典", keywords: ["tartan","scottish decor","burns night"], sourcing: "1688: 苏格兰格纹" },
    { sku: "威士忌酒杯(水晶玻璃)", skuEn: "Whisky Crystal Glass", category: "home", costRange: "¥8-18", priceRange: "£7.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "中", riskNote: "易碎品注意包装；需防震", keywords: ["whisky glass","crystal glass","scotch glass"], sourcing: "1688: 威士忌杯" },
    { sku: "苏格兰风笛音乐盒", skuEn: "Scottish Music Box Bagpipes", category: "gift", costRange: "¥10-20", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 3, riskLevel: "低", riskNote: "小众纪念品；苏格兰旅游季", keywords: ["scottish gift","music box","bagpipes souvenir"], sourcing: "1688: 苏格兰纪念品" },
    { sku: "格纹围巾/披肩", skuEn: "Tartan Scarf Shawl", category: "apparel", costRange: "¥10-20", priceRange: "£7.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "低", riskNote: "冬季实用；苏格兰风格", keywords: ["tartan scarf","scottish shawl","plaid scarf"], sourcing: "1688: 格纹围巾" },
    { sku: "苏格兰主题杯垫套装", skuEn: "Scottish Coaster Set", category: "home", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "轻小件；苏格兰元素", keywords: ["scottish coaster","tartan coaster","burns night coaster"], sourcing: "1688: 主题杯垫" },
    { sku: "短bread饼干礼盒(苏格兰特产)", skuEn: "Scottish Shortbread Gift Box", category: "gift", costRange: "¥10-20", priceRange: "£7.99-9.99", margin: "约35-45%", matchScore: 3, riskLevel: "中", riskNote: "食品类需UK食品认证；保质期管理", keywords: ["shortbread","scottish biscuit","food gift"], sourcing: "1688: 曲奇饼干礼盒" }
  ],
  validation: {
    googleTrends: ["burns night 2027","scottish gifts","tartan"],
    amazonCheck: "BSR < 20000；小众但1月峰值明显",
    sourcing: "1688搜索：苏格兰/格纹/威士忌配件",
    riskFlags: ["食品类需UK进口许可","易碎品包装成本高"]
  }
},
{
  id: "veganuary-2027",
  name: "纯素月/Veganuary", nameEn: "Veganuary", icon: "🥬",
  date: "2027-01-15", month: 1, importance: "A", category: "trend",
  themeColor: "#22c55e",
  products: [
    { sku: "植物奶搅拌杯", skuEn: "Plant Milk Frother Cup", category: "home", costRange: "¥10-20", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 5, riskLevel: "低", riskNote: "Veganuary刚需；电动搅拌", keywords: ["milk frother","plant milk","oat milk"], sourcing: "1688: 植物奶搅拌杯" },
    { sku: "纯素食谱书", skuEn: "Vegan Recipe Book", category: "gift", costRange: "¥10-20", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 5, riskLevel: "低", riskNote: "Veganuary必备；礼品属性", keywords: ["vegan cookbook","plant based recipes","veganuary book"], sourcing: "1688: 素食食谱" },
    { sku: "不锈钢午餐盒(分格)", skuEn: "Stainless Steel Bento Box", category: "home", costRange: "¥15-25", priceRange: "£8.99-9.99", margin: "约35-45%", matchScore: 4, riskLevel: "低", riskNote: "环保便携；纯素午餐", keywords: ["bento box","steel lunchbox","eco lunch"], sourcing: "1688: 不锈钢午餐盒" },
    { sku: "纯素主题购物袋", skuEn: "Vegan Theme Tote Bag", category: "apparel", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "环保+纯素标语", keywords: ["vegan bag","eco tote","plant based bag"], sourcing: "1688: 主题帆布袋" }
  ],
  validation: {
    googleTrends: ["veganuary 2027","vegan products","plant based uk"],
    amazonCheck: "BSR < 8000；1月纯素品类暴增300%+",
    sourcing: "1688搜索：纯素/植物基/素食",
    riskFlags: ["食品需UK认证","化妆品需CPNP","避免非纯素产品标注纯素"]
  }
},

// ===== 2027年2月（5个）=====
{
  id: "chinese-new-year-2027",
  name: "中国春节", nameEn: "Chinese New Year", icon: "🧧",
  date: "2027-02-06", month: 2, importance: "A", category: "festival",
  themeColor: "#dc2626",
  products: [
    { sku: "春节红包套装(创意款)", skuEn: "Chinese New Year Red Envelope Set", category: "gift", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 5, riskLevel: "低", riskNote: "轻小件；春节必备", keywords: ["red envelope","lucky money","chinese new year"], sourcing: "1688: 春节红包" },
    { sku: "春节灯笼装饰(LED)", skuEn: "Chinese New Year LED Lantern", category: "decor", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "LED注意UKCA；传统节日装饰", keywords: ["chinese lantern","new year lantern","led lantern"], sourcing: "1688: 春节灯笼" },
    { sku: "春节对联/福字贴", skuEn: "Chinese New Year Couplets Fu Stickers", category: "decor", costRange: "¥3-6", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "纸质品轻小；华人社区需求", keywords: ["spring couplets","fu sticker","chinese decoration"], sourcing: "1688: 春联福字" },
    { sku: "十二生肖摆件(当年款)", skuEn: "Chinese Zodiac Figurine", category: "gift", costRange: "¥5-12", priceRange: "£6.99-9.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "⚠️待复核: 陶瓷/树脂材质；礼品属性", keywords: ["zodiac figurine","chinese new year gift","animal figure"], sourcing: "1688: 生肖摆件" },
    { sku: "春节主题茶叶礼盒", skuEn: "Chinese Tea Gift Set New Year", category: "gift", costRange: "¥15-30", priceRange: "£8.99-9.99", margin: "约30-40%", matchScore: 3, riskLevel: "中", riskNote: "食品类需UK进口许可；保质期管理", keywords: ["tea gift set","chinese tea","new year gift"], sourcing: "1688: 茶叶礼盒" },
    { sku: "舞龙舞狮小模型", skuEn: "Dragon Lion Dance Miniature", category: "gift", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 3, riskLevel: "低", riskNote: "⚠️待复核: 文化创意品；摆件装饰", keywords: ["dragon dance","lion dance","chinese figurine"], sourcing: "1688: 舞龙舞狮模型" }
  ],
  validation: {
    googleTrends: ["chinese new year 2027","red envelope","chinese new year decorations"],
    amazonCheck: "BSR < 15000；1-2月峰值；华人社区+文化爱好者",
    sourcing: "1688搜索：春节用品/红包/灯笼",
    riskFlags: ["食品类需UK进口许可","时效性强需提前备货"]
  }
},
{
  id: "pancake-day-2027",
  name: "煎饼日/忏悔星期二", nameEn: "Pancake Day / Shrove Tuesday", icon: "🥞",
  date: "2027-02-16", month: 2, importance: "B", category: "festival",
  themeColor: "#f59e0b",
  products: [
    { sku: "不粘煎饼锅(平底)", skuEn: "Non-Stick Crepe Pan", category: "home", costRange: "¥15-25", priceRange: "£8.99-9.99", margin: "约35-45%", matchScore: 5, riskLevel: "低", riskNote: "煎饼日刚需；食品级涂层", keywords: ["crepe pan","pancake pan","non stick pan"], sourcing: "1688: 煎饼锅" },
    { sku: "硅胶煎饼模具(表情)", skuEn: "Silicone Pancake Mold Fun Shapes", category: "home", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "食品级硅胶；趣味造型", keywords: ["pancake mold","silicone mold","breakfast tool"], sourcing: "1688: 煎饼模具" },
    { sku: "量杯量勺套装", skuEn: "Measuring Cup Spoon Set", category: "home", costRange: "¥5-10", priceRange: "£6.49-8.49", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "烘焙刚需；常青品类", keywords: ["measuring cups","measuring spoons","baking tools"], sourcing: "1688: 量杯量勺" },
    { sku: "枫糖浆瓶(挤压式)", skuEn: "Maple Syrup Squeeze Bottle", category: "home", costRange: "¥5-10", priceRange: "£6.49-8.49", margin: "约45-55%", matchScore: 4, riskLevel: "中", riskNote: "食品接触材质；需BPA-Free", keywords: ["syrup bottle","pancake syrup","squeeze bottle"], sourcing: "1688: 调料瓶" },
  ],
  validation: {
    googleTrends: ["pancake day 2027","shrove tuesday","pancake accessories"],
    amazonCheck: "BSR < 20000；2月短期峰值",
    sourcing: "1688搜索：煎饼工具/烘焙配件",
    riskFlags: ["时效性强仅2月","食品接触材质需认证"]
  }
},
{
  id: "valentines-day-2027",
  name: "情人节", nameEn: "Valentine's Day", icon: "💝",
  date: "2027-02-14", month: 2, importance: "S", category: "festival",
  themeColor: "#e11d48",
  products: [
    { sku: "永生花礼盒(玫瑰)", skuEn: "Preserved Rose Flower Box", category: "gift", costRange: "¥15-30", priceRange: "£8.99-9.99", margin: "约35-45%", matchScore: 5, riskLevel: "低", riskNote: "情人节TOP1礼品；需防震包装", keywords: ["preserved rose","flower box","valentine flower"], sourcing: "1688: 永生花礼盒" },
    { sku: "情侣对杯(心形)", skuEn: "Couple Mugs Heart Design", category: "gift", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 5, riskLevel: "中", riskNote: "陶瓷易碎；需防震包装", keywords: ["couple mugs","valentine mug","heart mug"], sourcing: "1688: 情侣对杯" },
    { sku: "情人节巧克力礼盒", skuEn: "Valentine Chocolate Gift Box", category: "gift", costRange: "¥15-30", priceRange: "£8.99-9.99", margin: "约30-40%", matchScore: 5, riskLevel: "中", riskNote: "食品需UK认证；温控物流", keywords: ["chocolate box","valentine chocolate","gift chocolate"], sourcing: "1688: 巧克力礼盒" },
    { sku: "LED心形灯串", skuEn: "LED Heart String Lights", category: "decor", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 5, riskLevel: "低", riskNote: "UKCA认证；浪漫装饰", keywords: ["heart lights","led string","valentine decor"], sourcing: "1688: 心形灯串" },
    { sku: "情侣手链(可刻字)", skuEn: "Couple Bracelet Engraved", category: "apparel", costRange: "¥8-18", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 5, riskLevel: "低", riskNote: "可定制刻字增加附加值", keywords: ["couple bracelet","engraved bracelet","love bracelet"], sourcing: "1688: 情侣手链" },
    { sku: "情人节卡片套装(手工)", skuEn: "Handmade Valentine Card Set", category: "gift", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "手工感溢价高；轻小件", keywords: ["valentine card","handmade card","love card"], sourcing: "1688: 情人节贺卡" },
    { sku: "玫瑰花束香皂花", skuEn: "Soap Rose Flower Bouquet", category: "gift", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "不凋谢替代鲜花；香味卖点", keywords: ["soap rose","flower bouquet","valentine gift"], sourcing: "1688: 香皂花" },
    { sku: "情侣睡衣套装", skuEn: "Couple Pajama Set", category: "apparel", costRange: "¥15-25", priceRange: "£8.99-9.99", margin: "约35-45%", matchScore: 4, riskLevel: "中", riskNote: "UK尺码对照；面料舒适度", keywords: ["couple pajama","matching pjs","valentine pajama"], sourcing: "1688: 情侣睡衣" },
    { sku: "3D立体情人节贺卡", skuEn: "3D Pop-Up Valentine Card", category: "gift", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "创意设计溢价；轻小件", keywords: ["3d card","pop up card","valentine greeting"], sourcing: "1688: 3D立体贺卡" },
    { sku: "爱情存钱罐(情侣款)", skuEn: "Love Coin Bank Couple", category: "gift", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 3, riskLevel: "低", riskNote: "创意家居摆件", keywords: ["coin bank","love piggy bank","couple gift"], sourcing: "1688: 情侣存钱罐" },
    { sku: "定制照片相框(心形)", skuEn: "Heart Photo Frame Custom", category: "decor", costRange: "¥8-18", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "可定制照片增加情感价值", keywords: ["photo frame","heart frame","custom frame","valentine decor"], sourcing: "1688: 心形相框" },
    { sku: "情侣马克杯(变色)", skuEn: "Heat Change Couple Mug", category: "gift", costRange: "¥10-20", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "中", riskNote: "变色技术需测试稳定性", keywords: ["heat change mug","magic mug","couple mug"], sourcing: "1688: 变色马克杯" },
    { sku: "爱情钥匙扣(一对)", skuEn: "Love Keychain Pair Set", category: "gift", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "轻小件；情侣必备小礼品", keywords: ["couple keychain","love keychain","valentine keyring"], sourcing: "1688: 情侣钥匙扣" },
  ],
  validation: {
    googleTrends: ["valentine's day 2027","valentine gifts uk","romantic gifts"],
    amazonCheck: "BSR < 3000；1月底-2月中旬爆发期；TOP品类",
    sourcing: "1688搜索：情人节礼品/永生花/巧克力",
    riskFlags: ["食品类需UK认证","易碎品包装成本高","时效性极强2月14日前必须到仓"]
  }
},
{
  id: "random-acts-2027",
  name: "世界随机善行日", nameEn: "Random Acts of Kindness Day", icon: "🤝",
  date: "2027-02-17", month: 2, importance: "B", category: "festival",
  themeColor: "#10b981",
  products: [
    { sku: "感谢卡片套装", skuEn: "Thank You Card Set", category: "gift", costRange: "¥3-6", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "善行日主题；轻小件", keywords: ["thank you card","kindness card","greeting cards"], sourcing: "1688: 感谢贺卡" },
    { sku: "善行日徽章/贴纸", skuEn: "Kindness Badge Sticker Pack", category: "gift", costRange: "¥2-5", priceRange: "£5.99-6.99", margin: "约60-70%", matchScore: 4, riskLevel: "低", riskNote: "超轻小件高毛利", keywords: ["kindness badge","sticker pack","motivation sticker"], sourcing: "1688: 创意徽章贴纸" },
    { sku: "手工皂礼盒(天然)", skuEn: "Natural Handmade Soap Gift Box", category: "gift", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 3, riskLevel: "低", riskNote: "天然成分卖点；礼品属性", keywords: ["handmade soap","natural soap","gift soap"], sourcing: "1688: 手工皂礼盒" },
    { sku: "励志语录马克杯", skuEn: "Inspirational Quote Mug", category: "gift", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "陶瓷易碎；正能量语录", keywords: ["inspirational mug","quote mug","motivation gift"], sourcing: "1688: 励志马克杯" },
    { sku: "种子纸贺卡(可种植)", skuEn: "Plantable Seed Paper Card", category: "gift", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "环保概念；可种植创意", keywords: ["seed paper","plantable card","eco card","kindness"], sourcing: "1688: 种子纸" }
  ],
  validation: {
    googleTrends: ["random acts of kindness","kindness gifts"],
    amazonCheck: "BSR < 30000；小众但话题性强",
    sourcing: "1688搜索：贺卡/手工皂/创意礼品",
    riskFlags: ["小众节日备货量需控制"]
  }
},
{
  id: "six-nations-2027",
  name: "六国橄榄球赛", nameEn: "Six Nations Rugby", icon: "🏉",
  date: "2027-02-07", month: 2, importance: "B", category: "activity",
  themeColor: "#059669",
  products: [
    { sku: "橄榄球主题围巾", skuEn: "Rugby Team Scarf", category: "apparel", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "赛事期间刚需；球队配色", keywords: ["rugby scarf","sports scarf","six nations"], sourcing: "1688: 体育围巾" },
    { sku: "橄榄球形状抱枕", skuEn: "Rugby Ball Shaped Cushion", category: "home", costRange: "¥10-18", priceRange: "£7.99-9.99", margin: "约40-50%", matchScore: 3, riskLevel: "低", riskNote: "体育主题家居", keywords: ["rugby cushion","sports pillow","rugby decor"], sourcing: "1688: 橄榄球抱枕" },
    { sku: "球队旗帜/三角旗", skuEn: "Rugby Team Pennant Flag", category: "decor", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "赛事装饰；轻小件", keywords: ["pennant flag","rugby flag","sports banner"], sourcing: "1688: 三角旗" },
    { sku: "啤酒杯垫套装(橄榄球)", skuEn: "Rugby Beer Coaster Set", category: "home", costRange: "¥3-6", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 3, riskLevel: "低", riskNote: "看球配件；轻小件", keywords: ["beer coaster","rugby coaster","sports coaster"], sourcing: "1688: 啤酒杯垫" },
  ],
  validation: {
    googleTrends: ["six nations 2027","rugby accessories","match day"],
    amazonCheck: "BSR < 25000；2-3月赛季",
    sourcing: "1688搜索：橄榄球/体育用品/赛事周边",
    riskFlags: ["时效性2-3月","需避免球队商标侵权"]
  }
},

// ===== 2027年3月（6个）=====
{
  id: "st-davids-2027",
  name: "圣大卫节", nameEn: "St David's Day", icon: "🏴󠁧󠁢󠁷󠁬󠁳󠁿",
  date: "2027-03-01", month: 3, importance: "B", category: "festival",
  themeColor: "#16a34a",
  products: [
    { sku: "威尔士龙旗帜", skuEn: "Welsh Dragon Flag", category: "decor", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "威尔士国庆装饰；小众市场", keywords: ["welsh flag","dragon flag","st davids day"], sourcing: "1688: 威尔士旗帜" },
    { sku: "威尔士水仙花胸针", skuEn: "Welsh Daffodil Brooch", category: "apparel", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "圣大卫节传统配饰", keywords: ["daffodil brooch","welsh pin","st davids"], sourcing: "1688: 胸针徽章" },
    { sku: "威尔士主题马克杯", skuEn: "Welsh Theme Mug", category: "gift", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 3, riskLevel: "低", riskNote: "威尔士元素；礼品属性", keywords: ["welsh mug","st davids mug","wales gift"], sourcing: "1688: 主题马克杯" },
    { sku: "威尔士食谱书签", skuEn: "Welsh Recipe Bookmark Set", category: "gift", costRange: "¥2-5", priceRange: "£5.99-6.99", margin: "约60-70%", matchScore: 3, riskLevel: "低", riskNote: "文创小件；威尔士文化", keywords: ["bookmark","welsh gift","recipe bookmark"], sourcing: "1688: 创意书签" },
    { sku: "威尔士格纹围巾", skuEn: "Welsh Tartan Scarf", category: "apparel", costRange: "¥10-18", priceRange: "£7.99-9.99", margin: "约40-50%", matchScore: 3, riskLevel: "低", riskNote: "威尔士风格；春季保暖", keywords: ["welsh scarf","tartan","st davids scarf"], sourcing: "1688: 格纹围巾" }
  ],
  validation: {
    googleTrends: ["st davids day","welsh gifts","daffodil"],
    amazonCheck: "BSR < 30000；威尔士小众市场",
    sourcing: "1688搜索：威尔士/水仙花/旗帜",
    riskFlags: ["小众节日备货量需控制"]
  }
},
{
  id: "international-womens-2027",
  name: "国际妇女节", nameEn: "International Women's Day", icon: "♀️",
  date: "2027-03-08", month: 3, importance: "A", category: "festival",
  themeColor: "#d946ef",
  products: [
    { sku: "女性励志书籍套装", skuEn: "Women Empowerment Book Set", category: "gift", costRange: "¥10-20", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "低", riskNote: "妇女节礼品；正能量", keywords: ["women empowerment","inspirational book","gift book"], sourcing: "1688: 励志书籍" },
    { sku: "紫色丝带徽章(妇女节)", skuEn: "Purple Ribbon IWD Brooch", category: "apparel", costRange: "¥2-5", priceRange: "£5.99-6.99", margin: "约60-70%", matchScore: 4, riskLevel: "低", riskNote: "超轻小件；象征性配饰", keywords: ["purple ribbon","iwd brooch","womens day pin"], sourcing: "1688: 丝带徽章" },
    { sku: "女性主题帆布袋", skuEn: "Women Empowerment Tote Bag", category: "apparel", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 5, riskLevel: "低", riskNote: "环保实用；女权标语", keywords: ["tote bag","empowerment bag","feminist bag"], sourcing: "1688: 帆布袋定制" },
    { sku: "女性力量手链", skuEn: "Women Power Bracelet", category: "apparel", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "励志标语；串珠设计", keywords: ["power bracelet","women jewelry","empowerment"], sourcing: "1688: 励志手链" },
    { sku: "定制姓名项链", skuEn: "Personalized Name Necklace", category: "apparel", costRange: "¥10-20", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "低", riskNote: "可定制增加附加值", keywords: ["name necklace","personalized jewelry","custom necklace"], sourcing: "1688: 定制项链" }
  ],
  validation: {
    googleTrends: ["international womens day","women empowerment gifts","iwd 2027"],
    amazonCheck: "BSR < 8000；3月初峰值",
    sourcing: "1688搜索：妇女节礼品/女性用品/励志",
    riskFlags: ["化妆品需CPNP注册","精油需MSDS"]
  }
},
{
  id: "mothers-day-uk-2027",
  name: "英国母亲节", nameEn: "Mothering Sunday (UK)", icon: "💐",
  date: "2027-03-14", month: 3, importance: "S", category: "festival",
  themeColor: "#f472b6",
  products: [
    { sku: "母亲节花束礼盒(永生花)", skuEn: "Mother's Day Preserved Flower Box", category: "gift", costRange: "¥15-30", priceRange: "£8.99-9.99", margin: "约35-45%", matchScore: 5, riskLevel: "低", riskNote: "母亲节TOP1礼品；需防震", keywords: ["mothers day flower","preserved flower","flower box"], sourcing: "1688: 永生花礼盒" },
    { sku: "妈妈马克杯(定制文字)", skuEn: "Best Mom Mug Personalized", category: "gift", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 5, riskLevel: "低", riskNote: "经典母亲节礼品；可定制", keywords: ["mom mug","mothers day mug","personalized mug"], sourcing: "1688: 定制马克杯" },
    { sku: "SPA浴盐礼盒", skuEn: "Bath Salt Spa Gift Set", category: "gift", costRange: "¥10-20", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 5, riskLevel: "中", riskNote: "化妆品CPNP；液体注意", keywords: ["bath salt","spa gift","mothers day spa"], sourcing: "1688: 浴盐礼盒" },
    { sku: "母亲节贺卡(手工)", skuEn: "Handmade Mother's Day Card", category: "gift", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 5, riskLevel: "低", riskNote: "手工溢价高；情感价值", keywords: ["mothers day card","handmade card","greeting card"], sourcing: "1688: 母亲节贺卡" },
    { sku: "珍珠项链/手链套装", skuEn: "Pearl Necklace Bracelet Set", category: "apparel", costRange: "¥10-25", priceRange: "£8.99-9.99", margin: "约35-45%", matchScore: 4, riskLevel: "低", riskNote: "优雅礼品；母亲节经典", keywords: ["pearl jewelry","necklace set","mothers day jewelry"], sourcing: "1688: 珍珠饰品" },
    { sku: "围裙(妈妈主题印花)", skuEn: "Apron Mom Theme Print", category: "home", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "实用礼品；厨房主题", keywords: ["apron","mom apron","kitchen gift","cooking apron"], sourcing: "1688: 主题围裙" },
    { sku: "母亲节相框(家庭)", skuEn: "Family Photo Frame Mother's Day", category: "decor", costRange: "¥8-18", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "家庭温馨主题；可放照片", keywords: ["family frame","mothers day frame","photo frame"], sourcing: "1688: 相框" },
    { sku: "香薰蜡烛(薰衣草)", skuEn: "Lavender Scented Candle", category: "home", costRange: "¥8-18", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 4, riskLevel: "中", riskNote: "蜡烛运输安全；需MSDS", keywords: ["lavender candle","scented candle","relaxation candle"], sourcing: "1688: 香薰蜡烛" },
    { sku: "厨房计时器(可爱款)", skuEn: "Cute Kitchen Timer", category: "home", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "实用厨房小工具", keywords: ["kitchen timer","cooking timer","cute timer"], sourcing: "1688: 厨房计时器" },
    { sku: "园艺手套(妈妈款)", skuEn: "Gardening Gloves Mom Design", category: "home", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "春季园艺季；实用礼品", keywords: ["gardening gloves","mom gloves","garden gift"], sourcing: "1688: 园艺手套" },
    { sku: "母亲节早餐托盘", skuEn: "Breakfast in Bed Tray", category: "home", costRange: "¥10-20", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "低", riskNote: "母亲节早餐概念；实用", keywords: ["breakfast tray","bed tray","serving tray"], sourcing: "1688: 早餐托盘" },
    { sku: "定制抱枕(家庭照片)", skuEn: "Custom Photo Cushion", category: "home", costRange: "¥15-25", priceRange: "£8.99-9.99", margin: "约35-45%", matchScore: 4, riskLevel: "低", riskNote: "可定制照片；情感价值高", keywords: ["photo cushion","custom cushion","personalized pillow"], sourcing: "1688: 定制抱枕" },
    { sku: "母亲节糖果礼盒", skuEn: "Mother's Day Candy Gift Box", category: "gift", costRange: "¥10-20", priceRange: "£7.99-9.99", margin: "约35-45%", matchScore: 4, riskLevel: "中", riskNote: "食品需UK认证；保质期", keywords: ["candy gift","sweet box","mothers day treat"], sourcing: "1688: 糖果礼盒" },
    { sku: "母亲节茶巾套装", skuEn: "Mother's Day Tea Towel Set", category: "home", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "实用厨房用品；英式风格", keywords: ["tea towel","kitchen towel","mothers day towel"], sourcing: "1688: 茶巾" },
    { sku: "母亲节珠宝盒", skuEn: "Mother's Day Jewelry Box", category: "gift", costRange: "¥10-20", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "低", riskNote: "收纳+装饰；礼品属性", keywords: ["jewelry box","trinket box","mothers day gift"], sourcing: "1688: 珠宝盒" }
  ],
  validation: {
    googleTrends: ["mothers day uk 2027","mothers day gifts","mothering sunday"],
    amazonCheck: "BSR < 2000；3月中旬爆发期；TOP品类",
    sourcing: "1688搜索：母亲节礼品/永生花/SPA",
    riskFlags: ["化妆品需CPNP","食品需UK认证","时效性极强3月14日前到仓"]
  }
},
{
  id: "st-patricks-2027",
  name: "圣帕特里克节", nameEn: "St Patrick's Day", icon: "☘️",
  date: "2027-03-17", month: 3, importance: "A", category: "festival",
  themeColor: "#16a34a",
  products: [
    { sku: "绿色派对帽子套装", skuEn: "Green Party Hat Set", category: "decor", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 5, riskLevel: "低", riskNote: "圣帕特里克节必备；绿色主题", keywords: ["green hat","st patricks hat","party hat"], sourcing: "1688: 派对帽子" },
    { sku: "三叶草徽章/胸针", skuEn: "Shamrock Brooch Pin", category: "apparel", costRange: "¥2-5", priceRange: "£5.99-6.99", margin: "约60-70%", matchScore: 5, riskLevel: "低", riskNote: "节日标志；超轻小件", keywords: ["shamrock pin","st patricks brooch","clover pin"], sourcing: "1688: 三叶草胸针" },
    { sku: "爱尔兰主题围巾", skuEn: "Irish Theme Scarf", category: "apparel", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "爱尔兰风格；节日配饰", keywords: ["irish scarf","st patricks scarf","green scarf"], sourcing: "1688: 主题围巾" },
    { sku: "啤酒杯(圣帕特里克节)", skuEn: "St Patrick's Day Beer Mug", category: "home", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 4, riskLevel: "中", riskNote: "玻璃易碎；节日主题", keywords: ["beer mug","st patricks glass","irish mug"], sourcing: "1688: 啤酒杯" },
    { sku: "绿色气球装饰套装", skuEn: "Green Balloon Decoration Kit", category: "decor", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "派对装饰；绿色主题", keywords: ["green balloon","party decoration","st patricks decor"], sourcing: "1688: 气球装饰" },
    { sku: "爱尔兰咖啡杯(带盖)", skuEn: "Irish Coffee Mug with Lid", category: "home", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "实用+节日主题", keywords: ["coffee mug","irish mug","travel mug"], sourcing: "1688: 咖啡杯" },
    { sku: "三叶草种子种植套装", skuEn: "Shamrock Growing Kit", category: "gift", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "创意园艺；三叶草主题", keywords: ["shamrock kit","growing kit","plant kit"], sourcing: "1688: 种植套装" }
  ],
  validation: {
    googleTrends: ["st patricks day","irish decorations","shamrock"],
    amazonCheck: "BSR < 10000；3月中旬峰值",
    sourcing: "1688搜索：圣帕特里克/爱尔兰/绿色装饰",
    riskFlags: ["时效性3月17日前","避免国旗/国徽等敏感图案"]
  }
},
{
  id: "spring-equinox-2027",
  name: "春分/春季焕新", nameEn: "Spring Equinox / Spring Refresh", icon: "🌸",
  date: "2027-03-20", month: 3, importance: "B", category: "trend",
  themeColor: "#a855f7",
  products: [
    { sku: "春季花卉种子套装", skuEn: "Spring Flower Seed Kit", category: "home", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 5, riskLevel: "低", riskNote: "春分园艺季；种子需进口许可", keywords: ["flower seeds","spring planting","garden seeds"], sourcing: "1688: 花卉种子" },
    { sku: "园艺工具套装(初学者)", skuEn: "Beginner Gardening Tool Set", category: "home", costRange: "¥10-20", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "低", riskNote: "春季园艺刚需", keywords: ["gardening tools","garden set","plant tools"], sourcing: "1688: 园艺工具" },
    { sku: "春季窗帘/桌布(花卉)", skuEn: "Spring Floral Curtain Tablecloth", category: "home", costRange: "¥15-25", priceRange: "£8.99-9.99", margin: "约35-45%", matchScore: 3, riskLevel: "低", riskNote: "春季换装家居；花卉图案", keywords: ["spring curtain","floral tablecloth","home decor"], sourcing: "1688: 春季窗帘桌布" },
    { sku: "清洁收纳套装(春季大扫除)", skuEn: "Spring Cleaning Organization Set", category: "home", costRange: "¥8-18", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "春季大扫除刚需", keywords: ["spring cleaning","cleaning set","organization"], sourcing: "1688: 清洁收纳" },
    { sku: "蝴蝶装饰挂件", skuEn: "Butterfly Decor Hanging", category: "decor", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "春季装饰；轻小件", keywords: ["butterfly decor","spring decoration","wall hanging"], sourcing: "1688: 蝴蝶装饰" },
    { sku: "花盆/花架(多层)", skuEn: "Multi-Tier Plant Stand Pot", category: "home", costRange: "¥15-25", priceRange: "£8.99-9.99", margin: "约35-45%", matchScore: 3, riskLevel: "低", riskNote: "园艺季；注意FBA体积费", keywords: ["plant stand","flower pot","garden shelf"], sourcing: "1688: 花盆花架" }
  ],
  validation: {
    googleTrends: ["spring equinox","spring gardening","spring cleaning"],
    amazonCheck: "BSR < 15000；3月春季品类上升",
    sourcing: "1688搜索：园艺/花卉/春季家居",
    riskFlags: ["种子需UK进口许可","大件注意FBA费用"]
  }
},
{
  id: "red-nose-day-2027",
  name: "红鼻子日/喜剧救济", nameEn: "Red Nose Day / Comic Relief", icon: "🔴",
  date: "2027-03-13", month: 3, importance: "A", category: "festival",
  themeColor: "#ef4444",
  products: [
    { sku: "红鼻子日红鼻子道具", skuEn: "Red Nose Day Red Nose Prop", category: "gift", costRange: "¥2-5", priceRange: "£5.99-6.99", margin: "约60-70%", matchScore: 5, riskLevel: "低", riskNote: "红鼻子日标志；超轻小件", keywords: ["red nose","comic relief","charity nose"], sourcing: "1688: 红鼻子道具" },
    { sku: "喜剧主题派对套装", skuEn: "Comic Relief Party Kit", category: "decor", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "慈善派对装饰", keywords: ["comic relief party","charity party","red nose party"], sourcing: "1688: 派对用品" },
    { sku: "趣味假发/搞怪帽子", skuEn: "Fun Wig Silly Hat", category: "apparel", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "红鼻子日搞怪传统", keywords: ["funny wig","silly hat","comic hat"], sourcing: "1688: 搞怪帽子" },
    { sku: "慈善主题帆布袋", skuEn: "Charity Theme Tote Bag", category: "apparel", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "慈善+环保概念", keywords: ["charity bag","comic relief tote","red nose bag"], sourcing: "1688: 主题帆布袋" },
    { sku: "趣味徽章套装(慈善)", skuEn: "Charity Badge Pin Set", category: "apparel", costRange: "¥2-5", priceRange: "£5.99-6.99", margin: "约60-70%", matchScore: 4, riskLevel: "低", riskNote: "超轻小件；慈善义卖属性", keywords: ["charity badge","red nose pin","comic relief badge"], sourcing: "1688: 徽章" },
    { sku: "搞笑主题袜子", skuEn: "Silly Pattern Socks", category: "apparel", costRange: "¥5-10", priceRange: "£6.49-8.49", margin: "约50-60%", matchScore: 3, riskLevel: "低", riskNote: "搞怪风格；红鼻子日穿搭", keywords: ["funny socks","silly socks","charity socks"], sourcing: "1688: 搞怪袜子" }
  ],
  validation: {
    googleTrends: ["red nose day","comic relief","charity gifts uk"],
    amazonCheck: "BSR < 10000；3月中旬短期峰值",
    sourcing: "1688搜索：红鼻子/喜剧/慈善周边",
    riskFlags: ["BBC官方活动避免商标侵权","时效性强3月13日前"]
  }
},

// ===== 2027年4月（5个）=====
{
  id: "april-fools-2027",
  name: "愚人节", nameEn: "April Fools' Day", icon: "🤡",
  date: "2027-04-01", month: 4, importance: "B", category: "festival",
  themeColor: "#f59e0b",
  products: [
    { sku: "假虫子/蜘蛛整蛊道具", skuEn: "Fake Bug Spider Prank Props", category: "gift", costRange: "¥2-5", priceRange: "£5.99-6.99", margin: "约60-70%", matchScore: 4, riskLevel: "低", riskNote: "经典整蛊；超轻小件", keywords: ["fake bug","prank props","joke spider"], sourcing: "1688: 整蛊道具" },
    { sku: "搞笑眼镜/胡子套装", skuEn: "Funny Glasses Moustache Set", category: "apparel", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "派对道具；趣味拍照", keywords: ["funny glasses","disguise set","party props"], sourcing: "1688: 搞笑道具" },
    { sku: "会发声的坐垫", skuEn: "Whoopee Cushion", category: "gift", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "经典愚人节道具", keywords: ["whoopee cushion","prank cushion","fart cushion"], sourcing: "1688: 放屁坐垫" },
    { sku: "魔术道具入门套装", skuEn: "Magic Trick Starter Kit", category: "gift", costRange: "¥10-20", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 3, riskLevel: "低", riskNote: "愚人节+儿童兴趣", keywords: ["magic kit","magic tricks","prank magic"], sourcing: "1688: 魔术道具" }
  ],
  validation: {
    googleTrends: ["april fools day","prank gifts","joke toys"],
    amazonCheck: "BSR < 15000；3月底-4月初短期峰值",
    sourcing: "1688搜索：整蛊玩具/恶作剧/愚人节",
    riskFlags: ["注意产品安全标识","避免危险品"]
  }
},
{
  id: "easter-2027",
  name: "复活节", nameEn: "Easter", icon: "🐣",
  date: "2027-04-05", month: 4, importance: "S", category: "festival",
  themeColor: "#fbbf24",
  products: [
    { sku: "复活节彩蛋套装(巧克力)", skuEn: "Easter Chocolate Egg Set", category: "gift", costRange: "¥10-25", priceRange: "£8.99-9.99", margin: "约35-45%", matchScore: 5, riskLevel: "中", riskNote: "食品需UK认证；温控物流", keywords: ["easter egg","chocolate egg","easter candy"], sourcing: "1688: 巧克力彩蛋" },
    { sku: "复活节兔子毛绒玩具", skuEn: "Easter Bunny Plush Toy", category: "gift", costRange: "¥10-20", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 5, riskLevel: "低", riskNote: "儿童礼品；需CE/UKCA", keywords: ["easter bunny","plush toy","stuffed rabbit"], sourcing: "1688: 复活节兔子" },
    { sku: "彩蛋装饰DIY套装", skuEn: "Easter Egg Decorating Kit", category: "gift", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 5, riskLevel: "低", riskNote: "亲子活动；DIY卖点", keywords: ["egg decorating","easter craft","diy easter"], sourcing: "1688: 彩蛋装饰" },
    { sku: "复活节花环(门挂)", skuEn: "Easter Wreath Door Hanging", category: "decor", costRange: "¥15-25", priceRange: "£8.99-9.99", margin: "约35-45%", matchScore: 4, riskLevel: "低", riskNote: "春季装饰；门挂花环", keywords: ["easter wreath","door wreath","spring decoration"], sourcing: "1688: 复活节花环" },
    { sku: "兔子耳朵头饰", skuEn: "Bunny Ear Headband", category: "apparel", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 5, riskLevel: "低", riskNote: "复活节派对必备", keywords: ["bunny ears","easter headband","party accessory"], sourcing: "1688: 兔子头饰" },
    { sku: "复活节卡片套装", skuEn: "Easter Card Set", category: "gift", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "节日贺卡；轻小件", keywords: ["easter card","greeting card","easter wishes"], sourcing: "1688: 复活节贺卡" },
    { sku: "彩蛋篮/礼品篮", skuEn: "Easter Basket", category: "gift", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "复活节找彩蛋活动必备", keywords: ["easter basket","gift basket","egg hunt"], sourcing: "1688: 复活节篮子" },
    { sku: "春季花卉种子(复活节)", skuEn: "Spring Flower Seeds Easter", category: "home", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "春季园艺；种子需进口许可", keywords: ["flower seeds","spring planting","easter garden"], sourcing: "1688: 花卉种子" },
    { sku: "复活节桌布(兔子图案)", skuEn: "Easter Tablecloth Bunny Pattern", category: "home", costRange: "¥10-18", priceRange: "£7.99-9.99", margin: "约40-50%", matchScore: 3, riskLevel: "低", riskNote: "复活节聚餐装饰", keywords: ["easter tablecloth","bunny tablecloth","spring tablecloth"], sourcing: "1688: 复活节桌布" },
    { sku: "小鸡/小鸭毛绒挂件", skuEn: "Chick Duckling Plush Keyring", category: "gift", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "复活节小礼品；轻小件", keywords: ["chick plush","duckling keyring","easter keyring"], sourcing: "1688: 毛绒挂件" },
    { sku: "复活节饼干模具套装", skuEn: "Easter Cookie Cutter Set", category: "home", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "烘焙工具；兔子/彩蛋造型", keywords: ["cookie cutter","easter baking","bunny cutter"], sourcing: "1688: 饼干模具" },
    { sku: "彩蛋LED灯串", skuEn: "Easter Egg LED String Lights", category: "decor", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "UKCA认证；复活节装饰", keywords: ["easter lights","egg lights","led string"], sourcing: "1688: LED灯串" },
    { sku: "复活节主题围裙", skuEn: "Easter Theme Apron", category: "home", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 3, riskLevel: "低", riskNote: "烘焙主题；复活节厨房", keywords: ["easter apron","baking apron","kitchen apron"], sourcing: "1688: 主题围裙" },
    { sku: "兔子形状抱枕", skuEn: "Bunny Shaped Cushion", category: "home", costRange: "¥10-20", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "低", riskNote: "春季家居；兔子造型", keywords: ["bunny cushion","rabbit pillow","easter decor"], sourcing: "1688: 造型抱枕" }
  ],
  validation: {
    googleTrends: ["easter 2027","easter gifts","easter egg hunt"],
    amazonCheck: "BSR < 2000；3月底-4月初爆发期；TOP品类",
    sourcing: "1688搜索：复活节/彩蛋/兔子/春季",
    riskFlags: ["食品需UK认证","时效性极强4月5日前到仓","玩具需CE/UKCA"]
  }
},
{
  id: "earth-day-2027",
  name: "世界地球日", nameEn: "Earth Day", icon: "🌍",
  date: "2027-04-22", month: 4, importance: "B", category: "festival",
  themeColor: "#16a34a",
  products: [
    { sku: "可重复使用购物袋套装", skuEn: "Reusable Shopping Bag Set", category: "home", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 5, riskLevel: "低", riskNote: "环保主题刚需", keywords: ["reusable bag","eco bag","shopping bag"], sourcing: "1688: 环保购物袋" },
    { sku: "不锈钢吸管套装", skuEn: "Stainless Steel Straw Set", category: "home", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 5, riskLevel: "低", riskNote: "环保替代品；轻小件", keywords: ["steel straw","reusable straw","eco straw"], sourcing: "1688: 不锈钢吸管" },
    { sku: "竹制餐具套装", skuEn: "Bamboo Cutlery Set", category: "home", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "环保材质；便携餐具", keywords: ["bamboo cutlery","eco utensils","reusable cutlery"], sourcing: "1688: 竹制餐具" },
    { sku: "有机棉环保袋", skuEn: "Organic Cotton Eco Tote", category: "apparel", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "有机材质溢价", keywords: ["organic cotton","eco tote","sustainable bag"], sourcing: "1688: 有机棉袋" },
    { sku: "种子纸便签本", skuEn: "Seed Paper Notepad", category: "gift", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "可种植创意；环保概念", keywords: ["seed paper","eco notepad","plantable paper"], sourcing: "1688: 种子纸" },
    { sku: "蜂蜡保鲜布", skuEn: "Beeswax Food Wrap", category: "home", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 5, riskLevel: "低", riskNote: "环保替代保鲜膜", keywords: ["beeswax wrap","food wrap","eco wrap"], sourcing: "1688: 蜂蜡保鲜布" }
  ],
  validation: {
    googleTrends: ["earth day","eco products","sustainable living"],
    amazonCheck: "BSR < 15000；环保品类持续增长",
    sourcing: "1688搜索：环保产品/可持续/竹制",
    riskFlags: ["需避免漂绿(greenwashing)宣传"]
  }
},
{
  id: "st-georges-2027",
  name: "圣乔治节", nameEn: "St George's Day", icon: "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
  date: "2027-04-23", month: 4, importance: "B", category: "festival",
  themeColor: "#dc2626",
  products: [
    { sku: "英格兰旗帜/三角旗", skuEn: "England Flag St George Pennant", category: "decor", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 5, riskLevel: "低", riskNote: "圣乔治节必备；红十字旗", keywords: ["england flag","st georges flag","cross of st george"], sourcing: "1688: 英格兰旗帜" },
    { sku: "玫瑰花胸针(红玫瑰)", skuEn: "Red Rose Brooch", category: "apparel", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "英格兰象征；红玫瑰", keywords: ["red rose","england brooch","st georges pin"], sourcing: "1688: 玫瑰胸针" },
    { sku: "圣乔治主题马克杯", skuEn: "St George's Day Mug", category: "gift", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 3, riskLevel: "低", riskNote: "英格兰主题；礼品属性", keywords: ["st georges mug","england mug","english gift"], sourcing: "1688: 主题马克杯" },
    { sku: "骑士/龙小摆件", skuEn: "Knight Dragon Figurine", category: "gift", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "⚠️待复核: 圣乔治屠龙传说；文化创意", keywords: ["dragon figurine","knight figure","st georges dragon"], sourcing: "1688: 骑士龙摆件" },
    { sku: "英格兰主题围裙", skuEn: "England Theme Apron", category: "home", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 3, riskLevel: "低", riskNote: "厨房用品；英格兰风格", keywords: ["england apron","st georges apron","english apron"], sourcing: "1688: 主题围裙" }
  ],
  validation: {
    googleTrends: ["st georges day","england flag","english gifts"],
    amazonCheck: "BSR < 25000；英格兰小众节日",
    sourcing: "1688搜索：英格兰/圣乔治/旗帜",
    riskFlags: ["避免国旗滥用争议","小众备货量控制"]
  }
},
{
  id: "spring-bank-holiday-prep-2027",
  name: "春季银行假期准备", nameEn: "Spring Bank Holiday Prep", icon: "🌿",
  date: "2027-04-28", month: 4, importance: "A", category: "activity",
  themeColor: "#10b981",
  products: [
    { sku: "户外野餐篮(带餐具)", skuEn: "Picnic Basket with Cutlery", category: "home", costRange: "¥20-35", priceRange: "£8.99-9.99", margin: "约30-40%", matchScore: 4, riskLevel: "低", riskNote: "春季户外；注意FBA体积", keywords: ["picnic basket","outdoor dining","spring picnic"], sourcing: "1688: 野餐篮" },
    { sku: "便携折叠椅(户外)", skuEn: "Portable Folding Chair Outdoor", category: "home", costRange: "¥20-35", priceRange: "£8.99-9.99", margin: "约25-35%", matchScore: 3, riskLevel: "低", riskNote: "大件商品；FBA费用高", keywords: ["folding chair","outdoor chair","camping chair"], sourcing: "1688: 折叠椅" },
    { sku: "户外飞盘/抛接球套装", skuEn: "Outdoor Frisbee Catch Ball Set", category: "gift", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "户外运动；亲子互动", keywords: ["frisbee","catch ball","outdoor game"], sourcing: "1688: 户外玩具" },
    { sku: "防水野餐垫(加厚)", skuEn: "Thick Waterproof Picnic Blanket", category: "home", costRange: "¥10-20", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "低", riskNote: "春季户外刚需", keywords: ["picnic blanket","outdoor blanket","waterproof mat"], sourcing: "1688: 野餐垫" },
    { sku: "便携烧烤架(小型)", skuEn: "Portable Mini BBQ Grill", category: "home", costRange: "¥25-40", priceRange: "£8.99-9.99", margin: "约20-30%", matchScore: 3, riskLevel: "中", riskNote: "大件；注意FBA费用和毛利", keywords: ["portable grill","bbq grill","outdoor cooking"], sourcing: "1688: 便携烧烤架" },
    { sku: "户外游戏套装(家庭)", skuEn: "Family Outdoor Game Set", category: "gift", costRange: "¥10-20", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "低", riskNote: "家庭户外活动；多游戏组合", keywords: ["outdoor games","family games","garden games"], sourcing: "1688: 户外游戏" }
  ],
  validation: {
    googleTrends: ["spring bank holiday","outdoor picnic","garden party"],
    amazonCheck: "BSR < 10000；4-5月户外品类上升",
    sourcing: "1688搜索：户外用品/野餐/花园",
    riskFlags: ["大件商品FBA费用高","需提前4月备货"]
  }
},

// ===== 2027年5月（4个）=====
{
  id: "may-bank-holiday-2027",
  name: "五月初银行假期", nameEn: "Early May Bank Holiday", icon: "🌻",
  date: "2027-05-03", month: 5, importance: "A", category: "activity",
  themeColor: "#f59e0b",
  products: [
    { sku: "园艺围裙(多口袋)", skuEn: "Garden Apron Multi-Pocket", category: "home", costRange: "¥10-18", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "园艺季实用品", keywords: ["garden apron","gardening tool","apron pockets"], sourcing: "1688: 园艺围裙" },
    { sku: "鸟屋/鸟喂食器", skuEn: "Bird House Feeder", category: "home", costRange: "¥10-20", priceRange: "£7.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "低", riskNote: "春季观鸟；花园装饰", keywords: ["bird feeder","bird house","garden wildlife"], sourcing: "1688: 鸟屋喂食器" },
    { sku: "户外桌游套装", skuEn: "Outdoor Board Game Set", category: "gift", costRange: "¥15-25", priceRange: "£8.99-9.99", margin: "约35-45%", matchScore: 3, riskLevel: "低", riskNote: "假期家庭活动", keywords: ["outdoor game","family game","garden game"], sourcing: "1688: 户外桌游" },
    { sku: "花盆装饰贴纸", skuEn: "Flower Pot Decoration Stickers", category: "decor", costRange: "¥2-5", priceRange: "£5.99-6.99", margin: "约60-70%", matchScore: 4, riskLevel: "低", riskNote: "超轻小件高毛利；园艺装饰", keywords: ["pot sticker","garden decor","plant decoration"], sourcing: "1688: 花盆贴纸" }
  ],
  validation: {
    googleTrends: ["may bank holiday","garden accessories","outdoor living"],
    amazonCheck: "BSR < 8000；5月户外品类高峰",
    sourcing: "1688搜索：花园用品/户外装饰/太阳能",
    riskFlags: ["太阳能产品注意UKCA","大件注意FBA"]
  }
},
{
  id: "world-bee-day-2027",
  name: "世界蜜蜂日", nameEn: "World Bee Day", icon: "🐝",
  date: "2027-05-20", month: 5, importance: "B", category: "festival",
  themeColor: "#f59e0b",
  products: [
    { sku: "蜜蜂主题茶巾", skuEn: "Bee Theme Tea Towel", category: "home", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "蜜蜂主题；厨房用品", keywords: ["bee tea towel","kitchen towel","bee design"], sourcing: "1688: 主题茶巾" },
    { sku: "野花种子套装(蜜蜂友好)", skuEn: "Bee Friendly Wildflower Seeds", category: "home", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 5, riskLevel: "低", riskNote: "环保概念；蜜蜂保护", keywords: ["wildflower seeds","bee friendly","pollinator seeds"], sourcing: "1688: 野花种子" },
    { sku: "蜜蜂形状蜂蜜搅拌棒", skuEn: "Bee Shaped Honey Dipper", category: "home", costRange: "¥3-6", priceRange: "£5.99-6.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "创意厨房小工具", keywords: ["honey dipper","bee tool","kitchen gadget"], sourcing: "1688: 蜂蜜搅拌棒" },
    { sku: "蜜蜂主题马克杯", skuEn: "Bee Theme Mug", category: "gift", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 3, riskLevel: "低", riskNote: "蜜蜂主题礼品", keywords: ["bee mug","honey mug","cute mug"], sourcing: "1688: 主题马克杯" },
    { sku: "蜜蜂花园装饰标牌", skuEn: "Bee Garden Sign Decoration", category: "decor", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 3, riskLevel: "低", riskNote: "花园装饰；蜜蜂主题", keywords: ["garden sign","bee decoration","outdoor decor"], sourcing: "1688: 花园标牌" }
  ],
  validation: {
    googleTrends: ["world bee day","bee friendly","pollinator garden"],
    amazonCheck: "BSR < 30000；环保/园艺小众",
    sourcing: "1688搜索：蜜蜂主题/野花种子/环保",
    riskFlags: ["种子需UK进口许可","小众节日备货控制"]
  }
},
{
  id: "chelsea-flower-show-2027",
  name: "切尔西花展", nameEn: "Chelsea Flower Show", icon: "🌷",
  date: "2027-05-22", month: 5, importance: "B", category: "activity",
  themeColor: "#ec4899",
  products: [
    { sku: "园艺手套(高级款)", skuEn: "Premium Gardening Gloves", category: "home", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 5, riskLevel: "低", riskNote: "花展季园艺高峰", keywords: ["gardening gloves","premium gloves","garden tools"], sourcing: "1688: 园艺手套" },
    { sku: "园艺剪刀(修枝剪)", skuEn: "Pruning Shears Garden Scissors", category: "home", costRange: "¥10-20", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "中", riskNote: "锐器注意安全标识", keywords: ["pruning shears","garden scissors","plant cutting"], sourcing: "1688: 园艺剪刀" },
    { sku: "花盆标签/植物标识牌", skuEn: "Plant Label Garden Markers", category: "home", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "园艺实用品；轻小件", keywords: ["plant labels","garden markers","plant tags"], sourcing: "1688: 植物标签" },
    { sku: "园艺浇水壶(复古)", skuEn: "Vintage Style Watering Can", category: "home", costRange: "¥15-25", priceRange: "£8.99-9.99", margin: "约35-45%", matchScore: 3, riskLevel: "低", riskNote: "复古风格；花园装饰+实用", keywords: ["watering can","vintage garden","plant watering"], sourcing: "1688: 浇水壶" },
    { sku: "花展主题帆布袋", skuEn: "Flower Show Tote Bag", category: "apparel", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 3, riskLevel: "低", riskNote: "花展周边；花卉图案", keywords: ["tote bag","flower bag","garden bag"], sourcing: "1688: 帆布袋" },
    { sku: "种子发芽培育盒", skuEn: "Seed Germination Growing Kit", category: "home", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "园艺入门；教育属性", keywords: ["growing kit","seed starter","plant kit"], sourcing: "1688: 种植套装" }
  ],
  validation: {
    googleTrends: ["chelsea flower show","gardening uk","garden tools"],
    amazonCheck: "BSR < 12000；5月园艺品类高峰",
    sourcing: "1688搜索：园艺工具/花盆/种植",
    riskFlags: ["锐器需安全标识","大件注意FBA"]
  }
},
{
  id: "spring-bank-holiday-2027",
  name: "春季银行假期", nameEn: "Spring Bank Holiday", icon: "☀️",
  date: "2027-05-31", month: 5, importance: "A", category: "activity",
  themeColor: "#14b8a6",
  products: [
    { sku: "户外吊床", skuEn: "Outdoor Hammock", category: "home", costRange: "¥25-40", priceRange: "£8.99-9.99", margin: "约25-35%", matchScore: 4, riskLevel: "低", riskNote: "大件；注意FBA体积费", keywords: ["hammock","outdoor hammock","garden hammock"], sourcing: "1688: 户外吊床" },
    { sku: "便携冰袋/保冷袋", skuEn: "Portable Cooler Bag", category: "home", costRange: "¥10-20", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "低", riskNote: "户外野餐必备", keywords: ["cooler bag","picnic bag","insulated bag"], sourcing: "1688: 保冷袋" },
    { sku: "户外游戏套装(草地)", skuEn: "Lawn Game Set", category: "gift", costRange: "¥15-25", priceRange: "£8.99-9.99", margin: "约35-45%", matchScore: 4, riskLevel: "低", riskNote: "假期家庭活动", keywords: ["lawn games","garden games","outdoor fun"], sourcing: "1688: 草地游戏" },
    { sku: "遮阳伞/沙滩伞", skuEn: "Beach Parasol Sun Umbrella", category: "home", costRange: "¥15-25", priceRange: "£8.99-9.99", margin: "约35-45%", matchScore: 3, riskLevel: "低", riskNote: "户外防晒；大件注意物流", keywords: ["beach umbrella","sun shade","parasol"], sourcing: "1688: 沙滩伞" },
    { sku: "烧烤围裙(带工具口袋)", skuEn: "BBQ Apron with Tool Pockets", category: "home", costRange: "¥10-18", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "BBQ季实用品", keywords: ["bbq apron","grill apron","outdoor cooking"], sourcing: "1688: 烧烤围裙" }
  ],
  validation: {
    googleTrends: ["spring bank holiday","outdoor bbq","garden party"],
    amazonCheck: "BSR < 8000；5月底户外品类高峰",
    sourcing: "1688搜索：户外用品/BBQ/野餐",
    riskFlags: ["大件商品FBA费用高","需提前5月备货"]
  }
},

// ===== 2027年6月（6个）=====
{
  id: "childrens-day-2027",
  name: "国际儿童节", nameEn: "International Children's Day", icon: "👶",
  date: "2027-06-01", month: 6, importance: "A", category: "festival",
  themeColor: "#f472b6",
  products: [
    { sku: "家庭合影相框套装", skuEn: "Family Photo Frame Set", category: "gift", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "父母买给自己布置的纪念品；常规品类", keywords: ["family photo frame","picture frame set","gift frame"], sourcing: "1688: 家庭相框套装" },
    { sku: "儿童节主题气球横幅装饰", skuEn: "Celebration Balloon Banner Decoration Set", category: "decor", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约50-55%", matchScore: 4, riskLevel: "低", riskNote: "成人布置用装饰品，非玩具", keywords: ["party banner","balloon decoration","celebration decor"], sourcing: "1688: 气球横幅装饰套装" },
    { sku: "家庭烘焙硅胶模具套装", skuEn: "Silicone Baking Mould Set Family", category: "home", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "厨房用品；家庭共同烘焙场景", keywords: ["baking mould","silicone mould set","family baking"], sourcing: "1688: 硅胶烘焙模具" },
    { sku: "家庭成长纪念相册", skuEn: "Family Memory Photo Album", category: "gift", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "纪念相册；礼品属性强", keywords: ["photo album","memory book","family album"], sourcing: "1688: 纪念相册" },
    { sku: "礼品包装丝带贴纸套装", skuEn: "Gift Wrap Ribbon Sticker Set", category: "gift", costRange: "¥3-6", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 3, riskLevel: "低", riskNote: "轻小件高毛利；节日通用", keywords: ["gift wrap ribbon","gift sticker set","wrapping supplies"], sourcing: "1688: 礼品包装套装" }
  ],
  validation: {
    googleTrends: ["children's day family gifts","family celebration decor","photo frame gifts"],
    amazonCheck: "BSR < 10000；6月初峰值",
    sourcing: "1688搜索：家庭相框/烘焙模具/派对装饰",
    riskFlags: ["聚焦成人可用家庭用品，避免玩具/儿童专属品类（本店forbidden_keywords限制：toy/kids/children/baby）"]
  }
},
{
  id: "world-environment-2027",
  name: "世界环境日", nameEn: "World Environment Day", icon: "🌱",
  date: "2027-06-05", month: 6, importance: "B", category: "festival",
  themeColor: "#16a34a",
  products: [
    { sku: "可降解垃圾袋", skuEn: "Biodegradable Waste Bags", category: "home", costRange: "¥5-10", priceRange: "£6.49-8.49", margin: "约50-60%", matchScore: 5, riskLevel: "低", riskNote: "环保刚需；持续消耗品", keywords: ["biodegradable bags","eco bags","compost bags"], sourcing: "1688: 可降解垃圾袋" },
    { sku: "竹牙刷套装(家庭装)", skuEn: "Bamboo Toothbrush Family Pack", category: "home", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 5, riskLevel: "低", riskNote: "环保替代品；家庭装", keywords: ["bamboo toothbrush","eco toothbrush","family pack"], sourcing: "1688: 竹牙刷" },
    { sku: "可重复使用食品袋", skuEn: "Reusable Food Storage Bags", category: "home", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "食品级硅胶；环保替代", keywords: ["reusable bags","food storage","eco bags"], sourcing: "1688: 可重复使用食品袋" },
    { sku: "环保清洁布(超细纤维)", skuEn: "Microfibre Cleaning Cloth Eco", category: "home", costRange: "¥3-6", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "替代纸巾；可重复使用", keywords: ["cleaning cloth","microfibre","eco cloth"], sourcing: "1688: 超细纤维布" }
  ],
  validation: {
    googleTrends: ["world environment day","eco products","sustainable"],
    amazonCheck: "BSR < 15000；环保品类持续增长",
    sourcing: "1688搜索：环保产品/可降解/竹制",
    riskFlags: ["需避免漂绿宣传","化学品需MSDS"]
  }
},
{
  id: "queens-birthday-2027",
  name: "国王生日/皇家主题", nameEn: "King's Official Birthday", icon: "👑",
  date: "2027-06-12", month: 6, importance: "B", category: "festival",
  themeColor: "#7c3aed",
  products: [
    { sku: "英国国旗装饰品套装", skuEn: "Union Jack Decoration Set", category: "decor", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "皇家主题；英国国旗", keywords: ["union jack","british flag","royal decor"], sourcing: "1688: 英国国旗装饰" },
    { sku: "皇冠造型开瓶器", skuEn: "Crown Bottle Opener", category: "home", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "创意厨房工具；皇家元素", keywords: ["crown opener","bottle opener","royal gift"], sourcing: "1688: 创意开瓶器" },
    { sku: "皇家主题茶杯套装", skuEn: "Royal Theme Tea Cup Set", category: "home", costRange: "¥15-25", priceRange: "£8.99-9.99", margin: "约35-45%", matchScore: 3, riskLevel: "中", riskNote: "陶瓷易碎；英式下午茶", keywords: ["tea cup","royal tea","british tea set"], sourcing: "1688: 英式茶杯" },
    { sku: "皇家卫兵钥匙扣", skuEn: "Royal Guard Keyring", category: "gift", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "英国旅游纪念品", keywords: ["royal guard","keyring","british souvenir"], sourcing: "1688: 皇家卫兵钥匙扣" },
    { sku: "英国主题明信片套装", skuEn: "British Theme Postcard Set", category: "gift", costRange: "¥2-5", priceRange: "£5.99-6.99", margin: "约60-70%", matchScore: 3, riskLevel: "低", riskNote: "文创小件；英国风景", keywords: ["postcard","british cards","london postcards"], sourcing: "1688: 明信片" }
  ],
  validation: {
    googleTrends: ["kings birthday","royal gifts","british souvenirs"],
    amazonCheck: "BSR < 25000；皇家/旅游小众",
    sourcing: "1688搜索：皇家/英国/纪念品",
    riskFlags: ["避免皇家肖像版权问题"]
  }
},
{
  id: "fathers-day-uk-2027",
  name: "英国父亲节", nameEn: "Father's Day (UK)", icon: "👔",
  date: "2027-06-21", month: 6, importance: "S", category: "festival",
  themeColor: "#3b82f6",
  products: [
    { sku: "父亲节定制钥匙扣", skuEn: "Personalized Dad Keyring", category: "gift", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 5, riskLevel: "低", riskNote: "可刻字定制；情感价值", keywords: ["dad keyring","personalized keyring","fathers day"], sourcing: "1688: 定制钥匙扣" },
    { sku: "父亲节贺卡(手工)", skuEn: "Handmade Father's Day Card", category: "gift", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 5, riskLevel: "低", riskNote: "手工溢价高；必备小礼品", keywords: ["fathers day card","handmade card","dad card"], sourcing: "1688: 父亲节贺卡" },
    { sku: "皮质钱包(可刻字)", skuEn: "Leather Wallet Engraved", category: "gift", costRange: "¥15-30", priceRange: "£8.99-9.99", margin: "约30-40%", matchScore: 5, riskLevel: "低", riskNote: "经典父亲节礼品；可定制", keywords: ["leather wallet","engraved wallet","dad gift"], sourcing: "1688: 皮质钱包" },
    { sku: "BBQ工具套装(父亲节款)", skuEn: "BBQ Tool Set Father's Day", category: "home", costRange: "¥15-25", priceRange: "£8.99-9.99", margin: "约35-45%", matchScore: 5, riskLevel: "中", riskNote: "BBQ季+父亲节双重需求", keywords: ["bbq tools","grill set","fathers day bbq"], sourcing: "1688: BBQ工具套装" },
    { sku: "创意袜子礼盒(爸爸款)", skuEn: "Fun Socks Gift Box Dad", category: "apparel", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 5, riskLevel: "低", riskNote: "趣味图案；实用礼品", keywords: ["fun socks","sock gift box","dad socks"], sourcing: "1688: 创意袜子" },
    { sku: "父亲节马克杯(世界最佳爸爸)", skuEn: "World's Best Dad Mug", category: "gift", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 5, riskLevel: "低", riskNote: "经典父亲节礼品；标语款", keywords: ["best dad mug","fathers day mug","dad coffee mug"], sourcing: "1688: 父亲节马克杯" },
    { sku: "多功能工具笔", skuEn: "Multi-Function Tool Pen", category: "gift", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "创意工具；男性礼品", keywords: ["tool pen","multi pen","gadget gift"], sourcing: "1688: 多功能工具笔" },
    { sku: "高尔夫球套装(练习用)", skuEn: "Golf Ball Practice Set", category: "gift", costRange: "¥10-20", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "低", riskNote: "运动爱好者；父亲节主题", keywords: ["golf balls","practice golf","sports gift"], sourcing: "1688: 高尔夫球" },
    { sku: "定制照片钥匙扣", skuEn: "Custom Photo Keyring", category: "gift", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "可放照片；情感价值高", keywords: ["photo keyring","custom keyring","personalized gift"], sourcing: "1688: 照片钥匙扣" },
    { sku: "父亲节领带礼盒", skuEn: "Father's Day Tie Gift Set", category: "apparel", costRange: "¥10-20", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "低", riskNote: "正式礼品；含领带夹", keywords: ["tie set","fathers day tie","necktie gift"], sourcing: "1688: 领带礼盒" },
    { sku: "父亲节酒壶(不锈钢)", skuEn: "Stainless Steel Hip Flask", category: "gift", costRange: "¥10-20", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "低", riskNote: "经典男性礼品；可刻字", keywords: ["hip flask","flask","engraved flask"], sourcing: "1688: 随身酒壶" },
    { sku: "园艺工具套装(爸爸款)", skuEn: "Dad Gardening Tool Set", category: "home", costRange: "¥15-25", priceRange: "£8.99-9.99", margin: "约35-45%", matchScore: 4, riskLevel: "低", riskNote: "园艺季+父亲节", keywords: ["gardening tools","dad garden","garden set"], sourcing: "1688: 园艺工具套装" },
    { sku: "父亲节早餐托盘套装", skuEn: "Father's Day Breakfast Tray Set", category: "home", costRange: "¥15-25", priceRange: "£8.99-9.99", margin: "约35-45%", matchScore: 3, riskLevel: "低", riskNote: "父亲节早餐概念；含托盘+餐具", keywords: ["breakfast tray","fathers day tray","bed tray"], sourcing: "1688: 早餐托盘" }
  ],
  validation: {
    googleTrends: ["fathers day uk 2027","fathers day gifts","dad gifts"],
    amazonCheck: "BSR < 2000；6月中旬爆发期；TOP品类",
    sourcing: "1688搜索：父亲节礼品/男士用品/BBQ",
    riskFlags: ["电子类需UKCA","时效性极强6月21日前到仓","定制品需提前生产"]
  }
},
{
  id: "armed-forces-2027",
  name: "军人节/武装部队日", nameEn: "Armed Forces Day", icon: "🎖️",
  date: "2027-06-27", month: 6, importance: "B", category: "festival",
  themeColor: "#475569",
  products: [
    { sku: "军旅主题徽章套装", skuEn: "Military Badge Pin Set", category: "apparel", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "军人节纪念；收藏属性", keywords: ["military badge","armed forces pin","medal badge"], sourcing: "1688: 徽章套装" },
    { sku: "军绿主题腕带", skuEn: "Military Green Wristband", category: "apparel", costRange: "¥2-5", priceRange: "£5.99-6.99", margin: "约60-70%", matchScore: 4, riskLevel: "低", riskNote: "支持军人主题；轻小件", keywords: ["wristband","military bracelet","support bracelet"], sourcing: "1688: 硅胶腕带" },
    { sku: "迷彩帽子", skuEn: "Camouflage Cap", category: "apparel", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 3, riskLevel: "低", riskNote: "军旅风格；户外运动", keywords: ["camo cap","military hat","army cap"], sourcing: "1688: 迷彩帽" },
    { sku: "军人主题马克杯", skuEn: "Armed Forces Mug", category: "gift", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 3, riskLevel: "低", riskNote: "致敬军人主题", keywords: ["military mug","armed forces mug","army gift"], sourcing: "1688: 主题马克杯" },
    { sku: "军旅风贴纸套装", skuEn: "Military Sticker Set", category: "gift", costRange: "¥2-5", priceRange: "£5.99-6.99", margin: "约60-70%", matchScore: 3, riskLevel: "低", riskNote: "超轻小件；收藏/装饰", keywords: ["military stickers","army stickers","decal set"], sourcing: "1688: 贴纸" }
  ],
  validation: {
    googleTrends: ["armed forces day","military gifts","army merchandise"],
    amazonCheck: "BSR < 30000；小众军事迷市场",
    sourcing: "1688搜索：军事/军人/迷彩",
    riskFlags: ["避免官方军徽/国徽版权","小众备货控制"]
  }
},
{
  id: "pride-month-2027",
  name: "骄傲月/LGBTQ+", nameEn: "Pride Month", icon: "🏳️‍🌈",
  date: "2027-06-28", month: 6, importance: "A", category: "festival",
  themeColor: "#e11d48",
  products: [
    { sku: "彩虹旗帜/横幅", skuEn: "Rainbow Pride Flag Banner", category: "decor", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 5, riskLevel: "低", riskNote: "骄傲月标志性装饰", keywords: ["pride flag","rainbow flag","lgbtq flag"], sourcing: "1688: 彩虹旗帜" },
    { sku: "彩虹手环套装", skuEn: "Rainbow Bracelet Set", category: "apparel", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 5, riskLevel: "低", riskNote: "骄傲月配饰；轻小件", keywords: ["rainbow bracelet","pride wristband","lgbtq accessories"], sourcing: "1688: 彩虹手环" },
    { sku: "彩虹徽章/胸针", skuEn: "Rainbow Pride Brooch Pin", category: "apparel", costRange: "¥2-5", priceRange: "£5.99-6.99", margin: "约60-70%", matchScore: 5, riskLevel: "低", riskNote: "超轻小件；骄傲月标志", keywords: ["pride pin","rainbow brooch","lgbtq pin"], sourcing: "1688: 彩虹胸针" },
    { sku: "彩虹主题帆布袋", skuEn: "Pride Rainbow Tote Bag", category: "apparel", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "实用+骄傲月主题", keywords: ["pride tote","rainbow bag","lgbtq bag"], sourcing: "1688: 彩虹帆布袋" },
    { sku: "彩虹旗LED灯串", skuEn: "Rainbow LED String Lights", category: "decor", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "UKCA认证；派对装饰", keywords: ["rainbow lights","pride lights","led string"], sourcing: "1688: 彩虹灯串" },
    { sku: "彩虹主题马克杯", skuEn: "Pride Rainbow Mug", category: "gift", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "骄傲月礼品", keywords: ["pride mug","rainbow mug","lgbtq mug"], sourcing: "1688: 彩虹马克杯" },
    { sku: "彩虹贴纸套装", skuEn: "Pride Sticker Pack", category: "gift", costRange: "¥2-5", priceRange: "£5.99-6.99", margin: "约60-70%", matchScore: 4, riskLevel: "低", riskNote: "超轻小件；装饰/收藏", keywords: ["pride stickers","rainbow stickers","lgbtq stickers"], sourcing: "1688: 彩虹贴纸" },
  ],
  validation: {
    googleTrends: ["pride month","pride accessories","rainbow gifts","lgbtq"],
    amazonCheck: "BSR < 8000；6月整月峰值",
    sourcing: "1688搜索：彩虹/骄傲/LGBTQ",
    riskFlags: ["注意文化敏感性","避免刻板印象设计"]
  }
},

// ===== 7月（5个）=====
{
  id: "amazon-prime-day-2026",
  name: "Amazon Prime Day", nameEn: "Amazon Prime Day", icon: "📦",
  date: "2026-07-12", month: 7, importance: "A", category: "activity",
  themeColor: "#f59e0b",
  products: [
    { sku: "手机壳(多型号)", skuEn: "Phone Case Multi-Model", category: "gift", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 5, riskLevel: "低", riskNote: "Prime Day TOP品类；多型号SKU", keywords: ["phone case","iphone case","samsung case"], sourcing: "1688: 手机壳" },
    { sku: "厨房电子秤", skuEn: "Digital Kitchen Scale", category: "home", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "烘焙刚需；Prime Day热卖", keywords: ["kitchen scale","digital scale","baking scale"], sourcing: "1688: 电子秤" },
    { sku: "智能插座(WiFi)", skuEn: "WiFi Smart Plug", category: "home", costRange: "¥10-20", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "中", riskNote: "UKCA认证；智能家居入门", keywords: ["smart plug","wifi plug","smart home"], sourcing: "1688: 智能插座" }
  ],
  validation: {
    googleTrends: ["amazon prime day","prime day deals","best prime day"],
    amazonCheck: "BSR < 5000；7月最大流量峰值；电子/家居品类",
    sourcing: "1688搜索：电子配件/家居/智能家居",
    riskFlags: ["电子产品UKCA认证","Prime Day价格战需核算利润","需提前6月备货入仓"]
  }
},
{
  id: "wimbledon-2026",
  name: "温布尔登网球赛", nameEn: "Wimbledon", icon: "🎾",
  date: "2026-06-29", month: 7, importance: "A", category: "activity",
  themeColor: "#16a34a",
  products: [
    { sku: "网球主题马克杯", skuEn: "Tennis Theme Mug", category: "gift", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "温网主题；网球元素", keywords: ["tennis mug","wimbledon mug","sport mug"], sourcing: "1688: 主题马克杯" },
    { sku: "网球拍钥匙扣", skuEn: "Tennis Racket Keyring", category: "gift", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "温网纪念品；轻小件", keywords: ["tennis keyring","wimbledon keyring","sport keyring"], sourcing: "1688: 运动钥匙扣" },
    { sku: "草地球场图案杯垫", skuEn: "Grass Court Coaster Set", category: "home", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 3, riskLevel: "低", riskNote: "温网草场主题", keywords: ["tennis coaster","wimbledon coaster","grass coaster"], sourcing: "1688: 主题杯垫" },
    { sku: "网球运动毛巾", skuEn: "Tennis Sports Towel", category: "home", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "温网+运动双重需求", keywords: ["tennis towel","sports towel","wimbledon towel"], sourcing: "1688: 运动毛巾" },
    { sku: "网球训练器(回弹)", skuEn: "Tennis Trainer Rebound Ball", category: "gift", costRange: "¥10-20", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "低", riskNote: "温网季网球热；练习工具", keywords: ["tennis trainer","rebound ball","tennis practice"], sourcing: "1688: 网球训练器" },
    { sku: "温网主题围巾/丝巾", skuEn: "Wimbledon Theme Scarf", category: "apparel", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 3, riskLevel: "低", riskNote: "绿紫配色；温网传统", keywords: ["wimbledon scarf","tennis scarf","green purple"], sourcing: "1688: 主题围巾" }
  ],
  validation: {
    googleTrends: ["wimbledon","tennis uk","wimbledon gifts"],
    amazonCheck: "BSR < 12000；6月底-7月中网球品类",
    sourcing: "1688搜索：网球/温布尔登/运动",
    riskFlags: ["避免Wimbledon官方商标","时效性6月底-7月中"]
  }
},
{
  id: "summer-holidays-2026",
  name: "学校暑假开始", nameEn: "School Summer Holidays", icon: "🏖️",
  date: "2026-07-20", month: 7, importance: "A", category: "activity",
  themeColor: "#0ea5e9",
  products: [
    { sku: "旅行收纳袋套装", skuEn: "Travel Packing Cube Set", category: "home", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "暑假旅行刚需", keywords: ["packing cubes","travel organizer","luggage set"], sourcing: "1688: 旅行收纳" },
    { sku: "便携急救包(旅行)", skuEn: "Portable First Aid Kit Travel", category: "home", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "旅行安全必备", keywords: ["first aid kit","travel kit","safety kit"], sourcing: "1688: 急救包" },
  ],
  validation: {
    googleTrends: ["summer holidays","kids summer activities","beach toys uk"],
    amazonCheck: "BSR < 8000；7-8月儿童/户外品类爆发",
    sourcing: "1688搜索：儿童户外/沙滩/旅行",
    riskFlags: ["儿童产品CE/UKCA","防晒霜CPNP","充气玩具安全标准"]
  }
},
{
  id: "summer-bbq-2026",
  name: "夏季户外/BBQ季", nameEn: "Summer Outdoor & BBQ Season", icon: "🍖",
  date: "2026-07-01", month: 7, importance: "B", category: "trend",
  themeColor: "#f97316",
  products: [
    { sku: "户外野餐垫(防水)", skuEn: "Waterproof Picnic Blanket", category: "decor", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-50%", matchScore: 4, riskLevel: "低", riskNote: "常规品类", keywords: ["picnic blanket","outdoor mat"], sourcing: "1688: 户外野餐垫" },
    { sku: "烧烤工具套装(便携)", skuEn: "Portable BBQ Tool Set", category: "home", costRange: "¥10-18", priceRange: "£8.99-9.99", margin: "约40-45%", matchScore: 3, riskLevel: "中", riskNote: "食品级不锈钢认证；体积偏大注意FBA费用", keywords: ["bbq tools","grill set"], sourcing: "1688: 烧烤工具套装" },
    { sku: "户外防潮坐垫(折叠便携)", skuEn: "Portable Waterproof Seat Pad Foldable", category: "home", costRange: "¥5-10", priceRange: "£6.49-8.49", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "⚠️待复核: 常规品类", keywords: ["seat pad","waterproof cushion","outdoor mat","portable pad"], sourcing: "1688: 防潮坐垫" }
  ],
  validation: {
    googleTrends: ["bbq accessories uk","picnic blanket"],
    amazonCheck: "BSR < 10000；季节性强，7月峰值",
    sourcing: "1688搜索：BBQ/野餐/户外",
    riskFlags: ["体积大者FBA费用高，需核算毛利"]
  }
},
{
  id: "summer-sale-2026",
  name: "夏季促销", nameEn: "Summer Sale", icon: "☀️",
  date: "2026-07-15", month: 7, importance: "A", category: "activity",
  themeColor: "#14b8a6",
  products: [
    { sku: "冰丝凉爽坐垫", skuEn: "Cooling Gel Seat Cushion", category: "home", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-50%", matchScore: 4, riskLevel: "低", riskNote: "⚠️待复核: 常规品类无特殊风险", keywords: ["cooling cushion","gel seat pad"], sourcing: "1688: 冰丝凉垫" },
    { sku: "防晒冰袖套", skuEn: "UV Protection Cooling Arm Sleeves", category: "apparel", costRange: "¥3-6", priceRange: "£5.99-7.99", margin: "约50-60%", matchScore: 5, riskLevel: "低", riskNote: "注意UK成人尺码", keywords: ["arm sleeves","uv protection","cooling sleeves"], sourcing: "1688: 防晒冰袖" },
    { sku: "便携BBQ烧烤垫", skuEn: "Portable BBQ Grill Mat", category: "decor", costRange: "¥5-10", priceRange: "£6.49-8.49", margin: "约45-55%", matchScore: 4, riskLevel: "中", riskNote: "需食品级材质认证", keywords: ["bbq mat","grill mat","barbecue accessories"], sourcing: "1688: 烧烤垫" },
    { sku: "遮阳帽(可折叠大檐)", skuEn: "Foldable Sun Hat Wide Brim", category: "apparel", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "低", riskNote: "常规品类；注意UK尺码", keywords: ["sun hat","summer hat","foldable hat","wide brim hat"], sourcing: "1688: 遮阳帽折叠" },
    { sku: "硅胶冰格模具(创意造型)", skuEn: "Silicone Ice Cube Tray Creative", category: "home", costRange: "¥3-6", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 5, riskLevel: "低", riskNote: "食品级硅胶认证；轻小件高毛利", keywords: ["ice cube tray","silicone mould","summer drinks"], sourcing: "1688: 硅胶冰格" },
    { sku: "户外驱蚊手环(4只装)", skuEn: "Mosquito Repellent Bracelet 4 Pack", category: "apparel", costRange: "¥3-6", priceRange: "£5.99-7.99", margin: "约55-60%", matchScore: 4, riskLevel: "中", riskNote: "驱蚊产品需有安全认证；避免药物功效宣传", keywords: ["mosquito bracelet","bug repellent","insect repellent"], sourcing: "1688: 驱蚊手环" },
    { sku: "户外防水手机袋", skuEn: "Waterproof Phone Pouch Outdoor", category: "gift", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 5, riskLevel: "低", riskNote: "夏季水上活动刚需", keywords: ["waterproof pouch","phone case","beach accessory"], sourcing: "1688: 防水手机袋" },
    { sku: "便携充气沙发(户外)", skuEn: "Inflatable Air Lounger Sofa", category: "home", costRange: "¥15-25", priceRange: "£8.99-9.99", margin: "约35-45%", matchScore: 4, riskLevel: "低", riskNote: "户外休闲；注意FBA体积", keywords: ["air lounger","inflatable sofa","outdoor chair"], sourcing: "1688: 充气沙发" },
    { sku: "夏季主题太阳镜(偏光)", skuEn: "Polarized Summer Sunglasses", category: "apparel", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "夏季防晒；偏光镜片", keywords: ["sunglasses","polarized","summer eyewear"], sourcing: "1688: 偏光太阳镜" },
    { sku: "便携冷藏保鲜盒(午餐)", skuEn: "Portable Insulated Lunch Container", category: "home", costRange: "¥10-18", priceRange: "£7.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "低", riskNote: "夏季野餐/户外用餐", keywords: ["lunch box","insulated container","food storage"], sourcing: "1688: 保鲜午餐盒" }
  ],
  validation: {
    googleTrends: ["summer sale 2026","cooling products uk"],
    amazonCheck: "BSR < 8000 in Garden & Outdoors；头部评论 < 300",
    sourcing: "1688搜索：夏季用品/防晒/便携风扇",
    riskFlags: ["电子产品注意UKCA认证","食品接触材质需检测报告"]
  }
},

// ===== 8月（5个）=====
{
  id: "youth-day-2026",
  name: "国际青年节/亲子主题", nameEn: "International Youth Day", icon: "👨‍👩‍👧",
  date: "2026-08-12", month: 8, importance: "B", category: "trend",
  themeColor: "#a855f7",
  products: [
    { sku: "家庭出游便携餐具套装", skuEn: "Family Travel Cutlery Set", category: "home", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "全家出游场景；常规品类", keywords: ["travel cutlery set","picnic utensils","family outdoor"], sourcing: "1688: 便携餐具套装" },
    { sku: "亲子撞色帆布托特包", skuEn: "Family Matching Canvas Tote Bag", category: "gift", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 3, riskLevel: "低", riskNote: "成人尺寸帆布包，非服装类", keywords: ["canvas tote bag","family matching bag","travel bag"], sourcing: "1688: 帆布托特包" },
    { sku: "家庭户外野餐收纳篮", skuEn: "Family Picnic Storage Basket", category: "home", costRange: "¥10-18", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "低", riskNote: "户外出游刚需；常规品类", keywords: ["picnic basket","storage basket","family outdoor"], sourcing: "1688: 野餐收纳篮" },
    { sku: "家庭定制冰箱贴", skuEn: "Custom Family Fridge Magnet", category: "gift", costRange: "¥3-6", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 3, riskLevel: "低", riskNote: "轻小件高毛利；需支持定制", keywords: ["fridge magnet","custom magnet","family gift"], sourcing: "1688: 定制冰箱贴" }
  ],
  validation: {
    googleTrends: ["family day out gifts","family travel accessories","outdoor family gear"],
    amazonCheck: "BSR < 15000；小众但有稳定需求",
    sourcing: "1688搜索：家庭出游/野餐/定制礼品",
    riskFlags: ["聚焦成人可用家庭出游用品，避免玩具/儿童专属品类（本店forbidden_keywords限制：toy/kids/children/baby）"]
  }
},
{
  id: "back-to-school-prep-2026",
  name: "返校准备期", nameEn: "Back to School Prep", icon: "🎒",
  date: "2026-08-20", month: 8, importance: "A", category: "activity",
  themeColor: "#3b82f6",
  products: [
    { sku: "学生文具套装", skuEn: "Student Stationery Set", category: "gift", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约45-55%", matchScore: 5, riskLevel: "低", riskNote: "常规品类", keywords: ["stationery set","school supplies"], sourcing: "1688: 学生文具套装" },
    { sku: "书包挂饰/标签", skuEn: "Backpack Bag Tag", category: "gift", costRange: "¥2-5", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 5, riskLevel: "低", riskNote: "轻小件高毛利", keywords: ["bag tag","backpack accessories"], sourcing: "1688: 书包挂件" },
    { sku: "卡通姓名贴纸", skuEn: "Personalized Name Stickers", category: "gift", costRange: "¥3-6", priceRange: "£5.99-7.99", margin: "约60-70%", matchScore: 5, riskLevel: "低", riskNote: "需支持定制印刷", keywords: ["name stickers","school labels"], sourcing: "1688: 姓名贴定制" },
    { sku: "透明文件袋(A4拉链)", skuEn: "A4 Clear Document Pouch Zip", category: "gift", costRange: "¥3-6", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "轻小件实用刚需", keywords: ["document pouch","file bag","a4 folder","school pouch"], sourcing: "1688: A4文件袋" },
    { sku: "橡皮擦+尺子文具小套装", skuEn: "Eraser & Ruler Mini Stationery Set", category: "gift", costRange: "¥2-5", priceRange: "£5.99-6.99", margin: "约60-70%", matchScore: 4, riskLevel: "低", riskNote: "轻小件高毛利", keywords: ["eraser ruler set","stationery mini","school essentials"], sourcing: "1688: 橡皮尺子套装" }
  ],
  validation: {
    googleTrends: ["back to school 2026","school supplies uk"],
    amazonCheck: "BSR < 5000；8-9月强季节性",
    sourcing: "1688搜索：文具/午餐盒/学生用品",
    riskFlags: ["食品接触材质需认证","定制类需确认生产周期"]
  }
},
{
  id: "summer-bank-holiday-2026",
  name: "夏季银行假", nameEn: "Summer Bank Holiday", icon: "🏖️",
  date: "2026-08-31", month: 8, importance: "A", category: "activity",
  themeColor: "#0ea5e9",
  products: [
    { sku: "海滩沙滩垫", skuEn: "Beach Beach Mat", category: "decor", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "常规品类", keywords: ["beach mat","sand free blanket"], sourcing: "1688: 沙滩垫" },
    { sku: "防水手机袋", skuEn: "Waterproof Phone Pouch", category: "home", costRange: "¥3-6", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 5, riskLevel: "低", riskNote: "轻小件高毛利", keywords: ["waterproof phone case","beach pouch"], sourcing: "1688: 防水手机袋" },
    { sku: "夏日主题派对装饰套装", skuEn: "Summer Party Decoration Set", category: "decor", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-50%", matchScore: 4, riskLevel: "低", riskNote: "常规品类", keywords: ["summer party decorations","beach party"], sourcing: "1688: 夏日派对装饰" },
    { sku: "冷感毛巾", skuEn: "Cooling Towel Microfiber", category: "apparel", costRange: "¥4-8", priceRange: "£6.49-8.49", margin: "约50-55%", matchScore: 4, riskLevel: "低", riskNote: "常规品类", keywords: ["cooling towel","microfiber towel"], sourcing: "1688: 冰感毛巾" },
    { sku: "充气颈枕(旅行U型)", skuEn: "Inflatable Travel Neck Pillow U Shape", category: "home", costRange: "¥5-10", priceRange: "£6.49-8.49", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "常规品类", keywords: ["neck pillow","travel pillow","inflatable pillow","u pillow"], sourcing: "1688: 充气颈枕" },
    { sku: "遮阳伞(迷你便携防晒)", skuEn: "Compact UV Protection Umbrella", category: "apparel", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "低", riskNote: "季节尾注意库存控制", keywords: ["compact umbrella","uv umbrella","sun umbrella","travel umbrella"], sourcing: "1688: 迷你遮阳伞" }
  ],
  validation: {
    googleTrends: ["bank holiday","beach accessories uk"],
    amazonCheck: "BSR < 8000；8月底峰值",
    sourcing: "1688搜索：沙滩/防水/派对",
    riskFlags: ["季节末，注意不要积压库存"]
  }
},
{
  id: "edinburgh-festival-2026",
  name: "爱丁堡艺术节", nameEn: "Edinburgh Festival / Fringe", icon: "🎭",
  date: "2026-08-07", month: 8, importance: "A", category: "activity",
  themeColor: "#7c3aed",
  products: [
    { sku: "戏剧主题帆布袋", skuEn: "Theatre Theme Tote Bag", category: "apparel", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "艺术节周边；文艺风格", keywords: ["theatre bag","fringe bag","arts tote"], sourcing: "1688: 主题帆布袋" },
    { sku: "创意面具(威尼斯风格)", skuEn: "Venetian Style Masquerade Mask", category: "gift", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "艺术节派对；戏剧道具", keywords: ["masquerade mask","venetian mask","party mask"], sourcing: "1688: 面具" },
    { sku: "街头艺人帽子(礼帽)", skuEn: "Performer Top Hat Costume", category: "apparel", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 3, riskLevel: "低", riskNote: "艺术节氛围；戏剧风格", keywords: ["top hat","costume hat","performer hat"], sourcing: "1688: 礼帽" },
    { sku: "素描本套装(旅行)", skuEn: "Travel Sketchbook Set", category: "gift", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "艺术节写生；文创属性", keywords: ["sketchbook","travel sketch","art notebook"], sourcing: "1688: 素描本" },
    { sku: "爱丁堡主题明信片", skuEn: "Edinburgh Postcard Set", category: "gift", costRange: "¥2-5", priceRange: "£5.99-6.99", margin: "约60-70%", matchScore: 3, riskLevel: "低", riskNote: "旅游纪念品；超轻小件", keywords: ["edinburgh postcard","scotland card","tourist gift"], sourcing: "1688: 明信片" },
    { sku: "折叠坐垫(户外演出)", skuEn: "Foldable Seat Cushion Outdoor", category: "home", costRange: "¥5-10", priceRange: "£6.49-8.49", margin: "约45-55%", matchScore: 3, riskLevel: "低", riskNote: "⚠️待复核: 户外看演出实用", keywords: ["seat cushion","outdoor pad","festival cushion"], sourcing: "1688: 折叠坐垫" }
  ],
  validation: {
    googleTrends: ["edinburgh fringe","edinburgh festival","scotland august"],
    amazonCheck: "BSR < 15000；8月全月艺术/文化品类",
    sourcing: "1688搜索：艺术节/戏剧/爱丁堡",
    riskFlags: ["避免Edinburgh Festival官方商标","小众文艺市场备货控制"]
  }
},
{
  id: "notting-hill-carnival-2026",
  name: "诺丁山狂欢节", nameEn: "Notting Hill Carnival", icon: "🪇",
  date: "2026-08-30", month: 8, importance: "A", category: "festival",
  themeColor: "#f59e0b",
  products: [
    { sku: "加勒比风格头饰套装", skuEn: "Caribbean Style Headpiece Set", category: "apparel", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 5, riskLevel: "低", riskNote: "狂欢节必备；羽毛/亮片", keywords: ["carnival headpiece","caribbean costume","feather headband"], sourcing: "1688: 狂欢节头饰" },
    { sku: "彩色喷雾发蜡(临时)", skuEn: "Temporary Colour Hair Spray", category: "apparel", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 5, riskLevel: "中", riskNote: "化妆品CPNP；可水洗", keywords: ["colour spray","temporary hair dye","carnival spray"], sourcing: "1688: 彩色发蜡" },
    { sku: "狂欢节面具(亮片)", skuEn: "Carnival Sequin Mask", category: "apparel", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "派对面具；亮片装饰", keywords: ["carnival mask","sequin mask","party mask"], sourcing: "1688: 亮片面具" },
    { sku: "钢鼓乐器(小型)", skuEn: "Mini Steel Drum Instrument", category: "gift", costRange: "¥15-25", priceRange: "£8.99-9.99", margin: "约35-45%", matchScore: 3, riskLevel: "低", riskNote: "加勒比文化；音乐玩具", keywords: ["steel drum","caribbean music","carnival instrument"], sourcing: "1688: 钢鼓" },
    { sku: "彩色珠子项链套装", skuEn: "Colourful Bead Necklace Set", category: "apparel", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "狂欢节传统配饰", keywords: ["bead necklace","carnival beads","party beads"], sourcing: "1688: 珠子项链" },
    { sku: "加勒比香料礼盒", skuEn: "Caribbean Spice Gift Box", category: "gift", costRange: "¥10-20", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 3, riskLevel: "中", riskNote: "食品需UK认证；保质期", keywords: ["caribbean spice","jerk seasoning","spice gift"], sourcing: "1688: 香料礼盒" }
  ],
  validation: {
    googleTrends: ["notting hill carnival","carnival costume","caribbean festival"],
    amazonCheck: "BSR < 12000；8月底派对品类峰值",
    sourcing: "1688搜索：狂欢节/加勒比/派对装饰",
    riskFlags: ["避免文化挪用争议","化妆品CPNP","8月底时效性"]
  }
},

// ===== 9月（6个）=====
{
  id: "back-to-school-2026",
  name: "返校季", nameEn: "Back to School", icon: "📚",
  date: "2026-09-01", month: 9, importance: "A", category: "activity",
  themeColor: "#3b82f6",
  products: [
    { sku: "笔记本套装(A5 4本)", skuEn: "A5 Notebook Set 4 Pack", category: "gift", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约45-55%", matchScore: 5, riskLevel: "低", riskNote: "常规品类", keywords: ["notebook set","a5 notebooks","school stationery"], sourcing: "1688: A5笔记本套装" },
    { sku: "铅笔盒/笔袋", skuEn: "Pencil Case With Compartments", category: "gift", costRange: "¥4-8", priceRange: "£6.49-8.49", margin: "约50-60%", matchScore: 5, riskLevel: "低", riskNote: "轻小件高毛利", keywords: ["pencil case","pen bag"], sourcing: "1688: 笔袋" },
    { sku: "课程表/计划表磁贴", skuEn: "Magnetic Weekly Planner", category: "home", costRange: "¥3-6", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "轻小件", keywords: ["magnetic planner","weekly schedule"], sourcing: "1688: 磁性计划表" },
    { sku: "荧光笔套装(6色)", skuEn: "Highlighter Pen Set 6 Colors", category: "gift", costRange: "¥3-6", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 5, riskLevel: "低", riskNote: "轻小件刚需", keywords: ["highlighter set","marker pens","study highlighter"], sourcing: "1688: 荧光笔套装" },
    { sku: "书签套装(金属/磁性)", skuEn: "Bookmark Set Metal Magnetic", category: "gift", costRange: "¥2-5", priceRange: "£5.99-6.99", margin: "约60-70%", matchScore: 4, riskLevel: "低", riskNote: "轻小件高毛利", keywords: ["bookmarks","metal bookmark","magnetic bookmark","reading"], sourcing: "1688: 金属书签" },
    { sku: "学生卡套/证件挂绳", skuEn: "Student ID Card Holder Lanyard", category: "gift", costRange: "¥2-5", priceRange: "£5.99-7.99", margin: "约60-70%", matchScore: 5, riskLevel: "低", riskNote: "轻小件实用刚需", keywords: ["card holder","id lanyard","student card","badge holder"], sourcing: "1688: 卡套挂绳" },
    { sku: "姓名贴纸(防水定制)", skuEn: "Waterproof Name Labels Custom", category: "gift", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 5, riskLevel: "低", riskNote: "返校必备；可定制", keywords: ["name labels","school labels","waterproof stickers"], sourcing: "1688: 姓名贴" },
    { sku: "修正带套装(3只)", skuEn: "Correction Tape Set 3 Pack", category: "gift", costRange: "¥3-6", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "文具刚需；轻小件", keywords: ["correction tape","white out","stationery"], sourcing: "1688: 修正带" },
    { sku: "计算器(科学函数)", skuEn: "Scientific Calculator", category: "gift", costRange: "¥10-18", priceRange: "£7.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "低", riskNote: "中学/大学刚需", keywords: ["scientific calculator","math calculator","school calculator"], sourcing: "1688: 科学计算器" },
    { sku: "文件夹/风琴包(A4)", skuEn: "A4 Accordion File Folder", category: "gift", costRange: "¥5-10", priceRange: "£6.49-8.49", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "学生整理收纳刚需", keywords: ["file folder","accordion folder","document organizer"], sourcing: "1688: 风琴包" }
  ],
  validation: {
    googleTrends: ["back to school supplies","stationery uk"],
    amazonCheck: "BSR < 5000；9月初峰值",
    sourcing: "1688搜索：文具/笔记本/学生用品",
    riskFlags: ["食品接触材质需认证"]
  }
},
{
  id: "pirate-day-2026",
  name: "海盗说话日", nameEn: "Talk Like a Pirate Day", icon: "🏴‍☠️",
  date: "2026-09-19", month: 9, importance: "B", category: "trend",
  themeColor: "#92400e",
  products: [
    { sku: "海盗主题派对套装", skuEn: "Pirate Party Decoration Kit", category: "decor", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-50%", matchScore: 4, riskLevel: "低", riskNote: "常规品类", keywords: ["pirate party","pirate decorations"], sourcing: "1688: 海盗派对装饰" },
    { sku: "海盗眼罩/帽子配件", skuEn: "Pirate Eye Patch & Hat", category: "apparel", costRange: "¥3-6", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 5, riskLevel: "低", riskNote: "轻小件", keywords: ["pirate costume","eye patch"], sourcing: "1688: 海盗道具" },
    { sku: "海盗金币巧克力包装(10只)", skuEn: "Pirate Gold Coin Chocolate Wraps", category: "gift", costRange: "¥3-6", priceRange: "£5.99-7.99", margin: "约55-60%", matchScore: 4, riskLevel: "中", riskNote: "食品接触材质认证；不含巧克力仅包装", keywords: ["pirate coins","party favors","treasure chest","gold coins"], sourcing: "1688: 海盗金币包装" },
    { sku: "海盗宝箱造型存钱罐", skuEn: "Pirate Treasure Chest Coin Bank", category: "decor", costRange: "¥5-10", priceRange: "£6.49-8.49", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "小众控制首批量", keywords: ["treasure chest","coin bank","pirate decor","piggy bank"], sourcing: "1688: 海盗存钱罐" }
  ],
  validation: {
    googleTrends: ["pirate day","pirate party uk"],
    amazonCheck: "BSR < 20000；小众但精准",
    sourcing: "1688搜索：海盗/派对道具",
    riskFlags: ["小众节日，控制首批量"]
  }
},
{
  id: "apple-day-2026",
  name: "下午茶季/Apple Day", nameEn: "Afternoon Tea Season", icon: "🫖",
  date: "2026-09-21", month: 9, importance: "A", category: "trend",
  themeColor: "#84cc16",
  products: [
    { sku: "陶瓷下午茶杯碟套装", skuEn: "Ceramic Teacup & Saucer Set", category: "home", costRange: "¥10-18", priceRange: "£8.99-9.99", margin: "约40-45%", matchScore: 3, riskLevel: "中", riskNote: "易碎品包装成本；FBA尺寸重量", keywords: ["teacup set","afternoon tea","ceramic cups"], sourcing: "1688: 下午茶杯碟" },
    { sku: "木质茶点托盘", skuEn: "Wooden Serving Tray", category: "home", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约40-50%", matchScore: 3, riskLevel: "低", riskNote: "体积偏大注意FBA费用", keywords: ["serving tray","wooden tray","tea tray"], sourcing: "1688: 木质托盘" },
    { sku: "英式花纹餐巾纸套装", skuEn: "Floral Paper Napkin Set", category: "decor", costRange: "¥4-8", priceRange: "£6.49-8.49", margin: "约50-55%", matchScore: 4, riskLevel: "低", riskNote: "食品接触材质", keywords: ["paper napkins","floral napkins"], sourcing: "1688: 花纹餐巾纸" },
    { sku: "不锈钢茶叶滤网(球形)", skuEn: "Stainless Steel Tea Infuser Ball", category: "home", costRange: "¥3-6", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 5, riskLevel: "低", riskNote: "轻小件实用", keywords: ["tea infuser","tea strainer","tea ball","loose leaf tea"], sourcing: "1688: 茶叶滤网" },
    { sku: "亚麻餐垫套装(4片)", skuEn: "Linen Placemat Set 4 Pack", category: "home", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约40-50%", matchScore: 3, riskLevel: "低", riskNote: "常规品类", keywords: ["linen placemat","table mat","dining mat","table decor"], sourcing: "1688: 亚麻餐垫" },
    { sku: "花卉主题茶壶保温罩", skuEn: "Floral Teapot Cosy Cover", category: "home", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约40-50%", matchScore: 3, riskLevel: "低", riskNote: "体积偏大注意FBA；小众但英式场景", keywords: ["teapot cosy","tea cosy","teapot cover","afternoon tea"], sourcing: "1688: 茶壶保温罩" }
  ],
  validation: {
    googleTrends: ["afternoon tea","tea accessories uk"],
    amazonCheck: "BSR < 10000；秋季稳定需求",
    sourcing: "1688搜索：茶具/杯垫/托盘",
    riskFlags: ["陶瓷易碎需加强包装","体积大者核算FBA"]
  }
},
{
  id: "harvest-festival-2026",
  name: "收获节", nameEn: "Harvest Festival", icon: "🌾",
  date: "2026-09-27", month: 9, importance: "B", category: "festival",
  themeColor: "#ca8a04",
  products: [
    { sku: "秋季主题门环装饰", skuEn: "Autumn Wreath Decoration", category: "decor", costRange: "¥10-18", priceRange: "£8.99-9.99", margin: "约40-45%", matchScore: 3, riskLevel: "低", riskNote: "体积偏大注意FBA", keywords: ["autumn wreath","harvest wreath","fall decor"], sourcing: "1688: 秋季门环" },
    { sku: "南瓜主题摆件", skuEn: "Pumpkin Figurine Decor", category: "decor", costRange: "¥5-10", priceRange: "£6.49-8.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "⚠️待复核: 常规品类", keywords: ["pumpkin decor","fall decorations"], sourcing: "1688: 南瓜摆件" },
    { sku: "秋季叶形蜡烛托盘", skuEn: "Autumn Leaf Candle Holder Tray", category: "decor", costRange: "¥5-10", priceRange: "£6.49-8.49", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "与万圣节/圣诞衔接", keywords: ["leaf candle holder","autumn tray","fall decor","candle tray"], sourcing: "1688: 秋季蜡烛托盘" },
    { sku: "谷物丰收花束(干花装饰)", skuEn: "Harvest Dried Flower Bouquet Decor", category: "decor", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约45-50%", matchScore: 3, riskLevel: "低", riskNote: "体积偏大注意FBA", keywords: ["dried flowers","harvest bouquet","autumn flowers","fall wreath"], sourcing: "1688: 干花装饰" }
  ],
  validation: {
    googleTrends: ["harvest festival","autumn decorations uk"],
    amazonCheck: "BSR < 15000；与万圣节衔接",
    sourcing: "1688搜索：秋季/南瓜/丰收装饰",
    riskFlags: ["与万圣节备货可合并考虑"]
  }
},
{
  id: "autumn-equinox-2026",
  name: "秋分/秋季焕新", nameEn: "Autumn Equinox / Autumn Refresh", icon: "🍂",
  date: "2026-09-22", month: 9, importance: "B", category: "trend",
  themeColor: "#d97706",
  products: [
    { sku: "秋季香薰蜡烛(南瓜拿铁)", skuEn: "Pumpkin Spice Scented Candle", category: "home", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 5, riskLevel: "中", riskNote: "蜡烛运输安全；秋季爆款香型", keywords: ["pumpkin candle","autumn scent","fall candle"], sourcing: "1688: 秋季蜡烛" },
    { sku: "保暖毯子(法兰绒)", skuEn: "Fleece Throw Blanket", category: "home", costRange: "¥15-25", priceRange: "£8.99-9.99", margin: "约35-45%", matchScore: 5, riskLevel: "低", riskNote: "秋季保暖刚需；家居换装", keywords: ["fleece blanket","throw blanket","autumn blanket"], sourcing: "1688: 法兰绒毯子" },
    { sku: "南瓜造型马克杯", skuEn: "Pumpkin Shaped Mug", category: "gift", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "秋季+万圣节衔接", keywords: ["pumpkin mug","autumn mug","fall mug"], sourcing: "1688: 造型马克杯" },
    { sku: "秋季花环(门挂装饰)", skuEn: "Autumn Wreath Door Decoration", category: "decor", costRange: "¥15-25", priceRange: "£8.99-9.99", margin: "约35-45%", matchScore: 4, riskLevel: "低", riskNote: "秋季家居装饰；枫叶/南瓜元素", keywords: ["autumn wreath","fall wreath","door decor"], sourcing: "1688: 秋季花环" },
    { sku: "毛绒拖鞋(室内)", skuEn: "Indoor Plush Slippers", category: "apparel", costRange: "¥10-20", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "低", riskNote: "秋季保暖；注意UK尺码", keywords: ["plush slippers","indoor slippers","cozy slippers"], sourcing: "1688: 毛绒拖鞋" },
    { sku: "保温杯(不锈钢真空)", skuEn: "Stainless Steel Thermos Flask", category: "home", costRange: "¥15-25", priceRange: "£8.99-9.99", margin: "约35-45%", matchScore: 4, riskLevel: "低", riskNote: "秋冬热饮刚需", keywords: ["thermos flask","insulated bottle","hot drinks"], sourcing: "1688: 保温杯" }
  ],
  validation: {
    googleTrends: ["autumn home decor","fall decorations","cozy home"],
    amazonCheck: "BSR < 10000；9月秋季品类开始上升",
    sourcing: "1688搜索：秋季家居/保暖/南瓜",
    riskFlags: ["蜡烛需MSDS","与万圣节备货可衔接"]
  }
},

// ===== 10月（7个）=====
{
  id: "teachers-day-2026",
  name: "世界教师日", nameEn: "World Teachers Day", icon: "🍎",
  date: "2026-10-05", month: 10, importance: "B", category: "festival",
  themeColor: "#dc2626",
  products: [
    { sku: "教师主题马克杯", skuEn: "Teacher Themed Mug", category: "gift", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约45-55%", matchScore: 4, riskLevel: "中", riskNote: "陶瓷易碎", keywords: ["teacher mug","teacher gift","best teacher"], sourcing: "1688: 教师节马克杯" },
    { sku: "感谢卡+小礼品套装", skuEn: "Thank You Card & Gift Set", category: "gift", costRange: "¥4-8", priceRange: "£5.99-7.99", margin: "约50-60%", matchScore: 5, riskLevel: "低", riskNote: "轻小件", keywords: ["teacher card","thank you gift","appreciation"], sourcing: "1688: 感谢卡套装" },
    { sku: "教师主题书签套装", skuEn: "Teacher Bookmark Set", category: "gift", costRange: "¥2-5", priceRange: "£5.99-6.99", margin: "约60-70%", matchScore: 5, riskLevel: "低", riskNote: "轻小件高毛利", keywords: ["teacher bookmark","book lover","reading gift","school bookmark"], sourcing: "1688: 教师书签" },
    { sku: "桌面笔筒(创意造型)", skuEn: "Creative Pen Holder Desk Organizer", category: "home", costRange: "¥5-10", priceRange: "£6.49-8.49", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "常规品类", keywords: ["pen holder","desk organizer","pencil cup","teacher desk"], sourcing: "1688: 创意笔筒" }
  ],
  validation: {
    googleTrends: ["teacher gift","teachers day uk"],
    amazonCheck: "BSR < 15000；小众节日",
    sourcing: "1688搜索：教师节礼物/马克杯",
    riskFlags: ["避免印刷具体学校logo"]
  }
},
{
  id: "mental-health-day-2026",
  name: "世界精神卫生日", nameEn: "World Mental Health Day", icon: "💚",
  date: "2026-10-10", month: 10, importance: "B", category: "trend",
  themeColor: "#10b981",
  products: [
    { sku: "励志手环套装", skuEn: "Inspirational Bracelet Set", category: "apparel", costRange: "¥3-6", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 5, riskLevel: "低", riskNote: "轻小件", keywords: ["inspirational bracelet","mental health awareness"], sourcing: "1688: 励志手环" },
    { sku: "正能量语录卡片套装", skuEn: "Positive Affirmation Card Set", category: "gift", costRange: "¥2-5", priceRange: "£5.99-7.99", margin: "约60-70%", matchScore: 5, riskLevel: "低", riskNote: "轻小件高毛利", keywords: ["affirmation cards","positive quotes","mental health","self care"], sourcing: "1688: 正能量卡片" },
    { sku: "冥想瑜伽垫绑带套装", skuEn: "Yoga Mat Strap Carrying Band", category: "home", costRange: "¥3-6", priceRange: "£5.99-7.99", margin: "约55-60%", matchScore: 4, riskLevel: "低", riskNote: "轻小件", keywords: ["yoga strap","mat carrier","yoga accessories","fitness"], sourcing: "1688: 瑜伽绑带" }
  ],
  validation: {
    googleTrends: ["mental health awareness","stress relief"],
    amazonCheck: "BSR < 15000；趋势上升",
    sourcing: "1688搜索：减压/励志/心理",
    riskFlags: ["避免医疗功效宣传"]
  }
},
{
  id: "boss-day-2026",
  name: "Boss's Day老板节", nameEn: "Boss's Day", icon: "👔",
  date: "2026-10-16", month: 10, importance: "B", category: "festival",
  themeColor: "#1e40af",
  products: [
    { sku: "老板主题幽默马克杯", skuEn: "Funny Boss Mug", category: "gift", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约45-55%", matchScore: 4, riskLevel: "中", riskNote: "陶瓷易碎", keywords: ["boss mug","boss gift","funny mug"], sourcing: "1688: 老板节杯子" },
    { sku: "桌面收纳套装", skuEn: "Desk Organizer Set", category: "home", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约40-50%", matchScore: 3, riskLevel: "低", riskNote: "体积偏大", keywords: ["desk organizer","office accessories","boss gift"], sourcing: "1688: 桌面收纳" },
    { sku: "老板主题领带夹/袖扣", skuEn: "Boss Cufflinks Tie Clip Set", category: "gift", costRange: "¥5-10", priceRange: "£6.49-8.49", margin: "约50-55%", matchScore: 4, riskLevel: "低", riskNote: "轻小件", keywords: ["cufflinks","tie clip","boss gift","office accessories"], sourcing: "1688: 袖扣领带夹" },
  ],
  validation: {
    googleTrends: ["boss day gift","boss gift uk"],
    amazonCheck: "BSR < 20000；小众",
    sourcing: "1688搜索：办公礼品/马克杯",
    riskFlags: ["小众节日控制首批量"]
  }
},
{
  id: "diwali-2026",
  name: "排灯节", nameEn: "Diwali", icon: "🪔",
  date: "2026-10-20", month: 10, importance: "B", category: "festival",
  themeColor: "#facc15",
  products: [
    { sku: "LED装饰灯串(暖白)", skuEn: "LED Diya String Lights", category: "decor", costRange: "¥8-15", priceRange: "£6.99-8.99", margin: "约45-55%", matchScore: 5, riskLevel: "低", riskNote: "UKCA认证", keywords: ["diwali lights","string lights","diya decor"], sourcing: "1688: LED灯串" },
    { sku: "排灯节主题贺卡套装", skuEn: "Diwali Card Set", category: "gift", costRange: "¥4-8", priceRange: "£5.99-7.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "轻小件", keywords: ["diwali cards","festival cards"], sourcing: "1688: 排灯节贺卡" },
    { sku: "印度风彩色桌旗装饰", skuEn: "Indian Style Colourful Table Runner", category: "decor", costRange: "¥5-10", priceRange: "£6.49-8.49", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "常规品类", keywords: ["table runner","diwali decor","indian decor","festive table"], sourcing: "1688: 印度风桌旗" },
  ],
  validation: {
    googleTrends: ["diwali decorations","diwali gifts uk"],
    amazonCheck: "BSR < 10000；UK印度裔社区需求",
    sourcing: "1688搜索：排灯节/Diwali装饰",
    riskFlags: ["尊重宗教文化，避免不当元素"]
  }
},
{
  id: "halloween-2026",
  name: "万圣节", nameEn: "Halloween", icon: "🎃",
  date: "2026-10-31", month: 10, importance: "S", category: "festival",
  themeColor: "#fb923c",
  products: [
    { sku: "南瓜LED串灯", skuEn: "Pumpkin LED String Lights", category: "decor", costRange: "¥8-15", priceRange: "£6.99-8.99", margin: "约45-55%", matchScore: 5, riskLevel: "低", riskNote: "注意LED的UKCA/CE认证", keywords: ["halloween lights","pumpkin lights","outdoor halloween"], sourcing: "1688: 万圣节南瓜灯串" },
    { sku: "鬼怪窗贴纸套装", skuEn: "Halloween Window Clings Set", category: "decor", costRange: "¥3-6", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "轻小件高毛利", keywords: ["window clings","halloween stickers","window decor"], sourcing: "1688: 万圣节窗贴" },
    { sku: "蜘蛛网装饰套装", skuEn: "Spider Web Decoration Set", category: "decor", costRange: "¥5-10", priceRange: "£6.49-8.49", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "常规品类", keywords: ["spider web","halloween decorations","fake web"], sourcing: "1688: 蜘蛛网装饰" },
    { sku: "万圣节主题糖果袋(10只装)", skuEn: "Halloween Treat Bags 10 Pack", category: "gift", costRange: "¥6-12", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "食品接触材质", keywords: ["treat bags","halloween candy bags","trick or treat"], sourcing: "1688: 万圣节糖果袋" },
    { sku: "南瓜主题儿童斗篷", skuEn: "Kids Pumpkin Cape Costume", category: "apparel", costRange: "¥10-18", priceRange: "£8.99-9.99", margin: "约40-45%", matchScore: 3, riskLevel: "中", riskNote: "UK儿童尺码；含阻燃标签要求", keywords: ["kids costume","pumpkin cape","halloween costume"], sourcing: "1688: 儿童南瓜斗篷" },
    { sku: "万圣节主题餐垫套装", skuEn: "Halloween Placemat Set", category: "home", costRange: "¥5-10", priceRange: "£6.49-8.49", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "常规品类", keywords: ["halloween placemats","table decor","party supplies"], sourcing: "1688: 万圣节餐垫" },
    { sku: "骷髅骨架摆件", skuEn: "Skeleton Decoration Prop", category: "decor", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-50%", matchScore: 4, riskLevel: "低", riskNote: "常规品类", keywords: ["skeleton decoration","halloween props","bone decor"], sourcing: "1688: 骷髅摆件" },
    { sku: "万圣节派对气球套装", skuEn: "Halloween Party Balloon Set", category: "decor", costRange: "¥4-8", priceRange: "£5.99-7.99", margin: "约50-60%", matchScore: 5, riskLevel: "低", riskNote: "轻小件", keywords: ["halloween balloons","party balloons"], sourcing: "1688: 万圣节气球" },
    { sku: "主题马克杯(南瓜造型)", skuEn: "Pumpkin Shaped Mug", category: "home", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "中", riskNote: "陶瓷易碎包装", keywords: ["pumpkin mug","halloween mug","novelty cup"], sourcing: "1688: 南瓜造型杯" },
    { sku: "幽灵主题抱枕套", skuEn: "Ghost Throw Pillow Cover", category: "home", costRange: "¥5-10", priceRange: "£6.49-8.49", margin: "约50-55%", matchScore: 4, riskLevel: "低", riskNote: "注意是枕套非枕头", keywords: ["pillow cover","ghost decor","halloween home"], sourcing: "1688: 万圣节抱枕套" },
    { sku: "吸血鬼假牙道具套装", skuEn: "Vampire Fangs Prop Set", category: "apparel", costRange: "¥3-6", priceRange: "£5.99-7.99", margin: "约60-70%", matchScore: 5, riskLevel: "中", riskNote: "入口道具需食品级材质", keywords: ["vampire fangs","halloween props","fake teeth"], sourcing: "1688: 吸血鬼假牙" },
    { sku: "万圣节礼物盒套装(4只)", skuEn: "Halloween Gift Boxes 4 Pack", category: "gift", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "常规品类", keywords: ["gift boxes","halloween boxes","party favors"], sourcing: "1688: 万圣节礼盒" },
    { sku: "女巫帽子(儿童)", skuEn: "Kids Witch Hat Costume", category: "apparel", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 4, riskLevel: "低", riskNote: "万圣节经典造型；需阻燃标签", keywords: ["witch hat","kids costume","halloween hat"], sourcing: "1688: 女巫帽子" },
    { sku: "庭院墓碑装饰(泡沫)", skuEn: "Foam Graveyard Tombstone Decor", category: "decor", costRange: "¥10-20", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "低", riskNote: "户外庭院装饰；泡沫轻便", keywords: ["tombstone decor","graveyard prop","halloween outdoor"], sourcing: "1688: 墓碑装饰" },
    { sku: "万圣节主题围裙", skuEn: "Halloween Theme Apron", category: "home", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 3, riskLevel: "低", riskNote: "万圣节派对厨房", keywords: ["halloween apron","party apron","kitchen apron"], sourcing: "1688: 主题围裙" }
  ],
  validation: {
    googleTrends: ["halloween decorations 2026","halloween decor uk"],
    amazonCheck: "BSR < 3000；10月强季节性峰值",
    sourcing: "1688搜索：万圣节装饰/南瓜/骷髅",
    riskFlags: ["LED产品需UKCA认证","儿童服装需阻燃标签","避免Disney/IP侵权","入口道具需食品级"]
  }
},

// ===== 11月（7个）=====
{
  id: "bonfire-night-2026",
  name: "篝火节", nameEn: "Bonfire Night", icon: "🎆",
  date: "2026-11-05", month: 11, importance: "B", category: "festival",
  themeColor: "#ea580c",
  products: [
    { sku: "保暖暖手宝", skuEn: "Reusable Hand Warmers", category: "home", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约45-55%", matchScore: 4, riskLevel: "中", riskNote: "注意材质安全", keywords: ["hand warmers","reusable warmers","bonfire night"], sourcing: "1688: 暖手宝" },
    { sku: "篝火节主题围巾/披肩", skuEn: "Bonfire Night Scarf Wrap", category: "apparel", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约40-50%", matchScore: 3, riskLevel: "低", riskNote: "UK尺码；季节性需求", keywords: ["winter scarf","bonfire scarf","warm wrap","plaid scarf"], sourcing: "1688: 保暖围巾" }
  ],
  validation: {
    googleTrends: ["bonfire night","guy fawkes"],
    amazonCheck: "BSR < 12000；11月初峰值",
    sourcing: "1688搜索：荧光棒/暖手宝",
    riskFlags: ["荧光棒化学安全认证","暖手宝材质检测"]
  }
},
{
  id: "remembrance-day-2026",
  name: "国殇纪念日", nameEn: "Remembrance Day", icon: "🌹",
  date: "2026-11-11", month: 11, importance: "B", category: "festival",
  themeColor: "#7f1d1d",
  products: [
    { sku: "虞美人主题胸针", skuEn: "Poppy Brooch Pin", category: "gift", costRange: "¥3-6", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "高", riskNote: "罂粟图案有使用规范，建议中性设计；避免政治符号", keywords: ["poppy pin","remembrance day","memorial brooch"], sourcing: "1688: 胸针定制" },
    { sku: "纪念主题木牌摆件", skuEn: "Memorial Wooden Sign", category: "decor", costRange: "¥5-10", priceRange: "£6.49-8.49", margin: "约45-55%", matchScore: 3, riskLevel: "高", riskNote: "情绪敏感，文案需谨慎", keywords: ["remembrance","memorial decor","lest we forget"], sourcing: "1688: 木质摆件" },
    { sku: "白色和平主题蜡烛", skuEn: "White Peace Themed Candle", category: "home", costRange: "¥5-10", priceRange: "£6.49-8.49", margin: "约45-55%", matchScore: 3, riskLevel: "高", riskNote: "⚠️高度敏感：避免政治符号；蜡烛安全标签", keywords: ["peace candle","memorial candle","white candle","remembrance"], sourcing: "1688: 白色蜡烛" }
  ],
  validation: {
    googleTrends: ["remembrance day","poppy appeal"],
    amazonCheck: "BSR < 15000；情绪敏感品类",
    sourcing: "1688搜索：纪念/胸针/木牌",
    riskFlags: ["⚠️高度敏感：罂粟图案使用受Royal British Legion规范","避免军事/政治符号","建议只做中性纪念类"]
  }
},
{
  id: "kindness-day-2026",
  name: "世界友善日", nameEn: "World Kindness Day", icon: "💛",
  date: "2026-11-13", month: 11, importance: "B", category: "trend",
  themeColor: "#eab308",
  products: [
    { sku: "友善主题贴纸套装", skuEn: "Kindness Sticker Set", category: "gift", costRange: "¥2-5", priceRange: "£5.99-7.99", margin: "约60-70%", matchScore: 5, riskLevel: "低", riskNote: "轻小件高毛利", keywords: ["kindness stickers","positive stickers","school stickers"], sourcing: "1688: 励志贴纸" },
    { sku: "友善主题手环", skuEn: "Kindness Bracelet", category: "apparel", costRange: "¥3-6", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 5, riskLevel: "低", riskNote: "轻小件", keywords: ["kindness bracelet","be kind","awareness"], sourcing: "1688: 励志手环" },
    { sku: "友善主题钥匙扣(励志语)", skuEn: "Kindness Keychain Inspirational Quote", category: "gift", costRange: "¥2-5", priceRange: "£5.99-7.99", margin: "约60-70%", matchScore: 5, riskLevel: "低", riskNote: "轻小件高毛利", keywords: ["kindness keychain","inspirational key","motivational gift","positive"], sourcing: "1688: 励志钥匙扣" },
    { sku: "友善主题马克杯", skuEn: "Be Kind Themed Mug", category: "home", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约45-55%", matchScore: 4, riskLevel: "中", riskNote: "陶瓷易碎", keywords: ["kindness mug","be kind mug","positive mug","gift mug"], sourcing: "1688: 励志马克杯" }
  ],
  validation: {
    googleTrends: ["world kindness day","kindness gifts"],
    amazonCheck: "BSR < 20000；趋势型",
    sourcing: "1688搜索：友善/励志/贴纸",
    riskFlags: ["小众节日控制首批量"]
  }
},
{
  id: "mens-day-2026",
  name: "国际男人节", nameEn: "International Men's Day", icon: "👨",
  date: "2026-11-19", month: 11, importance: "A", category: "festival",
  themeColor: "#1d4ed8",
  products: [
    { sku: "男士主题马克杯", skuEn: "Men's Day Mug", category: "gift", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约45-55%", matchScore: 4, riskLevel: "中", riskNote: "陶瓷易碎", keywords: ["mens day mug","men gift","man mug"], sourcing: "1688: 男士马克杯" },
    { sku: "胡须护理套装", skuEn: "Beard Care Kit", category: "gift", costRange: "¥10-18", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 3, riskLevel: "中", riskNote: "化妆品类需成分合规", keywords: ["beard kit","beard care","mens grooming"], sourcing: "1688: 胡须护理套装" },
    { sku: "幽默领带/袜子", skuEn: "Funny Novelty Socks", category: "apparel", costRange: "¥5-10", priceRange: "£6.49-8.49", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "UK尺码", keywords: ["novelty socks","funny socks","mens socks"], sourcing: "1688: 搞怪袜子" },
    { sku: "多功能钥匙扣工具", skuEn: "Multi-tool Keychain", category: "home", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约45-55%", matchScore: 5, riskLevel: "低", riskNote: "轻小件实用", keywords: ["keychain tool","multi tool","edc keychain"], sourcing: "1688: 钥匙扣工具" },
    { sku: "男士皮质卡包(短款)", skuEn: "Men's Leather Card Wallet Short", category: "gift", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "常规品类", keywords: ["leather wallet","card wallet","mens wallet","slim wallet"], sourcing: "1688: 男士卡包" },
    { sku: "车载手机支架(出风口)", skuEn: "Car Phone Holder Air Vent Mount", category: "home", costRange: "¥5-10", priceRange: "£6.49-8.49", margin: "约50-55%", matchScore: 5, riskLevel: "低", riskNote: "实用刚需；轻小件", keywords: ["car phone holder","car mount","phone stand car","air vent holder"], sourcing: "1688: 车载手机支架" },
    { sku: "旅行洗漱包(防水)", skuEn: "Travel Toiletry Bag Waterproof", category: "gift", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "实用刚需", keywords: ["toiletry bag","travel bag","wash bag","grooming bag"], sourcing: "1688: 洗漱包" }
  ],
  validation: {
    googleTrends: ["mens day gift","men gifts uk"],
    amazonCheck: "BSR < 10000；11月稳定需求",
    sourcing: "1688搜索：男士礼品/胡须/袜子",
    riskFlags: ["化妆品类注意UK成分合规"]
  }
},
{
  id: "black-friday-2026",
  name: "黑五", nameEn: "Black Friday", icon: "🛍️",
  date: "2026-11-27", month: 11, importance: "S", category: "activity",
  themeColor: "#111827",
  products: [
    { sku: "保暖手套(触屏)", skuEn: "Touch Screen Winter Gloves", category: "apparel", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约45-55%", matchScore: 5, riskLevel: "低", riskNote: "UK尺码", keywords: ["touch screen gloves","winter gloves","warm gloves"], sourcing: "1688: 触屏手套" },
    { sku: "加湿器(便携)", skuEn: "Portable Humidifier", category: "home", costRange: "¥10-18", priceRange: "£8.99-9.99", margin: "约40-45%", matchScore: 4, riskLevel: "中", riskNote: "电子UKCA认证", keywords: ["humidifier","portable humidifier","desk humidifier"], sourcing: "1688: 便携加湿器" },
    { sku: "蓝牙耳机包/收纳", skuEn: "Earbuds Case Pouch", category: "gift", costRange: "¥3-6", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 5, riskLevel: "低", riskNote: "轻小件", keywords: ["earbuds case","airpods pouch","storage case"], sourcing: "1688: 耳机收纳包" },
    { sku: "冬季围巾", skuEn: "Winter Scarf", category: "apparel", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-50%", matchScore: 4, riskLevel: "低", riskNote: "UK尺码", keywords: ["winter scarf","warm scarf","mens scarf"], sourcing: "1688: 冬季围巾" },
    { sku: "手机支架(床头)", skuEn: "Phone Bed Stand Holder", category: "home", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约45-55%", matchScore: 5, riskLevel: "低", riskNote: "实用刚需", keywords: ["phone stand","bed stand","phone holder"], sourcing: "1688: 手机支架" },
    { sku: "保温杯(不锈钢)", skuEn: "Insulated Tumbler", category: "home", costRange: "¥10-18", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "中", riskNote: "食品级认证", keywords: ["tumbler","insulated cup","thermal flask"], sourcing: "1688: 保温杯" },
    { sku: "旅行收纳袋套装", skuEn: "Travel Organizer Bags Set", category: "gift", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 5, riskLevel: "低", riskNote: "实用", keywords: ["travel organizer","packing cubes","luggage bags"], sourcing: "1688: 旅行收纳套装" },
    { sku: "宠物玩具套装", skuEn: "Pet Toy Set", category: "gift", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "注意宠物安全材质", keywords: ["dog toys","pet toys","chew toys"], sourcing: "1688: 宠物玩具" },
    { sku: "厨房收纳架", skuEn: "Kitchen Organizer Rack", category: "home", costRange: "¥10-18", priceRange: "£8.99-9.99", margin: "约40-45%", matchScore: 3, riskLevel: "低", riskNote: "体积偏大", keywords: ["kitchen organizer","storage rack","pantry organizer"], sourcing: "1688: 厨房收纳" },
    { sku: "圣诞预热装饰小件", skuEn: "Mini Christmas Decorations", category: "decor", costRange: "¥5-10", priceRange: "£6.49-8.49", margin: "约50-55%", matchScore: 5, riskLevel: "低", riskNote: "衔接圣诞", keywords: ["mini christmas","small decor","tree ornaments"], sourcing: "1688: 迷你圣诞装饰" },
    { sku: "羊毛袜子礼盒(3双装)", skuEn: "Wool Socks Gift Box 3 Pairs", category: "apparel", costRange: "¥10-18", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 5, riskLevel: "低", riskNote: "冬季刚需礼品；UK尺码", keywords: ["wool socks","winter socks","sock gift box"], sourcing: "1688: 羊毛袜子" },
  ],
  validation: {
    googleTrends: ["black friday deals 2026","gift ideas uk"],
    amazonCheck: "BSR < 2000；全年最大流量节点",
    sourcing: "1688搜索：冬季/电子/家居/礼品",
    riskFlags: ["电子产品需UKCA认证","竞争最激烈需早备货","食品接触材质认证"]
  }
},
{
  id: "cyber-monday-2026",
  name: "网一", nameEn: "Cyber Monday", icon: "💻",
  date: "2026-11-30", month: 11, importance: "A", category: "activity",
  themeColor: "#4338ca",
  products: [
    { sku: "笔记本内胆包", skuEn: "Laptop Sleeve Case", category: "home", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-50%", matchScore: 4, riskLevel: "低", riskNote: "尺寸适配UK常见型号", keywords: ["laptop sleeve","laptop case","notebook bag"], sourcing: "1688: 笔记本内胆包" },
    { sku: "键盘清洁套装", skuEn: "Keyboard Cleaning Kit", category: "home", costRange: "¥5-10", priceRange: "£6.49-8.49", margin: "约50-55%", matchScore: 5, riskLevel: "低", riskNote: "轻小件实用", keywords: ["keyboard cleaner","cleaning kit","pc accessories"], sourcing: "1688: 键盘清洁套装" },
    { sku: "手机壳套装(3只)", skuEn: "Phone Case Set 3 Pack", category: "gift", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约50-55%", matchScore: 4, riskLevel: "低", riskNote: "注意适配新机型", keywords: ["phone case","phone cover","smartphone case"], sourcing: "1688: 手机壳套装" },
    { sku: "USB集线器收纳盒", skuEn: "USB Hub Storage Box", category: "home", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "桌面整理", keywords: ["cable management","desk organizer","cord holder"], sourcing: "1688: 线缆收纳盒" },
    { sku: "鼠标垫(加厚大号)", skuEn: "Extended Mouse Pad Large Thick", category: "home", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约45-50%", matchScore: 4, riskLevel: "低", riskNote: "体积偏大注意FBA", keywords: ["mouse pad","desk mat","large mousepad","gaming pad"], sourcing: "1688: 大号鼠标垫" },
    { sku: "笔记本支架(铝合金折叠)", skuEn: "Laptop Stand Aluminium Foldable", category: "home", costRange: "¥10-18", priceRange: "£7.99-9.99", margin: "约40-45%", matchScore: 4, riskLevel: "低", riskNote: "实用刚需；注意折叠尺寸FBA", keywords: ["laptop stand","notebook holder","ergonomic stand","foldable stand"], sourcing: "1688: 笔记本支架" },
  ],
  validation: {
    googleTrends: ["cyber monday deals","tech accessories uk"],
    amazonCheck: "BSR < 5000；与黑五衔接",
    sourcing: "1688搜索：数码配件/电脑周边",
    riskFlags: ["电子产品需UKCA认证","注意品牌专利（手机型号）"]
  }
},
{
  id: "singles-day-2026",
  name: "双十一/光棍节", nameEn: "Singles' Day / 11.11", icon: "🛍️",
  date: "2026-11-11", month: 11, importance: "A", category: "activity",
  themeColor: "#ef4444",
  products: [
    { sku: "电子配件套装(手机)", skuEn: "Phone Accessories Bundle", category: "gift", costRange: "¥10-20", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 5, riskLevel: "低", riskNote: "11.11爆款品类；多SKU组合", keywords: ["phone accessories","tech bundle","gadget set"], sourcing: "1688: 手机配件套装" },
    { sku: "家用投影仪幕布(便携)", skuEn: "Portable Projector Screen", category: "home", costRange: "¥15-25", priceRange: "£8.99-9.99", margin: "约35-45%", matchScore: 4, riskLevel: "低", riskNote: "家庭影院；配合投影仪", keywords: ["projector screen","portable screen","home cinema"], sourcing: "1688: 投影幕布" },
    { sku: "家用安防摄像头(WiFi)", skuEn: "WiFi Home Security Camera", category: "home", costRange: "¥25-40", priceRange: "£8.99-9.99", margin: "约25-35%", matchScore: 4, riskLevel: "中", riskNote: "UKCA认证；GDPR隐私标识", keywords: ["security camera","wifi camera","home cctv"], sourcing: "1688: 安防摄像头" },
    { sku: "多功能收纳盒(桌面)", skuEn: "Multi-Function Desktop Organizer", category: "home", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "办公/家居收纳；刚需", keywords: ["desk organizer","storage box","desktop tidy"], sourcing: "1688: 桌面收纳" }
  ],
  validation: {
    googleTrends: ["singles day 11.11","11.11 sale","singles day uk"],
    amazonCheck: "BSR < 8000；11月11日前后峰值；跨境卖家主场",
    sourcing: "1688搜索：电子配件/家居/数码",
    riskFlags: ["电子产品UKCA","与黑五备货时间重叠需规划","英国影响力逐年增长但不如黑五"]
  }
},

// ===== 12月（4个）=====
{
  id: "tree-dressing-day-2026",
  name: "National Tree Dressing Day", nameEn: "Tree Dressing Day", icon: "🌳",
  date: "2026-12-05", month: 12, importance: "A", category: "festival",
  themeColor: "#15803d",
  products: [
    { sku: "户外装饰彩带", skuEn: "Outdoor Decorative Ribbon", category: "decor", costRange: "¥5-10", priceRange: "£6.49-8.49", margin: "约50-55%", matchScore: 4, riskLevel: "低", riskNote: "常规品类", keywords: ["tree ribbon","outdoor ribbon","decorative ribbon"], sourcing: "1688: 装饰彩带" },
    { sku: "木质挂饰套装", skuEn: "Wooden Hanging Ornament Set", category: "decor", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "与圣诞衔接", keywords: ["wooden ornaments","tree decorations","hanging decor"], sourcing: "1688: 木质挂饰" },
    { sku: "LED灯串(户外防水暖白)", skuEn: "LED String Lights Outdoor Warm White", category: "decor", costRange: "¥8-15", priceRange: "£6.99-8.99", margin: "约45-55%", matchScore: 5, riskLevel: "低", riskNote: "UKCA认证；衔接圣诞", keywords: ["string lights","outdoor lights","garden lights","led lights"], sourcing: "1688: LED灯串户外" },
    { sku: "松果装饰挂件(天然)", skuEn: "Natural Pine Cone Hanging Decor", category: "decor", costRange: "¥3-6", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "天然材质；与圣诞衔接", keywords: ["pine cone","natural decor","rustic ornaments","tree hanging"], sourcing: "1688: 松果装饰" }
  ],
  validation: {
    googleTrends: ["tree dressing day","outdoor decorations"],
    amazonCheck: "BSR < 15000；小众与圣诞衔接",
    sourcing: "1688搜索：彩带/木质挂饰",
    riskFlags: ["与圣诞备货可合并"]
  }
},
{
  id: "christmas-2026",
  name: "圣诞节", nameEn: "Christmas", icon: "🎄",
  date: "2026-12-25", month: 12, importance: "S", category: "festival",
  themeColor: "#dc2626",
  products: [
    { sku: "圣诞树挂件套装(4只精选装)", skuEn: "Christmas Tree Ornaments 4 Pack", category: "decor", costRange: "¥8-15", priceRange: "£6.99-8.99", margin: "约45-55%", matchScore: 5, riskLevel: "低", riskNote: "常规品类", keywords: ["christmas ornaments","tree decorations","baubles"], sourcing: "1688: 圣诞挂件套装" },
    { sku: "圣诞主题LED串灯", skuEn: "Christmas LED String Lights", category: "decor", costRange: "¥8-15", priceRange: "£6.99-8.99", margin: "约45-55%", matchScore: 5, riskLevel: "低", riskNote: "UKCA认证", keywords: ["christmas lights","string lights","outdoor christmas"], sourcing: "1688: 圣诞LED灯串" },
    { sku: "圣诞袜(悬挂装饰)", skuEn: "Christmas Stocking Set", category: "decor", costRange: "¥5-10", priceRange: "£6.49-8.49", margin: "约50-55%", matchScore: 5, riskLevel: "低", riskNote: "常规品类", keywords: ["christmas stocking","hanging stocking","xmas decor"], sourcing: "1688: 圣诞袜" },
    { sku: "圣诞主题礼品袋套装", skuEn: "Christmas Gift Bags Set", category: "gift", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约50-55%", matchScore: 5, riskLevel: "低", riskNote: "刚需高销量", keywords: ["gift bags","christmas bags","present bags"], sourcing: "1688: 圣诞礼品袋" },
    { sku: "圣诞主题包装纸套装", skuEn: "Christmas Wrapping Paper Set", category: "gift", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约50-55%", matchScore: 5, riskLevel: "低", riskNote: "刚需", keywords: ["wrapping paper","christmas wrap","gift wrap"], sourcing: "1688: 圣诞包装纸" },
    { sku: "圣诞主题马克杯套装", skuEn: "Christmas Mug Set", category: "home", costRange: "¥10-18", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "中", riskNote: "陶瓷易碎", keywords: ["christmas mug","xmas mug","festive cup"], sourcing: "1688: 圣诞马克杯" },
    { sku: "圣诞主题抱枕套", skuEn: "Christmas Pillow Cover", category: "home", costRange: "¥5-10", priceRange: "£6.49-8.49", margin: "约50-55%", matchScore: 5, riskLevel: "低", riskNote: "枕套非枕头", keywords: ["pillow cover","christmas pillow","xmas decor"], sourcing: "1688: 圣诞抱枕套" },
    { sku: "圣诞主题餐垫套装", skuEn: "Christmas Placemat Set", category: "home", costRange: "¥5-10", priceRange: "£6.49-8.49", margin: "约50-55%", matchScore: 4, riskLevel: "低", riskNote: "常规品类", keywords: ["christmas placemats","table decor","xmas dining"], sourcing: "1688: 圣诞餐垫" },
    { sku: "圣诞主题餐具套装", skuEn: "Christmas Tableware Set", category: "home", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-50%", matchScore: 4, riskLevel: "中", riskNote: "食品接触材质", keywords: ["christmas tableware","paper plates","party supplies"], sourcing: "1688: 圣诞餐具" },
    { sku: "圣诞帽套装(4只)", skuEn: "Santa Hat Set 4 Pack", category: "apparel", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约50-55%", matchScore: 5, riskLevel: "低", riskNote: "派对刚需", keywords: ["santa hat","christmas hat","party hat"], sourcing: "1688: 圣诞帽" },
    { sku: "驯鹿发箍套装", skuEn: "Reindeer Headband Set", category: "apparel", costRange: "¥5-10", priceRange: "£6.49-8.49", margin: "约50-55%", matchScore: 5, riskLevel: "低", riskNote: "派对配件", keywords: ["reindeer headband","christmas accessory","party headband"], sourcing: "1688: 驯鹿发箍" },
    { sku: "圣诞老人胡子道具套装", skuEn: "Santa Beard Prop Set", category: "apparel", costRange: "¥4-8", priceRange: "£5.99-7.99", margin: "约55-60%", matchScore: 5, riskLevel: "低", riskNote: "轻小件", keywords: ["santa beard","christmas prop","party accessory"], sourcing: "1688: 圣诞老人胡子" },
    { sku: "圣诞主题门环装饰", skuEn: "Christmas Wreath", category: "decor", costRange: "¥10-20", priceRange: "£8.99-9.99", margin: "约40-45%", matchScore: 3, riskLevel: "低", riskNote: "体积大注意FBA", keywords: ["christmas wreath","door wreath","xmas decor"], sourcing: "1688: 圣诞门环" },
    { sku: "圣诞日历盲盒(玩具)", skuEn: "Advent Calendar Toys", category: "gift", costRange: "¥10-18", priceRange: "£8.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "中", riskNote: "儿童玩具安全认证", keywords: ["advent calendar","christmas countdown","toy calendar"], sourcing: "1688: 圣诞日历" },
    { sku: "圣诞主题蜡烛套装", skuEn: "Christmas Candle Set", category: "home", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-50%", matchScore: 4, riskLevel: "中", riskNote: "蜡烛安全标签要求", keywords: ["christmas candles","scented candles","festive candle"], sourcing: "1688: 圣诞蜡烛" },
    { sku: "圣诞爆竹拉炮(4只)", skuEn: "Christmas Crackers 4 Pack", category: "decor", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 5, riskLevel: "低", riskNote: "英国圣诞传统必备；含小礼物", keywords: ["christmas crackers","xmas crackers","party crackers"], sourcing: "1688: 圣诞拉炮" },
    { sku: "圣诞主题围巾(格纹)", skuEn: "Christmas Tartan Scarf", category: "apparel", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "圣诞格纹经典；UK尺码", keywords: ["christmas scarf","tartan scarf","festive scarf"], sourcing: "1688: 圣诞围巾" },
    { sku: "圣诞糖果拐杖装饰", skuEn: "Candy Cane Decoration Set", category: "decor", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "圣诞经典元素；轻小件", keywords: ["candy cane","christmas candy","xmas decor"], sourcing: "1688: 糖果拐杖" }
  ],
  validation: {
    googleTrends: ["christmas decorations 2026","christmas gifts uk"],
    amazonCheck: "BSR < 1500；全年最大消费节点",
    sourcing: "1688搜索：圣诞装饰/礼品/派对",
    riskFlags: ["⚠️最大节点需最早备货(T-55约10月底)","避免IP侵权(Disney等)","电子需UKCA","蜡烛/儿童玩具有安全要求"]
  }
},
{
  id: "boxing-week-2026",
  name: "节礼周", nameEn: "Boxing Week (Boxing Day + NYE)", icon: "🎊",
  date: "2026-12-26", month: 12, importance: "A", category: "activity",
  themeColor: "#7c3aed",
  products: [
    { sku: "新年主题装饰套装", skuEn: "New Year Decoration Set", category: "decor", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约45-50%", matchScore: 4, riskLevel: "低", riskNote: "常规品类", keywords: ["new year decorations","2027 decor","nye party"], sourcing: "1688: 新年装饰" },
    { sku: "派对popper套装", skuEn: "Party Poppers Set", category: "decor", costRange: "¥5-10", priceRange: "£6.49-8.49", margin: "约50-55%", matchScore: 4, riskLevel: "中", riskNote: "烟花类产品安全认证", keywords: ["party poppers","new year","celebration"], sourcing: "1688: 派对popper" },
    { sku: "新年主题眼镜道具", skuEn: "New Year Glasses Props", category: "apparel", costRange: "¥3-6", priceRange: "£5.99-7.99", margin: "约60-70%", matchScore: 5, riskLevel: "低", riskNote: "轻小件", keywords: ["new year glasses","2027 glasses","party props"], sourcing: "1688: 新年眼镜" },
    { sku: "清仓特价包装礼品", skuEn: "Clearance Gift Sets", category: "gift", costRange: "¥6-12", priceRange: "£6.99-8.99", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "消化圣诞余货", keywords: ["gift sets","sale items","clearance"], sourcing: "1688: 礼品套装" },
    { sku: "2027新年倒计时日历牌", skuEn: "2027 New Year Countdown Calendar", category: "decor", costRange: "¥5-10", priceRange: "£6.49-8.49", margin: "约45-55%", matchScore: 4, riskLevel: "低", riskNote: "衔接新年主题", keywords: ["new year countdown","2027 calendar","nye decor","party calendar"], sourcing: "1688: 新年倒计时牌" },
    { sku: "派对彩带喷花(安全型)", skuEn: "Party Streamers Spray Safe Type", category: "decor", costRange: "¥3-6", priceRange: "£5.99-7.99", margin: "约55-60%", matchScore: 4, riskLevel: "中", riskNote: "需安全认证；注意材质无毒", keywords: ["party streamers","spray string","nye party","celebration"], sourcing: "1688: 彩带喷花" },
    { sku: "冬季保暖围巾(新年红)", skuEn: "Winter Scarf New Year Red", category: "apparel", costRange: "¥8-15", priceRange: "£7.99-9.99", margin: "约40-50%", matchScore: 4, riskLevel: "低", riskNote: "UK尺码；红色新年主题", keywords: ["red scarf","new year scarf","winter scarf","festive scarf"], sourcing: "1688: 红色围巾" }
  ],
  validation: {
    googleTrends: ["boxing day sale","new year decorations"],
    amazonCheck: "BSR < 5000；清仓+新年衔接",
    sourcing: "1688搜索：新年装饰/派对用品",
    riskFlags: ["烟花类需安全认证","主要消化圣诞库存"]
  }
},
{
  id: "new-years-eve-2026",
  name: "跨年夜", nameEn: "New Year's Eve", icon: "🕛",
  date: "2026-12-31", month: 12, importance: "A", category: "festival",
  themeColor: "#fbbf24",
  products: [
    { sku: "跨年倒计时气球套装", skuEn: "NYE Countdown Balloon Set", category: "decor", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 5, riskLevel: "低", riskNote: "跨年派对必备；数字气球", keywords: ["countdown balloons","nye balloons","new year party"], sourcing: "1688: 倒计时气球" },
    { sku: "香槟杯套装(塑料派对款)", skuEn: "Plastic Champagne Flute Set", category: "home", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 5, riskLevel: "低", riskNote: "跨年必备；安全不易碎", keywords: ["champagne flute","party glass","nye cup"], sourcing: "1688: 塑料香槟杯" },
    { sku: "闪光派对横幅(2027)", skuEn: "Glitter 2027 Banner", category: "decor", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 5, riskLevel: "低", riskNote: "跨年装饰；年份时效性", keywords: ["2027 banner","new year banner","glitter banner"], sourcing: "1688: 新年横幅" },
    { sku: "派对帽子套装(跨年)", skuEn: "NYE Party Hat Set", category: "apparel", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "跨年派对传统", keywords: ["party hat","nye hat","new year hat"], sourcing: "1688: 派对帽子" },
    { sku: "LED闪光项链/手环", skuEn: "LED Flash Necklace Bracelet", category: "apparel", costRange: "¥3-8", priceRange: "£5.99-7.99", margin: "约55-65%", matchScore: 4, riskLevel: "低", riskNote: "跨年夜氛围配件", keywords: ["led jewelry","flash bracelet","nye accessory"], sourcing: "1688: LED饰品" },
    { sku: "许愿纸灯笼(天灯式)", skuEn: "Sky Lantern Wish Paper", category: "decor", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 3, riskLevel: "中", riskNote: "需安全认证；部分地区禁放", keywords: ["sky lantern","wish lantern","paper lantern"], sourcing: "1688: 许愿灯" },
    { sku: "新年许愿瓶套装", skuEn: "New Year Wish Bottle Set", category: "gift", costRange: "¥5-12", priceRange: "£6.99-8.99", margin: "约50-60%", matchScore: 3, riskLevel: "低", riskNote: "许愿仪式感；礼品属性", keywords: ["wish bottle","new year gift","resolution jar"], sourcing: "1688: 许愿瓶" }
  ],
  validation: {
    googleTrends: ["new years eve party","nye decorations","2027 party"],
    amazonCheck: "BSR < 5000；12月底派对品类爆发",
    sourcing: "1688搜索：跨年/派对/新年装饰",
    riskFlags: ["年份时效性强仅12月","烟花类需安全认证"]
  }
}

]