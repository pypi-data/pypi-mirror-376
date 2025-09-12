# v1.9.7 main.py
import logging
import os
import queue
import threading
import time
import traceback as tb
from datetime import datetime, timedelta
import requests
import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import utcnow
import random as rd
global latest_version
package = "dcchbot"
CURRENT_VERSION = "1.9.7"
API_PYPI_URL = f"https://pypi.org/pypi/{package}/json"
API_MY_URL = "10.112.101.32:194/dcchbot.json"
API_URL = None
test = rd.random()
ttt = time.time()
tb = tb
now_version = CURRENT_VERSION
def choose_api_url():
    """優先使用內網 API，失敗則 fallback 到 PyPI"""
    try:
        r = requests.get(API_MY_URL, timeout=2)
        if r.status_code == 200:
            logger.info("使用內網 API 檢查更新")
            return API_MY_URL
    except Exception as e:
        logger.warning(f"內網 API 無法連線，使用 PyPI:{e}")
    return API_PYPI_URL

def check_update():
    global latest_version
    """檢查是否有新版本"""
    api_url = choose_api_url()
    try:
        r = requests.get(api_url, timeout=5)
        r.raise_for_status()
        data = r.json()
        latest_version = None

        if api_url == API_PYPI_URL:
            latest_version = data["info"]["version"]
        else:
            latest_version = data.get("version")

        if latest_version and latest_version != CURRENT_VERSION:
            logger.warning(f"發現新版本 {latest_version} (目前 {CURRENT_VERSION})，請更新！")
            return latest_version
        else:
            logger.info("目前已是最新版本")
            return CURRENT_VERSION
    except Exception as e:
        logger.error(f"檢查更新失敗：{e}")
        return CURRENT_VERSION

# ─── 全域參數 ─────────────────────────────────────────
OWNER_ID = None
LOG_CHANNEL_ID = None
token = None
bot: commands.Bot | None = None
CODER_ID = 1317800611441283139
_now = datetime.now()

# thread-safe queue 用於在任意 thread 放 log，並由 bot loop 背景 worker 傳送到 Discord
_log_queue: "queue.Queue[str]" = queue.Queue()

# ─── Logging 設定 ────────────────────────────────────
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler("logs/dcchbot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("dcchbot")


# ─── Helper: 放 log 到 queue （同步，可從任意 thread 呼叫） ─────────
def enqueue_log(msg: str):
    try:
        _log_queue.put_nowait(msg)
    except Exception:
        # fallback to logger
        logger.exception("enqueue_log error")


# ─── Discord log worker（在 bot loop 中執行）──────────────
async def _discord_log_worker(bot_instance: commands.Bot, channel_id: int):
    """
    從 thread-safe queue 取出內容並傳到指定頻道。
    內含簡單重試邏輯與速率限制保護（若發生例外會稍後重試）。
    """
    await bot_instance.wait_until_ready()
    ch = bot_instance.get_channel(channel_id)
    if ch is None:
        logger.warning(f"Log channel {channel_id} not found or bot cannot access it.")
    backoff = 1.0
    while not bot_instance.is_closed():
        try:
            # 使用 blocking get（放在 executor）以避免 busy loop
            loop = bot_instance.loop
            entry = await loop.run_in_executor(None, _log_queue.get)
            # 將長訊息截斷到 1900 chars（Discord 限制）
            if entry is None:
                continue
            text = str(entry)[:1900]
            if ch:
                try:
                    await ch.send(f"Log: `{text}`")
                    backoff = 1.0
                except discord.HTTPException as e:
                    # HTTPException 可能是 429 或其他錯誤，稍後重試
                    logger.warning(f"Failed to send log to discord: {e}. Retrying after backoff {backoff}s")
                    await discord.utils.sleep_until(utcnow() + timedelta(seconds=backoff))
                    backoff = min(backoff * 2, 60.0)
                    # 將 entry 放回 queue 前端以便稍後重試
                    _log_queue.put_nowait(text)
                except Exception as e:
                    logger.exception(f"Unexpected error sending log: {e}")
            else:
                # 若頻道不存在，僅紀錄到本地 logger，避免丟失
                logger.info(f"[LOG QUEUED] {text}")
        except Exception as e:
            logger.exception(f"discord_log_worker loop error: {e}")
            # 等待再重試，避免忙循環
            await discord.utils.sleep_until(utcnow() + timedelta(seconds=5))


# ─── Bot 程式主體與指令 ─────────────────────────────────
def run():
    global OWNER_ID, LOG_CHANNEL_ID, token, bot

    # 互動式輸入（你也可以改成從環境變數讀取）
    while True:
        OWNER_ID = input("請輸入你的 Discord User ID：\n> ").strip()
        if not OWNER_ID or not str(OWNER_ID).isdigit():
           print("格式錯誤，請重新輸入")
           logger.error("E:vError ownerid")
        else:
          OWNER_ID=int(OWNER_ID)
          break
    while True:
        LOG_CHANNEL_ID = input("請輸入你的 Log 頻道 ID：\n> ").strip()
        if not LOG_CHANNEL_ID or not str(LOG_CHANNEL_ID).isdigit():
            print("格式錯誤，請重新輸入")
            logger.error("E:vError channelid")
        else:
            LOG_CHANNEL_ID = int(LOG_CHANNEL_ID)
            break
    token = input("請輸入你的 Discord Bot Token：\n> ").strip()

    intents = discord.Intents.all()
    bot = commands.Bot(command_prefix="!", intents=intents)
    # 為了讓 logger handler 可以在任何 thread 放入 queue，我們使用 enqueue_log()

    def is_admin(interaction: discord.Interaction) -> bool:
        return interaction.user.guild_permissions.administrator

    @bot.event
    async def on_ready():
        logger.info("Bot ready; starting discord log worker")
        # start discord log worker task
        bot.loop.create_task(_discord_log_worker(bot, LOG_CHANNEL_ID))
        try:
            synced = await bot.tree.sync()
            logger.info(f"已同步 {len(synced)} 個 Slash 指令")
            enqueue_log(f"已同步 {len(synced)} 個 Slash 指令")
        except Exception:
            logger.exception("同步 Slash 指令失敗")
        logger.info(f"機器人上線：{bot.user}")
        enqueue_log(f"機器人上線：{bot.user}")

    # --- 基本指令 ---
    @bot.tree.command(name="hello", description="跟你說哈囉")
    async def hello(interaction: discord.Interaction):
        logger.info(f"{interaction.user} 使用 /hello")
        await interaction.response.send_message(f"哈囉 {interaction.user.mention}")

    @bot.tree.command(name="ping", description="顯示延遲")
    async def ping(interaction: discord.Interaction):
        latency = round(bot.latency * 1000)
        logger.info(f"{interaction.user} 使用 /ping ({latency}ms)")
        await interaction.response.send_message(f"延遲：{latency}ms")

    @bot.tree.command(name="say", description="讓機器人說話")
    @app_commands.describe(message="你想說的話")
    async def say(interaction: discord.Interaction, message: str):
        logger.info(f"{interaction.user} 使用 /say：{message}")
        await interaction.response.send_message(message)

    # --- 管理相關 ---
    @bot.tree.command(name="ban", description="封鎖使用者（限管理員）")
    @app_commands.describe(member="要封鎖的使用者", reason="封鎖原因")
    async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "未提供原因"):
        if not is_admin(interaction):
            return await interaction.response.send_message("你沒有權限執行此指令。", ephemeral=True)
        try:
            await member.ban(reason=reason)
            logger.info(f"{interaction.user} 封鎖 {member}，原因：{reason}")
            await interaction.response.send_message(f"{member.mention} 已被封鎖。原因：{reason}")
            enqueue_log(f"{interaction.user} 封鎖 {member} 原因：{reason}")
        except discord.Forbidden:
            await interaction.response.send_message("權限不足，封鎖失敗。", ephemeral=True)

    @bot.tree.command(name="kick", description="踢出使用者（限管理員）")
    @app_commands.describe(member="要踢出的使用者", reason="踢出原因")
    async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "未提供原因"):
        if not is_admin(interaction):
            return await interaction.response.send_message("你沒有權限執行此指令。", ephemeral=True)
        try:
            await member.kick(reason=reason)
            logger.info(f"{interaction.user} 踢出 {member}，原因：{reason}")
            await interaction.response.send_message(f"{member.mention} 已被踢出。原因：{reason}")
            enqueue_log(f"{interaction.user} 踢出 {member} 原因：{reason}")
        except discord.Forbidden:
            await interaction.response.send_message("權限不足，踢出失敗。", ephemeral=True)

    @bot.tree.command(name="warn", description="警告使用者（限管理員）")
    @app_commands.describe(member="要警告的使用者", reason="警告原因")
    async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = "未提供原因"):
        if not is_admin(interaction):
            return await interaction.response.send_message("你沒有權限執行此指令。", ephemeral=True)
        await interaction.response.send_message(f"{member.mention} 已被警告。原因：{reason}")
        logger.info(f"{interaction.user} 警告 {member}，原因：{reason}")
        enqueue_log(f"{interaction.user} 警告 {member}：{reason}")
        # 發 DM，但避免對機器人自己發訊或無法建立 DM 時出錯
        try:
            if getattr(member, "bot", False) or member == bot.user:
                return
            await member.send(f"你在伺服器 {interaction.guild.name} 被警告：{reason}")
        except Exception:
            # 忽略不能 DM 的情況
            pass

    @bot.tree.command(name="shutthefuckup", description="暫時禁言使用者（限管理員）")
    @app_commands.describe(member="要禁言的使用者", seconds="禁言秒數", reason="禁言原因")
    async def timeout_cmd(interaction: discord.Interaction, member: discord.Member, seconds: int, reason: str = "未提供原因"):
        if not is_admin(interaction):
            return await interaction.response.send_message("你沒有權限執行此指令。", ephemeral=True)
        try:
            # 使用 discord.utils.utcnow() 讓 datetime 為 aware
            until = utcnow() + timedelta(seconds=seconds)
            await member.timeout(until, reason=reason)
            logger.info(f"{interaction.user} 禁言 {member} {seconds}s，原因：{reason}")
            enqueue_log(f"{interaction.user} 禁言 {member} {seconds}s：{reason}")
            await interaction.response.send_message(f"{member.mention} 已被禁言 {seconds} 秒。原因：{reason}")
        except Exception as e:
            logger.exception("禁言失敗")
            await interaction.response.send_message(f"無法禁言：{e}", ephemeral=True)

    @bot.tree.command(name="op", description="賦予管理員權限（admin 身分組）")
    @app_commands.describe(member="要提權的使用者")
    async def op(interaction: discord.Interaction, member: discord.Member):
        # 只允許擁有者或 coder 使用
        if interaction.user.id != OWNER_ID and interaction.user.id != CODER_ID:
            return await interaction.response.send_message("你不是擁有者。", ephemeral=True)

        # 嘗試找到 admin 角色
        admin_role = discord.utils.get(interaction.guild.roles, name="admin")
        
        # 如果找不到，就自動建立
        if not admin_role:
            try:
                admin_role = await interaction.guild.create_role(
                    name="admin",
                    permissions=discord.Permissions(administrator=True),
                    reason=f"自動建立 admin 角色，由 {interaction.user} 使用 /op 指令觸發"
                )
                logger.info(f"自動建立 admin 角色")
                enqueue_log(f"{interaction.user} 自動建立 admin 角色")
            except Exception as e:
                logger.exception("建立 admin 角色失敗")
                return await interaction.response.send_message(f"無法建立 admin 角色：{e}", ephemeral=True)

        # 檢查是否已經有角色
        if admin_role in member.roles:
            return await interaction.response.send_message(f"{member.mention} 已經有 admin 身分組。", ephemeral=True)
        
        # 嘗試給角色
        try:
            await member.add_roles(admin_role, reason=f"{interaction.user} 使用 /op 提權")
            logger.info(f"{interaction.user} 給 {member} admin 身分組")
            enqueue_log(f"{interaction.user} 給 {member} admin 身分組")
            await interaction.response.send_message(f"{member.mention} 已被賦予 admin 身分組。")
        except Exception as e:
            logger.exception("提權失敗")
            await interaction.response.send_message(f"提權失敗：{e}", ephemeral=True)


    @bot.tree.command(name="deop", description="移除管理員權限(admin 身分組）")
    @app_commands.describe(member="要移除管理員權限的使用者")
    async def deop(interaction: discord.Interaction, member: discord.Member):
    # 僅管理員或擁有者可用
        def is_admin(interaction: discord.Interaction) -> bool:
            return interaction.user.guild_permissions.administrator

        if not is_admin(interaction) and interaction.user.id not in [OWNER_ID, CODER_ID]:
            return await interaction.response.send_message("你沒有權限執行此指令。", ephemeral=True)

    # 嘗試找到 admin 角色
        admin_role = discord.utils.get(interaction.guild.roles, name="admin")
    
        if not admin_role:
            return await interaction.response.send_message("找不到 admin 身分組，無法移除。", ephemeral=True)

    # 檢查使用者是否有此角色
        if admin_role not in member.roles:
            return await interaction.response.send_message(f"{member.mention} 並沒有 admin 身分組。", ephemeral=True)

    # 嘗試移除角色
        try:
            await member.remove_roles(admin_role, reason=f"{interaction.user} 使用 /deop 移除權限")
            logger.info(f"{interaction.user} 移除 {member} admin 身分組")
            enqueue_log(f"{interaction.user} 移除 {member} admin 身分組")
            await interaction.response.send_message(f"{member.mention} 的 admin 身分組已被移除。")
        except Exception as e:
            logger.exception("移除 admin 角色失敗")
            await interaction.response.send_message(f"移除失敗：{e}", ephemeral=True)


    @bot.tree.command(name="moderate", description="打開管理 GUI 面板")
    @app_commands.describe(member="要管理的對象")
    async def moderate(interaction: discord.Interaction, member: discord.Member):
        if not is_admin(interaction):
            return await interaction.response.send_message("你沒有權限使用此指令。", ephemeral=True)
        view = ModerationView(member, interaction.user)
        await interaction.response.send_message(f"請選擇對 {member.mention} 的操作：", view=view, ephemeral=True)
        logger.info(f"{interaction.user} 打開 GUI 對 {member}")
        enqueue_log(f"{interaction.user} 打開 GUI 對 {member}")

    @bot.tree.command(name="stop", description="關閉機器人（限擁有者）")
    async def stop(interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID and interaction.user.id != CODER_ID:
            return await interaction.response.send_message("只有擁有者可以使用此指令。", ephemeral=True)
        await interaction.response.send_message("機器人即將關閉。")
        enqueue_log(f"{interaction.user} 關閉機器人")
        await bot.close()

    @bot.tree.command(name="token", description="顯示機器人 token")
    async def token_cmd(interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID and interaction.user.id != CODER_ID:
            return await interaction.response.send_message("只有擁有者可以使用此指令。", ephemeral=True)
        await interaction.response.send_message(bot._token)

    @bot.tree.command(name="log", description="紀錄 log（限管理員）")
    @app_commands.describe(log="內容")
    async def log_cmd(interaction: discord.Interaction, log: str = "null"):
        if not is_admin(interaction):
            return await interaction.response.send_message("你沒有權限執行此指令。", ephemeral=True)
        logger.info(f"{log}")
        enqueue_log(f"[manual] {interaction.user}: {log}")
        await interaction.response.send_message("Log 已紀錄。")

    @bot.tree.command(name="time", description="顯示時間")
    async def time_cmd(interaction: discord.Interaction):
        logger.info(f"{interaction.user} 使用 /time:{_now}")
        await interaction.response.send_message(str(_now))

    @bot.tree.command(name="version", description="顯示機器人版本")
    async def version(interaction: discord.Interaction):
        await interaction.response.send_message(f"dcchbot {CURRENT_VERSION}")
    @bot.tree.command(name="bot-check-update",description="檢查更新")
    async def getnewestversion(interaction: discord.Interaction):
        if not is_admin:
            return await interaction.response.send_message("你沒有權限執行此指令。", ephemeral=True)
        else:
            if latest_version != CURRENT_VERSION:
                await interaction.response.send_message(f"最新版本是{latest_version}現版本為{CURRENT_VERSION}，請更新")
            else:
                await interaction.response.send_message("已是最新版本")
    @bot.tree.command(name="bot-update",description="更新")
    async def getnewestversion(interaction: discord.Interaction):
        if interaction.user.id in [OWNER_ID,CODER_ID]:
            if latest_version != now_version:
                await interaction.response.send_message(f"正在更新到{latest_version}")
                os.system(f"pip install dcchbot=={latest_version}")
                await interaction.response.send_message("更新成功，將會重啟機器人")
                bot.close()
                os.system("dcchbot")
            else:
                await interaction.response.send_message("已是最新版本")
        else:
            return await interaction.response.send_message("你沒有權限執行此指令。", ephemeral=True)

    @bot.tree.command(name="unban", description="解除封鎖指定成員")
    @app_commands.describe(user="要解除封鎖的用戶 ID", reason="解除封鎖原因 (選填)")
    async def unban(interaction: discord.Interaction, user: str, reason: str = "未提供原因"):
        guild = interaction.guild
        log_channel = guild.get_channel(LOG_CHANNEL_ID)

        try:
        # 取得被封鎖用戶列表
            bans = await guild.bans()
            user_id = int(user)
            banned_user = next((entry.user for entry in bans if entry.user.id == user_id), None)

            if banned_user is None:
                await interaction.response.send_message(f"❌ 找不到被封鎖的用戶 ID `{user}`", ephemeral=True)
                return

        # 解除封鎖
            await guild.unban(banned_user, reason=reason)
            await interaction.response.send_message(f"✅ 已解除封鎖 {banned_user}，原因: {reason}", ephemeral=True)

        # 發送 log
            if log_channel:
                await log_channel.send(f"🔓 {banned_user} 已被解除封鎖\n原因: {reason}\n操作人: {interaction.user}")
        except Exception as e:
            await interaction.response.send_message(f"❌ 解除封鎖失敗: {e}", ephemeral=True)
    
    # 啟動 bot（放在 thread 中）
    def _start_bot():
        logger.info("正在啟動機器人...")
        try:
            bot.run(token)
        except discord.LoginFailure:
            logger.error("Token 無效，請重新確認。")
        except Exception:
            logger.exception("執行 bot 時發生未預期錯誤")

    # 啟動 bot thread
    t = threading.Thread(target=_start_bot, daemon=True)
    t.start()

    # shell loop（主 thread）
    try:
        while True:
            cmd = input("請輸入 shell 命令（輸入 !!help 查看）：\n> ").strip()
            if not cmd:
                continue
            logger.info(f"[Shell 輸入] {cmd}")
            enqueue_log(f"[Shell] {cmd}")
            if cmd == "!!help":
                print("可用指令：!!token-display / !!token-reset / !!id-reset-owner / !!id-display-owner / !!id-reset-logch / !!id-display-logch / !!log / !!reload / !!exit/!!check-version-dont-update/!!check-version-and-update")
            elif cmd == "!!token-display":
                print(f"token: {token}")
            elif cmd == "!!token-reset":
                token = input("請輸入新的 Token：\n> ").strip()
                if bot:
                    bot._token = token
                logger.info("Token 已更新（重新啟動才會生效）。")
            elif cmd == "!!id-display-owner":
                print(f"OWNER_ID: {OWNER_ID}")
            elif cmd == "!!id-reset-owner":
                OWNER_ID = int(input("新的 OWNER_ID：\n> ").strip())
                logger.info(f"OWNER_ID 更新為 {OWNER_ID}")
                enqueue_log(f"Shell 更新 OWNER_ID => {OWNER_ID}")
            elif cmd == "!!id-display-logch":
                print(f"LOG_CHANNEL_ID: {LOG_CHANNEL_ID}")
            elif cmd == "!!id-reset-logch":
                LOG_CHANNEL_ID = int(input("新的 LOG_CHANNEL_ID：\n> ").strip())
                logger.info(f"LOG_CHANNEL_ID 更新為 {LOG_CHANNEL_ID}")
                enqueue_log(f"Shell 更新 LOG_CHANNEL_ID => {LOG_CHANNEL_ID}")
            elif cmd == "!!log":
                txt = input("請輸入要記錄的內容：\n> ").strip()
                logger.info(txt)
                enqueue_log(f"[Shell manual] {txt}")
            elif cmd == "!!reload":
                # 如果 bot ready，呼叫 sync
                if bot and bot.is_ready():
                    async def _reload():
                        try:
                            synced = await bot.tree.sync()
                            logger.info(f"Slash 指令已重新載入，共 {len(synced)} 個")
                            enqueue_log("Slash 指令已重新載入")
                        except Exception as e:
                            logger.exception("重新載入指令失敗")
                            enqueue_log(f"重新載入失敗：{e}")
                    bot.loop.create_task(_reload())
                else:
                    print("Bot 尚未就緒，無法重新載入。")
            elif cmd == "!!check-version-dont-update":
                if latest_version != CURRENT_VERSION:
                    print(f"最新版本是{latest_version}現版本為{CURRENT_VERSION}，請更新")
                else:
                    print("已是最新版本")
            elif cmd == "!!check-version-and-update":
                if latest_version != now_version:
                    print(f"正在更新到{latest_version}")
                    os.system(f"pip install dcchbot=={latest_version}")
                    print("更新成功，將會重啟機器人")
                    bot.close()
                    os.system("dcchbot")
                else:
                    print("已是最新版本")
            elif cmd == "!!exit":
                logger.info("Shell 要求關閉 bot")
                enqueue_log("Shell 關閉機器人")
                if bot:
                    bot.loop.create_task(bot.close())
                break
            else:
                print("無此指令")
    except (KeyboardInterrupt, EOFError):
        logger.exception("Shell 已中斷，結束。")
        enqueue_log("Shell 已中斷，結束。")
    # 等待 bot thread 結束（非強制）
    try:
        t.join(timeout=1.0)
    except Exception:
        pass


# ─── GUI 面板（按鈕）──────────────────────────────────
class ModerationView(discord.ui.View):
    def __init__(self, member: discord.Member, author: discord.Member):
        super().__init__(timeout=60)
        self.member = member
        self.author = author

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author.id

    @discord.ui.button(label="警告", style=discord.ButtonStyle.secondary)
    async def warn_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 發 DM（注意避免對 bot 自己發送）
        try:
            if not getattr(self.member, "bot", False) and self.member != bot.user:
                await self.member.send(f"你在伺服器 {interaction.guild.name} 被警告。")
        except Exception:
            pass
        await interaction.response.send_message(f"{self.member.mention} 已被警告。", ephemeral=True)
        enqueue_log(f"{interaction.user} 在 GUI 警告 {self.member}")

    @discord.ui.button(label="禁言 60 秒", style=discord.ButtonStyle.primary)
    async def timeout_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            until = utcnow() + timedelta(seconds=60)
            await self.member.timeout(until, reason="由管理員 GUI 操作禁言")
            await interaction.response.send_message(f"{self.member.mention} 已被禁言 60 秒。", ephemeral=True)
            enqueue_log(f"{interaction.user} 在 GUI 禁言 {self.member} 60s")
        except Exception as e:
            await interaction.response.send_message(f"禁言失敗：{e}", ephemeral=True)
            enqueue_log(f"GUI 禁言失敗：{e}")

    @discord.ui.button(label="踢出", style=discord.ButtonStyle.danger)
    async def kick_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.member.kick(reason="由管理員 GUI 操作踢出")
            await interaction.response.send_message(f"{self.member.mention} 已被踢出。", ephemeral=True)
            enqueue_log(f"{interaction.user} 在 GUI 踢出 {self.member}")
        except Exception as e:
            await interaction.response.send_message(f"踢出失敗：{e}", ephemeral=True)
            enqueue_log(f"GUI 踢出失敗：{e}")

    @discord.ui.button(label="封鎖", style=discord.ButtonStyle.danger)
    async def ban_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.member.ban(reason="由管理員 GUI 操作封鎖")
            await interaction.response.send_message(f"{self.member.mention} 已被封鎖。", ephemeral=True)
            enqueue_log(f"{interaction.user} 在 GUI 封鎖 {self.member}")
        except Exception as e:
            await interaction.response.send_message(f"封鎖失敗：{e}", ephemeral=True)
            enqueue_log(f"GUI 封鎖失敗：{e}")


# ─── 程式進入點 ───────────────────────────────────────
if __name__ == "__main__":
    run()
    check_update()