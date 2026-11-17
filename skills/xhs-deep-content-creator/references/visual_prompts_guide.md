# 小红书 3:4 高转化视觉与生图提示词工程手册 (Visual & Image Generation Guide)

小红书本质是一个**“视觉第一、文字第二”**的平台。用户在双列瀑布流中滑动时，**停留时间通常不足 0.8 秒**。封面图的抓眼度与信息密度决定了 80% 的点击率（CTR），而内页排版的舒适度决定了完播与收藏率。

---

## 一、 视觉设计黄金物理法则 (Physical Layout Standards)

1. **绝对标准比例**：严格遵循 **3:4 比例**（分辨率推荐 **1200 × 1600 px** 或 **1080 × 1440 px**）。
   - 严禁使用 16:9 横图（在手机流中只有极小高度，视觉弱势）。
   - 严禁使用 1:1 正方形（浪费了上下至少 25% 的可视面积）。
2. **三秒定生死：封面三层视线动线 (Visual Eye-Flow)**：
   ```
   ┌────────────────────────────────────────┐
   │ [顶部 20%]  视觉反差标签 (例: 🌿老中医调理经方) │
   │             主标题大字 (≤16字，粗黑体高反差)     │
   ├────────────────────────────────────────┤
   │ [中部 65%]  核心焦点物 / 结构化卡片      │
   │             · 真实生药材/陶罐/自然光摄影  │
   │             · 或 3个信息分块/步骤拆解     │
   │             · 画面干净，绝不杂乱拥挤      │
   ├────────────────────────────────────────┤
   │ [底部 15%]  行动号召与安全锚点            │
   │             · 建议收藏防走丢 / 免责合规标  │
   └────────────────────────────────────────┘
   ```
3. **色彩心理学与色系规范**：
   - **中医/健康养生**：大地暖色调、砂锅陶土棕（`#8C6239`）、草本橄榄绿（`#4A6B53`）、米白宣纸底色（`#F7F4EB`）。拒绝刺眼的荧光绿和血红色。
   - **AI/科技办公**：深空灰碳黑底（`#141414` / `#1E1E24`）、科技冰蓝（`#3875FF`）、极简冷白（`#FFFFFF`）、高亮强调橙（`#FF7D00`）。

---

## 二、 三大主流视觉生图提示词范式 (Image Generation Prompts)

在使用 AI 图像生成模型（如 Gemini Imagen、Midjourney、Stable Diffusion 等）时，按以下三种成熟范式出图：

### 范式 1：真实高质感静物摄影风 (Aesthetic Still Life Photography)
适用于中医草本、茶饮、食材养生等真实体验类笔记。强调自然光、微距细节与生活温度。

- **Prompt 结构**：
  `[主体与环境] + [构图与比例] + [光影与材质] + [镜头参数与画质] + [排除劣质词]`
- **实战提示词模板（以健脾祛湿陈皮茶为例）**：
  > **Prompt**: Top-down aesthetic flatlay photography, dried aged tangerine peel (Chenpi), dried poria cocos cubes, and white atractylodes neatly placed on a rustic wooden tray, a delicate ceramic teacup with steaming warm amber herbal tea next to it, subtle morning natural window sunlight, warm earthy tones, clean linen tablecloth background, minimalist zen lifestyle, hyper-detailed texture, 8k resolution, shot on 50mm f/1.8 lens, 3:4 aspect ratio.
  >
  > **Negative Prompt**: plastic, artificial, oversaturated, deformed, blurry, cartoon, illustration, watermark, low quality, messy, noisy, neon colors.

---

### 范式 2：结构化极简知识卡片风 (Structured Infographic / UI Card)
适用于职场提效、工具合集、经方干货对比笔记。通过代码或排版引擎（Pillow/HTML-to-Image）渲染。

- **设计规范**：
  - **背景**：深色哑光磨砂质感（科技类）或米黄色棉麻微质感（健康类）。
  - **卡片容器**：采用圆角矩形（Radius 16~24px）、内发光边框（Border 1px rgba(255,255,255,0.1)）或柔和弥散阴影。
  - **排版节奏**：大号序号（1️⃣ 2️⃣ 3️⃣）、加粗工具名/方剂名、标签高亮（胶囊 Tag）、两行以内白话实操要点。
- **生图/代码规范**：
  - 必须使用开源且笔画清晰的商用免费字体（如思源黑体、MiSans）。
  - 行距保持在 1.4~1.6，字间距适当放开，移动端阅读完全不费眼。

---

### 范式 3：避坑对比与痛点分镜风 (Before & After / Problem vs Solution)
展示强烈认知冲突，瞬间激发点击欲。

- **Prompt 模板（以错误养生 vs 正确养生为例）**：
  > **Prompt**: Split-screen conceptual composition in 3:4 ratio. Left side: an oversized iced coffee glass filled with condensed water droplets with a red transparent "X" mark, cold blue dim lighting, tired and bloated mood. Right side: a steaming warm ceramic mug of traditional herbal tea with fresh ginger and dried tangerine peel, golden morning sunlight, vibrant green potted plant, cozy energetic vibe with a soft green checkmark. Realistic lifestyle photography, 8k, cinematic lighting.

---

## 三、 绝对规避的视觉雷区 (Negative Filter)

1. **拒绝假人假笑的“AI 塑料感”**：
   - 很多 AI 生图人物皮肤像融化的蜡像、反光油腻、五官僵硬，小红书用户一眼能识破并本能排斥。
   - 优选：**手部特写、静物台面特写、背影、或纯排版卡片**，尽量不生成无意义的 AI 假人立绘。
2. **严防文字错乱**：
   - AI 生图模型直接生成的中文通常会出现鬼画符和拼写错误。
   - **最佳实践**：AI 负责生成纯净高清背景/场景，中文文字标题与内容卡片由代码（Pillow/Canvas）精准绘制合成！
3. **避免要素过载**：
   - 一张图绝不要试图塞满 10 个知识点。遵循“一图讲透 1~3 个核心点”，信息过载会导致读者视线疲劳直接滑走。
