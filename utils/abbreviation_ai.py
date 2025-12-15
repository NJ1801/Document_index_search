# import google.generativeai as genai
# from config.settings import settings

# def expand_abbreviations(keyword: str) -> str:
#     """
#     Uses Gemini 2.5 Flash to expand abbreviations.
#     Example: HB → hemoglobin, ECG → electrocardiogram
#     """
#     try:
#         genai.configure(api_key=settings.GEMINI_API_KEY)

#         prompt = f"""
#         The user typed this medical/technical abbreviation: "{keyword}".
#         Expand it into full possible words. 
#         Only return keywords separated by commas, no sentences.
#         """

#         model = genai.GenerativeModel("gemini-2.5-flash")
#         response = model.generate_content(prompt)

#         expanded = response.text.strip()

#         print(f"[AI-EXPAND] expanded '{keyword}' → '{expanded}'")

#         return expanded
#     except Exception as e:
#         print(f"[AI-EXPAND-ERROR] {e}")
#         return keyword

import google.generativeai as genai
from config.settings import settings

def expand_abbreviations(keyword: str) -> str:
    """
    Expand abbreviations using Gemini 2.5 Flash.
    OUTPUT → always a comma-separated STRING.
    
    Example:
        Input: "HGB"
        Output: "HGB, Hemoglobin, Haemoglobin, HB"
    
    This preserves compatibility with your existing
    multi-keyword processing, which expects a string.
    """

    try:
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            #print("[AI-EXPAND-ERROR] Gemini API key missing")
            return keyword  # return original safely

        genai.configure(api_key=api_key)

        prompt = f"""
        The user entered this abbreviation: "{keyword}".
        Return ALL related expansions (full terms, variants, plural forms).
        Output format MUST be:
            word1, word2, word3, ...
        NO sentences. NO explanations.
        """

        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)

        raw = response.text.strip()
        #print(f"[AI-EXPAND] raw='{raw}'")

        # Convert the output to a clean list
        parts = [p.strip() for p in raw.split(",") if p.strip()]

        # Guarantee original term is included
        if keyword not in parts:
            parts.insert(0, keyword)

        # Convert list → comma-separated string (expected by search engine)
        final_string = ", ".join(parts)

        print(f"[AI-EXPAND] cleaned='{final_string}'")
        return final_string

    except Exception as e:
        print(f"[AI-EXPAND-ERROR] {e}")
        return keyword
