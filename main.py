"""Điểm khởi động chính của bot âm nhạc."""

import discord
from discord.ext import commands
import config
import asyncio
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Cấu hình intents
intents = discord.Intents.default()
intents.message_content = True

# Khởi tạo bot
bot = commands.Bot(command_prefix=config.Config.PREFIX, intents=intents, case_insensitive=True)
bot.remove_command("help")

@bot.event
async def on_ready():
    logger.info(f"Bot đã sẵn sàng với tên: {bot.user}")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name=f"{config.Config.PREFIX}help | Bee BOT"
        )
    )

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    ctx = await bot.get_context(message)
    if ctx.valid:  # Chỉ xóa nếu là lệnh hợp lệ
        # Kiểm tra kênh
        if message.channel.id != config.Config.ALLOWED_CHANNEL_ID and not message.author.id == config.Config.OWNER_ID:
            return  # Bỏ qua nếu không phải kênh cho phép và không phải owner
        await message.delete()
    await bot.process_commands(message)

async def load_cogs():
    cogs = ["cogs.music", "cogs.moderation", "cogs.admin"]
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            logger.info(f"Đã load {cog}")
        except Exception as e:
            logger.error(f"Lỗi khi load {cog}: {e}")

async def main():
    try:
        await load_cogs()
        await bot.start(config.Config.TOKEN)
    except Exception as e:
        logger.error(f"Lỗi khởi động bot: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot đã dừng bởi người dùng.")