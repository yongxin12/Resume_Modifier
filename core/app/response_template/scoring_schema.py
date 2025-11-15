"""
Schema template for resume scoring with detailed sub-scores
"""

SCORING_TEMPLATE = {
    "overall_score": 0,  # 0-100, weighted average of all sub-scores
    "scores": {
        "keyword_matching": {
            "score": 0,  # 0-100
            "weight": 0.35,  # 35% weight
            "details": {
                "matched_keywords": [],
                "missing_keywords": [],
                "keyword_density": 0.0,
                "comment": ""
            }
        },
        "language_expression": {
            "score": 0,  # 0-100
            "weight": 0.35,  # 35% weight
            "details": {
                "grammar_quality": 0,  # 0-100
                "professional_tone": 0,  # 0-100
                "clarity": 0,  # 0-100
                "action_verbs_usage": 0,  # 0-100
                "comment": ""
            }
        },
        "ats_readability": {
            "score": 0,  # 0-100
            "weight": 0.30,  # 30% weight
            "details": {
                "format_compatibility": 0,  # 0-100
                "structure_clarity": 0,  # 0-100
                "parsing_friendliness": 0,  # 0-100
                "section_organization": 0,  # 0-100
                "comment": ""
            }
        }
    },
    "recommendations": [],
    "strengths": [],
    "weaknesses": []
}
