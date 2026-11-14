import discord
from discord.ext import commands
import os
import time
import json
import re
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

QRIS_URL = "https://raw.githubusercontent.com/charynmarket/charyn-market-bot/main/lv_0_20261112135233.jpeg"
BANNER_URL = "https://raw.githubusercontent.com/charynmarket/charyn-market-bot/main/0a1fb8b8-aa93-4433-bee4-f3e933a9c5cd.jpeg"

BLUE = 0x3498db
PINK_SALDO = 0xff2d95

ticket_data = {}
ticket_counter = 0

# ===== SISTEM SALDO =====
SALDO_FILE = "saldo.json"
HARGA = {
    100: 16000, 200: 32000, 300: 48000, 400: 64000, 500: 75000,
    1000: 150000, 1500: 225000, 2000: 300000, 2500: 375000, 3000: 450000
}

def load_saldo():
    if os.path.exists(SALDO_FILE):
        try:
            with open(SALDO_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_saldo(data):
    with open(SALDO_FILE, "w") as f: json.dump(data, f, indent=2)

saldo_data = load_saldo()

def parse_paket(paket_text):
    m = re.search(r'(\d+)', paket_text.replace(".", "").replace(",", ""))
    if not m: return 0, 0
    robux = int(m.group(1))
    harga = HARGA.get(robux, int(robux * 160))
    return robux, harga

def get_saldo_embed(user):
    data = saldo_data.get(str(user.id), {"belanja": 0, "robux": 0, "transaksi": 0})
    embed = discord.Embed(color=PINK_SALDO)
    embed.title = "💳 INFORMASI SALDO / TOTAL TRANSAKSI ✨"
    embed.description = (
        f"Halo {user.mention},\n"
        f"berikut adalah rincian total transaksi atau saldo belanja kamu di **CHARYN MARKET:**\n\n"
        f"💰 **Total Belanja:** Rp {data['belanja']:,}\n".replace(",", ".") +
        f"📦 **Total Robux:** {data['robux']:,} R$\n".replace(",", ".") +
        f"🧾 **Total Transaksi:** {data['transaksi']}x\n\n"
        f"CHARYN MARKET • CHECK SALDO"
    )
    embed.set_footer(text="Charyn Market • Rafi Store")
    return embed

def get_ticket_category(guild):
    for cat in guild.categories:
        if "TIKET" in cat.name.upper() or "TICKET" in cat.name.upper(): return cat
    return None

async def do_close(guild, channel, data, admin_user=None):
    if data and data.get("user_id"):
        user_id = str(data["user_id"])
        robux = data.get("robux", 0)
        harga = data.get("harga", 0)
        if robux > 0:
            if user_id not in saldo_data:
                saldo_data[user_id] = {"belanja": 0, "robux": 0, "transaksi": 0}
            saldo_data[user_id]["belanja"] += harga
            saldo_data[user_id]["robux"] += robux
            saldo_data[user_id]["transaksi"] += 1
            save_saldo(saldo_data)
            try:
                user = await bot.fetch_user(int(user_id))
                await user.send(f"✅ Transaksi kamu berhasil dicatat di CHARYN MARKET!\n\n📦 Robux: {robux} R$\n💰 Total: Rp {harga:,}\n\nMakasih udah order ya! 💙".replace(",", "."))
            except: pass
    if channel.id in ticket_data: del ticket_data[channel.id]
    try: await channel.delete()
    except: pass

class PesananModal(discord.ui.Modal, title="Pesanan Robux"):
    nickname = discord.ui.TextInput(label="Nickname Roblox", placeholder="Nickname Roblox kamu", required=True, max_length=50)
    username = discord.ui.TextInput(label="Username", placeholder="UsernameRoblox", required=True, max_length=50)
    paket = discord.ui.TextInput(label="Paket yang dipilih", placeholder="Contoh: 500 Robux", required=True, max_length=50)
    metode = discord.ui.TextInput(label="Metode Pembayaran", placeholder="QRIS", default="QRIS", required=True, max_length=20)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        channel = await create_ticket(interaction, nickname=self.nickname.value, username_roblox=self.username.value, paket=self.paket.value, metode=self.metode.value)
        go_view = discord.ui.View()
        go_view.add_item(discord.ui.Button(label="🚀 BUKA TICKET SAYA", style=discord.ButtonStyle.link, url=f"https://discord.com/channels/{interaction.guild.id}/{channel.id}"))
        await interaction.followup.send(f"✅ Pesanan kamu sudah diterima!\nTicket kamu sudah dibuat 👇\n👉 {channel.mention}", view=go_view, ephemeral=True)
        try: await interaction.user.send(f"✅ Pesanan CHARYN MARKET kamu sudah diterima!\nNickname: {self.nickname.value}\nUsername: {self.username.value}\nPaket: {self.paket.value}\n\nLangsung klik disini ya: 👉 {channel.mention}\nLink: https://discord.com/channels/{interaction.guild.id}/{channel.id}\n\nKirim bukti QRIS kamu disana ya 💙")
        except: pass

async def create_ticket(interaction, nickname="-", username_roblox="-", paket="-", metode="QRIS"):
    global ticket_counter
    ticket_counter += 1
    guild = interaction.guild
    overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False), interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True), guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
    category = get_ticket_category(guild)
    channel = await guild.create_text_channel(name=f"ticket-{ticket_counter}-{interaction.user.name}", overwrites=overwrites, category=category)
    robux, harga = parse_paket(paket)
    ticket_data[channel.id] = {"user_id": interaction.user.id, "username": interaction.user.name, "created_at": time.time(), "number": ticket_counter, "robux": robux, "harga": harga, "paket": paket}
    embed = discord.Embed(title=f"🎫 Ticket Baru - {interaction.user.name}", description=f"**Ticket #{ticket_counter}**\n\nHalo {interaction.user.mention}!\n\n**📝 Pesanan Robux:**\n**Nickname Roblox:** {nickname}\n**Username Roblox:** {username_roblox}\n**Paket yang dipilih:** {paket}\n**Metode Pembayaran:** {metode}\n\nLalu scan QRIS dibawah & kirim bukti pembayaran disini ya 💙", color=BLUE)
    embed.set_image(url=BANNER_URL)
    await channel.send(f"{interaction.user.mention} Halo! Selamat datang di CHARYN MARKET! 🌸", embed=embed, view=CloseView())
    embed_qris = discord.Embed(title="💳 Scan QRIS Disini", description="Silahkan scan QRIS ini untuk pembayaran ya 💙\n\nBisa bayar via Bank / GoPay / OVO / DANA / ShopeePay!\nKirim bukti transfer nya disini!", color=BLUE)
    embed_qris.set_image(url=QRIS_URL)
    await channel.send(embed=embed_qris)
    return channel

class CloseView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🔒 CLOSE TICKET", style=discord.ButtonStyle.danger, custom_id="close_ticket_charyn")
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_owner = interaction.user.id == interaction.guild.owner_id
        is_admin_perm = interaction.user.guild_permissions.administrator
        role_names = [r.name.lower() for r in interaction.user.roles]
        is_admin_role = any(x in role_names for x in ["admin", "owner", "staff", "moderator", "adm"])
        if not (is_owner or is_admin_perm or is_admin_role):
            await interaction.response.send_message("❌ Hanya **Admin & Owner** yang bisa menutup ticket ini!", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        channel = interaction.channel; data = ticket_data.get(channel.id)
        if not data:
            await interaction.followup.send("Ticket ditutup..."); await channel.delete(); return
        await interaction.followup.send(f"Ticket ditutup oleh {interaction.user.mention}.")
        await do_close(interaction.guild, channel, data, admin_user=interaction.user)

class SaldoView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="💳 CEK SALDO SAYA", style=discord.ButtonStyle.primary, custom_id="cek_saldo_charyn")
    async def cek_saldo(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(embed=get_saldo_embed(interaction.user), ephemeral=True)

class OrderView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🛒 ORDER ROBUX", style=discord.ButtonStyle.primary, custom_id="order_robux_charyn")
    async def order_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PesananModal())

@bot.event
async def on_message(message):
    if message.author.bot: return
    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"Login {bot.user} - CHARYN MARKET")
    bot.add_view(OrderView()); bot.add_view(CloseView()); bot.add_view(SaldoView())
    await bot.tree.sync()

@bot.tree.command(name="ticket", description="Tampilkan panel order CHARYN MARKET")
async def ticket(interaction: discord.Interaction):
    # 1. JADI SATU - TEKS + FOTO NYATU
    embed1 = discord.Embed(title="Charyn Market - Order Robux 💙", description="🌸 **ROBUX VIA USERNAME**\n⚡ Fast Process • 🛡️ Aman • ✨ Instan\n\nSyarat top up via username:\n>> 🔞 SUDAH 18+\n>> ✅ SUDAH TERVERIFIKASI 2 LANGKAH", color=BLUE)
    embed1.set_image(url=BANNER_URL)

    # 2. PRICELIST BARU - UDAH MASUK KODE
    embed2 = discord.Embed(
        title="📊 PRICELIST ROBUX CLEAN VIA USERNAME 💎",
        description=(
            "💰 `⏣ 100 RBX `      =  `16.000`\n"
            "💰 `⏣ 200 RBX `      =  `32.000`\n"
            "💰 `⏣ 300 RBX `      =  `48.000`\n"
            "💰 `⏣ 400 RBX `      =  `64.000`\n"
            "💰 `⏣ 500 RBX `      =  `75.000`\n"
            "\n"
            "🌟 *BEST SELLER*\n"
            "👑 `⏣ 1.000 RBX ` = `150.000`\n"
            "👑 `⏣ 1.500 RBX ` = `225.000`\n"
            "👑 `⏣ 2.000 RBX ` = `300.000`\n"
            "👑 `⏣ 2.500 RBX ` = `375.000`\n"
            "👑 `⏣ 3.000 RBX ` = `450.000`\n"
            "➕ *DAN SETERUSNYA*\n"
            "\n"
            "📋 *NOTE:*\n"
            "> 🛒 UNTUK ORDER KLIK DIBAWAH BACAAN NYA \" ORDER ROBUX \"\n"
            "\n"
            "> ⚠️ SEGALA KESALAHAN PADA BUYER TIDAK MENJADI TANGGUNG JAWAB ADMIN\n"
            "\n"
            "> ✅ PASTIKAN USERNAME DAN NICKNAME DI ISI DENGAN BENAR YA!!"
        ),
        color=BLUE
    )
    embed2.set_footer(text="✨ projek By mipi store 💙")

    await interaction.response.send_message(embed=embed1)
    await interaction.followup.send(embed=embed2, view=OrderView())

@bot.tree.command(name="saldo", description="Cek saldo kamu di CHARYN MARKET")
async def saldo_slash(interaction: discord.Interaction):
    await interaction.response.send_message(embed=get_saldo_embed(interaction.user), ephemeral=True)

@bot.command(name="saldo")
async def saldo_prefix(ctx):
    await ctx.send(embed=get_saldo_embed(ctx.author), delete_after=30)

@bot.tree.command(name="setup-saldo", description="Kirim panel cek saldo (Owner only)")
async def setup_saldo(interaction: discord.Interaction):
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ Hanya Owner!", ephemeral=True); return
    embed = discord.Embed(title="💳 CEK SALDO - CHARYN MARKET", description="🌸 **MAU TAU UDAH HABIS BERAPA DI CHARYN MARKET?**\n\nPencet tombol **💳 CEK SALDO SAYA** dibawah!", color=BLUE)
    embed.set_footer(text="Charyn Market • Check Saldo")
    await interaction.response.send_message(embed=embed, view=SaldoView())

@bot.tree.command(name="add-saldo", description="Tambah saldo manual (Admin only)")
async def add_saldo(interaction: discord.Interaction, user: discord.User, robux: int):
    if not interaction.user.guild_permissions.administrator and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ Hanya Admin!", ephemeral=True); return
    _, harga = parse_paket(str(robux))
    uid = str(user.id)
    if uid not in saldo_data: saldo_data[uid] = {"belanja": 0, "robux": 0, "transaksi": 0}
    saldo_data[uid]["belanja"] += harga
    saldo_data[uid]["robux"] += robux
    saldo_data[uid]["transaksi"] += 1
    save_saldo(saldo_data)
    await interaction.response.send_message(f"✅ Saldo {user.mention} ditambah!\n📦 +{robux} R$\n💰 +Rp {harga:,}".replace(",", "."))

bot.run(os.getenv("DISCORD_TOKEN"))
