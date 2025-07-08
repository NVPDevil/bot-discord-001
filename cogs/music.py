"""Module xử lý chức năng phát nhạc của bot."""

import discord
from discord.ext import commands
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import asyncio
from utils.permissions import has_special_role, can_skip, can_stop, is_owner
from utils.embed import EmbedManager
from config import Config
import logging
import urllib.parse
import re

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []
        self.is_playing = False
        self.current_source = None
        self.current_requester = None
        self.current_song = None
        self.previous_song = None
        self.volume = 0.3
        self.loop_mode = 0
        self.ctx = None
        self.embed = EmbedManager(cog=self, is_owner_func=is_owner, has_special_role_func=has_special_role)
        self.FFMPEG_PATH = "D:\\ffmpeg\\bin\\ffmpeg.exe"
        self.YTDL_OPTIONS = {
            "format": "bestaudio/best",
            "format_sort": ["hasaud", "ext:mp4"],
            "quiet": True,
            "no-check-formats": True,
            "extractor-args": "youtube:player-client=web;skip=webpage",
            "nocheckcertificate": True,
            "extract_flat": True,
            "retries": 3,
            "playlist_items": "1-25",
        }
        self.FFMPEG_OPTIONS = {
            "executable": self.FFMPEG_PATH,
            "options": "-vn",
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
        }
        self.DISCONNECT_TIMEOUT = 300
        self.EXTRACT_TIMEOUT = 15  # Timeout 15 giây
        self.MAX_PLAYLIST_ITEMS = 25  # Giới hạn 25 bài
        # Khởi tạo Spotify client
        try:
            self.sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
                client_id=Config.SPOTIPY_CLIENT_ID,
                client_secret=Config.SPOTIFY_CLIENT_SECRET
            ))
            logger.info("Đã khởi tạo Spotify client thành công.")
        except Exception as e:
            logger.error(f"Lỗi khởi tạo Spotify client: {e}")
            self.sp = None

    async def extract_info(self, url, is_playlist=False):
        ytdl_opts = self.YTDL_OPTIONS.copy()
        if is_playlist:
            ytdl_opts["extract_flat"] = True
        with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
            try:
                logger.info(f"Đang trích xuất thông tin từ URL: {url}")
                info = await asyncio.to_thread(ydl.extract_info, url, download=False)
                if is_playlist and "entries" in info:
                    if not info["entries"]:
                        logger.warning(f"Playlist tại {url} không có bài nào.")
                        return None
                    playlist_name = info.get("title", "Unknown Playlist")
                    logger.info(f"Tìm thấy playlist với {len(info['entries'])} bài, tên: {playlist_name}")
                    return {"entries": info["entries"], "title": playlist_name}
                logger.info(f"Tìm thấy video đơn lẻ: {info.get('title', 'Unknown')}")
                return info
            except Exception as e:
                logger.error(f"Lỗi trích xuất '{url}': {e}")
                return None

    async def extract_single_video(self, url):
        try:
            info = await asyncio.wait_for(self.extract_info(url, is_playlist=False), timeout=self.EXTRACT_TIMEOUT)
            if info and "url" not in info:
                logger.error(f"Thông tin trích xuất từ {url} thiếu trường 'url': {info}")
                return None
            return info
        except asyncio.TimeoutError:
            logger.error(f"Trích xuất video {url} vượt quá thời gian {self.EXTRACT_TIMEOUT}s.")
            return None
        except Exception as e:
            logger.error(f"Lỗi khi trích xuất video {url}: {e}")
            return None

    async def search_youtube(self, query, duration=None, artist=None):
        ytdl_opts = self.YTDL_OPTIONS.copy()
        ytdl_opts["default_search"] = "ytsearch5"  # Tìm kiếm 5 kết quả
        with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
            try:
                logger.info(f"Tìm kiếm YouTube với query: {query}")
                info = await asyncio.to_thread(ydl.extract_info, f"ytsearch5:{query}", download=False)
                if "entries" in info and info["entries"]:
                    best_match = None
                    for entry in info["entries"]:
                        is_official = entry.get("uploader", "").lower() in ["official", "vevo"]
                        entry_duration = entry.get("duration", 0)
                        duration_diff = abs(entry_duration - (duration or 0)) if duration else float("inf")
                        if is_official and duration_diff < 10:  # Độ lệch thời lượng dưới 10 giây
                            best_match = entry
                            break
                        elif not best_match or (duration_diff < abs(best_match.get("duration", 0) - (duration or 0)) and entry.get("view_count", 0) > best_match.get("view_count", 0)):
                            best_match = entry
                    return best_match.get("webpage_url", best_match.get("url")) if best_match else None
                logger.warning(f"Không tìm thấy video YouTube cho query: {query}")
                return None
            except Exception as e:
                logger.error(f"Lỗi tìm kiếm YouTube '{query}': {e}")
                return None

    async def search_spotify_and_convert(self, query, artist=None, genre=None):
        if not self.sp:
            logger.error("Spotify client không được khởi tạo.")
            return None
        try:
            logger.info(f"Tìm kiếm Spotify với query: {query}, artist: {artist}, genre: {genre}")
            # Tìm kiếm chính xác bài hát
            track_results = self.sp.search(q=f"track:{query} artist:{artist}" if artist else query, type="track", limit=5)
            urls = []
            if track_results["tracks"]["items"]:
                for track in track_results["tracks"]["items"][:self.MAX_PLAYLIST_ITEMS]:
                    name = track["name"]
                    artists = ", ".join(artist["name"] for artist in track["artists"])
                    track_duration_ms = track.get("duration_ms", 0) / 1000
                    youtube_url = await self.search_youtube(f"{name} {artists}", track_duration_ms, artists.split(",")[0])
                    if youtube_url:
                        urls.append(youtube_url)
                        logger.info(f"Đã tìm thấy YouTube URL từ Spotify cho {name} - {artists}: {youtube_url}")
            
            # Nếu không đủ bài, tìm playlist dựa trên chủ đề
            if len(urls) < self.MAX_PLAYLIST_ITEMS and (artist or genre):
                playlist_query = f"artist:{artist} genre:{genre}" if genre else f"artist:{artist}"
                playlist_results = self.sp.search(q=playlist_query, type="playlist", limit=5)
                if playlist_results["playlists"]["items"]:
                    for playlist in playlist_results["playlists"]["items"]:
                        playlist_id = playlist["id"]
                        playlist_info = self.sp.playlist_items(playlist_id, limit=self.MAX_PLAYLIST_ITEMS)
                        for item in playlist_info["items"]:
                            track = item["track"]
                            name = track["name"]
                            artists = ", ".join(artist["name"] for artist in track["artists"])
                            track_duration_ms = track.get("duration_ms", 0) / 1000
                            youtube_url = await self.search_youtube(f"{name} {artists}", track_duration_ms, artists.split(",")[0])
                            if youtube_url and youtube_url not in urls:
                                urls.append(youtube_url)
                                logger.info(f"Đã tìm thấy YouTube URL từ playlist Spotify cho {name} - {artists}: {youtube_url}")
                            if len(urls) >= self.MAX_PLAYLIST_ITEMS:
                                break
                        if len(urls) >= self.MAX_PLAYLIST_ITEMS:
                            break
            
            if urls:
                return urls[:self.MAX_PLAYLIST_ITEMS]
            logger.warning(f"Không tìm thấy track hoặc playlist Spotify cho query: {query}")
            return None
        except Exception as e:
            logger.error(f"Lỗi tìm kiếm Spotify '{query}': {e}")
            return None

    async def extract_spotify_playlist(self, playlist_url):
        if not self.sp:
            logger.error("Spotify client không được khởi tạo.")
            return []
        try:
            playlist_id = re.match(r"https?://open\.spotify\.com/playlist/([a-zA-Z0-9]+)", playlist_url)
            if not playlist_id:
                logger.error(f"URL Spotify không hợp lệ: {playlist_url}")
                return []
            playlist_id = playlist_id.group(1)
            logger.info(f"Trích xuất playlist Spotify: {playlist_id}")
            playlist = self.sp.playlist(playlist_id, fields="name")
            if not playlist:
                logger.error(f"Playlist Spotify {playlist_id} không tồn tại hoặc không khả dụng.")
                return []
            playlist_name = playlist.get("name", "Unknown Playlist")
            results = self.sp.playlist_items(playlist_id, limit=self.MAX_PLAYLIST_ITEMS)
            tracks = results["items"]
            urls = []
            for track in tracks:
                if not track.get("track"):
                    continue
                track_info = track["track"]
                name = track_info["name"]
                artists = ", ".join(artist["name"] for artist in track_info.get("artists", []))
                track_duration_ms = track_info.get("duration_ms", 0) / 1000
                youtube_url = await self.search_youtube(f"{name} {artists}", track_duration_ms, artists.split(",")[0] if artists else None)
                if youtube_url:
                    urls.append(youtube_url)
                    logger.info(f"Đã tìm thấy YouTube URL cho Spotify track: {name} - {artists} -> {youtube_url}")
                else:
                    logger.warning(f"Không tìm thấy YouTube URL cho Spotify track: {name} - {artists}")
            logger.info(f"Đã trích xuất {len(urls)} bài từ playlist Spotify: {playlist_name}")
            return {"urls": urls, "title": playlist_name}
        except Exception as e:
            logger.error(f"Lỗi trích xuất playlist Spotify {playlist_url}: {e}")
            return []

    def _get_queue_position(self, author):
        author_id = author.id
        if is_owner(self, author):
            last_owner_pos = -1
            for i, (_, req_id) in enumerate(self.queue):
                if req_id == author_id:
                    last_owner_pos = i
            return last_owner_pos + 1 if last_owner_pos != -1 else 0
        elif has_special_role(self, author):
            last_special_pos = -1
            for i, (_, req_id) in enumerate(self.queue):
                user = self.ctx.guild.get_member(req_id)
                if user and (is_owner(self, user) or (req_id == author_id)):
                    last_special_pos = i
                elif user and has_special_role(self, user):
                    last_special_pos = i
                else:
                    break
            return last_special_pos + 1 if last_special_pos != -1 else 0
        return len(self.queue)

    async def play_next(self):
        if self.embed.now_playing_message:
            await self.embed.now_playing_message.edit(view=None)
        if self.current_song and self.loop_mode == 1:
            self.queue.insert(0, self.current_song)
        elif self.current_song:
            self.previous_song = self.current_song
        if not self.queue:
            self.is_playing = False
            if self.ctx.voice_client and self.ctx.voice_client.is_connected():
                await self.embed.send_queue_empty(self.ctx, queue_ref=self.queue)
            self.current_source = None
            self.current_requester = None
            self.current_song = None
            logger.info("Hàng đợi rỗng, dừng phát nhạc.")
            return
        self.is_playing = True
        url, requester_id = self.queue.pop(0)
        self.current_requester = requester_id
        self.current_song = (url, requester_id)
        if not self.ctx.voice_client or not self.ctx.voice_client.is_connected():
            await self.ctx.author.voice.channel.connect()
            logger.info(f"Bot đã kết nối lại đến voice channel {self.ctx.author.voice.channel.name}")
        info = await self.extract_single_video(url)
        if not info:
            logger.error(f"Không thể phát bài từ URL {url}, chuyển sang bài tiếp theo.")
            await self.embed.send_error(self.ctx, f"Không thể phát bài từ URL: {url}", delete_after=15)
            await self.play_next()
            return
        try:
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(info["url"], **self.FFMPEG_OPTIONS), volume=self.volume)
            self.current_source = source
            def after_play(error):
                if error:
                    logger.error(f"Lỗi phát nhạc: {error}")
                if self.ctx.voice_client and not self.ctx.voice_client.is_playing():
                    asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop)
            if not self.ctx.voice_client.is_playing():
                self.ctx.voice_client.play(source, after=after_play)
                logger.info(f"Đang phát: {info.get('title', 'Unknown')} (URL: {url})")
                await self.embed.send_now_playing(self.ctx, info, url, requester_id, self.volume)
            else:
                logger.warning(f"Đang phát bài khác, bỏ qua: {url}")
        except Exception as e:
            logger.error(f"Lỗi khi phát bài {url}: {e}")
            await self.embed.send_error(self.ctx, f"Lỗi phát bài: {str(e)[:100]}", delete_after=15)
            await self.play_next()

    @commands.command(name="play")
    async def play(self, ctx, *, query: str):
        self.ctx = ctx
        if not ctx.author.voice:
            logger.warning(f"Người dùng {ctx.author} không ở trong voice channel.")
            return await self.embed.send_error(ctx, "Bạn cần vào voice channel!", delete_after=15)
        if not ctx.voice_client:
            try:
                await ctx.author.voice.channel.connect()
                logger.info(f"Bot đã kết nối đến voice channel {ctx.author.voice.channel.name}")
            except Exception as e:
                logger.error(f"Lỗi kết nối voice channel: {e}")
                return await self.embed.send_error(ctx, "Không thể kết nối đến voice channel!", delete_after=15)
        await self.embed.cancel_disconnect()
        if not query.startswith(("http://", "https://")):
            logger.warning(f"URL không hợp lệ: {query}")
            return await self.embed.send_error(ctx, "Vui lòng cung cấp một URL hợp lệ!", delete_after=15)

        # Kiểm tra loại URL
        parsed_url = urllib.parse.urlparse(query)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        is_youtube = "youtube.com" in parsed_url.netloc or "youtu.be" in parsed_url.netloc
        is_spotify = "open.spotify.com" in parsed_url.netloc
        is_youtube_radio = is_youtube and ("list=RD" in query or "start_radio" in query_params)
        is_youtube_playlist = is_youtube and ("list=" in query.lower() or "playlist" in query.lower()) and not is_youtube_radio

        if is_spotify:
            # Ưu tiên Spotify
            logger.info("Phát hiện URL Spotify, trích xuất danh sách bài.")
            result = await self.extract_spotify_playlist(query)
            if not result or not result.get("urls"):
                logger.error(f"Không thể trích xuất playlist Spotify: {query}")
                return await self.embed.send_error(ctx, "Không thể tải playlist Spotify!", delete_after=15)
            urls = result["urls"]
            playlist_name = result.get("title", "Unknown Playlist")
            added_count = 0
            pos = self._get_queue_position(ctx.author)
            for url in urls[:self.MAX_PLAYLIST_ITEMS]:
                self.queue.insert(pos, (url, ctx.author.id))
                pos += 1
                added_count += 1
                logger.info(f"Đã thêm bài từ Spotify vào hàng đợi: {url}")
            if not self.is_playing:
                await self.play_next()
            await self.embed.send_success(ctx, f"Đã thêm {added_count} bài từ playlist Spotify vào hàng đợi.", delete_after=15, playlist_name=playlist_name)
        elif is_youtube:
            if is_youtube_radio:
                # Playlist radio YouTube: Tìm kiếm trên Spotify
                logger.info("Phát hiện URL playlist radio YouTube, tìm kiếm trên Spotify.")
                clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                if "v" in query_params:
                    clean_url += f"?v={query_params['v'][0]}&list={query_params['list'][0]}"
                result = await asyncio.wait_for(self.extract_info(clean_url, is_playlist=True), timeout=self.EXTRACT_TIMEOUT)
                if not result or not isinstance(result, dict) or not result.get("entries") or not isinstance(result["entries"], list):
                    logger.warning(f"Không thể trích xuất playlist radio từ {clean_url}, tìm kiếm Spotify.")
                    info = await self.extract_single_video(query)
                    if not info:
                        logger.error(f"Không thể trích xuất thông tin từ URL: {query}")
                        return await self.embed.send_error(ctx, "Không thể tải playlist radio YouTube!", delete_after=15)
                    title = info.get("title", "Unknown")
                    artist = info.get("uploader", "").split(",")[0] if info.get("uploader") else None
                    genre = info.get("categories", ["Unknown"])[0] if info.get("categories") else None
                    spotify_urls = await self.search_spotify_and_convert(title, artist, genre)
                    if spotify_urls and isinstance(spotify_urls, list):
                        added_count = 0
                        pos = self._get_queue_position(ctx.author)
                        for url in spotify_urls[:self.MAX_PLAYLIST_ITEMS]:
                            self.queue.insert(pos, (url, ctx.author.id))
                            pos += 1
                            added_count += 1
                            logger.info(f"Đã thêm bài từ Spotify vào hàng đợi: {url}")
                        if not self.is_playing:
                            await self.play_next()
                        await self.embed.send_success(ctx, f"Đã thêm {added_count} bài từ Spotify vào hàng đợi.", delete_after=15, playlist_name="Fallback from Radio")
                        await self.embed.send_error(ctx, "Playlist radio YouTube không tải được, đã tìm kiếm từ Spotify.", delete_after=15)
                    else:
                        logger.warning(f"Không tìm thấy playlist Spotify cho {title}, phát trực tiếp từ Spotify không được hỗ trợ.")
                        return await self.embed.send_error(ctx, "Không tìm thấy danh sách từ YouTube hoặc Spotify. Phát trực tiếp từ Spotify không được hỗ trợ!", delete_after=15)
                else:
                    entries = result["entries"]
                    playlist_name = result.get("title", "Unknown Playlist")
                    added_count = 0
                    pos = self._get_queue_position(ctx.author)
                    for entry in entries[:self.MAX_PLAYLIST_ITEMS]:
                        if isinstance(entry, dict) and (entry.get("webpage_url") or entry.get("url")):
                            song_url = entry.get("webpage_url", entry.get("url"))
                            self.queue.insert(pos, (song_url, ctx.author.id))
                            pos += 1
                            added_count += 1
                            logger.info(f"Đã thêm bài từ playlist radio YouTube vào hàng đợi: {song_url}")
                    if not self.is_playing:
                        await self.play_next()
                    await self.embed.send_success(ctx, f"Đã thêm {added_count} bài từ playlist radio YouTube vào hàng đợi.", delete_after=15, playlist_name=playlist_name)
            elif is_youtube_playlist:
                # Playlist YouTube thông thường: Tìm kiếm trên Spotify
                logger.info("Phát hiện URL playlist YouTube, tìm kiếm trên Spotify.")
                clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                if "list" in query_params:
                    clean_url += f"?list={query_params['list'][0]}"
                result = await asyncio.wait_for(self.extract_info(clean_url, is_playlist=True), timeout=self.EXTRACT_TIMEOUT)
                if not result or not isinstance(result, dict) or not result.get("entries") or not isinstance(result["entries"], list):
                    logger.warning(f"Không thể tải playlist từ {clean_url}, tìm kiếm Spotify.")
                    info = await self.extract_single_video(query)
                    if not info:
                        logger.error(f"Không thể trích xuất thông tin từ URL: {query}")
                        return await self.embed.send_error(ctx, "Không thể tải playlist hoặc video!", delete_after=15)
                    title = info.get("title", "Unknown")
                    artist = info.get("uploader", "").split(",")[0] if info.get("uploader") else None
                    genre = info.get("categories", ["Unknown"])[0] if info.get("categories") else None
                    spotify_urls = await self.search_spotify_and_convert(title, artist, genre)
                    if spotify_urls and isinstance(spotify_urls, list):
                        added_count = 0
                        pos = self._get_queue_position(ctx.author)
                        for url in spotify_urls[:self.MAX_PLAYLIST_ITEMS]:
                            self.queue.insert(pos, (url, ctx.author.id))
                            pos += 1
                            added_count += 1
                            logger.info(f"Đã thêm bài từ Spotify vào hàng đợi: {url}")
                        if not self.is_playing:
                            await self.play_next()
                        await self.embed.send_success(ctx, f"Đã thêm {added_count} bài từ Spotify vào hàng đợi.", delete_after=15, playlist_name="Fallback from Playlist")
                        await self.embed.send_error(ctx, "Playlist YouTube không tải được, đã tìm kiếm từ Spotify.", delete_after=15)
                    else:
                        logger.warning(f"Không tìm thấy playlist Spotify cho {title}, phát trực tiếp từ Spotify không được hỗ trợ.")
                        return await self.embed.send_error(ctx, "Không tìm thấy danh sách từ YouTube hoặc Spotify. Phát trực tiếp từ Spotify không được hỗ trợ!", delete_after=15)
                else:
                    entries = result["entries"]
                    playlist_name = result.get("title", "Unknown Playlist")
                    added_count = 0
                    pos = self._get_queue_position(ctx.author)
                    for entry in entries[:self.MAX_PLAYLIST_ITEMS]:
                        if isinstance(entry, dict) and (entry.get("webpage_url") or entry.get("url")):
                            song_url = entry.get("webpage_url", entry.get("url"))
                            self.queue.insert(pos, (song_url, ctx.author.id))
                            pos += 1
                            added_count += 1
                            logger.info(f"Đã thêm bài từ playlist YouTube vào hàng đợi: {song_url}")
                    if not self.is_playing:
                        await self.play_next()
                    await self.embed.send_success(ctx, f"Đã thêm {added_count} bài từ playlist YouTube vào hàng đợi.", delete_after=15, playlist_name=playlist_name)
            else:
                # Video YouTube đơn lẻ: Tìm kiếm trên Spotify
                logger.info("Phát hiện video YouTube đơn lẻ, tìm kiếm trên Spotify.")
                info = await self.extract_single_video(query)
                if not info:
                    logger.warning(f"Không thể trích xuất video từ {query}, thử tìm kiếm Spotify.")
                    title = re.search(r"(?:v=|watch\?v=)([\w-]+)", query)
                    if title:
                        title = info.get("title", "Unknown") if info else "Unknown"
                        artist = info.get("uploader", "").split(",")[0] if info.get("uploader") else None
                        genre = info.get("categories", ["Unknown"])[0] if info.get("categories") else None
                        spotify_urls = await self.search_spotify_and_convert(title, artist, genre)
                        if spotify_urls and isinstance(spotify_urls, list):
                            pos = self._get_queue_position(ctx.author)
                            for url in spotify_urls[:self.MAX_PLAYLIST_ITEMS]:
                                self.queue.insert(pos, (url, ctx.author.id))
                                pos += 1
                                logger.info(f"Đã thêm bài từ Spotify vào hàng đợi: {url}")
                            if not self.is_playing:
                                await self.play_next()
                            await self.embed.send_error(ctx, "Video YouTube không tải được, đã tìm kiếm từ Spotify.", delete_after=15, playlist_name="Fallback from Video")
                        else:
                            logger.warning(f"Không tìm thấy playlist Spotify cho {title}, phát trực tiếp từ Spotify không được hỗ trợ.")
                            return await self.embed.send_error(ctx, "Không tìm thấy danh sách từ YouTube hoặc Spotify. Phát trực tiếp từ Spotify không được hỗ trợ!", delete_after=15)
                else:
                    if not self.is_playing:
                        self.current_requester = ctx.author.id
                        self.current_song = (query, ctx.author.id)
                        try:
                            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(info["url"], **self.FFMPEG_OPTIONS), volume=self.volume)
                            self.current_source = source
                            def after_play(error):
                                if error:
                                    logger.error(f"Lỗi phát nhạc: {error}")
                                if self.ctx.voice_client and not self.ctx.voice_client.is_playing():
                                    asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop)
                            if not self.ctx.voice_client.is_playing():
                                self.ctx.voice_client.play(source, after=after_play)
                                self.is_playing = True
                                logger.info(f"Đang phát video đơn lẻ: {info.get('title', 'Unknown')} (URL: {query})")
                                await self.embed.send_now_playing(self.ctx, info, query, ctx.author.id, self.volume)
                            else:
                                logger.warning(f"Đang phát bài khác, thêm vào hàng đợi: {query}")
                                pos = self._get_queue_position(ctx.author)
                                self.queue.insert(pos, (query, ctx.author.id))
                                await self.embed.send_added_to_queue(self.ctx, info, query, ctx.author.id, is_privileged=has_special_role(self, ctx.author), delete_after=15)
                        except Exception as e:
                            logger.error(f"Lỗi khi phát bài {query}: {e}")
                            await self.embed.send_error(self.ctx, f"Lỗi phát bài: {str(e)[:100]}", delete_after=15)
                            await self.play_next()
                    else:
                        pos = self._get_queue_position(ctx.author)
                        self.queue.insert(pos, (query, ctx.author.id))
                        logger.info(f"Đã thêm video đơn lẻ vào hàng đợi: {info.get('title', 'Unknown')}")
                        await self.embed.send_added_to_queue(self.ctx, info, query, ctx.author.id, is_privileged=has_special_role(self, ctx.author), delete_after=15)
        else:
            logger.warning(f"URL không được hỗ trợ: {query}")
            return await self.embed.send_error(ctx, "URL không được hỗ trợ!", delete_after=15)

    @commands.command(name="queue")
    async def queue(self, ctx):
        self.ctx = ctx
        await self.embed.send_queue(ctx, self.queue, self.extract_info, delete_after=60)

    @commands.command(name="volume")
    async def volume(self, ctx, vol: float):
        self.ctx = ctx
        if not self.is_playing or not self.ctx.voice_client:
            return await self.embed.send_error(ctx, "Không có nhạc đang phát!", delete_after=15)
        max_vol = 5.0 if is_owner(self, ctx.author) else 3.0 if has_special_role(self, ctx.author) else 2.0
        self.volume = max(0.0, min(vol / 100, max_vol))
        if self.current_source:
            self.current_source.volume = self.volume
        if self.current_song:
            url, requester_id = self.current_song
            info = await self.extract_info(url)
            await self.embed.update_now_playing(self.ctx, info, url, requester_id, self.volume)
        await self.embed.send_volume(self.ctx, self.volume, delete_after=15)

    @commands.command(name="skip")
    async def skip(self, ctx):
        self.ctx = ctx
        if not can_skip(self, ctx.author):
            return await self.embed.send_error(ctx, "Bạn không có quyền skip!", delete_after=15)
        if self.ctx.voice_client and self.ctx.voice_client.is_playing():
            self.ctx.voice_client.stop()
            logger.info(f"Đã skip bài hát bởi {ctx.author}")
            await self.embed.send_success(self.ctx, "Đã skip bài hát.", delete_after=15)

    @commands.command(name="stop")
    async def stop(self, ctx):
        self.ctx = ctx
        if not can_stop(self, ctx.author):
            return await self.embed.send_error(ctx, "Bạn không có quyền stop!", delete_after=15)
        if self.ctx.voice_client:
            self.queue.clear()
            if self.ctx.voice_client.is_playing():
                self.ctx.voice_client.stop()
            await self.ctx.voice_client.disconnect()
            self.current_source = None
            self.current_requester = None
            self.current_song = None
            self.is_playing = False
            if self.embed.queue_empty_message:
                await self.embed.queue_empty_message.delete()
                self.embed.queue_empty_message = None
            if self.embed.now_playing_message:
                await self.embed.now_playing_message.edit(view=None)
            logger.info(f"Bot đã dừng và rời voice channel bởi {ctx.author}")
            await self.embed.send_success(self.ctx, "Đã dừng và rời voice.", delete_after=15)

    @commands.command(name="loop")
    async def loop(self, ctx):
        self.ctx = ctx
        if not self.is_playing:
            return await self.embed.send_error(ctx, "Không có nhạc đang phát!", delete_after=15)
        self.loop_mode = 1 - self.loop_mode
        if self.current_song:
            url, requester_id = self.current_song
            info = await self.extract_info(url)
            await self.embed.update_now_playing(self.ctx, info, url, requester_id, self.volume)
        logger.info(f"Chế độ lặp: {'Bật' if self.loop_mode else 'Tắt'} bởi {ctx.author}")
        await self.embed.send_loop(self.ctx, f"{'Bật' if self.loop_mode else 'Tắt'}", delete_after=15)

    @commands.command(name="summon")
    async def summon(self, ctx, channel: discord.VoiceChannel = None):
        self.ctx = ctx
        if not is_owner(self, ctx.author):
            return self.embed.send_error(ctx, "Chỉ owner mới dùng được lệnh này!", delete_after=15)
        if not channel and ctx.author.voice:
            channel = ctx.author.voice.channel
        elif not channel:
            return self.embed.send_error(ctx, "Bạn cần chỉ định kênh voice hoặc tham gia một kênh voice trong server!", delete_after=15)
        if not ctx.voice_client:
            await channel.connect()
            logger.info(f"Bot đã được triệu hồi đến {channel.name} bởi {ctx.author}")
            await self.embed.send_success(self.ctx, f"Đã triệu hồi bot đến {channel.name}.", delete_after=15)
        elif ctx.voice_client.channel != channel:
            await ctx.voice_client.move_to(channel)
            logger.info(f"Bot đã được di chuyển đến {channel.name} bởi {ctx.author}")
            await self.embed.send_success(self.ctx, f"Đã triệu hồi bot đến {channel.name}.", delete_after=15)
        else:
            return self.embed.send_error(self.ctx, "Bot đã ở trong kênh này!", delete_after=15)

    @commands.command(name="clearqueue")
    async def clear_queue(self, ctx):
        self.ctx = ctx
        if not is_owner(self, ctx.author):
            return self.embed.send_error(ctx, "Chỉ owner mới dùng được lệnh này!", delete_after=15)
        if not ctx.author.voice or not ctx.voice_client or ctx.author.voice.channel != ctx.voice_client.channel:
            return self.embed.send_error(self.ctx, "Bạn cần ở cùng voice channel với bot để dùng lệnh này!", delete_after=15)
        if not self.queue and not self.is_playing:
            return self.embed.send_error(self.ctx, "Không có bài hát nào trong danh sách chờ hoặc đang phát!", delete_after=15)
        self.queue.clear()
        if self.ctx.voice_client and self.ctx.voice_client.is_playing():
            self.ctx.voice_client.stop()
            self.current_source = None
            self.current_requester = None
            self.current_song = None
            self.is_playing = False
            if self.embed.now_playing_message:
                await self.embed.now_playing_message.edit(view=None)
        logger.info(f"Hàng đợi đã được xóa bởi {ctx.author}")
        await self.embed.send_success(self.ctx, "Đã xóa toàn bộ danh sách chờ và bài đang phát.", delete_after=15)

async def setup(bot):
    await bot.add_cog(Music(bot))