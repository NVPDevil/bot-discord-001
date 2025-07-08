"""Module chứa các lệnh quản trị cho bot."""

import discord
from discord.ext import commands
from utils.permissions import is_owner
from utils.embed import EmbedManager
from config import Config

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed = EmbedManager()

    async def send_help(self, ctx, bot, is_admin=False, delete_after=60):
        embed1 = discord.Embed(
            title="🎧 NGƯỜI DÙNG THƯỜNG 🎧",
            description="Quyền cơ bản cho mọi người:",
            color=discord.Color.from_rgb(66, 135, 245)
        )
        embed1.add_field(
            name="Lệnh khả dụng",
            value="`!play <tên/URL>`: Phát nhạc\n`!queue`: Xem danh sách chờ\n`!volume <0-200>`: Điều chỉnh âm lượng\n`!skip`: Bỏ qua (bài mình yêu cầu)\n`!stop`: Dừng (bài mình yêu cầu)\n`!loop`: Bật/tắt lặp\n`!help`: Xem hướng dẫn",
            inline=False
        )
        embed1.add_field(
            name="Đặc quyền",
            value="Phát nhạc, điều khiển bài của mình, volume tối đa 200%.",
            inline=False
        )

        embed2 = discord.Embed(
            title="🎤 SPECIAL ROLES 🎤",
            description="Quyền nâng cao (bao gồm quyền người thường):",
            color=discord.Color.from_rgb(255, 215, 0)
        )
        embed2.add_field(
            name="Lệnh bổ sung",
            value="`!skip`: Bỏ qua bất kỳ bài\n`!stop`: Dừng bất kỳ lúc nào\n`!volume <0-300>`: Volume tối đa 300%",
            inline=False
        )
        embed2.add_field(
            name="Đặc quyền",
            value="Ưu tiên queue, quyền skip/stop tất cả, volume tối đa 300%.",
            inline=False
        )

        embed3 = discord.Embed(
            title="👑 OWNER 👑",
            description="Quyền quản trị (bao gồm quyền special roles):",
            color=discord.Color.from_rgb(255, 0, 0)
        )
        embed3.add_field(
            name="Lệnh bổ sung",
            value="`!specialroles`: Xem special roles\n`!addspecial <role_id>`: Thêm role\n`!removespecial <role_id>`: Xóa role\n`!servers`: Xem server\n`!volume <0-500>`: Volume tối đa 500%\n`!summon <channel>`: Triệu hồi bot\n`!clearqueue`: Xóa queue",
            inline=False
        )
        embed3.add_field(
            name="Đặc quyền",
            value="Quản lý bot, volume tối đa 500%, triệu hồi bot, xóa queue.",
            inline=False
        )

        if is_admin:
            await self.embed.send(ctx, embed1, delete_after=delete_after)
            await self.embed.send(ctx, embed2, delete_after=delete_after)
            await self.embed.send(ctx, embed3, delete_after=delete_after)
        else:
            embed1.set_thumbnail(url=self.embed.thumbnail)
            embed1.set_footer(text=self.embed.footer_text, icon_url=self.embed.footer_icon)
            embed2.set_thumbnail(url=self.embed.thumbnail)
            embed2.set_footer(text=self.embed.footer_text, icon_url=self.embed.footer_icon)
            embed3.set_thumbnail(url=self.embed.thumbnail)
            embed3.set_footer(text=self.embed.footer_text, icon_url=self.embed.footer_icon)
            await ctx.send(embed=embed1, ephemeral=True, delete_after=delete_after)
            await ctx.send(embed=embed2, ephemeral=True, delete_after=delete_after)
            await ctx.send(embed=embed3, ephemeral=True, delete_after=delete_after)

    @commands.command(name="specialroles")
    async def list_special_roles(self, ctx):
        if not is_owner(self, ctx.author):
            return await self.embed.send_error(ctx, "Chỉ owner mới dùng được lệnh này!", delete_after=15)
        role_list = "\n".join(f"- <@&{role_id}> (ID: {role_id})" for role_id in Config.SPECIAL_ROLE_IDS)
        await self.embed.send_special_roles(ctx, role_list or "Chưa có role nào.", delete_after=15)

    @commands.command(name="addspecial")
    async def add_special_role(self, ctx, role_id: int):
        if not is_owner(self, ctx.author):
            return await self.embed.send_error(ctx, "Chỉ owner mới dùng được lệnh này!", delete_after=15)
        if role_id in Config.SPECIAL_ROLE_IDS:
            return await self.embed.send_error(ctx, "Role này đã là special role!", delete_after=15)
        Config.SPECIAL_ROLE_IDS.append(role_id)
        await self.embed.send_success(ctx, f"Đã thêm <@&{role_id}> vào special roles.", delete_after=15)

    @commands.command(name="removespecial")
    async def remove_special_role(self, ctx, role_id: int):
        if not is_owner(self, ctx.author):
            return await self.embed.send_error(ctx, "Chỉ owner mới dùng được lệnh này!", delete_after=15)
        if role_id not in Config.SPECIAL_ROLE_IDS:
            return await self.embed.send_error(ctx, "Role này không phải special role!", delete_after=15)
        Config.SPECIAL_ROLE_IDS.remove(role_id)
        await self.embed.send_success(ctx, f"Đã xóa <@&{role_id}> khỏi special roles.", delete_after=15)

    @commands.command(name="servers")
    async def list_servers(self, ctx):
        if not is_owner(self, ctx.author):
            return await self.embed.send_error(ctx, "Chỉ owner mới dùng được lệnh này!", delete_after=15)
        server_list = "\n".join(f"- {guild.name} (ID: {guild.id})" for guild in self.bot.guilds)
        await self.embed.send_server_list(ctx, server_list or "Bot chưa tham gia server nào.", delete_after=15)

    @commands.command(name="help")
    async def help(self, ctx):
        await self.send_help(ctx, self.bot, is_admin=False, delete_after=60)

async def setup(bot):
    await bot.add_cog(Admin(bot))