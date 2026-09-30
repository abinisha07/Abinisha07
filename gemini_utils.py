import os
import base64

from dotenv import load_dotenv

load_dotenv()


# --------------------------------------------------
# GEMINI IMPORT
# --------------------------------------------------

try:
    import google.generativeai as genai
except Exception:
    genai = None


# --------------------------------------------------
# GEMINI SETTINGS
# --------------------------------------------------

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
    ""
)

MODEL_NAME = os.getenv(
    "GEMINI_MODEL",
    "gemini-1.5-flash"
)


# --------------------------------------------------
# CONFIGURE GEMINI
# --------------------------------------------------

if genai and GEMINI_API_KEY:
    genai.configure(
        api_key=GEMINI_API_KEY
    )


# --------------------------------------------------
# HOME FALLBACK
# --------------------------------------------------

def _fallback_home(data):

    budget = data["budget"]
    room = data["room"]

    return f"""
HOME INTERIOR PLAN

Budget: ₹{budget:,.0f}
Room: {room}
Style: {data['style']}

Suggested allocation:

• Furniture: ₹{budget * 0.40:,.0f}
• Lighting: ₹{budget * 0.15:,.0f}
• Fans/Electrical: ₹{budget * 0.15:,.0f}
• Decor: ₹{budget * 0.20:,.0f}
• Buffer: ₹{budget * 0.10:,.0f}

Recommended items:

1. {data['style']} {room} furniture.
2. {data['lights']} LED light(s).
3. {data['fans']} energy-efficient fan(s).
4. {data['tables']} table(s), if required.
5. Curtains, wall art and small decorations.

Platforms to compare:

• Amazon
• Flipkart
• IKEA

Note:
Prices are planning estimates.
Please verify current prices before purchasing.
"""


# --------------------------------------------------
# PARTY FALLBACK
# --------------------------------------------------

def _fallback_party(data):

    budget = data["budget"]

    return f"""
PARTY BUDGET PLAN

Event: {data['event_type']}
Guests: {data['guests']}
Budget: ₹{budget:,.0f}
Venue: {data['venue']}
Food Preference: {data['food_preference']}

Suggested allocation:

• Food/Catering: ₹{budget * 0.45:,.0f}
• Venue: ₹{budget * 0.20:,.0f}
• Decoration: ₹{budget * 0.15:,.0f}
• Entertainment: ₹{budget * 0.10:,.0f}
• Buffer: ₹{budget * 0.10:,.0f}

Planning ideas:

1. Compare catering options.
2. Select a venue suitable for the guest count.
3. Use simple and reusable decorations.
4. Keep some money for unexpected expenses.
5. Consider accommodation when required.

Platforms to check:

• Swiggy
• Zomato
• OYO

Note:
Vendor availability and prices should be verified before booking.
"""


# --------------------------------------------------
# JEWELRY FALLBACK
# --------------------------------------------------

def _fallback_jewelry(data):

    budget = data["budget"]

    color = data.get(
        "outfit_color"
    ) or "your outfit color"

    return f"""
JEWELRY RECOMMENDATION

Occasion: {data['occasion']}
Style: {data['style']}
Outfit Color: {color}
Budget: ₹{budget:,.0f}

Suggested allocation:

• Main Jewelry: ₹{budget * 0.55:,.0f}
• Earrings: ₹{budget * 0.20:,.0f}
• Bracelet/Bangle: ₹{budget * 0.15:,.0f}
• Buffer: ₹{budget * 0.10:,.0f}

Suggestions:

1. Select jewelry that complements {color}.
2. For an elegant style, consider a simple necklace with matching earrings.
3. For festive occasions, consider traditional or statement pieces.
4. Compare options across Amazon and Flipkart.
5. Check material, size and return policy before buying.

Note:
These are style recommendations, not live product listings.
"""


# --------------------------------------------------
# FALLBACK FUNCTION
# --------------------------------------------------

def fallback(category, data):

    if category == "home":
        return _fallback_home(data)

    if category == "party":
        return _fallback_party(data)

    return _fallback_jewelry(data)


# --------------------------------------------------
# BUILD GEMINI PROMPT
# --------------------------------------------------

def build_prompt(category, data):

    common = """
You are PocketSmart AI,
a budget planning and recommendation assistant.

Return a clear and practical answer
using Indian Rupees (₹).

Respect the user's maximum budget.

Do not claim live prices or availability.

Mention that platform and vendor
details must be verified.

Use headings and numbered recommendations.
"""


    # --------------------------------------------------
    # HOME PROMPT
    # --------------------------------------------------

    if category == "home":

        task = f"""
Create a home interior shopping plan.

Budget: ₹{data['budget']}
Room: {data['room']}
Style: {data['style']}
Lights: {data['lights']}
Fans: {data['fans']}
Tables: {data['tables']}

Extra requirements:
{data.get('extra', '')}

Compare suitable options conceptually
from Amazon, Flipkart and IKEA.
"""


    # --------------------------------------------------
    # PARTY PROMPT
    # --------------------------------------------------

    elif category == "party":

        task = f"""
Create a party budget plan.

Budget: ₹{data['budget']}
Guests: {data['guests']}
Event: {data['event_type']}
Venue: {data['venue']}
Food preference: {data['food_preference']}

Extra requirements:
{data.get('extra', '')}

Discuss:

• Food
• Venue
• Decoration
• Entertainment

Mention Swiggy, Zomato and OYO only
as examples of platforms/services to check.
"""


    # --------------------------------------------------
    # JEWELRY PROMPT
    # --------------------------------------------------

    else:

        task = f"""
Create jewelry recommendations.

Budget: ₹{data['budget']}
Occasion: {data['occasion']}
Style: {data['style']}
Outfit color: {data.get('outfit_color', '')}

Extra requirements:
{data.get('extra', '')}

Suggest jewelry combinations and explain
why they suit the occasion and outfit.

Mention Amazon and Flipkart
as platforms to compare.
"""


    return common + task


# --------------------------------------------------
# GENERATE GEMINI RECOMMENDATION
# --------------------------------------------------

def generate_recommendation(
    category,
    data,
    image_bytes=None
):

    # If Gemini is not configured,
    # use the built-in fallback.
    if not (
        genai
        and GEMINI_API_KEY
    ):
        return fallback(
            category,
            data
        )


    try:

        # Create Gemini model
        model = genai.GenerativeModel(
            MODEL_NAME
        )

        # Create prompt
        prompt = build_prompt(
            category,
            data
        )

        contents = [prompt]


        # --------------------------------------------------
        # OPTIONAL OUTFIT IMAGE
        # --------------------------------------------------

        if image_bytes:

            image_part = {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(
                    image_bytes
                ).decode("utf-8")
            }

            contents.append(
                image_part
            )

            contents[0] += """
            
An outfit image is attached.

Use the image only to discuss
broad color and style coordination.
"""


        # --------------------------------------------------
        # SEND REQUEST TO GEMINI
        # --------------------------------------------------

        response = model.generate_content(
            contents
        )


        # Get generated text
        result_text = getattr(
            response,
            "text",
            None
        )


        # If Gemini returned text
        if result_text:

            return result_text.strip()


        # Otherwise use fallback
        return fallback(
            category,
            data
        )


    except Exception as exc:

        # If Gemini fails,
        # keep the application working.
        return (
            fallback(
                category,
                data
            )
            + f"""

[Gemini fallback used:
{type(exc).__name__}]
"""
        )