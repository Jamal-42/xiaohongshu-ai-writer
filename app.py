import os
import streamlit as st
import dashscope
from dashscope import Generation
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DASHSCOPE_API_KEY", "")

st.set_page_config(page_title="AI 小红书文案生成器", page_icon="📝", layout="wide")

# 自定义CSS美化
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #ff2442 0%, #ff6b81 100%);
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    .main-header h1 {
        color: white;
        font-size: 2.2rem;
        margin-bottom: 0.3rem;
    }
    .main-header p {
        color: rgba(255,255,255,0.9);
        font-size: 1.1rem;
    }
    .result-card {
        background: #fafafa;
        border: 1px solid #eee;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .score-badge {
        display: inline-block;
        background: linear-gradient(135deg, #ff2442, #ff6b81);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: bold;
    }
    .history-item {
        background: white;
        border: 1px solid #f0f0f0;
        border-radius: 8px;
        padding: 0.8rem;
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #ff2442 0%, #ff6b81 100%);
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: bold;
    }
    .tip-box {
        background: #fff8f0;
        border-left: 4px solid #ff9500;
        padding: 0.8rem 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>📝 AI 小红书文案生成器</h1>
    <p>专业级爆款文案引擎 · 基于通义千问大模型 · 支持多风格智能创作</p>
</div>
""", unsafe_allow_html=True)

# 初始化session state
if "history" not in st.session_state:
    st.session_state.history = []
if "generated_result" not in st.session_state:
    st.session_state.generated_result = None
if "score_result" not in st.session_state:
    st.session_state.score_result = None

# ===== PROMPT 模板 =====
FEW_SHOT_EXAMPLES = """
以下是几个高赞小红书文案的真实案例，请学习它们的写作模式：

【案例1 - 种草推荐】
标题：姐妹们！这个底妆搭配让我省了2000💰
正文：之前柜姐推荐的贵妇粉底一直不舍得买…直到我发现这个平替组合！
持妆力：⭐⭐⭐⭐⭐ 一整天不脱妆
遮瑕度：⭐⭐⭐⭐ 痘印bye bye
性价比：⭐⭐⭐⭐⭐ 两个加一起不到200
互动引导：姐妹们还有什么好用的平替推荐吗！评论区交作业📝

【案例2 - 教程攻略】
标题：跟着做！3步搞定ins风卧室改造🏠
正文：租房4年终于把猪窝变仙境✨
Step1: 灯光氛围感（氛围灯+落地灯，冷暖搭配）
Step2: 软装三件套（床品+地毯+窗帘同色系）
Step3: 墙面装饰（ins贴纸+照片墙+藤编镜）
总花费：487元！全部1688可入
互动引导：想看客厅改造的扣1！收藏=不吃灰📌
"""

SYSTEM_PROMPT = """你是一位年收入百万的小红书头部博主，精通爆款内容创作方法论。
你深谙小红书算法推荐机制和用户心理。

## 你的核心能力
1. 标题党大师：懂得用数字冲击、情绪共鸣、悬念钩子、身份认同来写标题
2. 内容结构师：开头3秒抓住注意力，中间信息密度高且易读，结尾引导行动
3. 平台调性专家：了解小红书用户画像（18-35岁年轻女性为主），用她们的语言说话
4. SEO意识：标签策略兼顾大词流量和长尾精准

## 你的写作铁律
- 绝不写空洞无信息量的废话
- 每一句都要有"获得感"或"情绪价值"
- 避免过于专业的术语，如需使用必须加口语化解释
- 严格遵守字数限制
- 互动引导必须自然，不能生硬

## 爆款标题公式（任选其一）
- 数字+结果："3步搞定XX"、"月省2000的XX方法"
- 反差+悬念："被骂了3年，终于翻红的XX"
- 身份+痛点："打工人必看！XX神器"
- 情绪+共鸣："谁懂啊！XX真的绝了"

""" + FEW_SHOT_EXAMPLES

def build_user_prompt(topic, style, tone, emoji_level, word_count, extra_info, target_audience):
    emoji_desc = {
        1: "几乎不使用emoji，纯文字",
        2: "少量emoji点缀，仅在关键处使用",
        3: "适中emoji，每段1-2个",
        4: "较多emoji，增强视觉节奏感",
        5: "大量emoji，每句都有，营造活泼氛围"
    }
    word_range = {
        "短文案（100-200字）": "100-200字",
        "中等（200-400字）": "200-400字",
        "长文案（400-600字）": "400-600字"
    }
    prompt = f"""请为以下主题创作一篇小红书爆款文案：

【主题】{topic}
【文案风格】{style}
【语气调性】{tone}
【目标受众】{target_audience}
【Emoji策略】{emoji_desc[emoji_level]}
【字数硬限制】正文必须在{word_range[word_count]}之间，不可超出
"""
    if extra_info:
        prompt += f"【补充要求】{extra_info}\n"

    prompt += """
请严格按以下结构输出，每个板块都不能省略：

## 🏷️ 标题方案（3个，注明使用了哪种标题公式）
标题1（公式：XX）：
标题2（公式：XX）：
标题3（公式：XX）：

## 📝 正文
（开头必须3秒内抓住注意力，中间高信息密度，结尾自然过渡到互动）

## 💬 互动引导（1-2句，自然不生硬）

## 🏷️ 标签策略（8-10个，前3个为大流量词，后面为长尾精准词）

## 📊 爆款预测
- 预估互动类型：（点赞/收藏/评论哪个会最高，为什么）
- 最佳发布时间：（根据内容类型推荐）
- 封面建议：（简述配图方向）
"""
    return prompt


def build_score_prompt(content):
    return f"""请以小红书运营专家的视角，对以下文案进行专业评分和改进建议：

{content}

请从以下5个维度打分（每项1-10分），并给出总分和具体改进建议：

## 评分维度
1. 标题吸引力（是否有点击欲望）：X/10
2. 内容信息密度（是否有干货/获得感）：X/10
3. 情绪价值（是否能引起共鸣）：X/10
4. 互动潜力（是否会引发评论/收藏）：X/10
5. 平台适配度（是否符合小红书调性）：X/10

## 总分：XX/50

## 💡 优化建议（列出最关键的2-3条可操作建议）
"""


def call_api(api_key, system_prompt, user_prompt):
    dashscope.api_key = api_key
    response = Generation.call(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        result_format="message",
    )
    if response.status_code == 200:
        return response.output.choices[0].message.content
    else:
        raise Exception(f"API错误 {response.code}: {response.message}")


# ===== 侧边栏 =====
with st.sidebar:
    st.markdown("### 🎨 创作参数")
    style = st.selectbox("文案风格", ["种草推荐", "产品测评", "教程攻略", "日常分享", "避雷吐槽", "好物合集"])
    tone = st.selectbox("语气调性", ["活泼俏皮", "专业理性", "温柔治愈", "犀利直白", "幽默搞笑"])
    target_audience = st.selectbox("目标受众", [
        "18-25岁学生党", "25-30岁职场新人", "30-35岁精致妈妈",
        "泛人群（不限定）"
    ])
    emoji_level = st.slider("Emoji 密度", min_value=1, max_value=5, value=3,
                            help="1=纯文字 3=适中 5=每句都有")
    word_count = st.selectbox("文案长度", ["短文案（100-200字）", "中等（200-400字）", "长文案（400-600字）"])

    st.markdown("---")
    st.markdown("### 📜 历史记录")
    if st.session_state.history:
        for i, item in enumerate(reversed(st.session_state.history[-5:])):
            st.markdown(f"""<div class="history-item">
                <strong>{item['topic']}</strong><br>
                <small>{item['style']} · {item['time']}</small>
            </div>""", unsafe_allow_html=True)
    else:
        st.caption("暂无历史记录")

# ===== 主区域 =====
col_input, col_output = st.columns([2, 3])

with col_input:
    st.markdown("### ✍️ 输入创作需求")
    topic = st.text_input("📌 主题/产品关键词",
                          placeholder="例如：夏季防晒霜推荐、自制冰美式、通勤穿搭")

    extra_info = st.text_area("💡 补充信息（可选）",
                              placeholder="例如：价格50元以内、适合油皮、学生党友好、想突出性价比",
                              height=100)

    st.markdown("""<div class="tip-box">
        💡 <strong>提示</strong>：关键词越具体，生成效果越好。<br>
        好的输入："油皮学生党 50元内防晒霜 不搓泥"<br>
        差的输入："防晒"
    </div>""", unsafe_allow_html=True)

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        generate_btn = st.button("✨ 生成文案", type="primary", use_container_width=True)
    with col_btn2:
        score_btn = st.button("📊 评分优化", use_container_width=True,
                              disabled=st.session_state.generated_result is None)

with col_output:
    st.markdown("### 📄 生成结果")

    if generate_btn:
        if not topic:
            st.error("请输入主题关键词")
        else:
            user_prompt = build_user_prompt(topic, style, tone, emoji_level,
                                           word_count, extra_info, target_audience)
            with st.spinner("🚀 正在创作中...AI正在调用爆款方法论"):
                try:
                    result = call_api(API_KEY, SYSTEM_PROMPT, user_prompt)
                    st.session_state.generated_result = result
                    st.session_state.score_result = None
                    st.session_state.history.append({
                        "topic": topic,
                        "style": style,
                        "time": datetime.now().strftime("%H:%M"),
                        "result": result
                    })
                except Exception as e:
                    st.error(f"生成失败：{str(e)}")

    if score_btn and st.session_state.generated_result:
        with st.spinner("📊 正在评分分析..."):
            try:
                score_prompt = build_score_prompt(st.session_state.generated_result)
                score_result = call_api(API_KEY, "你是小红书运营专家，擅长分析文案数据表现。", score_prompt)
                st.session_state.score_result = score_result
            except Exception as e:
                st.error(f"评分失败：{str(e)}")

    if st.session_state.generated_result:
        st.markdown(f"""<div class="result-card">{""}</div>""", unsafe_allow_html=True)
        st.markdown(st.session_state.generated_result)

        col_dl, col_copy = st.columns(2)
        with col_dl:
            st.download_button(
                label="📥 下载文案",
                data=st.session_state.generated_result,
                file_name=f"xiaohongshu_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with col_copy:
            st.download_button(
                label="📋 导出 Markdown",
                data=st.session_state.generated_result,
                file_name=f"xiaohongshu_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown",
                use_container_width=True,
            )

    if st.session_state.score_result:
        st.markdown("---")
        st.markdown("### 📊 文案质量评分")
        st.markdown(st.session_state.score_result)

    if not st.session_state.generated_result:
        st.markdown("""
        <div style="text-align:center; padding:3rem; color:#999;">
            <p style="font-size:3rem;">✨</p>
            <p>在左侧输入关键词，点击生成按钮</p>
            <p>AI 将为你创作专业级小红书文案</p>
        </div>
        """, unsafe_allow_html=True)

# 底部
st.markdown("---")
st.caption("📌 生成后可点击「评分优化」获取改进建议 · 关键词越具体效果越好")
