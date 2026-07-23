import streamlit as st
import dashscope
from dashscope import Generation

st.set_page_config(page_title="AI 小红书文案生成器", page_icon="📝", layout="centered")

st.title("📝 AI 小红书文案生成器")
st.caption("输入关键词，一键生成小红书风格文案")

# 侧边栏配置
with st.sidebar:
    st.header("⚙️ 设置")
    api_key = st.text_input("通义千问 API Key", type="password")
    style = st.selectbox("文案风格", ["种草推荐", "产品测评", "教程攻略", "日常分享"])
    tone = st.selectbox("语气", ["活泼俏皮", "专业理性", "温柔治愈"])
    emoji_level = st.slider("Emoji 密度", min_value=1, max_value=5, value=3)
    word_count = st.selectbox("文案长度", ["短文案（100-200字）", "中等（200-400字）", "长文案（400-600字）"])

# 主区域
topic = st.text_input("📌 输入主题/产品关键词", placeholder="例如：夏季防晒霜推荐、自制冰美式、通勤穿搭")
extra_info = st.text_area("💡 补充信息（可选）", placeholder="例如：价格50元以内、适合油皮、学生党友好", height=80)

SYSTEM_PROMPT = """你是一位资深小红书文案创作者，擅长写出高互动、高收藏的爆款笔记。
你的目标读者是18-35岁的年轻用户，以女性为主。

你的写作特点：
1. 标题吸引眼球，善用数字、emoji和悬念
2. 正文结构清晰，善用分段和小标题
3. 语言贴近年轻用户，自然不做作，避免过于专业的术语（如需使用请加通俗解释）
4. 结尾必须有互动引导语（引导点赞、收藏或评论）
5. 标签精准，覆盖热门话题
6. 严格遵守用户要求的字数范围，不得超出"""


def build_user_prompt(topic, style, tone, emoji_level, word_count, extra_info):
    emoji_desc = {1: "极少使用emoji", 2: "少量emoji点缀", 3: "适中emoji", 4: "较多emoji", 5: "大量emoji，每句都有"}
    prompt = f"""请为以下主题生成一篇小红书文案：

【主题】{topic}
【风格】{style}
【语气】{tone}
【Emoji要求】{emoji_desc[emoji_level]}
【字数要求】{word_count}
"""
    if extra_info:
        prompt += f"【补充信息】{extra_info}\n"

    prompt += """
请严格按以下格式输出，正文字数必须在要求范围内：
## 标题（提供3个备选）
标题1：
标题2：
标题3：

## 正文

## 互动引导（1句话，引导点赞/收藏/评论）

## 推荐标签（5-8个）
"""
    return prompt


if st.button("✨ 生成文案", type="primary", use_container_width=True):
    if not api_key:
        st.error("请在左侧输入通义千问 API Key")
    elif not topic:
        st.error("请输入主题关键词")
    else:
        dashscope.api_key = api_key
        user_prompt = build_user_prompt(topic, style, tone, emoji_level, word_count, extra_info)

        with st.spinner("正在生成文案..."):
            try:
                response = Generation.call(
                    model="qwen-plus",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    result_format="message",
                )

                if response.status_code == 200:
                    result = response.output.choices[0].message.content
                    st.markdown("---")
                    st.markdown("### 📄 生成结果")
                    st.markdown(result)
                    st.markdown("---")
                    st.download_button(
                        label="📋 复制到剪贴板（下载文本）",
                        data=result,
                        file_name="xiaohongshu_copy.txt",
                        mime="text/plain",
                    )
                else:
                    st.error(f"API 调用失败：{response.code} - {response.message}")
            except Exception as e:
                st.error(f"发生错误：{str(e)}")

# 页脚
st.markdown("---")
st.caption("💡 提示：生成效果取决于关键词的具体程度，越具体越好。")
