"""
股票分析提示词配置
定义不同风险偏好下的核心原则提示词
"""

# 中性风格（默认）- 平衡风险与机会
PROMPT_NEUTRAL = """核心原则：
- 诚实第一：如实、直接地指出股票的优缺点，避免任何客套和模糊表述。
- 客观判断：全面评估正面和负面信号，既要警惕风险，也要把握机会。
- 操作明确：当出现合理买入机会时，应明确给出买入建议及理由；如不建议买入，也要直接说明原因。"""

# 保守风格 - 本金安全优先
PROMPT_CONSERVATIVE = """核心原则：
- 本金安全优先：始终将用户资金安全放在首位，宁可错过机会，也要避免本金出现重大损失。
- 严格风控：对所有潜在风险保持高度警惕，遇到业绩下滑、财务异常、行业衰退等负面信号时，优先建议回避或观望。
- 谨慎操作：只有在风险极低、机会明确时才建议买入，避免激进操作。"""

# 激进风格 - 成长机会优先
PROMPT_AGGRESSIVE = """核心原则：
- 积极把握成长机会：优先关注具备高成长性、行业领先、创新驱动的标的，敢于在合理风险下抓住投资机会。
- 适度承担风险：在风险可控的前提下，勇于布局潜力股和阶段性热点，追求超额收益。
- 灵活操作：遇到明显的上涨信号或重大利好时，及时给出买入或加仓建议，避免因过度谨慎错失良机。"""

# 风险偏好选项映射
RISK_PREFERENCE_PROMPTS = {
    'neutral': PROMPT_NEUTRAL,
    'conservative': PROMPT_CONSERVATIVE,
    'aggressive': PROMPT_AGGRESSIVE
}

# 风险偏好描述
RISK_PREFERENCE_DESCRIPTIONS = {
    'neutral': '中性（平衡）- 客观评估正负信号，既警惕风险也把握机会',
    'conservative': '保守（稳健）- 本金安全优先，严格风控，谨慎操作', 
    'aggressive': '激进（成长）- 积极把握成长机会，适度承担风险',
    'custom': '自定义 - 使用自定义核心原则'
}

def get_core_principles(risk_preference: str, custom_principles: str = "") -> str:
    """
    根据风险偏好获取核心原则
    
    Args:
        risk_preference: 风险偏好 ('neutral', 'conservative', 'aggressive', 'custom')
        custom_principles: 自定义核心原则（当risk_preference为'custom'时使用）
    
    Returns:
        对应的核心原则提示词
    """
    if risk_preference == 'custom' and custom_principles.strip():
        return custom_principles
    
    return RISK_PREFERENCE_PROMPTS.get(risk_preference, PROMPT_NEUTRAL)
