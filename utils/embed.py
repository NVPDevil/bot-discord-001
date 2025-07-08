"""Module quản lý embed với giao diện chuyên nghiệp."""

import discord
import time
import logging
import asyncio
from utils.permissions import is_owner, has_special_role, can_skip, can_stop
from discord.ui import Button, View

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class NowPlayingControls(View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.primary, emoji="⏭️")
    async def skip_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        if not can_skip(self.cog, interaction.user):
            timestamp = int(time.time()) + 15
            embed = discord.Embed(
                title="❌ LỖI",
                description="```Bạn không có quyền skip!```",
                color=discord.Color.from_rgb(255, 87, 87)
            )
            embed.set_thumbnail(url=self.cog.embed.thumbnail)
            embed.set_footer(text=self.cog.embed.footer_text, icon_url=self.cog.embed.footer_icon)
            embed.add_field(name="Tự xóa sau", value=f"<t:{timestamp}:R>", inline=False)
            msg = await interaction.followup.send(embed=embed)
            await asyncio.sleep(15)
            await msg.delete()
            return
        if self.cog.ctx.voice_client and self.cog.ctx.voice_client.is_playing():
            self.cog.ctx.voice_client.stop()
            timestamp = int(time.time()) + 15
            embed = discord.Embed(
                title="✅ THÀNH CÔNG",
                description="```Đã skip bài hát.```",
                color=discord.Color.from_rgb(87, 255, 87)
            )
            embed.set_thumbnail(url=self.cog.embed.thumbnail)
            embed.set_footer(text=self.cog.embed.footer_text, icon_url=self.cog.embed.footer_icon)
            embed.add_field(name="Tự xóa sau", value=f"<t:{timestamp}:R>", inline=False)
            msg = await interaction.followup.send(embed=embed)
            await asyncio.sleep(15)
            await msg.delete()

    @discord.ui.button(label="Vol Up", style=discord.ButtonStyle.secondary, emoji="🔊")
    async def volume_up_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        if not self.cog.is_playing or not self.cog.ctx.voice_client:
            timestamp = int(time.time()) + 15
            embed = discord.Embed(
                title="❌ LỖI",
                description="```Không có nhạc đang phát!```",
                color=discord.Color.from_rgb(255, 87, 87)
            )
            embed.set_thumbnail(url=self.cog.embed.thumbnail)
            embed.set_footer(text=self.cog.embed.footer_text, icon_url=self.cog.embed.footer_icon)
            embed.add_field(name="Tự xóa sau", value=f"<t:{timestamp}:R>", inline=False)
            msg = await interaction.followup.send(embed=embed)
            await asyncio.sleep(15)
            await msg.delete()
            return
        max_vol = 5.0 if is_owner(self.cog, interaction.user) else 3.0 if has_special_role(self.cog, interaction.user) else 2.0
        self.cog.volume = min(self.cog.volume + 0.1, max_vol)
        if self.cog.current_source:
            self.cog.current_source.volume = self.cog.volume
        await self.cog.embed.update_now_playing(self.cog.ctx, await self.cog.extract_info(self.cog.current_song[0]), 
                                               self.cog.current_song[0], self.cog.current_song[1], self.cog.volume)
        timestamp = int(time.time()) + 15
        embed = discord.Embed(
            title="🔊 ÂM LƯỢNG",
            description=f"Tăng lên: **{int(self.cog.volume * 100)}%**",
            color=discord.Color.from_rgb(147, 112, 219)
        )
        embed.set_thumbnail(url=self.cog.embed.thumbnail)
        embed.set_footer(text=self.cog.embed.footer_text, icon_url=self.cog.embed.footer_icon)
        embed.add_field(name="Tự xóa sau", value=f"<t:{timestamp}:R>", inline=False)
        msg = await interaction.followup.send(embed=embed)
        await asyncio.sleep(15)
        await msg.delete()

    @discord.ui.button(label="Vol Down", style=discord.ButtonStyle.secondary, emoji="🔉")
    async def volume_down_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        if not self.cog.is_playing or not self.cog.ctx.voice_client:
            timestamp = int(time.time()) + 15
            embed = discord.Embed(
                title="❌ LỖI",
                description="```Không có nhạc đang phát!```",
                color=discord.Color.from_rgb(255, 87, 87)
            )
            embed.set_thumbnail(url=self.cog.embed.thumbnail)
            embed.set_footer(text=self.cog.embed.footer_text, icon_url=self.cog.embed.footer_icon)
            embed.add_field(name="Tự xóa sau", value=f"<t:{timestamp}:R>", inline=False)
            msg = await interaction.followup.send(embed=embed)
            await asyncio.sleep(15)
            await msg.delete()
            return
        self.cog.volume = max(self.cog.volume - 0.1, 0.0)
        if self.cog.current_source:
            self.cog.current_source.volume = self.cog.volume
        await self.cog.embed.update_now_playing(self.cog.ctx, await self.cog.extract_info(self.cog.current_song[0]), 
                                               self.cog.current_song[0], self.cog.current_song[1], self.cog.volume)
        timestamp = int(time.time()) + 15
        embed = discord.Embed(
            title="🔊 ÂM LƯỢNG",
            description=f"Giảm xuống: **{int(self.cog.volume * 100)}%**",
            color=discord.Color.from_rgb(147, 112, 219)
        )
        embed.set_thumbnail(url=self.cog.embed.thumbnail)
        embed.set_footer(text=self.cog.embed.footer_text, icon_url=self.cog.embed.footer_icon)
        embed.add_field(name="Tự xóa sau", value=f"<t:{timestamp}:R>", inline=False)
        msg = await interaction.followup.send(embed=embed)
        await asyncio.sleep(15)
        await msg.delete()

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="⏹️")
    async def stop_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        if not can_stop(self.cog, interaction.user):
            timestamp = int(time.time()) + 15
            embed = discord.Embed(
                title="❌ LỖI",
                description="```Bạn không có quyền stop!```",
                color=discord.Color.from_rgb(255, 87, 87)
            )
            embed.set_thumbnail(url=self.cog.embed.thumbnail)
            embed.set_footer(text=self.cog.embed.footer_text, icon_url=self.cog.embed.footer_icon)
            embed.add_field(name="Tự xóa sau", value=f"<t:{timestamp}:R>", inline=False)
            msg = await interaction.followup.send(embed=embed)
            await asyncio.sleep(15)
            await msg.delete()
            return
        if self.cog.ctx.voice_client:
            self.cog.queue.clear()
            self.cog.ctx.voice_client.stop()
            await self.cog.ctx.voice_client.disconnect()
            self.cog.current_source = None
            self.cog.current_requester = None
            self.cog.current_song = None
            self.cog.is_playing = False
            # Xóa thông báo "Danh sách chờ rỗng" nếu có
            if self.cog.embed.queue_empty_message:
                await self.cog.embed.queue_empty_message.delete()
                self.cog.embed.queue_empty_message = None
            # Disable nút ở embed "Đang phát" cũ
            if self.cog.embed.now_playing_message:
                await self.cog.embed.now_playing_message.edit(view=None)
            timestamp = int(time.time()) + 15
            embed = discord.Embed(
                title="✅ THÀNH CÔNG",
                description="```Đã dừng và rời voice.```",
                color=discord.Color.from_rgb(87, 255, 87)
            )
            embed.set_thumbnail(url=self.cog.embed.thumbnail)
            embed.set_footer(text=self.cog.embed.footer_text, icon_url=self.cog.embed.footer_icon)
            embed.add_field(name="Tự xóa sau", value=f"<t:{timestamp}:R>", inline=False)
            msg = await interaction.followup.send(embed=embed)
            await asyncio.sleep(15)
            await msg.delete()

    @discord.ui.button(label="Loop", style=discord.ButtonStyle.grey, emoji="🔁")
    async def loop_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        if not self.cog.is_playing:
            timestamp = int(time.time()) + 15
            embed = discord.Embed(
                title="❌ LỖI",
                description="```Không có nhạc đang phát!```",
                color=discord.Color.from_rgb(255, 87, 87)
            )
            embed.set_thumbnail(url=self.cog.embed.thumbnail)
            embed.set_footer(text=self.cog.embed.footer_text, icon_url=self.cog.embed.footer_icon)
            embed.add_field(name="Tự xóa sau", value=f"<t:{timestamp}:R>", inline=False)
            msg = await interaction.followup.send(embed=embed)
            await asyncio.sleep(15)
            await msg.delete()
            return
        self.cog.loop_mode = 1 - self.cog.loop_mode
        button.label = "Loop (On)" if self.cog.loop_mode else "Loop (Off)"
        button.style = discord.ButtonStyle.green if self.cog.loop_mode else discord.ButtonStyle.grey
        await interaction.edit_original_response(view=self)
        await self.cog.embed.update_now_playing(self.cog.ctx, await self.cog.extract_info(self.cog.current_song[0]), 
                                               self.cog.current_song[0], self.cog.current_song[1], self.cog.volume)
        timestamp = int(time.time()) + 15
        embed = discord.Embed(
            title="🔁 CHẾ ĐỘ LẶP",
            description=f"Trạng thái: **{'Bật' if self.cog.loop_mode else 'Tắt'}**",
            color=discord.Color.from_rgb(147, 112, 219)
        )
        embed.set_thumbnail(url=self.cog.embed.thumbnail)
        embed.set_footer(text=self.cog.embed.footer_text, icon_url=self.cog.embed.footer_icon)
        embed.add_field(name="Tự xóa sau", value=f"<t:{timestamp}:R>", inline=False)
        msg = await interaction.followup.send(embed=embed)
        await asyncio.sleep(15)
        await msg.delete()

class EmbedManager:
    def __init__(self, cog=None, is_owner_func=None, has_special_role_func=None):
        self.thumbnail = "https://cdn.discordapp.com/attachments/934360282615132172/1390920397486161990/simple_baby_bee.png?ex=686a0310&is=6868b190&hm=301e6ff2e10d29122d3b81dcbc0bbf593190291b96c15cb13551b3536514227d&"
        self.footer_icon = "https://cdn.discordapp.com/attachments/934360282615132172/1390920397486161990/simple_baby_bee.png?ex=686a0310&is=6868b190&hm=301e6ff2e10d29122d3b81dcbc0bbf593190291b96c15cb13551b3536514227d&"
        self.footer_text = "Bee BOT | Powered by Kieeu Ngaa"
        self.now_playing_message = None
        self.queue_empty_message = None
        self.disconnect_task = None
        self.cog = cog
        self.is_owner_func = is_owner_func or (lambda cog, user: False)
        self.has_special_role_func = has_special_role_func or (lambda cog, user: False)

    async def send(self, ctx, embed, delete_after=None, view=None):
        embed.set_thumbnail(url=self.thumbnail)
        embed.set_footer(text=self.footer_text, icon_url=self.footer_icon)
        embed.timestamp = discord.utils.utcnow()
        if delete_after:
            timestamp = int(time.time()) + delete_after
            embed.add_field(name="Tự xóa sau", value=f"<t:{timestamp}:R>", inline=False)
        message = await ctx.send(embed=embed, delete_after=delete_after, view=view)
        if embed.title == "🎧 ĐANG PHÁT":
            self.now_playing_message = message
        if embed.title == "📭 DANH SÁCH CHỜ RỖNG":
            self.queue_empty_message = message
        return message

    async def send_error(self, ctx, message, delete_after=15, ephemeral=False):
        timestamp = int(time.time()) + delete_after
        embed = discord.Embed(
            title="❌ LỖI",
            description=f"```{message[:200]}```",
            color=discord.Color.from_rgb(255, 87, 87)
        )
        embed.set_thumbnail(url=self.thumbnail)
        embed.set_footer(text=self.footer_text, icon_url=self.footer_icon)
        embed.add_field(name="Tự xóa sau", value=f"<t:{timestamp}:R>", inline=False)
        if ephemeral:
            msg = await ctx.send(embed=embed, ephemeral=True)
            await asyncio.sleep(delete_after)
            await msg.delete()
        else:
            return await self.send(ctx, embed, delete_after)

    async def send_success(self, ctx, message, delete_after=15, playlist_name=None, ephemeral=False):
        description = f"```{message[:200]}```"
        if playlist_name:
            description += f"\n**Playlist:** {playlist_name}"
        embed = discord.Embed(
            title="✅ THÀNH CÔNG",
            description=description,
            color=discord.Color.from_rgb(87, 255, 87)
        )
        embed.set_thumbnail(url=self.thumbnail)
        embed.set_footer(text=self.footer_text, icon_url=self.footer_icon)
        if delete_after:
            timestamp = int(time.time()) + delete_after
            embed.add_field(name="Tự xóa sau", value=f"<t:{timestamp}:R>", inline=False)
        if ephemeral:
            msg = await ctx.send(embed=embed, ephemeral=True)
            if delete_after:
                await asyncio.sleep(delete_after)
                await msg.delete()
        else:
            return await self.send(ctx, embed, delete_after)

    async def send_now_playing(self, ctx, info, url, requester_id, volume, playlist_name=None):
        user = ctx.guild.get_member(requester_id)
        color = discord.Color.from_rgb(255, 0, 0) if self.is_owner_func(self.cog, user) else \
                discord.Color.from_rgb(255, 215, 0) if self.has_special_role_func(self.cog, user) else \
                discord.Color.from_rgb(66, 135, 245)
        embed = discord.Embed(title="🎧 ĐANG PHÁT", color=color)
        embed.description = (
            f"**Tên bài hát:** [{info.get('title', 'Unknown')}]({url})\n"
            f"**Kênh:** [{info.get('uploader', 'Unknown')}]({info.get('channel_url', url)})\n"
            f"**Người yêu cầu:** <@{requester_id}>\n"
            f"**Âm lượng:** {int(volume * 100)}%\n"
            f"**Lặp:** {'Bật' if self.cog.loop_mode else 'Tắt'}"
        )
        if playlist_name:
            embed.description += f"\n**Playlist:** {playlist_name}"
        view = NowPlayingControls(self.cog)
        return await self.send(ctx, embed, view=view)

    async def update_now_playing(self, ctx, info, url, requester_id, volume):
        if self.now_playing_message:
            user = ctx.guild.get_member(requester_id)
            color = discord.Color.from_rgb(255, 0, 0) if self.is_owner_func(self.cog, user) else \
                    discord.Color.from_rgb(255, 215, 0) if self.has_special_role_func(self.cog, user) else \
                    discord.Color.from_rgb(66, 135, 245)
            embed = discord.Embed(title="🎧 ĐANG PHÁT", color=color)
            embed.description = (
                f"**Tên bài hát:** [{info.get('title', 'Unknown')}]({url})\n"
                f"**Kênh:** [{info.get('uploader', 'Unknown')}]({info.get('channel_url', url)})\n"
                f"**Người yêu cầu:** <@{requester_id}>\n"
                f"**Âm lượng:** {int(volume * 100)}%\n"
                f"**Lặp:** {'Bật' if self.cog.loop_mode else 'Tắt'}"
            )
            embed.set_thumbnail(url=self.thumbnail)
            embed.set_footer(text=self.footer_text, icon_url=self.footer_icon)
            embed.timestamp = discord.utils.utcnow()
            await self.now_playing_message.edit(embed=embed)

    async def send_added_to_queue(self, ctx, info, url, requester_id, is_privileged, delete_after=15):
        user = ctx.guild.get_member(requester_id)
        title = "➕ ĐÃ THÊM VÀO QUEUE" + (" (ĐẶC QUYỀN)" if is_privileged else "")
        color = discord.Color.from_rgb(255, 0, 0) if self.is_owner_func(self.cog, user) else \
                discord.Color.from_rgb(255, 215, 0) if self.has_special_role_func(self.cog, user) else \
                discord.Color.from_rgb(66, 135, 245)
        embed = discord.Embed(title=title, color=color)
        embed.add_field(
            name="Tên bài hát",
            value=f"[{info.get('title', 'Unknown')}]({url})" if info.get('title') else "Unknown",
            inline=False
        )
        embed.add_field(
            name="Kênh",
            value=f"[{info.get('uploader', 'Unknown')}]({info.get('channel_url', url)})",
            inline=True
        )
        embed.add_field(
            name="Người yêu cầu",
            value=f"<@{requester_id}>",
            inline=True
        )
        return await self.send(ctx, embed, delete_after=delete_after)

    async def send_queue(self, ctx, queue, extract_info, delete_after=60):
        if not queue:
            return await ctx.send("**Danh sách chờ trống!**", delete_after=delete_after)
        messages = []
        current_message = "**DANH SÁCH CHỜ**\n─────────────────────\n"
        current_length = len(current_message)
        for i, (url, requester_id) in enumerate(queue, 1):
            info = await extract_info(url)
            title = info.get('title', 'Unknown')
            uploader = info.get('uploader', 'Unknown')
            channel_url = info.get('channel_url', url)
            entry = f"**{i}. Tên bài hát:** [{title}]({url})\n**Kênh:** [{uploader}]({channel_url})\n**Người yêu cầu:** <@{requester_id}>\n─────────────────────\n"
            if current_length + len(entry) > 1900:
                messages.append(current_message)
                current_message = "**DANH SÁCH CHỜ (TIẾP THEO)**\n─────────────────────\n"
                current_length = len(current_message)
            current_message += entry
            current_length += len(entry)
        current_message += f"**Tổng:** {len(queue)} bài"
        messages.append(current_message)
        for message in messages:
            await ctx.send(message, suppress_embeds=True, delete_after=delete_after)

    async def send_volume(self, ctx, volume, delete_after=15):
        timestamp = int(time.time()) + delete_after
        embed = discord.Embed(
            title="🔊 ĐIỀU CHỈNH ÂM LƯỢNG",
            description=f"Đã đặt: **{int(volume * 100)}%**",
            color=discord.Color.from_rgb(147, 112, 219)
        )
        embed.set_thumbnail(url=self.thumbnail)
        embed.set_footer(text=self.footer_text, icon_url=self.footer_icon)
        embed.add_field(name="Tự xóa sau", value=f"<t:{timestamp}:R>", inline=False)
        return await self.send(ctx, embed, delete_after)

    async def send_loop(self, ctx, message, delete_after=15):
        timestamp = int(time.time()) + delete_after
        embed = discord.Embed(
            title="🔁 CHẾ ĐỘ LẶP",
            description=f"Trạng thái: **{message}**",
            color=discord.Color.from_rgb(147, 112, 219)
        )
        embed.set_thumbnail(url=self.thumbnail)
        embed.set_footer(text=self.footer_text, icon_url=self.footer_icon)
        embed.add_field(name="Tự xóa sau", value=f"<t:{timestamp}:R>", inline=False)
        return await self.send(ctx, embed, delete_after)

    async def send_special_roles(self, ctx, role_list, delete_after=15):
        embed = discord.Embed(
            title="📜 DANH SÁCH SPECIAL ROLES",
            description=role_list or "Chưa có role nào.",
            color=discord.Color.from_rgb(66, 135, 245)
        )
        return await self.send(ctx, embed, delete_after=delete_after)

    async def send_server_list(self, ctx, server_list, delete_after=15):
        embed = discord.Embed(
            title="🌐 DANH SÁCH SERVER",
            description=server_list or "Bot chưa tham gia server nào.",
            color=discord.Color.from_rgb(66, 135, 245)
        )
        return await self.send(ctx, embed, delete_after=delete_after)

    async def send_queue_empty(self, ctx, timeout=300, queue_ref=None):
        timestamp = int(time.time()) + timeout
        embed = discord.Embed(
            title="📭 DANH SÁCH CHỜ RỖNG",
            description=f"Queue đã hết. Bot sẽ rời voice sau <t:{timestamp}:R>.",
            color=discord.Color.from_rgb(255, 165, 0)
        )
        message = await self.send(ctx, embed)
        self.disconnect_task = asyncio.create_task(self._wait_and_disconnect(ctx, message, timeout, queue_ref))
        return message

    async def _wait_and_disconnect(self, ctx, message, timeout, queue_ref):
        try:
            elapsed = 0
            while elapsed < timeout:
                await asyncio.sleep(1)
                elapsed += 1
                if queue_ref and len(queue_ref) > 0:
                    logger.info("Queue không còn rỗng, hủy rời voice và xóa thông báo.")
                    if self.queue_empty_message:
                        await self.queue_empty_message.delete()
                        self.queue_empty_message = None
                    self.disconnect_task = None
                    return
            if ctx.voice_client and ctx.voice_client.is_connected():
                logger.info("Bot đang rời voice do queue rỗng.")
                await asyncio.ensure_future(ctx.voice_client.disconnect(force=True))
                if self.queue_empty_message:
                    await self.queue_empty_message.delete()
                    self.queue_empty_message = None
                # Disable nút ở embed "Đang phát" cũ
                if self.now_playing_message:
                    await self.now_playing_message.edit(view=None)
                embed = discord.Embed(
                    title="⏹ ĐÃ RỜI VOICE",
                    description="Bot đã rời voice do danh sách chờ rỗng.",
                    color=discord.Color.from_rgb(255, 87, 87)
                )
                await self.send(ctx, embed)
            else:
                logger.info("Bot không rời voice vì không còn kết nối.")
            self.disconnect_task = None
        except discord.errors.NotFound:
            logger.warning("Thông báo 'Danh sách chờ rỗng' đã bị xóa trước đó.")
            self.queue_empty_message = None
            self.disconnect_task = None
        except Exception as e:
            logger.error(f"Lỗi khi xử lý rời voice: {e}")
            if self.queue_empty_message:
                await self.queue_empty_message.delete()
                self.queue_empty_message = None
            self.disconnect_task = None

    async def cancel_disconnect(self):
        if self.disconnect_task:
            logger.info("Hủy task rời voice do queue có bài mới.")
            self.disconnect_task.cancel()
            self.disconnect_task = None
            if self.queue_empty_message:
                await self.queue_empty_message.delete()
                self.queue_empty_message = None