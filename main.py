import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# === DATA TOKO ===
STOCK = {
    "robux 100": 10,
    "robux 500": 5,
    "robux 1000": 3,
}

HARGA = {
    "robux 100": "Rp 15.000",
    "robux 500": "Rp 70.000",
    "robux 1000": "Rp 135.000",
}

@bot.event
async def on_ready():
    print(f"LOGIN SEBAGAI {bot.user}")
    await bot.change_presence(activity=discord.Game(name="!help | CHARYN MARKET"))

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! Bot CHARYN MARKET Online! 🟢")

@bot.command()
async def price(ctx):
    embed = discord.Embed(title="💎 PRICE LIST - CHARYN MARKET", color=0xFFD700, description="Harga Robux Termurah!")
    for item, harga in HARGA.items():
        embed.add_field(name=item.upper(), value=f"{harga} | Stok: {STOCK.get(item,0)}", inline=False)
    embed.set_footer(text="Order? Ketik !order robux 100")
    await ctx.send(embed=embed)

@bot.command()
async def stock(ctx):
    embed = discord.Embed(title="📦 STOK CHARYN MARKET", color=0x00FF00)
    for item, jumlah in STOCK.items():
        status = "✅ Ready" if jumlah > 0 else "❌ Habis"
        embed.add_field(name=item.upper(), value=f"Stok: {jumlah} - {status}", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def order(ctx, *, item: str = None):
    if not item:
        await ctx.send("Cara pakai: `!order robux 100`\nKetik `!price` buat liat list!")
        return
    item = item.lower()
    if item not in STOCK:
        await ctx.send("Item gak ada! Ketik `!price` buat cek!")
        return
    if STOCK[item] <= 0:
        await ctx.send("Maaf stok habis! Coba item lain.")
        return
    embed = discord.Embed(title="🧾 ORDER BARU!", color=0x0099FF)
    embed.add_field(name="Pembeli", value=ctx.author.mention, inline=False)
    embed.add_field(name="Item", value=item.upper(), inline=False)
    embed.add_field(name="Harga", value=HARGA[item], inline=False)
    embed.add_field(name="Status", value="⏳ Menunggu Pembayaran", inline=False)
    embed.set_footer(text="Silahkan transfer & kirim bukti ke admin! - CHARYN MARKET")
    await ctx.send(embed=embed)
    await ctx.send(f"{ctx.author.mention} Order kamu dicatat! Admin bakal hubungin kamu! 🙏")

@bot.command()
async def testi(ctx):
    embed = discord.Embed(title="⭐ TESTIMONI CHARYN MARKET", color=0xFF00FF, description="100% Trusted & Amanah!")
    embed.add_field(name="⭐⭐⭐⭐⭐", value="Fast respon, robux langsung masuk! - Buyer 1", inline=False)
    embed.add_field(name="⭐⭐⭐⭐⭐", value="Admin ramah banget, recommended! - Buyer 2", inline=False)
    embed.add_field(name="⭐⭐⭐⭐⭐", value="Udah 3x order disini aman terus! - Buyer 3", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def help_charyn(ctx):
    await ctx.send("**CHARYN MARKET COMMANDS:**\n`!price` - Liat harga\n`!stock` - Liat stok\n`!order robux 100` - Order\n`!testi` - Liat testi\n`!ping` - Cek bot online")

bot.run(os.getenv("TOKEN"))
