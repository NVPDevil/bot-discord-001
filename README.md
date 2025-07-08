# Pii Music Bot

**Pii Music Bot** là một bot Discord được phát triển bằng Python sử dụng thư viện `discord.py`, cho phép người dùng phát nhạc từ YouTube trong voice channel. Bot có giao diện chuyên nghiệp với embed đẹp mắt, hệ thống hàng đợi (queue), và phân quyền linh hoạt cho người dùng thường, special roles, và owner.

## Tính năng chính
- **Phát nhạc**: Hỗ trợ phát nhạc từ URL YouTube.
- **Hàng đợi (Queue)**: Quản lý danh sách nhạc với ưu tiên cho owner và special roles.
- **Điều khiển âm lượng**: Người dùng thường (200%), special roles (300%), owner (500%).
- **Nút điều khiển**: Skip, Stop, Volume Up/Down, Loop qua embed "Đang phát".
- **Phân quyền**: Quyền skip/stop linh hoạt dựa trên người yêu cầu, special roles, hoặc owner.
- **Giới hạn kênh**: Chỉ hoạt động trong một kênh cố định (trừ owner).
- **Tự động xóa**: Tin nhắn lệnh bị xóa ngay lập tức, thông báo tự xóa sau 15s (hoặc 60s với `queue` và `help`).

## Yêu cầu hệ thống
- **Python**: 3.8 trở lên.
- **FFmpeg**: Để xử lý âm thanh (cần cài đặt riêng).
- **Thư viện Python**: Được liệt kê trong `requirements.txt`.

## Cài đặt

### 1. Clone repository
```bash
git clone <đường-dẫn-repository-của-bạn>
cd music-bot
```

### 2. Cài đặt thư viện
Cài đặt các thư viện cần thiết bằng lệnh:
```bash
pip install -r requirements.txt
```

### 3. Cài đặt FFmpeg
- **Windows**:
  1. Tải FFmpeg từ [trang chính thức](https://ffmpeg.org/download.html).
  2. Giải nén và thêm đường dẫn tới thư mục `bin` (chứa `ffmpeg.exe`) vào biến môi trường PATH.
  3. Cập nhật đường dẫn trong `music.py`:
     ```python
     self.FFMPEG_PATH = "đường-dẫn-đến-ffmpeg.exe"
     ```
- **Linux/MacOS**:
  ```bash
  sudo apt-get install ffmpeg  # Ubuntu/Debian
  brew install ffmpeg          # MacOS với Homebrew
  ```

### 4. Cấu hình bot
Mở file `config.py` và chỉnh sửa các thông tin sau:
```python
class Config:
    PREFIX = "!"  # Tiền tố lệnh
    TOKEN = "YOUR_BOT_TOKEN"  # Token bot từ Discord Developer Portal
    OWNER_ID = YOUR_OWNER_ID  # ID Discord của bạn
    SPECIAL_ROLE_IDS = [ROLE_ID_1, ROLE_ID_2]  # Danh sách ID role đặc biệt
    ALLOWED_CHANNEL_ID = YOUR_CHANNEL_ID  # ID kênh cố định cho bot hoạt động
```
- **Token**: Tạo bot tại [Discord Developer Portal](https://discord.com/developers/applications), lấy token từ tab "Bot".
- **Owner ID**: Nhấp chuột phải vào tên bạn trên Discord -> "Copy ID" (bật Developer Mode trong Discord).
- **Channel ID**: Nhấp chuột phải vào kênh -> "Copy ID".

### 5. Chạy bot
```bash
python main.py
```
Bot sẽ đăng nhập và hiển thị trạng thái: "Listening to !help | Pii Music".

## Danh sách lệnh

### Người dùng thường
- `!play <URL>`: Phát nhạc từ URL YouTube.
- `!queue`: Xem danh sách nhạc đang chờ (tự xóa sau 60s).
- `!volume <0-200>`: Điều chỉnh âm lượng (tối đa 200%).
- `!skip`: Bỏ qua bài hát (chỉ bài do bạn yêu cầu).
- `!stop`: Dừng và rời voice (chỉ bài do bạn yêu cầu).
- `!loop`: Bật/tắt chế độ lặp bài hiện tại.
- `!help`: Xem hướng dẫn sử dụng (tự xóa sau 60s).

### Special Roles
- Bao gồm tất cả lệnh người dùng thường.
- `!skip`: Bỏ qua bất kỳ bài hát nào.
- `!stop`: Dừng và rời voice bất kỳ lúc nào.
- `!volume <0-300>`: Âm lượng tối đa 300%.

### Owner
- Bao gồm tất cả lệnh của special roles.
- `!specialroles`: Xem danh sách special roles.
- `!addspecial <role_id>`: Thêm role vào special roles.
- `!removespecial <role_id>`: Xóa role khỏi special roles.
- `!servers`: Xem danh sách server bot đang tham gia.
- `!volume <0-500>`: Âm lượng tối đa 500%.
- `!summon <channel>`: Triệu hồi bot đến voice channel cụ thể.
- `!clearqueue`: Xóa toàn bộ hàng đợi và bài đang phát.

## Chất lượng âm thanh
- **Hiện tại**: 
  - Bitrate: ~128-256 kbps (AAC).
  - Sample rate: 44.1-48 kHz.
  - Nguồn: YouTube (giới hạn bởi định dạng "bestaudio").
- **Giới hạn**: Chất lượng bị ảnh hưởng bởi nguồn YouTube và bitrate voice channel Discord (128 kbps cho server free, 384 kbps cho server boost cao cấp).

## Cấu trúc thư mục
```
music-bot/
├── cogs/
│   ├── admin.py      # Lệnh quản trị
│   ├── moderation.py # Chức năng quản lý (trống)
│   └── music.py      # Chức năng phát nhạc
├── utils/
│   ├── embed.py      # Quản lý giao diện embed
│   └── permissions.py # Kiểm tra quyền
├── config.py         # Cấu hình bot
├── main.py           # Điểm khởi động
├── requirements.txt  # Danh sách thư viện
└── README.md         # Tài liệu này
```

## Góp ý & Báo lỗi
- Nếu gặp lỗi, kiểm tra log trong console và gửi issue kèm chi tiết.
- Góp ý qua Discord: <@745800027364130876> hoặc email: vanphimt123@gmail.com.

## Tác giả
- **NVP Devil**: Người phát triển chính.
- **Pii BOT**: Powered by NVP Devil.

## Giấy phép
- Dự án này sử dụng mã nguồn mở, không có giấy phép chính thức. Vui lòng ghi nhận tác giả nếu sử dụng lại.