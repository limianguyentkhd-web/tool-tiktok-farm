# SỔ TAY BÀI HỌC VẬN HÀNH DÀN PHONE FARM TIKTOK 16-17 MÁY
*(Tài liệu cuốn chiếu ghi nhớ các kinh nghiệm, bài học xương máu và quy tắc kỹ thuật)*

---

## 📌 I. QUY TẮC MẠNG & PROXY (NGUYÊN TẮC SỐNG CÒN)

1. **Tuyệt đối bật Proxy trước khi mở TikTok:**
   - Trước khi chạm vào bất kỳ tác vụ nào liên quan đến TikTok, bắt buộc phải kiểm tra giao diện mạng ảo `tun0` đang `UP POINTOPOINT RUNNING`.
   - Luôn sử dụng hàm an toàn `proxy_guard.ensure_proxy_connected(serial)`. Nếu proxy chưa thông mạng, tuyệt đối không được mở app TikTok để tránh lộ IP thật gây shadowban.

2. **Chống trùng lặp cấu hình trên v2rayNG:**
   - Trong v2rayNG, mỗi lần nạp cấu hình mới qua nút `+`, app sẽ tạo thêm một thẻ mới trong danh sách chứ không tự động ghi đè.
   - Khi nạp proxy mới cho máy, phải tự động quét nút thùng rác `layout_remove` để xóa sạch các thẻ proxy cũ/thừa, đảm bảo trên mỗi máy luôn chỉ tồn tại **duy nhất 1 thẻ cấu hình chuẩn**.

3. **Cẩn trọng tuyệt đối với ký tự hoa/thường (Case Sensitivity):**
   - Font chữ hiển thị trên web bán proxy dễ gây nhầm lẫn giữa chữ `I` (viết hoa - India) và chữ `l` (viết thường - Lima) hoặc số `1`.
   - Điển hình: Mật khẩu `TPayuI` có chữ cuối là `I` hoa, nếu nhập `l` thường sẽ bị lỗi `407 Proxy Authentication Required`. Khi gặp lỗi 407, phải kiểm tra đối chiếu ngay các biến thể ký tự này.

---

## 🎬 II. QUY TẮC RENDER & VƯỢT BẢN QUYỀN VIDEO

1. **Pipeline GPU NVENC Siêu Tốc (10 - 15 giây / video):**
   - Bắt buộc xử lý toàn diện chuỗi lọc:
     - Phóng to & Cắt viền: `scale=1112:1976,crop=1080:1920` (khử hash hình ảnh gốc).
     - Chỉnh màu & Độ nét: `eq=contrast=1.03:brightness=0.01:saturation=1.04,unsharp=3:3:0.5:3:3:0.0`.
     - Chỉnh cao độ & Tốc độ âm thanh: `atempo=1.02,volume=1.05` (vượt hệ thống nhận diện bản quyền nhạc).
     - Khử sạch dữ liệu gốc: `-map_metadata -1`.

2. **Luôn chuyển sang tab `Videos` khi chọn video trên TikTok:**
   - Khi vào Album TikTok, luôn bấm tab `Videos` (`x=340, y=240`) thay vì để tab mặc định `All` để không bị chọn nhầm ảnh đại diện hoặc ảnh chụp màn hình vừa chụp.

---

## 👤 III. QUY TẮC HỒ SƠ TIKTOK & NUÔI CLONE LÀM GOLIKE / BUMX

1. **Giới hạn 30 ngày đổi Username:**
   - Nick TikTok mới mua/tạo bị giới hạn đổi Username 30 ngày một lần.
   - Có thể đổi Nickname và Avatar logo AI không giới hạn. Do đó, ưu tiên đổi Nickname thương hiệu và Logo AI trước, Username đổi sau khi hết thời gian cooldown.

2. **Mô hình Hybrid Farm (1 Nick Chính + Nick Phụ):**
   - **Nick Chính (Kênh Affiliate / Live Studio):** Chỉ dùng để đăng video reup chuẩn ngách, nuôi đề xuất, gắn giỏ hàng TikTok Shop. **Tuyệt đối KHÔNG dùng để cày job GoLike / BumX**.
   - **Nick Phụ (Cày GoLike / BumX / Seeding):** Dùng nick clone giá rẻ luân phiên cày job để tạo dòng tiền bù chi phí và tăng tương tác chéo.

3. **QUY TẮC XƯƠNG MÁU: CLONE TRẮNG BẮT BUỘC PHẢI NGÂM NUÔI MỚI CẮN FL, CẮN TIM LÀM NHIỆM VỤ:**
   - **Hiện tượng nếu vội:** Nick clone mới tạo hoặc nick trắng vừa mua về nếu cho vào cày nhiệm vụ GoLike/BumX ngay lập tức thì **TikTok sẽ không ghi nhận tương tác** (hiện tượng "nhả follow, nhả tim", GoLike/BumX báo lỗi nhiệm vụ chưa hoàn thành, hoặc nick bị dính cờ spam/checkpoint 0 view).
   - **Quy trình ngâm nuôi chuẩn (3 giai đoạn):**
     - **Ngày 1 (Ngâm IP & Thiết bị):** Đăng nhập vào máy có Proxy riêng sạch, bật app lướt video trang "Dành cho bạn" (For You) tự nhiên từ 10 - 15 phút. Xem hết video, dừng lại xem comment, tuyệt đối không follow/like dồn dập.
     - **Ngày 2 (Tạo độ Trust người thật):** Cập nhật ảnh đại diện, viết tiểu sử (bio), lướt feed 15 phút, thả 3 - 5 tim tự nhiên cho các video yêu thích, xem livestream 3 - 5 phút.
     - **Ngày 3 trở đi (Bắt đầu làm nhiệm vụ):** Lúc này tài khoản đã được TikTok ghi nhận là người dùng thật (High Trust). Bắt đầu kích hoạt GoLike/BumX từ số lượng ít (10 - 20 job/ngày), sau đó tăng dần đều. Khi đó tài khoản sẽ **cắn 100% follow, cắn tim mượt mà, không bao giờ bị nhả job hay checkpoint!**

---

## 📊 IV. ĐỒNG BỘ DỮ LIỆU
- Mọi ID video sau khi tải phải ghi ngay vào `da_tai.txt` để chống trùng lặp.
- Mọi thông tin tài khoản, mật khẩu, proxy, số view, số like phải cập nhật tự động vào `tai_khoan_farm.json` và bảng tổng hợp `danh_sach_nick_tiktok.xlsx`.
- Mọi nguồn mua nick, bằng chứng hóa đơn phải ghi vào `LICH_SU_MUA_HANG.md` và thư mục `lich_su_mua_hang/`.
