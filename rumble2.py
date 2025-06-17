import discord
from discord.ext import commands
from discord.ui import Button, View
from discord import app_commands
import random
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

rumble_participants = []
rumble_started = False
registration_open = False
auto_start_task = None
participant_count_message = None
intro_message = None
revive_percent = 0.0
revive_selected = False
join_open = False
join_message = None
kill_log = {}

ADMIN_ROLE_IDS = [
    1381509311024337008,
    1362624947557503006,
    1384176855292313741
]

def is_admin(user: discord.Member):
    return any(role.id in ADMIN_ROLE_IDS for role in user.roles)

class JoinView(View):
    def __init__(self, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx
        join_button = Button(label="🔥 Join Rumble", style=discord.ButtonStyle.success)
        join_button.callback = self.join_rumble
        self.add_item(join_button)

    async def join_rumble(self, interaction: discord.Interaction):
        global rumble_participants, registration_open, participant_count_message
        user = interaction.user
        if not join_open or not registration_open:
            await interaction.response.send_message("❌ Pendaftaran belum dibuka atau sudah ditutup.", ephemeral=True)
            return
        if user in rumble_participants:
            await interaction.response.send_message("⚠️ Kamu sudah bergabung sebelumnya.", ephemeral=True)
            return
        rumble_participants.append(user)
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("✅ Kamu berhasil bergabung!", ephemeral=True)
        if participant_count_message:
            await participant_count_message.edit(content=f"👥 Total peserta saat ini: **{len(rumble_participants)}**")

@tree.command(name="rumble", description="Mulai RUMBLE dengan parameter")
@app_commands.describe(waiting="Durasi pendaftaran (2m / 5m)", revive="Aktifkan revive? (yes/no)")
async def rumble(interaction: discord.Interaction, waiting: str, revive: str):
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ Hanya admin yang bisa menjalankan perintah ini.", ephemeral=True)
        return
    global revive_percent, revive_selected
    if waiting not in ["2m", "5m"] or revive.lower() not in ["yes", "no"]:
        await interaction.response.send_message("❌ Parameternya salah. Gunakan waiting: 2m/5m, revive: yes/no", ephemeral=True)
        return
    duration = 2 if waiting == "2m" else 5
    revive_percent = 0.2 if revive.lower() == "yes" else 0.0
    revive_selected = True
    await interaction.response.send_message(f"✅ Durasi: {duration} menit | Revive: {revive.upper()}", ephemeral=False)
    await start_rumble_registration(interaction.channel, duration)

@tree.command(name="start", description="Admin memulai RUMBLE secara manual")
async def start_command(interaction: discord.Interaction):
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ Hanya admin.", ephemeral=True)
        return
    global registration_open, auto_start_task
    if not registration_open:
        await interaction.response.send_message("⚠️ Pendaftaran sudah ditutup.", ephemeral=True)
        return
    registration_open = False
    if auto_start_task and not auto_start_task.done():
        auto_start_task.cancel()
    await interaction.response.send_message("⚡ RUMBLE dimulai oleh admin!")
    await do_rumble(interaction.channel)

@tree.command(name="stop", description="Menghentikan RUMBLE")
async def stop_rumble(interaction: discord.Interaction):
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ Hanya admin.", ephemeral=True)
        return
    global registration_open, rumble_started, auto_start_task
    registration_open = False
    rumble_started = False
    if auto_start_task and not auto_start_task.done():
        auto_start_task.cancel()
    await interaction.response.send_message("🛑 RUMBLE dihentikan oleh admin.")

@tree.command(name="search", description="Cari siapa yang membunuh player")
@app_commands.describe(user="Player yang ingin dicari pembunuhnya")
async def search_killer(interaction: discord.Interaction, user: discord.Member):
    killer = kill_log.get(user)
    if killer:
        await interaction.response.send_message(f"🔍 {user.mention} dibunuh oleh {killer.mention}.")
    else:
        await interaction.response.send_message(f"🔍 Tidak ditemukan siapa yang membunuh {user.mention}.")

async def start_rumble_registration(ctx, duration_minutes):
    global rumble_participants, rumble_started, registration_open, auto_start_task
    global participant_count_message, join_open

    rumble_participants = []
    rumble_started = False
    registration_open = True
    join_open = True

    await ctx.send(f"# 🔥 **RUMBLE DIMULAI!** Pendaftaran selama {duration_minutes} menit. Winner dapet 10k dana <@&1362625935727399022>")
    participant_count_message = await ctx.send("👥 Total peserta saat ini: **0**")
    
    countdown_message = await ctx.send(f"⏳ Pendaftaran ditutup dalam: **{duration_minutes}:00** menit")
    await ctx.send("🎮 Klik tombol di bawah untuk bergabung:", view=JoinView(ctx))

    end_time = asyncio.get_event_loop().time() + (duration_minutes * 60)

    async def update_countdown():
        while registration_open:
            remaining = int(end_time - asyncio.get_event_loop().time())
            if remaining <= 0:
                break
            minutes, seconds = divmod(remaining, 60)
            try:
                await countdown_message.edit(content=f"⏳ Pendaftaran ditutup dalam: **{minutes}:{seconds:02d}** menit")
            except discord.NotFound:
                break
            await asyncio.sleep(10)

    async def auto_start_after_timeout():
        global registration_open
        await asyncio.sleep(duration_minutes * 60)
        if registration_open:
            registration_open = False
            await ctx.send("⏰ Waktu habis! Memulai RUMBLE secara otomatis...")
            await do_rumble(ctx)

    asyncio.create_task(update_countdown())
    auto_start_task = asyncio.create_task(auto_start_after_timeout())

async def do_rumble(ctx):
    global rumble_started, kill_log
    if rumble_started: return
    rumble_started = True
    kill_log = {}

    if len(rumble_participants) < 2:
        await ctx.send("❗ Tidak cukup peserta.")
        return

    if intro_message:
        await ctx.send(f"📢 {intro_message}")
    await ctx.send("⚔️ Pertarungan dimulai...\n━━━━━━━━━━━━━━━")

    elimination_stories = [
        "🔥 Dalam kekacauan, {killer} menjatuhkan {eliminated} dengan satu tembakan presisi!",
        "⚔️ {killer} menyerang dari balik kabut dan menghabisi {eliminated} dalam duel cepat!",
        "💣 {eliminated} tak sempat menghindar dari ledakan yang diluncurkan oleh {killer}!",
        "🏹 Dari kejauhan, {killer} melepaskan panah yang tepat menembus jantung {eliminated}!",
        "🥷 Dalam senyap, {killer} menyelinap dan menebas leher {eliminated} dari belakang!",
        "💥 {killer} menembak {eliminated} dengan tank. WTF kok ada tank?",
        "🚁 Dari atas helikopter, {killer} menghujani {eliminated} dengan peluru!",
        "🐍 {killer} mengkhianati {eliminated} di saat paling tidak terduga!",
        "🔫 {killer} menarik pelatuk tepat saat {eliminated} berbalik badan...",
        "🔫 {killer} menolak ajakan kencannya dan {eliminated} memutuskan untuk bunuh diri. Sungguh tragis."
    ]

    round_num = 1
    initial_count = len(rumble_participants)
    revived = False
    mass_kill_done = False
    mass_kill_round = random.randint(2, 5)

    while len(rumble_participants) > 1:
        await asyncio.sleep(2)

        if not mass_kill_done and round_num == mass_kill_round and len(rumble_participants) > 5:
            mk_percent = random.uniform(0.01, 0.15)
            mk_count = max(1, int(initial_count * mk_percent))
            mk_victims = random.sample(rumble_participants, min(mk_count, len(rumble_participants) - 1))
            for victim in mk_victims:
                rumble_participants.remove(victim)
                kill_log[victim] = None
            description = (
                "**☠️ Para peserta ini hilang secara misterius:**\n" +
                "\n".join(f"💀 {v.mention}" for v in mk_victims) +
                "\n\n🪓 Mereka salah memasuki medan perang dan tiba-tiba diserang suku kanibal.\n"
                "Sampai sekarang kabar mereka tidak diketahui. Bjir banget. Mereka harus nyari siapa yang mimpin pasukan"
            )
            embed = discord.Embed(
                title="💀 Pembantaian Misterius!",
                description=description,
                color=discord.Color.dark_purple()
            )
            embed.set_footer(text=f"Pemain tersisa: {len(rumble_participants)}")
            await ctx.send(embed=embed)
            mass_kill_done = True
            await asyncio.sleep(2)

        embed = discord.Embed(title=f"Round {round_num}", color=discord.Color.red())
        kills_this_round = min(random.randint(2, 5), len(rumble_participants) - 1)
        messages = []

        for _ in range(kills_this_round):
            if len(rumble_participants) <= 1:
                break
            eliminated = random.choice(rumble_participants)
            killer = random.choice([p for p in rumble_participants if p != eliminated])
            rumble_participants.remove(eliminated)
            kill_log[eliminated] = killer
            msg = random.choice(elimination_stories).format(killer=killer.mention, eliminated=eliminated.mention)
            messages.append(msg)

        embed.description = "\n".join(messages) if messages else "Tidak ada korban di ronde ini. Sumpah narator juga kaget!!!!"
        embed.set_footer(text=f"Pemain tersisa: {len(rumble_participants)}")
        await ctx.send(embed=embed)
        round_num += 1

        if not revived and len(rumble_participants) <= initial_count // 2 and revive_percent > 0:
            dead_players = list(kill_log.keys())
            count = max(1, int(initial_count * revive_percent))
            to_revive = random.sample(dead_players, min(count, len(dead_players)))
            for user in to_revive:
                rumble_participants.append(user)
                del kill_log[user]
            revive_embed = discord.Embed(
                title="⚡ Revive Aktif!",
                description="Beberapa pemain hidup kembali secara ajaib!\n\n" +
                            "\n".join(f"✨ {u.mention}" for u in to_revive),
                color=discord.Color.green()
            )
            revive_embed.set_footer(text=f"Pemain tersisa: {len(rumble_participants)}")
            await ctx.send(embed=revive_embed)
            revived = True

    winner = rumble_participants[0]
    await asyncio.sleep(3)
    await ctx.send("━━━━━━━━━━━━━━━")
    await ctx.send("H O R E E E E E E E")
    await ctx.send("━━━━━━━━━━━━━━━")
    await ctx.send(f"🏆 **{winner.mention} adalah pemenang RUMBLE!**")
    await ctx.send("━━━━━━━━━━━━━━━")

    survivors = list(kill_log.keys())[-4:] + [winner]
    survivors = survivors[::-1]
    msg = "**🧱 Top 5 Survivor Terakhir:**\n" + "\n".join(f"{i+1}. {u.mention}" for i, u in enumerate(survivors))
    await ctx.send(msg)
    await ctx.send("━━━━━━━━━━━━━━━")

    kill_count = {}
    for killer in kill_log.values():
        if killer:
            kill_count[killer] = kill_count.get(killer, 0) + 1
    top_killers = sorted(kill_count.items(), key=lambda x: x[1], reverse=True)[:5]
    if top_killers:
        msg = "**🔪 Top 5 Pembunuh Berdarah Dingin:**\n"
        msg += "\n".join(f"{i+1}. {k.mention} - {v} kill" for i, (k, v) in enumerate(top_killers))
        await ctx.send(msg)
        await ctx.send("━━━━━━━━━━━━━━━")

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot aktif sebagai {bot.user}")

bot.run("DISCORD TOKEN")
