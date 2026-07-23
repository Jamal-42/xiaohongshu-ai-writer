import os
import json
import sqlite3
import streamlit as st
import dashscope
from dashscope import Generation
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "user_data.db")
POSTS_PATH = os.path.join(os.path.dirname(__file__), "data", "trending_posts.json")

# ===== 数据库初始化 =====
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT, style TEXT, tone TEXT, audience TEXT,
        final_result TEXT, score INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS preferences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE, value TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        history_id INTEGER, action TEXT, detail TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()
    conn.close()

def save_history(topic, style, tone, audience, result, score):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO history (topic, style, tone, audience, final_result, score) VALUES (?, ?, ?, ?, ?, ?)",
              (topic, style, tone, audience, result, score))
    history_id = c.lastrowid
    conn.commit()
    conn.close()
    return history_id

def save_feedback(history_id, action, detail):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO feedback (history_id, action, detail) VALUES (?, ?, ?)",
              (history_id, action, detail))
    conn.commit()
    conn.close()

# PLACEHOLDER_MORE_DB

def get_user_preferences():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT key, value FROM preferences")
    prefs = {row[0]: row[1] for row in c.fetchall()}
    conn.close()
    return prefs

def update_preference(key, value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO preferences (key, value, updated_at) VALUES (?, ?, ?)",
              (key, value, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_history_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT style, COUNT(*) FROM history GROUP BY style ORDER BY COUNT(*) DESC LIMIT 3")
    top_styles = c.fetchall()
    c.execute("SELECT AVG(score) FROM history WHERE score > 0")
    avg_score = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM history")
    total = c.fetchone()[0]
    conn.close()
    return {"top_styles": top_styles, "avg_score": round(avg_score, 1), "total": total}

def get_recent_history(limit=10):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, topic, style, score, created_at FROM history ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows


# ===== 案例库检索 =====
def load_trending_posts():
    with open(POSTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def retrieve_relevant_posts(topic, style, n=3):
    posts = load_trending_posts()
    scored = []
    topic_lower = topic.lower()
    for post in posts:
        score = 0
        if post["style"] == style:
            score += 3
        if any(kw in topic_lower for kw in [post["category"], post["style"]]):
            score += 2
        if any(kw in post["title"].lower() or kw in post["content"].lower() for kw in topic_lower.split()):
            score += 2
        engagement = post["metrics"]["likes"] + post["metrics"]["collects"] * 1.5 + post["metrics"]["comments"] * 2
        score += engagement / 50000
        scored.append((score, post))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:n]]


# ===== 规则评分引擎 =====
def rule_based_score(content):
    scores = {"title": 0, "density": 0, "emotion": 0, "interaction": 0, "platform": 0}
    lines = content.split("\n")
    title_section = ""
    body_section = ""
    interaction_section = ""
    current = None
    for line in lines:
        if "标题" in line and "##" in line:
            current = "title"
        elif "正文" in line and "##" in line:
            current = "body"
        elif "互动" in line and "##" in line:
            current = "interaction"
        elif "##" in line:
            current = "other"
        else:
            if current == "title":
                title_section += line
            elif current == "body":
                body_section += line
            elif current == "interaction":
                interaction_section += line

    # 标题评分
    title_score = 5
    if any(c.isdigit() for c in title_section):
        title_score += 1.5
    if any(e in title_section for e in ["！", "‼️", "!!", "？"]):
        title_score += 1
    if any(e in title_section for e in ["💰", "✨", "🔥", "❤️", "😭", "☀️"]):
        title_score += 1
    if len(title_section) > 30:
        title_score += 0.5
    scores["title"] = min(title_score, 10)

    # 信息密度评分
    density_score = 5
    if any(sym in body_section for sym in ["✅", "❌", "1️⃣", "Step", "步骤"]):
        density_score += 2
    if any(c.isdigit() for c in body_section):
        density_score += 1
    if len(body_section) > 100:
        density_score += 1
    if "：" in body_section or "=" in body_section:
        density_score += 1
    scores["density"] = min(density_score, 10)

    # 情绪价值评分
    emotion_score = 5
    emotion_markers = ["😭", "🥹", "❤️", "绝了", "真的", "谁懂", "救命", "哭了", "爱了", "神器", "天花板", "yyds"]
    emotion_count = sum(1 for m in emotion_markers if m in body_section)
    emotion_score += min(emotion_count * 1.2, 4)
    if "…" in body_section or "！" in body_section:
        emotion_score += 0.5
    scores["emotion"] = min(emotion_score, 10)

    # 互动潜力评分
    interact_score = 5
    if interaction_section:
        interact_score += 2
    interact_cues = ["评论", "收藏", "点赞", "关注", "扣1", "交作业", "你们", "姐妹", "宝子"]
    interact_count = sum(1 for c in interact_cues if c in content)
    interact_score += min(interact_count * 1, 3)
    scores["interaction"] = min(interact_score, 10)

    # 平台适配度评分
    platform_score = 5
    if "#" in content:
        tag_count = content.count("#")
        platform_score += min(tag_count * 0.3, 2)
    emoji_count = sum(1 for c in content if ord(c) > 0x1F000)
    platform_score += min(emoji_count * 0.15, 2)
    if len(body_section) < 800:
        platform_score += 1
    scores["platform"] = min(platform_score, 10)

    total = sum(scores.values())
    return scores, round(total, 1)

# PLACEHOLDER_AGENT_CORE

# ===== Agent 多轮迭代核心 =====
def call_api_stream(api_key, system_prompt, user_prompt):
    dashscope.api_key = api_key
    responses = Generation.call(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        result_format="message",
        stream=True,
        incremental_output=True,
    )
    for chunk in responses:
        if chunk.status_code == 200:
            content = chunk.output.choices[0].message.content
            if content:
                yield content
        else:
            raise Exception(f"API错误 {chunk.code}: {chunk.message}")


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


def build_system_prompt(relevant_posts, user_prefs):
    examples_text = ""
    for i, post in enumerate(relevant_posts, 1):
        examples_text += f"""
【参考案例{i}】(点赞{post['metrics']['likes']} 收藏{post['metrics']['collects']} 评论{post['metrics']['comments']})
标题：{post['title']}
正文：{post['content']}
标签：{' '.join(post['tags'])}
"""
    pref_text = ""
    if user_prefs:
        if user_prefs.get("preferred_tone"):
            pref_text += f"\n用户历史偏好语气：{user_prefs['preferred_tone']}"
        if user_prefs.get("avg_score_feedback"):
            pref_text += f"\n用户历史平均满意度：{user_prefs['avg_score_feedback']}/10"

    return f"""你是一位年收入百万的小红书头部博主，精通爆款内容创作方法论。
你深谙小红书算法推荐机制和用户心理。

## 你的核心能力
1. 标题党大师：用数字冲击、情绪共鸣、悬念钩子、身份认同写标题
2. 内容结构师：开头3秒抓住注意力，中间高信息密度，结尾引导行动
3. 平台调性专家：18-35岁年轻女性用户画像，用她们的语言说话
4. SEO意识：标签策略兼顾大词流量和长尾精准

## 写作铁律
- 每一句都有"获得感"或"情绪价值"，绝不写废话
- 避免专业术语，如需使用必须加口语化解释
- 严格遵守字数限制
- 互动引导必须自然

## 爆款标题公式
- 数字+结果："3步搞定XX"、"月省2000的XX方法"
- 反差+悬念："被骂了3年，终于翻红的XX"
- 身份+痛点："打工人必看！XX神器"
- 情绪+共鸣："谁懂啊！XX真的绝了"

## 以下是与当前主题最相关的真实爆款案例（来自数据库检索），请深度学习其写作模式：
{examples_text}
{pref_text}"""


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
请严格按以下结构输出：

## 🏷️ 标题方案（3个，标注公式）
标题1（公式：XX）：
标题2（公式：XX）：
标题3（公式：XX）：

## 📝 正文

## 💬 互动引导（1-2句）

## 🏷️ 标签策略（8-10个，前3个大流量词，后面长尾精准词）
"""
    return prompt


def build_critique_prompt(draft, scores):
    return f"""作为小红书内容质量审核官，请严格评审以下文案初稿，指出具体问题并给出修改指令：

【文案初稿】
{draft}

【规则引擎评分】
- 标题吸引力：{scores['title']:.1f}/10
- 信息密度：{scores['density']:.1f}/10
- 情绪价值：{scores['emotion']:.1f}/10
- 互动潜力：{scores['interaction']:.1f}/10
- 平台适配度：{scores['platform']:.1f}/10

请输出：
1. 最严重的2-3个问题（具体指出哪里不好）
2. 针对每个问题的修改指令（不要重写，只给指令）
3. 评分最低的维度应如何提升"""


def build_refine_prompt(draft, critique):
    return f"""请根据以下审稿意见，对文案进行精修优化。保留原有格式结构，只改进内容质量：

【原始文案】
{draft}

【审稿意见】
{critique}

请输出优化后的完整文案（保持原格式结构不变）。重点提升审稿中指出的薄弱环节。"""


def agent_generate(topic, style, tone, emoji_level, word_count, extra_info, target_audience, status_container):
    """Agent 核心：生成 → 自评 → 优化 → 输出"""
    relevant_posts = retrieve_relevant_posts(topic, style)
    user_prefs = get_user_preferences()
    system_prompt = build_system_prompt(relevant_posts, user_prefs)
    user_prompt = build_user_prompt(topic, style, tone, emoji_level, word_count, extra_info, target_audience)

    # === Round 1: 初始生成 ===
    with status_container:
        st.markdown("#### 🔄 Agent 迭代过程")
        st.markdown("**Round 1** · 生成初稿...")
        r1_area = st.empty()

    draft = ""
    for chunk in call_api_stream(API_KEY, system_prompt, user_prompt):
        draft += chunk
        r1_area.markdown(draft)

    # === 规则评分 ===
    scores, total_score = rule_based_score(draft)
    with status_container:
        st.markdown(f"**评分** · 初稿得分：**{total_score}/50**")

    # === Round 2: 自我审稿 ===
    with status_container:
        st.markdown("**Round 2** · AI 自我审稿...")
        r2_area = st.empty()

    critique_prompt = build_critique_prompt(draft, scores)
    critique = ""
    for chunk in call_api_stream(API_KEY, "你是小红书内容质量审核官，擅长发现文案的薄弱环节。", critique_prompt):
        critique += chunk
        r2_area.markdown(critique)

    # === Round 3: 精修优化 ===
    with status_container:
        st.markdown("**Round 3** · 根据审稿意见精修...")
        r3_area = st.empty()

    refine_prompt = build_refine_prompt(draft, critique)
    refined = ""
    for chunk in call_api_stream(API_KEY, system_prompt, refine_prompt):
        refined += chunk
        r3_area.markdown(refined)

    # === 终稿评分 ===
    final_scores, final_total = rule_based_score(refined)
    with status_container:
        improvement = final_total - total_score
        direction = "📈" if improvement > 0 else "➡️"
        st.markdown(f"**最终得分：{final_total}/50** {direction} (较初稿{'+'if improvement>0 else ''}{improvement:.1f})")

    return draft, critique, refined, scores, total_score, final_scores, final_total, relevant_posts

# PLACEHOLDER_UI

# ===== 初始化 =====
init_db()
st.set_page_config(page_title="AI 小红书文案生成器", page_icon="📝", layout="wide")

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
    .main-header h1 { color: white; font-size: 2.2rem; margin-bottom: 0.3rem; }
    .main-header p { color: rgba(255,255,255,0.9); font-size: 1rem; }
    .score-card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .score-bar {
        height: 8px;
        border-radius: 4px;
        background: #eee;
        margin-top: 4px;
    }
    .score-fill {
        height: 100%;
        border-radius: 4px;
        background: linear-gradient(90deg, #ff2442, #ff6b81);
    }
    .tip-box {
        background: #fff8f0;
        border-left: 4px solid #ff9500;
        padding: 0.8rem 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }
    .ref-post {
        background: #f0f7ff;
        border-radius: 8px;
        padding: 0.6rem 0.8rem;
        margin: 0.3rem 0;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>📝 AI 小红书文案生成器</h1>
    <p>Agent 多轮迭代 · 爆款案例库检索 · 规则引擎评分 · 个性化学习</p>
</div>
""", unsafe_allow_html=True)

if "agent_result" not in st.session_state:
    st.session_state.agent_result = None

# ===== 侧边栏 =====
with st.sidebar:
    st.markdown("### 🎨 创作参数")
    style = st.selectbox("文案风格", ["种草推荐", "产品测评", "教程攻略", "日常分享", "避雷吐槽", "好物合集"])
    tone = st.selectbox("语气调性", ["活泼俏皮", "专业理性", "温柔治愈", "犀利直白", "幽默搞笑"])
    target_audience = st.selectbox("目标受众", [
        "18-25岁学生党", "25-30岁职场新人", "30-35岁精致妈妈", "泛人群（不限定）"
    ])
    emoji_level = st.slider("Emoji 密度", min_value=1, max_value=5, value=3)
    word_count = st.selectbox("文案长度", ["短文案（100-200字）", "中等（200-400字）", "长文案（400-600字）"])

    st.markdown("---")
    st.markdown("### 📊 使用统计")
    stats = get_history_stats()
    if stats["total"] > 0:
        st.metric("累计生成", f"{stats['total']} 篇")
        st.metric("平均质量分", f"{stats['avg_score']}/50")
        if stats["top_styles"]:
            st.caption(f"最常用风格：{stats['top_styles'][0][0]}")
    else:
        st.caption("开始创作后这里会显示你的使用数据")

    st.markdown("---")
    st.markdown("### 📜 历史记录")
    history = get_recent_history(5)
    if history:
        for h in history:
            st.markdown(f"**{h[1]}** · {h[2]} · {h[3]}/50")
            st.caption(h[4][:16] if h[4] else "")
    else:
        st.caption("暂无记录")

# PLACEHOLDER_MAIN

# ===== 主区域 =====
col_input, col_output = st.columns([2, 3])

with col_input:
    st.markdown("### ✍️ 创作需求")
    topic = st.text_input("📌 主题/产品关键词",
                          placeholder="例如：油皮学生党 50元内防晒霜 不搓泥")
    extra_info = st.text_area("💡 补充信息（可选）",
                              placeholder="价格区间、适用人群、核心卖点、想突出的特色",
                              height=80)

    st.markdown("""<div class="tip-box">
        💡 <strong>关键词越具体，Agent检索到的参考案例越精准</strong><br>
        好："油皮学生党 50元内防晒霜 不搓泥 军训用"<br>
        差："防晒"
    </div>""", unsafe_allow_html=True)

    generate_btn = st.button("🤖 Agent 智能创作（3轮迭代）", type="primary", use_container_width=True)

    # 反馈区域
    if st.session_state.agent_result:
        st.markdown("---")
        st.markdown("### 💬 反馈（影响未来生成）")
        satisfaction = st.slider("对本次结果满意度", 1, 10, 7, key="satisfaction")
        feedback_text = st.text_input("哪里需要改进？", placeholder="比如：标题不够吸引、正文太长、语气太正式")
        if st.button("提交反馈", use_container_width=True):
            result = st.session_state.agent_result
            save_feedback(result.get("history_id", 0), "rating", str(satisfaction))
            if feedback_text:
                save_feedback(result.get("history_id", 0), "text_feedback", feedback_text)
                update_preference("last_feedback", feedback_text)
            if satisfaction >= 7:
                update_preference("preferred_tone", tone)
            st.success("反馈已记录，将影响后续生成质量 ✅")

with col_output:
    if generate_btn:
        if not topic:
            st.error("请输入主题关键词")
        elif not API_KEY:
            st.error("未配置 API Key，请在 .env 文件中设置 DASHSCOPE_API_KEY")
        else:
            status_container = st.container()
            try:
                draft, critique, refined, scores, total, final_scores, final_total, ref_posts = agent_generate(
                    topic, style, tone, emoji_level, word_count, extra_info, target_audience, status_container
                )

                st.markdown("---")
                st.markdown("### 📄 最终文案")
                st.markdown(refined)

                # 评分可视化
                st.markdown("---")
                st.markdown("### 📊 质量评分对比")
                dims = ["标题吸引力", "信息密度", "情绪价值", "互动潜力", "平台适配度"]
                keys = ["title", "density", "emotion", "interaction", "platform"]
                score_cols = st.columns(5)
                for i, (dim, key) in enumerate(zip(dims, keys)):
                    with score_cols[i]:
                        before = scores[key]
                        after = final_scores[key]
                        delta = after - before
                        st.metric(dim, f"{after:.1f}", delta=f"{delta:+.1f}")

                # 参考案例展示
                st.markdown("---")
                st.markdown("### 📚 本次检索的参考案例")
                for post in ref_posts:
                    st.markdown(f"""<div class="ref-post">
                        <strong>{post['title']}</strong><br>
                        <small>👍{post['metrics']['likes']} 📌{post['metrics']['collects']} 💬{post['metrics']['comments']} · {post['style']}</small>
                    </div>""", unsafe_allow_html=True)

                # 导出
                st.markdown("---")
                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    st.download_button("📥 下载最终文案", refined,
                                       file_name=f"xhs_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                                       mime="text/plain", use_container_width=True)
                with col_dl2:
                    full_report = f"# 初稿\n{draft}\n\n# 审稿意见\n{critique}\n\n# 最终文案\n{refined}"
                    st.download_button("📋 下载完整迭代报告", full_report,
                                       file_name=f"xhs_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                                       mime="text/markdown", use_container_width=True)

                # 存入数据库
                history_id = save_history(topic, style, tone, target_audience, refined, int(final_total))
                st.session_state.agent_result = {
                    "history_id": history_id,
                    "refined": refined,
                    "final_total": final_total
                }

            except Exception as e:
                st.error(f"Agent 执行出错：{str(e)}")

    elif not st.session_state.agent_result:
        st.markdown("""
        <div style="text-align:center; padding:3rem; color:#999;">
            <p style="font-size:3rem;">🤖</p>
            <p><strong>Agent 智能创作流程</strong></p>
            <p>Round 1：基于案例库检索生成初稿</p>
            <p>Round 2：AI 自我审稿，发现问题</p>
            <p>Round 3：根据审稿意见精修输出终稿</p>
            <br>
            <p style="font-size:0.85rem; color:#bbb;">输入关键词，点击按钮开始</p>
        </div>
        """, unsafe_allow_html=True)
