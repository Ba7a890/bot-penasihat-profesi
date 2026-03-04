import discord
from discord.ext import commands
from discord.ui import View, Button, Select
from discord import app_commands
import json
import os
from dotenv import load_dotenv
import google.generativeai as genai

# ================= LOAD ENV =================
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not DISCORD_TOKEN or not GEMINI_API_KEY:
    raise ValueError("Token atau GEMINI_API_KEY belum diisi di file .env")

# ================= GEMINI SETUP =================
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# ================= LOAD DATABASE =================
with open("career.json", "r", encoding="utf-8") as f:
    career_data = json.load(f)

# ================= DISCORD SETUP =================
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ================= AI FUNCTION =================
def ask_ai(user_input, extra_data=None):
    system_prompt = """
    Kamu adalah penasihat karier profesional untuk remaja Indonesia.
    Gunakan bahasa sederhana, jelas, mudah dipahami.
    Berikan saran realistis dan membangun.
    """

    if extra_data:
        user_prompt = f"""
        Data profesi:
        {json.dumps(extra_data, indent=2)}

        Permintaan:
        {user_input}
        """
    else:
        user_prompt = user_input

    full_prompt = system_prompt + "\n\n" + user_prompt

    try:
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"Terjadi error saat menghubungi Gemini:\n{e}"

# ================= DROPDOWN =================
class CategorySelect(Select):
    def __init__(self):
        categories = list(set([c["kategori"] for c in career_data]))
        options = [discord.SelectOption(label=cat) for cat in categories]

        super().__init__(
            placeholder="Pilih kategori minat kamu",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        filtered = [c for c in career_data if c["kategori"] == selected]

        await interaction.response.defer()

        result = ask_ai(
            "Berikan 3 rekomendasi terbaik lengkap dengan alasan, jalur pendidikan, skill, dan prospek 5 tahun.",
            filtered
        )
        if len(result) > 4000:
            result = result[:4000] + "\n\n... (jawaban dipotong karena terlalu panjang)"

        embed = discord.Embed(
            title=f"🎯 Rekomendasi Karier - {selected}",
            description=result,
            color=0x00ff99
        )

        await interaction.followup.send(embed=embed)

class CategoryView(View):
    def __init__(self):
        super().__init__()
        self.add_item(CategorySelect())

# ================= BUTTON =================
class StartButton(Button):
    def __init__(self):
        super().__init__(
            label="🔍 Mulai Konsultasi",
            style=discord.ButtonStyle.primary
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Silakan pilih kategori minat kamu:",
            view=CategoryView()
        )

class StartView(View):
    def __init__(self):
        super().__init__()
        self.add_item(StartButton())

# ================= SLASH COMMAND =================
@bot.tree.command(name="konsultasi", description="Mulai konsultasi karier AI")
async def konsultasi(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Halo! Saya penasihat karier AI 🤖\nKlik tombol di bawah untuk mulai.",
        view=StartView()
    )

# ================= TANYA BEBAS =================
@bot.tree.command(name="tanya", description="Tanya bebas soal karier ke AI")
@app_commands.describe(pertanyaan="Masukkan pertanyaan kamu")
async def tanya(interaction: discord.Interaction, pertanyaan: str):

    await interaction.response.defer()

    result = ask_ai(pertanyaan)

    if len(result) > 4000:
        result = result[:4000] + "\n\n... (jawaban dipotong karena terlalu panjang)"

    embed = discord.Embed(
        title="💬 Jawaban Konsultasi Karier",
        description=result,
        color=0x3498db
    )

    await interaction.followup.send(embed=embed)

# ================= ABOUT COMMAND =================
@bot.tree.command(name="about", description="Informasi tentang bot ini")
async def about(interaction: discord.Interaction):


    embed = discord.Embed(
        title="🤖 Career Advisor AI Bot (Gemini Version)",
        description="Bot penasihat karier berbasis AI Gemini untuk membantu remaja memilih profesi dan jalur pendidikan.",
        color=0x9b59b6
    )

    embed.add_field(
        name="🎯 Fitur Utama",
        value="""
• Konsultasi karier berbasis AI
• Rekomendasi dari database profesi
• Sistem kategori minat
• Tanya bebas seputar karier
        """,
        inline=False
    )

    embed.add_field(
        name="🛠 Powered By",
        value="""
• Python
• discord.py
• Google Gemini API
• JSON Database
        """,
        inline=False
    )

    embed.set_footer(text="Gunakan /konsultasi untuk mulai atau /tanya untuk bertanya bebas.")

    await interaction.response.send_message(embed=embed)

# ================= READY =================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot siap sebagai {bot.user}")

# ================= RUN =================
bot.run(DISCORD_TOKEN)