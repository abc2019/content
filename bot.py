import os
import json
import asyncio
import logging
from datetime import datetime, time
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import anthropic
from openai import OpenAI
import requests
from io import BytesIO
import base64

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== SOZLAMALAR ====================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CLAUDE_KEY = os.environ.get("CLAUDE_API_KEY", "")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
CHAT_ID = int(os.environ.get("CHAT_ID", "1002821803"))
TIMEZONE = "Asia/Tashkent"
SEND_HOUR = 9

claude = anthropic.Anthropic(api_key=CLAUDE_KEY)
openai_client = OpenAI(api_key=OPENAI_KEY)

# ==================== SHOHONA BREND ====================
SHOHONA_INFO = """
Sen SHOHONA brendining professional SMM mutaxassisisan.
Brend: SHOHONA — "Halal and Excellent"
Instagram: @shohona_taom | Tel: 010-5586-1916 | bit.ly/4qAoFui
Joylashuv: Koreya, Hwaseong-si
Auditoriya: Koreyadagi o'zbeklar, ruslar, markaziy osiyoliklar
Mahsulotlar: Palov ₩5,650 | Lag'mon ₩6,950 | Qozon Kabob ₩8,250 | Mastava ₩4,000 | Sho'rva ₩4,000 | va boshqalar
Xususiyatlar: 100% Halol, Konservantsiz, 3 daqiqada tayyor, Made in Korea
"""

AZANMARKET_INFO = """
Sen AzanMarket brendining professional SMM mutaxassisisan.
Brend: AzanMarket — Halol oziq-ovqat onlayn do'koni
Website: azanmarket.com | Tel: 010-5586-1916
Joylashuv: Koreya
Auditoriya: Koreyadagi o'zbeklar, ruslar, markaziy osiyoliklar
Xususiyatlar: 100% Halol mahsulotlar, Koreya bo'ylab yetkazib berish, BEPUL yetkazish
"""

# ==================== 30 KUNLIK KALENDAR ====================
CALENDAR = [
    {"mavzu": "Kun hikmati", "tavsif": "Motivatsion hikmat"},
    {"mavzu": "Kun taomi", "tavsif": "Shohona mahsulot tavsiyasi"},
    {"mavzu": "Hajviya", "tavsif": "Kulgili kontent"},
    {"mavzu": "Sog'liq fakti", "tavsif": "Sog'liq va taom haqida fakt"},
    {"mavzu": "Mahsulot reklama", "tavsif": "Shohona mahsulot"},
    {"mavzu": "Kun hikmati", "tavsif": "Motivatsion hikmat"},
    {"mavzu": "Kun taomi", "tavsif": "Shohona mahsulot tavsiyasi"},
    {"mavzu": "Hajviya", "tavsif": "Kulgili kontent"},
    {"mavzu": "Sog'liq fakti", "tavsif": "Sog'liq va taom haqida fakt"},
    {"mavzu": "Mahsulot reklama", "tavsif": "Shohona mahsulot"},
    {"mavzu": "Kun hikmati", "tavsif": "Motivatsion hikmat"},
    {"mavzu": "Kun taomi", "tavsif": "Shohona mahsulot tavsiyasi"},
    {"mavzu": "Hajviya", "tavsif": "Kulgili kontent"},
    {"mavzu": "Sog'liq fakti", "tavsif": "Sog'liq va taom haqida fakt"},
    {"mavzu": "Mahsulot reklama", "tavsif": "Shohona mahsulot"},
    {"mavzu": "Kun hikmati", "tavsif": "Motivatsion hikmat"},
    {"mavzu": "Kun taomi", "tavsif": "Shohona mahsulot tavsiyasi"},
    {"mavzu": "Hajviya", "tavsif": "Kulgili kontent"},
    {"mavzu": "Sog'liq fakti", "tavsif": "Sog'liq va taom haqida fakt"},
    {"mavzu": "Mahsulot reklama", "tavsif": "Shohona mahsulot"},
    {"mavzu": "Kun hikmati", "tavsif": "Motivatsion hikmat"},
    {"mavzu": "Kun taomi", "tavsif": "Shohona mahsulot tavsiyasi"},
    {"mavzu": "Hajviya", "tavsif": "Kulgili kontent"},
    {"mavzu": "Sog'liq fakti", "tavsif": "Sog'liq va taom haqida fakt"},
    {"mavzu": "Mahsulot reklama", "tavsif": "Shohona mahsulot"},
    {"mavzu": "Kun hikmati", "tavsif": "Motivatsion hikmat"},
    {"mavzu": "Kun taomi", "tavsif": "Shohona mahsulot tavsiyasi"},
    {"mavzu": "Hajviya", "tavsif": "Kulgili kontent"},
    {"mavzu": "Sog'liq fakti", "tavsif": "Sog'liq va taom haqida fakt"},
    {"mavzu": "Mahsulot reklama", "tavsif": "Shohona mahsulot"},
]

# ==================== USER STATE ====================
user_states = {}

def get_state(user_id):
    if user_id not in user_states:
        user_states[user_id] = {"brend": None, "mavzu": None, "rasm": None, "step": "start"}
    return user_states[user_id]

def set_state(user_id, **kwargs):
    state = get_state(user_id)
    state.update(kwargs)

# ==================== CLAUDE FUNKSIYALAR ====================
def claude_generate(prompt, system):
    resp = claude.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2000,
        system=system,
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.content[0].text

def translate_to_russian(text):
    return claude_generate(
        f"Quyidagi O'zbek matnni Ruscha tarjima qil. Faqat tarjimani ber, boshqa hech narsa yozma:\n\n{text}",
        "Sen professional tarjimon san. Faqat tarjima ber."
    )

def generate_hajviya():
    return claude_generate(
        """Shohona brendiga aloqador kulgili, hazil-mazax story matni yoz.
        Mavzular: Koreyadagi o'zbek hayoti, ona yurt sog'inch, tez-tez Shohona yeyish.
        Format:
        🇺🇿 O'ZBEKCHA:
        [Story matni]
        
        🇷🇺 RUSCHA:
        [Tarjima]""",
        SHOHONA_INFO
    )

def generate_story(brend, mavzu, matn=None, rasm_base64=None):
    info = SHOHONA_INFO if brend == "shohona" else AZANMARKET_INFO

    if mavzu == "hajviya":
        return generate_hajviya()

    if mavzu == "mahsulot_reklama" and brend == "shohona":
        return claude_generate(
            "Shohona mahsulotlari uchun 5 ta yangi Instagram post g'oyasi va promptlarini yoz.",
            info
        )

    content = []
    if rasm_base64:
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/jpeg", "data": rasm_base64}
        })

    # Rasm berilgan — rasmdagi matnni o'qib story yaratsin
    if rasm_base64 and not matn:
        prompt_text = """Bu rasmdagi barcha matnni o'qi.
Agar matn bo'lsa — aynan o'sha matnni ishlatib story yarat.
Agar matn bo'lmasa — rasmni tavsiflab story yarat.

MUHIM: Qo'shimcha narsa yozma. Faqat quyidagi format:
🇺🇿 O'ZBEKCHA:
[aynan rasmdagi matn yoki tavsif]

🇷🇺 RUSCHA:
[ruscha tarjima]"""

    # Foydalanuvchi matn bergan — aynan o'shani ishlatamiz
    elif matn:
        prompt_text = f"""Quyidagi matnni aynan o'zi bilan ishlatib Instagram Story formatlash:

Matn: "{matn}"

Ruscha tarjima qil va quyidagi formatda chiqar:
🇺🇿 O'ZBEKCHA:
{matn}

🇷🇺 RUSCHA:
[Ruscha tarjima]

MUHIM: O'zbekcha qismga hech narsa qo'shma, aynan yuqoridagi matnni yoz."""

    # Na rasm na matn — o'zi yaratsin
    else:
        mavzu_map = {
            "kun_hikmati": "Koreyadagi o'zbeklar uchun motivatsion kun hikmati",
            "kun_taomi": "Shohona tayyor taomlardan birini tavsiya qiluvchi story",
            "sogliq_fakti": "Sog'liq va taom haqida qiziqarli fakt",
            "mahsulot_reklama": "Shohona mahsulot reklama story",
        }
        prompt_text = f"""Quyidagi mavzu uchun Instagram Story matni yoz:
Mavzu: {mavzu_map.get(mavzu, mavzu)}

Format (AYNAN SHU FORMATDA YOZ):
🇺🇿 O'ZBEKCHA:
[Story matni - 2-3 ta gap, emoji bilan]

🇷🇺 RUSCHA:
[Tarjima]"""

    content.append({"type": "text", "text": prompt_text})
    
    resp = claude.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        system=info,
        messages=[{"role": "user", "content": content}]
    )
    return resp.content[0].text

# ==================== DALL-E RASM ====================
def create_collage(rasmlar_b64, bg_color=(245, 245, 245)):
    """Bir nechta rasmni bir xil background bilan birlashtirib collage yasaydi"""
    from PIL import Image, ImageOps
    import io

    SIZE = 1024
    CELL_PAD = 12  # Rasmlar orasidagi bo'shliq
    BG = Image.new("RGB", (SIZE, SIZE), bg_color)

    imgs = []
    for b64 in rasmlar_b64[:4]:
        data = base64.b64decode(b64)
        img = Image.open(io.BytesIO(data)).convert("RGBA")

        # Oq background ga joylashtirish
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        try:
            bg.paste(img, mask=img.split()[3])
        except Exception:
            bg.paste(img)
        img = bg.convert("RGB")
        imgs.append(img)

    n = len(imgs)

    def fit_image(img, w, h):
        """Rasmni belgilangan o'lchamga moslashtirish (crop)"""
        img_ratio = img.width / img.height
        target_ratio = w / h
        if img_ratio > target_ratio:
            new_h = h
            new_w = int(h * img_ratio)
        else:
            new_w = w
            new_h = int(w / img_ratio)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        left = (img.width - w) // 2
        top = (img.height - h) // 2
        return img.crop((left, top, left + w, top + h))

    if n == 1:
        cell = fit_image(imgs[0], SIZE - CELL_PAD * 2, SIZE - CELL_PAD * 2)
        BG.paste(cell, (CELL_PAD, CELL_PAD))

    elif n == 2:
        w = (SIZE - CELL_PAD * 3) // 2
        h = SIZE - CELL_PAD * 2
        for i, img in enumerate(imgs):
            cell = fit_image(img, w, h)
            x = CELL_PAD + i * (w + CELL_PAD)
            BG.paste(cell, (x, CELL_PAD))

    elif n == 3:
        # Yuqorida 1 ta katta, pastda 2 ta
        top_h = (SIZE - CELL_PAD * 3) // 2
        bot_h = SIZE - CELL_PAD * 3 - top_h
        top_w = SIZE - CELL_PAD * 2
        bot_w = (SIZE - CELL_PAD * 3) // 2

        cell0 = fit_image(imgs[0], top_w, top_h)
        BG.paste(cell0, (CELL_PAD, CELL_PAD))

        for i, img in enumerate(imgs[1:]):
            cell = fit_image(img, bot_w, bot_h)
            x = CELL_PAD + i * (bot_w + CELL_PAD)
            y = CELL_PAD * 2 + top_h
            BG.paste(cell, (x, y))

    elif n >= 4:
        w = (SIZE - CELL_PAD * 3) // 2
        h = (SIZE - CELL_PAD * 3) // 2
        for i, img in enumerate(imgs[:4]):
            cell = fit_image(img, w, h)
            x = CELL_PAD + (i % 2) * (w + CELL_PAD)
            y = CELL_PAD + (i // 2) * (h + CELL_PAD)
            BG.paste(cell, (x, y))

    buf = io.BytesIO()
    BG.save(buf, format="JPEG", quality=95)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()

def create_image_with_text(rasm_b64, matn_uz, matn_ru, matn_en=None):
    """Berilgan rasmdan foydalanib 1:1 formatda 3 tilda rasm yaratadi"""
    results = []

    langs = [
        ("O'zbekcha", matn_uz),
        ("Ruscha", matn_ru),
    ]
    if matn_en:
        langs.append(("English", matn_en))

    for lang_name, matn in langs:
        # Agar rasm berilgan bo'lsa — edit API ishlatamiz
        if rasm_b64:
            from openai import OpenAI
            import io

            img_data = base64.b64decode(rasm_b64)
            img_file = io.BytesIO(img_data)
            img_file.name = "image.jpg"

            response = openai_client.images.edit(
                model="gpt-image-2",
                image=img_file,
                prompt=f"""Professional Instagram post (1:1 square format).
Keep the product photo as background.
Add text overlay: "{matn}" — large, bold, beautiful font, white or contrasting color.
Add semi-transparent dark overlay at bottom for text readability.
Clean, modern design. No logos. Instagram-ready.""",
                size="1024x1024",
                quality="medium",
                n=1
            )
        else:
            response = openai_client.images.generate(
                model="gpt-image-2",
                prompt=f"""Professional Instagram post (1:1 square format).
Modern clean food brand design. Elegant background.
Text: "{matn}" — large, bold, beautiful font.
Instagram-ready. No logos.""",
                size="1024x1024",
                quality="medium",
                n=1
            )

        img_bytes = BytesIO(base64.b64decode(response.data[0].b64_json))
        results.append({
            "bytes": img_bytes,
            "lang": lang_name
        })

    return results

def create_story_image(matn_uz, matn_ru, style="hikmat"):
    """Story uchun rasm yaratadi (2 tilda, bir xil style)"""
    
    style_map = {
        "hikmat": "Elegant motivational quote card. Dark green or deep navy background. Beautiful serif font. Gold accents. Minimalist design.",
        "sogliq": "Clean health infographic style. White or light background. Fresh green colors. Modern sans-serif font.",
        "hajviya": "Funny meme style. Bright warm colors. Bold comic-style font. Playful design.",
        "taom": "Food photography style. Warm golden light. Appetizing. Professional food blog aesthetic.",
    }

    prompt = f"""{style_map.get(style, style_map['hikmat'])}

IMPORTANT: Show ONLY these exact texts, do not add any other words:
Top section: "{matn_uz}"
Bottom section: "{matn_ru}"
Thin divider line between sections.
Vertical 9:16 format (1080x1920). Instagram Story ready. No logos. No extra text."""

    response = openai_client.images.generate(
        model="gpt-image-2",
        prompt=prompt,
        size="1024x1792",
        quality="medium",
        n=1
    )
    return BytesIO(base64.b64decode(response.data[0].b64_json))

# ==================== KEYBOARD ====================
def main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🥫 Shohona", callback_data="brend_shohona"),
            InlineKeyboardButton("🛒 AzanMarket", callback_data="brend_azanmarket"),
        ]
    ])

def shohona_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💡 Kun hikmati", callback_data="mavzu_kun_hikmati")],
        [InlineKeyboardButton("🍲 Kun taomi", callback_data="mavzu_kun_taomi")],
        [InlineKeyboardButton("🌿 Sog'liq va taom faktlari", callback_data="mavzu_sogliq_fakti")],
        [InlineKeyboardButton("😄 Hajviya", callback_data="mavzu_hajviya")],
        [InlineKeyboardButton("📦 Mahsulot reklama", callback_data="mavzu_mahsulot_reklama")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="start")],
    ])

def after_keyboard():
    """Yaratilgandan keyin chiqadigan 4 ta tugma"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Matnni tuzat", callback_data="tuzatish_matn")],
        [InlineKeyboardButton("🎨 Stil tuzat", callback_data="tuzatish_stil")],
        [InlineKeyboardButton("🔄 Boshqacha qil", callback_data="qayta_yaratish")],
        [InlineKeyboardButton("✅ Qabul", callback_data="start")],
    ])

def input_keyboard(mavzu):
    """Har mavzu uchun input knopkalari"""
    if mavzu == "kun_taomi":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📸 Rasm + direction beraman", callback_data="input_rasm")],
            [InlineKeyboardButton("🤖 Bot yaratsin", callback_data="matn_yoq")],
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📸 Rasm beraman", callback_data="input_rasm")],
            [InlineKeyboardButton("✍️ Matn yozaman", callback_data="matn_ha")],
            [InlineKeyboardButton("🤖 Bot yaratsin", callback_data="matn_yoq")],
        ])



# ==================== HANDLERS ====================
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    set_state(uid, brend=None, mavzu=None, rasm=None, step="start")
    await update.message.reply_text(
        "🤖 *Salom! Qaysi brend uchun kontent yaratamiz?*",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    data = query.data
    state = get_state(uid)

    # Brend tanlash
    if data == "brend_shohona":
        set_state(uid, brend="shohona", step="mavzu")
        await query.edit_message_text(
            "🥫 *Shohona* — Mavzuni tanlang:",
            reply_markup=shohona_keyboard(),
            parse_mode="Markdown"
        )

    elif data == "brend_azanmarket":
        set_state(uid, brend="azanmarket", step="rasm")
        await query.edit_message_text(
            "🛒 *AzanMarket* — Mahsulot rasmini yuboring 📸",
            parse_mode="Markdown"
        )

    elif data == "start":
        set_state(uid, brend=None, mavzu=None, rasm=None, step="start")
        await query.edit_message_text(
            "🤖 *Qaysi brend uchun kontent yaratamiz?*",
            reply_markup=main_keyboard(),
            parse_mode="Markdown"
        )

    # Shohona mavzu tanlash
    elif data.startswith("mavzu_"):
        mavzu = data.replace("mavzu_", "")
        set_state(uid, mavzu=mavzu, step="input")

        if mavzu == "hajviya":
            await query.edit_message_text("😄 *Hajviya yaratilmoqda...*", parse_mode="Markdown")
            await process_shohona(uid, query, ctx)

        elif mavzu == "mahsulot_reklama":
            await query.edit_message_text("📦 *G'oyalar yaratilmoqda...*", parse_mode="Markdown")
            await process_shohona(uid, query, ctx)

        elif mavzu == "kun_taomi":
            await query.edit_message_text(
                "🍲 *Kun taomi*\n\nQanday input berasiz?",
                reply_markup=input_keyboard("kun_taomi"),
                parse_mode="Markdown"
            )

        elif mavzu == "kun_hikmati":
            await query.edit_message_text(
                "💡 *Kun hikmati*\n\nQanday input berasiz?",
                reply_markup=input_keyboard("kun_hikmati"),
                parse_mode="Markdown"
            )

        elif mavzu == "sogliq_fakti":
            # Sog'liq fakti — mavzu nomini so'rash kerak
            set_state(uid, step="sogliq_mavzu")
            await query.edit_message_text(
                "🌿 *Sog'liq va taom faktlari*\n\nQaysi mavzu haqida fakt kerak?\n\nMisol: *Palov*, *Nuxat*, *Zira*, *Sarimsoq*, *Guruch*...",
                parse_mode="Markdown"
            )

        else:
            await query.edit_message_text(
                "Qanday input berasiz?",
                reply_markup=input_keyboard(mavzu),
                parse_mode="Markdown"
            )

    elif data == "input_rasm":
        set_state(uid, step="rasm")
        await query.edit_message_text(
            "📸 *Rasm yuboring:*",
            parse_mode="Markdown"
        )

    elif data == "tuzatish_matn":
        set_state(uid, step="tuzatish_wait", tuzatish_tur="matn")
        await query.edit_message_text(
            "✏️ *Matnni qanday tuzatish kerak?*\n\nMisol:\n— Ruscha qismini qayta yoz\n— Qisqaroq qil\n— Birinchi gapni o'zgartir",
            parse_mode="Markdown"
        )

    elif data == "tuzatish_stil":
        set_state(uid, step="tuzatish_wait", tuzatish_tur="stil")
        await query.edit_message_text(
            "🎨 *Stilni qanday tuzatish kerak?*\n\nMisol:\n— Ko'proq emoji qo'sh\n— Rasmiyroq qil\n— Qiziqarliroq qil\n— Hazilroq ohang ber",
            parse_mode="Markdown"
        )

    elif data == "tuzatish":
        set_state(uid, step="tuzatish_wait", tuzatish_tur="matn")
        await query.edit_message_text(
            "✏️ *Tuzatishni yozing:*",
            parse_mode="Markdown"
        )

    elif data == "qayta_yaratish":
        state = get_state(uid)
        mavzu = state.get("mavzu")
        if mavzu:
            set_state(uid, step="processing", rasm=None)
            await query.edit_message_text("🔄 *Boshqacha yaratilmoqda...*", parse_mode="Markdown")
            await process_shohona(uid, query, ctx)
        else:
            await query.edit_message_text(
                "🤖 *Yangi kontent yaratamizmi?*",
                reply_markup=main_keyboard(),
                parse_mode="Markdown"
            )

    elif data == "nusxa":
        state = get_state(uid)
        last_story = state.get("last_story", "")
        if last_story:
            await query.answer("📋 Matn nusxalandi!", show_alert=False)
            await query.message.reply_text(f"📋 *Nusxa:*\n\n{last_story}", parse_mode="Markdown")
        else:
            await query.answer("Matn topilmadi!", show_alert=True)

    elif data == "matn_ha":
        set_state(uid, step="matn_wait")
        await query.edit_message_text(
            "✍️ *Matnni yuboring:*",
            parse_mode="Markdown"
        )

    elif data == "matn_yoq":
        set_state(uid, step="processing")
        await query.edit_message_text("⏳ *Yaratilmoqda...*", parse_mode="Markdown")
        await process_shohona(uid, query, ctx)

async def message_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = get_state(uid)
    step = state.get("step")
    brend = state.get("brend")

    # Rasm yuborildi
    if update.message.photo:
        photo = update.message.photo[-1]
        file = await ctx.bot.get_file(photo.file_id)
        response = requests.get(file.file_path)
        img_b64 = base64.b64encode(response.content).decode()
        caption = update.message.caption or ""

        if brend == "azanmarket":
            # Ko'p rasm bo'lsa — listga qo'shib borish
            existing = get_state(uid).get("rasmlar", [])
            existing.append(img_b64)
            set_state(uid, rasmlar=existing, rasm=img_b64, step="matn_wait_az")

            if caption:
                await update.message.reply_text("⏳ *3 ta rasm yaratilmoqda...*", parse_mode="Markdown")
                await process_azanmarket(uid, update, ctx, matn=caption)
            else:
                await update.message.reply_text(
                    f"📸 *{len(existing)} ta rasm qabul qilindi!*\n\nYana rasm yuborasizmi yoki matn yozasizmi?\n\nMatn yozmasangiz /skip yozing",
                    parse_mode="Markdown"
                )

        elif brend == "shohona":
            set_state(uid, rasm=img_b64)
            if caption:
                set_state(uid, step="processing")
                await update.message.reply_text("⏳ *Yaratilmoqda...*", parse_mode="Markdown")
                await process_shohona(uid, update, ctx, matn=caption)
            else:
                set_state(uid, step="matn_wait")
                await update.message.reply_text(
                    "📝 Rasm qabul qilindi! Matn/direction yozasizmi?",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("✍️ Ha, yozaman", callback_data="matn_ha")],
                        [InlineKeyboardButton("🤖 Bot o'zi yaratsin", callback_data="matn_yoq")],
                    ])
                )
        else:
            # Brend tanlanmagan — AzanMarket deb qabul qil
            set_state(uid, brend="azanmarket", rasmlar=[img_b64], rasm=img_b64, step="matn_wait_az")
            await update.message.reply_text(
                "📸 *Rasm qabul qilindi!*\n\nYana rasm yuborasizmi yoki matn yozasizmi?\n\nMatn yozmasangiz /skip yozing",
                parse_mode="Markdown"
            )
        return

    # Matn yuborildi
    text = update.message.text

    if text == "/skip" and brend == "azanmarket":
        await update.message.reply_text("⏳ *3 ta rasm yaratilmoqda...*", parse_mode="Markdown")
        await process_azanmarket(uid, update, ctx, matn=None)
        return

    if step == "matn_wait_az":
        await update.message.reply_text("⏳ *3 ta rasm yaratilmoqda...*", parse_mode="Markdown")
        await process_azanmarket(uid, update, ctx, matn=text)

    elif step == "tuzatish_wait":
        # Tuzatish ko'rsatmasi keldi
        set_state(uid, step="processing")
        await update.message.reply_text("⏳ *Tuzatilmoqda...*", parse_mode="Markdown")
        await process_tuzatish(uid, update, ctx, koʻrsatma=text)

    elif step == "sogliq_mavzu":
        # Sog'liq fakti mavzusi keldi
        set_state(uid, step="processing")
        await update.message.reply_text("⏳ *Fakt yaratilmoqda...*", parse_mode="Markdown")
        await process_sogliq_fakti(uid, update, ctx, mavzu=text)

    elif step == "matn_wait":
        set_state(uid, step="processing")
        await update.message.reply_text("⏳ *Yaratilmoqda...*", parse_mode="Markdown")
        await process_shohona(uid, update, ctx, matn=text)

    elif step == "start":
        await update.message.reply_text(
            "🤖 Qaysi brend?",
            reply_markup=main_keyboard()
        )

async def process_tuzatish(uid, update, ctx, koʻrsatma=None):
    """Yaratilgan story ni tuzatish"""
    state = get_state(uid)
    last_story = state.get("last_story", "")
    last_style = state.get("last_style", "hikmat")
    tuzatish_tur = state.get("tuzatish_tur", "matn")

    try:
        if tuzatish_tur == "stil":
            prompt = f"""Quyidagi Instagram Story matnining STILINI tuzat (matnni o'zgartirma, faqat uslubini):

MAVJUD MATN:
{last_story}

STIL KO'RSATMASI:
{koʻrsatma}

MUHIM: Matn ma'nosini o'zgartirma. Faqat uslub, emoji, ton ni o'zgartir.
Format:
🇺🇿 O'ZBEKCHA:
[tuzatilgan]

🇷🇺 RUSCHA:
[tuzatilgan]"""
        else:
            prompt = f"""Quyidagi Instagram Story MATNINI tuzat:

MAVJUD MATN:
{last_story}

TUZATISH:
{koʻrsatma}

Format:
🇺🇿 O'ZBEKCHA:
[tuzatilgan]

🇷🇺 RUSCHA:
[tuzatilgan]"""

        new_story = claude_generate(prompt, SHOHONA_INFO)

        uz_text = ru_text = ""
        if "🇺🇿" in new_story and "🇷🇺" in new_story:
            parts = new_story.split("🇷🇺")
            uz_text = parts[0].replace("🇺🇿", "").replace("O'ZBEKCHA:", "").strip()
            ru_text = parts[1].replace("RUSCHA:", "").strip() if len(parts) > 1 else ""

        image_bytes = create_story_image(
            uz_text or new_story[:200],
            ru_text or translate_to_russian(new_story[:200]),
            last_style
        )
        image_bytes.seek(0)

        await ctx.bot.send_photo(
            chat_id=update.message.chat_id,
            photo=image_bytes,
            caption=f"✅ *Tuzatilgan*\n\n{new_story}"[:1024],
            parse_mode="Markdown"
        )

        set_state(uid, last_story=new_story, last_uz=uz_text, last_ru=ru_text)

        await update.message.reply_text(
            "Nima qilasiz?",
            reply_markup=after_keyboard()
        )

    except Exception as e:
        logger.error(f"Tuzatish error: {e}")
        await update.message.reply_text(f"❌ Xatolik: {str(e)}")

async def process_sogliq_fakti(uid, update_or_query, ctx, mavzu=None):
    """Sog'liq fakti — qisqa bo'lsa 1 rasm, uzun bo'lsa 2 ta alohida rasm"""
    if hasattr(update_or_query, 'message') and update_or_query.message:
        chat_id = update_or_query.message.chat_id
    else:
        chat_id = CHAT_ID

    # Fakt yaratish
    prompt = f"""Quyidagi mavzu haqida qisqa va qiziqarli Instagram Story fakti yoz:
Mavzu: {mavzu or "o'zbek taomlari"}

MUHIM QOIDALAR:
- Faqat 2-3 ta qisqa gap yoz
- Emoji ishlat
- Ilmiy, qiziqarli, foydali bo'lsin
- Faqat O'zbekcha yoz (tarjima shart emas)
- JUDA QISQA bo'lsin — maksimum 120 belgi"""

    uz_fakt = claude_generate(prompt, SHOHONA_INFO)
    ru_fakt = translate_to_russian(uz_fakt)

    # Uzunlikni tekshir
    QISQA_CHEGARA = 120

    if hasattr(update_or_query, 'edit_message_text'):
        await update_or_query.edit_message_text("⏳ *Fakt yaratilmoqda...*", parse_mode="Markdown")

    sogliq_title = mavzu or "Sog'liq fakti"
    sogliq_ru_title = mavzu or "Факт о здоровье"

    if len(uz_fakt) <= QISQA_CHEGARA:
        # Qisqa — 1 ta rasm, ikki tilda
        image_bytes = create_story_image(uz_fakt, ru_fakt, "sogliq")
        image_bytes.seek(0)
        await ctx.bot.send_photo(
            chat_id=chat_id,
            photo=image_bytes,
            caption=f"🌿 *{sogliq_title}*\n\n🇺🇿 {uz_fakt}\n\n🇷🇺 {ru_fakt}"[:1024],
            parse_mode="Markdown"
        )
    else:
        # Uzun — 2 ta alohida rasm
        uz_bytes = create_story_image(uz_fakt, "", "sogliq")
        uz_bytes.seek(0)
        await ctx.bot.send_photo(
            chat_id=chat_id,
            photo=uz_bytes,
            caption=f"🇺🇿 *{sogliq_title}*\n\n{uz_fakt}"[:1024],
            parse_mode="Markdown"
        )
        ru_bytes = create_story_image(ru_fakt, "", "sogliq")
        ru_bytes.seek(0)
        await ctx.bot.send_photo(
            chat_id=chat_id,
            photo=ru_bytes,
            caption=f"🇷🇺 *{sogliq_ru_title}*\n\n{ru_fakt}"[:1024],
            parse_mode="Markdown"
        )

    # Oxirgi story saqlash va 4 ta tugma
    full_story = f"🇺🇿 O'ZBEKCHA:\n{uz_fakt}\n\n🇷🇺 RUSCHA:\n{ru_fakt}"
    set_state(uid, last_story=full_story, last_style="sogliq",
              last_uz=uz_fakt, last_ru=ru_fakt)

    await ctx.bot.send_message(
        chat_id=chat_id,
        text="Nima qilasiz?",
        reply_markup=after_keyboard()
    )

async def process_shohona(uid, update_or_query, ctx, matn=None):
    state = get_state(uid)
    mavzu = state.get("mavzu")
    rasm_b64 = state.get("rasm")

    try:
        # Sog'liq fakti — maxsus jarayon
        if mavzu == "sogliq_fakti":
            await process_sogliq_fakti(uid, update_or_query, ctx, mavzu=matn)
            return

        # Story matni yarat
        story_text = generate_story("shohona", mavzu, matn, rasm_b64)

        # O'zbek va Rus qismlarini ajrat
        uz_text = ""
        ru_text = ""
        
        if "🇺🇿" in story_text and "🇷🇺" in story_text:
            parts = story_text.split("🇷🇺")
            uz_text = parts[0].replace("🇺🇿", "").replace("O'ZBEKCHA:", "").strip()
            ru_text = parts[1].replace("RUSCHA:", "").strip() if len(parts) > 1 else ""

        # Mavzu bo'yicha style
        style_map = {
            "kun_hikmati": "hikmat",
            "sogliq_fakti": "sogliq",
            "hajviya": "hajviya",
            "kun_taomi": "taom",
            "mahsulot_reklama": "taom",
        }
        style = style_map.get(mavzu, "hikmat")

        if mavzu == "mahsulot_reklama":
            msg = f"📦 *Shohona — Mahsulot reklama g'oyalari:*\n\n{story_text}"
            if hasattr(update_or_query, 'edit_message_text'):
                await update_or_query.edit_message_text(msg, parse_mode="Markdown")
            else:
                await update_or_query.message.reply_text(msg, parse_mode="Markdown")
        else:
            if uz_text and ru_text:
                image_bytes = create_story_image(uz_text, ru_text, style)
            else:
                image_bytes = create_story_image(
                    story_text[:200],
                    translate_to_russian(story_text[:200]),
                    style
                )

            caption = f"✅ *Shohona Story*\n\n{story_text}"

            if hasattr(update_or_query, 'message') and update_or_query.message:
                chat_id = update_or_query.message.chat_id
            else:
                chat_id = CHAT_ID

            image_bytes.seek(0)
            await ctx.bot.send_photo(
                chat_id=chat_id,
                photo=image_bytes,
                caption=caption[:1024],
                parse_mode="Markdown"
            )

            # Oxirgi story matni va style ni saqla (tuzatish uchun)
            set_state(uid, last_story=story_text, last_style=style,
                      last_uz=uz_text, last_ru=ru_text)

            # 4 ta tugma
            await ctx.bot.send_message(
                chat_id=chat_id,
                text="Nima qilasiz?",
                reply_markup=after_keyboard()
            )
            return

        # State reset
        set_state(uid, brend=None, mavzu=None, rasm=None, step="start")

        if hasattr(update_or_query, 'message') and update_or_query.message:
            await update_or_query.message.reply_text(
                "Nima qilasiz?",
                reply_markup=after_keyboard()
            )

    except Exception as e:
        logger.error(f"Shohona error: {e}")
        err_msg = f"❌ Xatolik: {str(e)}"
        if hasattr(update_or_query, 'message') and update_or_query.message:
            await update_or_query.message.reply_text(err_msg)

async def process_azanmarket(uid, update, ctx, matn=None):
    state = get_state(uid)
    rasm_b64 = state.get("rasm")
    rasmlar = state.get("rasmlar", [])

    try:
        if not rasm_b64 and not rasmlar:
            await update.message.reply_text("❌ Rasm topilmadi. Qaytadan yuboring.")
            return

        # Asosiy rasm — 1 ta bo'lsa o'zi, ko'p bo'lsa collage
        if len(rasmlar) > 1:
            await update.message.reply_text(
                f"🖼️ *{len(rasmlar)} ta rasm birlashtirilyapti...*",
                parse_mode="Markdown"
            )
            asosiy_rasm = create_collage(rasmlar)
        else:
            asosiy_rasm = rasmlar[0] if rasmlar else rasm_b64

        # Matn yaratish
        if matn:
            uz_matn = matn
        else:
            # Rasmdagi matnni o'qi
            content = [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": asosiy_rasm}},
                {"type": "text", "text": "Bu mahsulot haqida qisqa, jozibali Instagram post matni yoz (O'zbek tilida, 2-3 gap, emoji bilan):"}
            ]
            if len(rasmlar) > 1:
                content[1]["text"] = f"Bu {len(rasmlar)} ta mahsulot rasmi uchun qisqa, jozibali Instagram post matni yoz (O'zbek tilida, 2-3 gap, emoji bilan):"
            
            resp = claude.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=300,
                messages=[{"role": "user", "content": content}]
            )
            uz_matn = resp.content[0].text

        ru_matn = translate_to_russian(uz_matn)
        en_matn = claude_generate(
            f"Translate to English (short, catchy Instagram style, 2-3 sentences):\n{uz_matn}",
            "You are a professional translator. Give only the translation."
        )

        await update.message.reply_text("🖼️ *3 ta rasm yaratilmoqda...*", parse_mode="Markdown")

        rasms = create_image_with_text(asosiy_rasm, uz_matn, ru_matn, en_matn)

        langs = ["🇺🇿 O'zbekcha", "🇷🇺 Ruscha", "🇬🇧 English"]
        matns = [uz_matn, ru_matn, en_matn]

        for i, rasm in enumerate(rasms):
            rasm["bytes"].seek(0)
            await ctx.bot.send_photo(
                chat_id=update.message.chat_id,
                photo=rasm["bytes"],
                caption=f"{langs[i]}\n\n{matns[i]}"
            )

        # State yangilash
        set_state(uid, last_story=f"🇺🇿 {uz_matn}\n\n🇷🇺 {ru_matn}\n\n🇬🇧 {en_matn}",
                  rasmlar=[], rasm=None)

        await update.message.reply_text(
            "Nima qilasiz?",
            reply_markup=after_keyboard()
        )

    except Exception as e:
        logger.error(f"AzanMarket error: {e}")
        await update.message.reply_text(f"❌ Xatolik: {str(e)}")

# ==================== AVTOMATIK YUBORISH ====================
async def daily_send(ctx: ContextTypes.DEFAULT_TYPE):
    try:
        tz = pytz.timezone(TIMEZONE)
        today = datetime.now(tz)
        day_index = (today.timetuple().tm_yday - 1) % 30
        calendar_item = CALENDAR[day_index]
        mavzu = calendar_item["mavzu"]

        mavzu_map = {
            "Kun hikmati": "kun_hikmati",
            "Kun taomi": "kun_taomi",
            "Hajviya": "hajviya",
            "Sog'liq fakti": "sogliq_fakti",
            "Mahsulot reklama": "mahsulot_reklama",
        }
        mavzu_key = mavzu_map.get(mavzu, "kun_hikmati")

        await ctx.bot.send_message(
            chat_id=CHAT_ID,
            text=f"⏰ *Bugungi kontent — Kun {day_index+1}*\nMavzu: *{mavzu}*\n\nYaratilmoqda...",
            parse_mode="Markdown"
        )

        story_text = generate_story("shohona", mavzu_key)

        uz_text = ru_text = ""
        if "🇺🇿" in story_text and "🇷🇺" in story_text:
            parts = story_text.split("🇷🇺")
            uz_text = parts[0].replace("🇺🇿", "").replace("O'ZBEKCHA:", "").strip()
            ru_text = parts[1].replace("RUSCHA:", "").strip() if len(parts) > 1 else ""

        style_map = {
            "kun_hikmati": "hikmat",
            "sogliq_fakti": "sogliq",
            "hajviya": "hajviya",
            "kun_taomi": "taom",
            "mahsulot_reklama": "taom",
        }
        style = style_map.get(mavzu_key, "hikmat")

        if mavzu_key != "mahsulot_reklama":
            image_bytes = create_story_image(
                uz_text or story_text[:200],
                ru_text or translate_to_russian(story_text[:200]),
                style
            )
            image_bytes.seek(0)
            await ctx.bot.send_photo(
                chat_id=CHAT_ID,
                photo=image_bytes,
                caption=f"📅 *Kun {day_index+1} | {mavzu}*\n\n{story_text}"[:1024],
                parse_mode="Markdown"
            )
        else:
            await ctx.bot.send_message(
                chat_id=CHAT_ID,
                text=f"📅 *Kun {day_index+1} | {mavzu}*\n\n{story_text}",
                parse_mode="Markdown"
            )

    except Exception as e:
        logger.error(f"Daily send error: {e}")
        await ctx.bot.send_message(chat_id=CHAT_ID, text=f"❌ Avtomatik yuborishda xatolik: {e}")

# ==================== BUYRUQLAR ====================
async def cmd_bugun(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    tz = pytz.timezone(TIMEZONE)
    today = datetime.now(tz)
    day_index = (today.timetuple().tm_yday - 1) % 30
    item = CALENDAR[day_index]
    await update.message.reply_text(
        f"📅 *Bugun — Kun {day_index+1}*\nMavzu: *{item['mavzu']}*\nTavsif: {item['tavsif']}",
        parse_mode="Markdown"
    )

async def cmd_vaqt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global TIMEZONE
    args = ctx.args
    if args and args[0].lower() == "kst":
        TIMEZONE = "Asia/Seoul"
        await update.message.reply_text("✅ Vaqt zonasi: Koreya (KST) ga o'zgartirildi!")
    elif args and args[0].lower() == "uzt":
        TIMEZONE = "Asia/Tashkent"
        await update.message.reply_text("✅ Vaqt zonasi: O'zbekiston (UZT) ga o'zgartirildi!")
    else:
        await update.message.reply_text(f"⏰ Hozirgi vaqt zonasi: *{TIMEZONE}*\n\nO'zgartirish: /vaqt kst yoki /vaqt uzt", parse_mode="Markdown")

async def cmd_story(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    set_state(uid, brend=None, mavzu=None, rasm=None, step="start")
    await update.message.reply_text(
        "🤖 *Qaysi brend uchun?*",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

async def cmd_kalendar(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    tz = pytz.timezone(TIMEZONE)
    today = datetime.now(tz)
    current_day = (today.timetuple().tm_yday - 1) % 30

    text = "📅 *30 Kunlik Shohona Kalendar:*\n\n"
    for i, item in enumerate(CALENDAR):
        marker = "▶️" if i == current_day else f"{i+1}."
        text += f"{marker} {item['mavzu']}\n"

    await update.message.reply_text(text, parse_mode="Markdown")

# ==================== MAIN ====================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("story", cmd_story))
    app.add_handler(CommandHandler("bugun", cmd_bugun))
    app.add_handler(CommandHandler("vaqt", cmd_vaqt))
    app.add_handler(CommandHandler("kalendar", cmd_kalendar))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO | filters.TEXT & ~filters.COMMAND, message_handler))

    # Avtomatik yuborish — har kuni 09:00
    app.job_queue.run_daily(
        daily_send,
        time=time(hour=SEND_HOUR, minute=0, tzinfo=pytz.timezone(TIMEZONE))
    )

    logger.info("Bot ishga tushdi!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
