import discord
from discord.ext import commands
from discord.ui import View, Button
import datetime
import os
from dotenv import load_dotenv

# .env 파일에서 환경변수 불러오기
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # 서버 멤버 정보 접근을 위해 반드시 필요!

bot = commands.Bot(command_prefix="!", intents=intents)

# 유저별 데이터 저장
user_data = {}

def get_today():
    return datetime.date.today().isoformat()

def get_all_records(guild):
    if not user_data:
        return "아직 아무도 기록이 없습니다."
    lines = []
    for uid, data in user_data.items():
        member = guild.get_member(uid)
        if member:
            name = member.display_name
        else:
            user = bot.get_user(uid)
            name = user.name if user else f"ID:{uid}"
        lines.append(
            f"{name} - 스택: {data['stack']}, 범버거: {data['bumburger']}회"
        )
    return "\n".join(lines)

class BumburgerView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="성공", style=discord.ButtonStyle.success)
    async def success(self, interaction: discord.Interaction, button: Button):
        uid = interaction.user.id
        data = user_data.setdefault(uid, {"stack": 0, "bumburger": 0, "last_attend": None})
        msg = ""
        if data["stack"] < 1:
            data["stack"] += 1
            msg += f"성공! 현재 스택: {data['stack']}\n"
            if data["stack"] == 1:
                data["bumburger"] += 1
                data["stack"] = 0
                msg += f"범버거 획득! 총 범버거: {data['bumburger']}\n"
        else:
            msg += "스택은 최대 +1까지만 쌓을 수 있습니다.\n"
        msg += self.get_status(uid, interaction.guild)
        await interaction.response.send_message(msg, delete_after=20)

    @discord.ui.button(label="실패", style=discord.ButtonStyle.danger)
    async def fail(self, interaction: discord.Interaction, button: Button):
        uid = interaction.user.id
        data = user_data.setdefault(uid, {"stack": 0, "bumburger": 0, "last_attend": None})
        data["stack"] -= 1
        msg = f"실패! 현재 스택: {data['stack']}\n" + self.get_status(uid, interaction.guild)
        await interaction.response.send_message(msg, delete_after=20)

    @discord.ui.button(label="출석", style=discord.ButtonStyle.primary)
    async def attend(self, interaction: discord.Interaction, button: Button):
        uid = interaction.user.id
        today = get_today()
        data = user_data.setdefault(uid, {"stack": 0, "bumburger": 0, "last_attend": None})
        msg = ""
        if data["last_attend"] == today:
            msg += "출석은 하루에 한 번만 가능합니다. 내일 다시 시도해 주세요.\n"
        else:
            data["last_attend"] = today
            if data["stack"] < 0:
                data["stack"] += 1
                msg += f"출석! 음수 스택이 1만큼 회복되어 현재 스택: {data['stack']}\n"
            else:
                msg += "음수 스택이 없으므로 출석 효과가 없습니다.\n"
        msg += self.get_status(uid, interaction.guild)
        await interaction.response.send_message(msg, delete_after=20)

    @discord.ui.button(label="내 기록 보기", style=discord.ButtonStyle.secondary)
    async def show(self, interaction: discord.Interaction, button: Button):
        uid = interaction.user.id
        msg = self.get_status(uid, interaction.guild)
        await interaction.response.send_message(msg, delete_after=20)

    @discord.ui.button(label="전체 기록 보기", style=discord.ButtonStyle.secondary)
    async def show_all(self, interaction: discord.Interaction, button: Button):
        msg = get_all_records(interaction.guild)
        await interaction.response.send_message(msg, delete_after=20)

    def get_status(self, uid, guild):
        data = user_data.get(uid, {"stack": 0, "bumburger": 0, "last_attend": None})
        member = guild.get_member(uid)
        if member:
            name = member.display_name
        else:
            user = bot.get_user(uid)
            name = user.name if user else f"ID:{uid}"
        return (
            f"📊 **{name}님의 범버거 기록**\n"
            f"현재 스택: {data['stack']}\n"
            f"범버거 획득 횟수: {data['bumburger']}회"
        )

@bot.event
async def on_ready():
    print(f"Ready! Logged in as {bot.user}")
    # 이벤트 메시지를 특정 채널에 자동으로 전송
    channel_id = os.getenv("EVENT_CHANNEL_ID")
    if channel_id:
        channel = bot.get_channel(int(channel_id))
        if channel:
            await channel.send(
                "**🍔 범버거 이벤트! 🍔**\n버튼을 눌러 미션 결과를 기록하거나, 내 기록을 확인하세요.",
                view=BumburgerView()
            )
        else:
            print("채널을 찾을 수 없습니다. EVENT_CHANNEL_ID를 확인하세요.")
    else:
        print("EVENT_CHANNEL_ID가 .env 파일에 없습니다.")

bot.run(os.getenv("DISCORD_TOKEN"))
