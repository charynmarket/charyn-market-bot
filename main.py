import discord
from discord.ext import commands, tasks
import os
import time
import re
import asyncio
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

# === QRIS BARU CHARYN MARKET - UDAH KEPASANG ===
QRIS_URL = "https://raw.githubusercontent.com/charynmarket/charyn-market-bot/main/lv_0_20261112135233.jpeg"

ticket_data = {}
ticket_counter = 0

def get_status_channel(guild):
    for ch in guild.text_channels:
        if "order-status" in ch.name.lower(): return ch
    for ch in guild.text_channels:
        if "ticket-order" in ch.name.lower(): return ch
    return None

def get_ticket_category(guild):
    for cat in guild.categories:
        if "TIKET" in cat.name.upper() or "TICKET" in cat.name.upper(): return cat
    return None

async def send_status_update(guild, number, username, user_id, paket, status_text, color):
    ch = get_status_channel(guild)
    if not ch: return
    embed = discord.Embed(title=f"📦 Order Status - Ticket #{number}", description=f"**Customer:** <@{user_id}> ({username})\n**Paket:** {paket}\n**Status:** {status_text}", color=color)
    embed.set_footer(text="CHARYN MARKET • Order Status")
    await ch.send(embed=embed)

async def do_close(guild, channel, data, admin_user=None):
    if channel.id in ticket_data: del ticket_data[channel.id]
    try: await channel.delete()
    except: pass

@tasks.loop(minutes=1)
async def check_inactive():
    now = time.time()
    for channel_id, data in list(ticket_data.items()):
        last = data.get("last_activity", data["created_at"])
        if now - last > 15*60:
            ch = bot.get_channel(channel_id)
            if not ch: del ticket_data[channel_id]; continue
            await do_close(ch.guild, ch, data)

class StatusView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="⏳ Menunggu Pembayaran", style=discord.ButtonStyle.secondary, custom_id="status_waiting_charyn")
    async def waiting(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.followup.send("❌ Hanya **Owner** yang bisa update status!", ephemeral=True); return
        data = ticket_data.get(interaction.channel.id, {})
        if data: data["last_activity"] = time.time()
        await interaction.followup.send("⏳ Status diubah: **Menunggu Pembayaran**")
        await send_status_update(interaction.guild, data.get("number", "?"), data.get("username", interaction.user.name), data.get("user_id", interaction.user.id), data.get("paket", "ORDER ROBUX"), "⏳ Menunggu Pembayaran", 0xfee75c)
    @discord.ui.button(label="🔄 Diproses", style=discord.ButtonStyle.primary, custom_id="status_process_charyn")
    async def process(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.followup.send("❌ Hanya **Owner** yang bisa update status!", ephemeral=True); return
        data = ticket_data.get(interaction.channel.id, {})
        if data: data["last_activity"] = time.time()
        await interaction.followup.send("🔄 Status diubah: **Sedang Diproses**")
        await send_status_update(interaction.guild, data.get("number", "?"), data.get("username", interaction.user.name), data.get("user_id", interaction.user.id), data.get("paket", "ORDER ROBUX"), "🔄 Sedang Diproses", 0x5865f2)
    @discord.ui.button(label="✅ Selesai", style=discord.ButtonStyle.success, custom_id="status_done_charyn")
    async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.followup.send("❌ Hanya **Owner** yang bisa update status!", ephemeral=True); return
        data = ticket_data.get(interaction.channel.id, {})
        if data: data["last_activity"] = time.time()
        await interaction.followup.send("✅ Status diubah: **Selesai** - Robux sudah masuk!")
        await send_status_update(interaction.guild, data.get("number", "?"), data.get("username", interaction.user.name), data.get("user_id", interaction.user.id), data.get("paket", "ORDER ROBUX"), "✅ Selesai / Done", 0x57f287)

class CloseView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🔒 CLOSE TICKET", style=discord.ButtonStyle.danger, custom_id="close_ticket_charyn")
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.followup.send("❌ Hanya **Owner** yang bisa menutup ticket ini!", ephemeral=True); return
        channel = interaction.channel; data = ticket_data.get(channel.id)
        if not data:
            await interaction.followup.send("Ticket ditutup..."); await channel.delete(); return
        await interaction.followup.send(f"Ticket ditutup oleh {interaction.user.mention}.")
        await do_close(interaction.guild, channel, data, admin_user=interaction.user)

class SaldoView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="💳 CEK SALDO SAYA", style=discord.ButtonStyle.primary, custom_id="cek_saldo_charyn")
    async def cek_saldo(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(color=0xff1493)
        embed.description = f"💳 **INFORMASI SALDO / TOTAL TRANSAKSI** ✨\n\nHalo {interaction.user.mention},\n\nSilahkan chat Owner untuk cek total belanja kamu di **CHARYN MARKET** ya 💗\n\nCHARYN MARKET • CHECK SALDO"
        embed.set_footer(text="Charyn Market")
        await interaction.response.send_message(embed=embed, ephemeral=True)

class OrderModal(discord.ui.Modal, title="Pesanan Robux - CHARYN MARKET"):
    username = discord.ui.TextInput(label="Username Roblox", placeholder="UsernameRoblox", required=True)
    paket = discord.ui.TextInput(label="Paket yang dipilih", placeholder="Contoh: 500 Robux", required=True)
    pembayaran = discord.ui.TextInput(label="Metode Pembayaran", placeholder="QRIS", default="QRIS", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        global ticket_counter
        ticket_counter += 1
        guild = interaction.guild
        overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False), interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True), guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
        category = get_ticket_category(guild)
        channel = await guild.create_text_channel(name=f"ticket-{ticket_counter}-{interaction.user.name}", overwrites=overwrites, category=category)
        ticket_data[channel.id] = {"user_id": interaction.user.id, "username": interaction.user.name, "roblox_username": self.username.value, "pembayaran": self.pembayaran.value, "created_at": time.time(), "last_activity": time.time(), "number": ticket_counter, "paket": self.paket.value}
        embed = discord.Embed(title=f"🎫 Ticket Baru - {interaction.user.name}", description=f"**Username Roblox:** {self.username.value}\n**Paket:** {self.paket.value}\n**Pembayaran:** {self.pembayaran.value}\n**Ticket #{ticket_counter}**\n\nSilahkan scan QRIS dibawah & kirim bukti pembayaran disini ya 💗", color=0xff69b4)
        await channel.send(f"{interaction.user.mention} Halo! Selamat datang di CHARYN MARKET! 🌸", embed=embed, view=CloseView())
        embed_qris = discord.Embed(title="💳 Scan QRIS Disini", description="Silahkan scan QRIS ini untuk pembayaran ya 💗\n\nBisa bayar via Bank / GoPay / OVO / DANA / ShopeePay!\nKirim bukti transfer nya disini!", color=0xff69b4)
        embed_qris.set_image(url=QRIS_URL)
        await channel.send(embed=embed_qris)
        await channel.send("**📦 STATUS ORDER - Owner only:**", view=StatusView())
        await send_status_update(guild, ticket_counter, interaction.user.name, interaction.user.id, self.paket.value, "🆕 Ticket Baru Dibuat", 0xff69b4)
        go_view = discord.ui.View()
        go_view.add_item(discord.ui.Button(label="🚀 BUKA TICKET SAYA", style=discord.ButtonStyle.link, url=f"https://discord.com/channels/{guild.id}/{channel.id}"))
        await interaction.response.send_message(f"✅ Ticket kamu sudah dibuat!\nPencet tombol dibawah untuk langsung masuk ke ticket kamu 👇\n👉 {channel.mention}", view=go_view, ephemeral=True)
        try: await interaction.user.send(f"✅ Ticket CHARYN MARKET kamu sudah dibuat!\nLangsung klik disini ya: 👉 {channel.mention}\nLink: https://discord.com/channels/{guild.id}/{channel.id}\n\nKirim bukti QRIS kamu disana ya 💗")
        except: pass

class OrderView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="ORDER ROBUX", style=discord.ButtonStyle.primary, custom_id="order_robux_charyn")
    async def order_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(OrderModal())

@bot.event
async def on_message(message):
    if message.author.bot: return
    if message.channel.id in ticket_data: ticket_data[message.channel.id]["last_activity"] = time.time()
    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"Login {bot.user} - CHARYN MARKET")
    bot.add_view(OrderView()); bot.add_view(CloseView()); bot.add_view(StatusView()); bot.add_view(SaldoView())
    if not check_inactive.is_running(): check_inactive.start()
    await bot.tree.sync()

@bot.tree.command(name="ticket", description="Tampilkan panel order CHARYN MARKET")
async def ticket(interaction: discord.Interaction):
    embed1 = discord.Embed(title="Charyn Market - Order Robux 💗", description="🌸 **ROBUX VIA USERNAME**\nFast Process • Aman • Instan\n\nSyarat top up via username:\n>> SUDAH 18+\n>> SUDAH TERVERIFIKASI 2 LANGKAH", color=0xff69b4)
    embed2 = discord.Embed(title="💰 ROBUX FAST SEND - CHARYN MARKET", description="🌸 **Robux Via Username - READY! ✅**\n\n🛒 **Cara Order**\nClick tombol ORDER ROBUX dibawah, isi formulir, lalu scan QRIS dibawah & tunggu admin. Pembayaran **hanya QRIS**.", color=0xff69b4)
    embed2.set_image(url=QRIS_URL)
    embed2.set_footer(text="Charyn Market")
    await interaction.response.send_message(embed=embed1)
    await interaction.followup.send(embed=embed2, view=OrderView())

@bot.tree.command(name="saldo", description="Cek saldo kamu di CHARYN MARKET")
async def saldo_slash(interaction: discord.Interaction):
    embed = discord.Embed(color=0xff1493)
    embed.description = f"💳 **INFORMASI SALDO / TOTAL TRANSAKSI** ✨\n\nHalo {interaction.user.mention},\n\nSilahkan chat Owner untuk cek total belanja kamu di **CHARYN MARKET** ya 💗\n\nCHARYN MARKET • CHECK SALDO"
    embed.set_footer(text="Charyn Market")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="setup-saldo", description="Kirim panel cek saldo (Owner only)")
async def setup_saldo(interaction: discord.Interaction):
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ Hanya Owner!", ephemeral=True); return
    embed = discord.Embed(title="💳 CEK SALDO - CHARYN MARKET", description="🌸 **MAU TAU UDAH HABIS BERAPA DI CHARYN MARKET?**\n\nPencet tombol **💳 CEK SALDO SAYA** dibawah!", color=0xff69b4)
    embed.set_footer(text="Charyn Market • Check Saldo")
    await interaction.response.send_message(embed=embed, view=SaldoView())

bot.run(os.getenv("DISCORD_TOKEN"))
