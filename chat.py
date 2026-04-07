from flask import Flask, render_template, request, jsonify, session
import re
import os
from datetime import datetime
from difflib import SequenceMatcher
from google import genai

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ==================== DỮ LIỆU SIÊU THỊ ====================

PRODUCTS = {
    # === SỮA ===
    "sữa vinamilk 1l": {"giá": 32000, "vị_trí": "Kệ A1 - Tầng 1", "danh_mục": "sữa", "mô_tả": "Sữa tươi tiệt trùng Vinamilk 1 lít", "khuyến_mãi": "Mua 2 giảm 10%", "hình": "🥛", "đánh_giá": 4.5},
    "sữa th true milk 1l": {"giá": 35000, "vị_trí": "Kệ A1 - Tầng 1", "danh_mục": "sữa", "mô_tả": "Sữa tươi sạch TH True Milk 1 lít", "khuyến_mãi": None, "hình": "🥛", "đánh_giá": 4.7},
    "sữa grow plus 900g": {"giá": 285000, "vị_trí": "Kệ A2 - Tầng 1", "danh_mục": "sữa", "mô_tả": "Sữa bột Abbott Grow Plus cho trẻ 2-6 tuổi", "khuyến_mãi": "Giảm 15% đến hết tháng", "hình": "🍼", "đánh_giá": 4.6},
    "sữa enfamil 900g": {"giá": 395000, "vị_trí": "Kệ A2 - Tầng 1", "danh_mục": "sữa", "mô_tả": "Sữa bột Enfamil A+ cho trẻ 0-6 tháng", "khuyến_mãi": "Tặng bình sữa khi mua 2 hộp", "hình": "🍼", "đánh_giá": 4.8},
    "sữa optimum gold 900g": {"giá": 310000, "vị_trí": "Kệ A2 - Tầng 1", "danh_mục": "sữa", "mô_tả": "Sữa bột Vinamilk Optimum Gold cho trẻ 1-2 tuổi", "khuyến_mãi": "Giảm 20.000đ", "hình": "🍼", "đánh_giá": 4.5},
    "sữa chua vinamilk lốc 4": {"giá": 28000, "vị_trí": "Kệ A3 - Tầng 1", "danh_mục": "sữa", "mô_tả": "Sữa chua Vinamilk có đường lốc 4 hộp", "khuyến_mãi": None, "hình": "🥛", "đánh_giá": 4.3},
    "sữa ensure 850g": {"giá": 520000, "vị_trí": "Kệ A2 - Tầng 1", "danh_mục": "sữa", "mô_tả": "Sữa Ensure Gold dành cho người lớn tuổi 850g", "khuyến_mãi": "Giảm 50.000đ", "hình": "🥛", "đánh_giá": 4.7},
    "sữa đậu nành fami 1l": {"giá": 22000, "vị_trí": "Kệ A3 - Tầng 1", "danh_mục": "sữa", "mô_tả": "Sữa đậu nành Fami nguyên chất 1 lít", "khuyến_mãi": None, "hình": "🥛", "đánh_giá": 4.2},

    # === MÌ - THỰC PHẨM KHÔ ===
    "mì hảo hảo tôm chua cay": {"giá": 4000, "vị_trí": "Kệ B1 - Tầng 1", "danh_mục": "mì", "mô_tả": "Mì Hảo Hảo vị tôm chua cay", "khuyến_mãi": "Mua thùng 30 gói giảm 15%", "hình": "🍜", "đánh_giá": 4.4},
    "mì omachi xốt bò hầm": {"giá": 5500, "vị_trí": "Kệ B1 - Tầng 1", "danh_mục": "mì", "mô_tả": "Mì khoai tây Omachi xốt bò hầm", "khuyến_mãi": None, "hình": "🍜", "đánh_giá": 4.5},
    "phở bò vifon": {"giá": 6000, "vị_trí": "Kệ B1 - Tầng 1", "danh_mục": "mì", "mô_tả": "Phở bò ăn liền Vifon", "khuyến_mãi": "Mua 5 tặng 1", "hình": "🍜", "đánh_giá": 4.3},
    "cháo ăn liền cây thị": {"giá": 7000, "vị_trí": "Kệ B2 - Tầng 1", "danh_mục": "mì", "mô_tả": "Cháo ăn liền Cây Thị vị gà", "khuyến_mãi": None, "hình": "🥣", "đánh_giá": 4.1},
    "bún bò huế vifon": {"giá": 6500, "vị_trí": "Kệ B1 - Tầng 1", "danh_mục": "mì", "mô_tả": "Bún bò Huế ăn liền Vifon", "khuyến_mãi": None, "hình": "🍜", "đánh_giá": 4.2},

    # === NƯỚC GIẢI KHÁT ===
    "coca cola 330ml": {"giá": 10000, "vị_trí": "Kệ C1 - Tầng 1", "danh_mục": "nước giải khát", "mô_tả": "Nước ngọt Coca Cola lon 330ml", "khuyến_mãi": "Mua lốc 6 giảm 5.000đ", "hình": "🥤", "đánh_giá": 4.5},
    "pepsi 330ml": {"giá": 9500, "vị_trí": "Kệ C1 - Tầng 1", "danh_mục": "nước giải khát", "mô_tả": "Nước ngọt Pepsi lon 330ml", "khuyến_mãi": None, "hình": "🥤", "đánh_giá": 4.4},
    "trà xanh 0 độ 500ml": {"giá": 10000, "vị_trí": "Kệ C2 - Tầng 1", "danh_mục": "nước giải khát", "mô_tả": "Trà xanh không độ 500ml", "khuyến_mãi": "Mua 2 tặng 1", "hình": "🍵", "đánh_giá": 4.6},
    "nước suối aquafina 500ml": {"giá": 5000, "vị_trí": "Kệ C2 - Tầng 1", "danh_mục": "nước giải khát", "mô_tả": "Nước tinh khiết Aquafina 500ml", "khuyến_mãi": None, "hình": "💧", "đánh_giá": 4.2},
    "sting dâu 330ml": {"giá": 10000, "vị_trí": "Kệ C1 - Tầng 1", "danh_mục": "nước giải khát", "mô_tả": "Nước tăng lực Sting dâu 330ml", "khuyến_mãi": None, "hình": "⚡", "đánh_giá": 4.1},
    "nước ép cam teppy 1l": {"giá": 28000, "vị_trí": "Kệ C2 - Tầng 1", "danh_mục": "nước giải khát", "mô_tả": "Nước ép cam Teppy 1 lít", "khuyến_mãi": "Mua 2 giảm 10%", "hình": "🍊", "đánh_giá": 4.4},
    "cà phê g7 hộp 18 gói": {"giá": 52000, "vị_trí": "Kệ C3 - Tầng 1", "danh_mục": "nước giải khát", "mô_tả": "Cà phê hòa tan G7 3in1 hộp 18 gói", "khuyến_mãi": None, "hình": "☕", "đánh_giá": 4.5},

    # === BÁNH KẸO ===
    "bánh oreo 133g": {"giá": 22000, "vị_trí": "Kệ D1 - Tầng 2", "danh_mục": "bánh kẹo", "mô_tả": "Bánh quy Oreo nhân kem vani 133g", "khuyến_mãi": None, "hình": "🍪", "đánh_giá": 4.4},
    "bánh chocopie 396g": {"giá": 45000, "vị_trí": "Kệ D1 - Tầng 2", "danh_mục": "bánh kẹo", "mô_tả": "Bánh Chocopie hộp 12 cái 396g", "khuyến_mãi": "Giảm 10.000đ", "hình": "🍫", "đánh_giá": 4.6},
    "kẹo alpenliebe hộp": {"giá": 35000, "vị_trí": "Kệ D2 - Tầng 2", "danh_mục": "bánh kẹo", "mô_tả": "Kẹo Alpenliebe hộp 16 thỏi", "khuyến_mãi": None, "hình": "🍬", "đánh_giá": 4.2},
    "snack poca khoai tây 54g": {"giá": 12000, "vị_trí": "Kệ D2 - Tầng 2", "danh_mục": "bánh kẹo", "mô_tả": "Snack Poca khoai tây vị tự nhiên 54g", "khuyến_mãi": "Mua 3 giảm 20%", "hình": "🥔", "đánh_giá": 4.3},
    "bánh mì sandwich kinh đô": {"giá": 25000, "vị_trí": "Kệ D3 - Tầng 2", "danh_mục": "bánh kẹo", "mô_tả": "Bánh mì sandwich Kinh Đô 100g", "khuyến_mãi": None, "hình": "🍞", "đánh_giá": 4.1},

    # === GIA VỊ ===
    "nước mắm nam ngư 500ml": {"giá": 28000, "vị_trí": "Kệ E1 - Tầng 2", "danh_mục": "gia vị", "mô_tả": "Nước mắm Nam Ngư 500ml", "khuyến_mãi": None, "hình": "🍶", "đánh_giá": 4.3},
    "dầu ăn neptune 1l": {"giá": 42000, "vị_trí": "Kệ E1 - Tầng 2", "danh_mục": "gia vị", "mô_tả": "Dầu ăn Neptune 1 lít", "khuyến_mãi": "Giảm 8.000đ", "hình": "🫗", "đánh_giá": 4.4},
    "bột ngọt ajinomoto 454g": {"giá": 30000, "vị_trí": "Kệ E2 - Tầng 2", "danh_mục": "gia vị", "mô_tả": "Bột ngọt Ajinomoto 454g", "khuyến_mãi": None, "hình": "🧂", "đánh_giá": 4.5},
    "nước tương maggi 300ml": {"giá": 15000, "vị_trí": "Kệ E2 - Tầng 2", "danh_mục": "gia vị", "mô_tả": "Nước tương Maggi 300ml", "khuyến_mãi": None, "hình": "🍶", "đánh_giá": 4.3},
    "tương ớt chinsu 250ml": {"giá": 14000, "vị_trí": "Kệ E2 - Tầng 2", "danh_mục": "gia vị", "mô_tả": "Tương ớt Chinsu 250ml", "khuyến_mãi": None, "hình": "🌶️", "đánh_giá": 4.2},
    "hạt nêm knorr 400g": {"giá": 38000, "vị_trí": "Kệ E2 - Tầng 2", "danh_mục": "gia vị", "mô_tả": "Hạt nêm Knorr từ thịt 400g", "khuyến_mãi": "Giảm 5.000đ", "hình": "🧂", "đánh_giá": 4.5},

    # === THỊT - HẢI SẢN ===
    "thịt heo xay 500g": {"giá": 65000, "vị_trí": "Quầy tươi sống F1 - Tầng 1", "danh_mục": "thịt", "mô_tả": "Thịt heo xay 500g", "khuyến_mãi": None, "hình": "🥩", "đánh_giá": 4.3},
    "thịt bò úc 500g": {"giá": 180000, "vị_trí": "Quầy tươi sống F1 - Tầng 1", "danh_mục": "thịt", "mô_tả": "Thịt bò Úc nhập khẩu 500g", "khuyến_mãi": "Giảm 15% cuối tuần", "hình": "🥩", "đánh_giá": 4.6},
    "gà ta nguyên con": {"giá": 120000, "vị_trí": "Quầy tươi sống F1 - Tầng 1", "danh_mục": "thịt", "mô_tả": "Gà ta nguyên con ~1.2kg", "khuyến_mãi": None, "hình": "🍗", "đánh_giá": 4.5},
    "cá hồi fillet 300g": {"giá": 120000, "vị_trí": "Quầy tươi sống F2 - Tầng 1", "danh_mục": "hải sản", "mô_tả": "Cá hồi fillet đông lạnh 300g", "khuyến_mãi": "Giảm 20% vào thứ 6", "hình": "🐟", "đánh_giá": 4.7},
    "tôm sú 500g": {"giá": 95000, "vị_trí": "Quầy tươi sống F2 - Tầng 1", "danh_mục": "hải sản", "mô_tả": "Tôm sú tươi 500g", "khuyến_mãi": None, "hình": "🦐", "đánh_giá": 4.4},
    "mực ống 500g": {"giá": 85000, "vị_trí": "Quầy tươi sống F2 - Tầng 1", "danh_mục": "hải sản", "mô_tả": "Mực ống tươi 500g", "khuyến_mãi": None, "hình": "🦑", "đánh_giá": 4.3},

    # === RAU CỦ QUẢ ===
    "cà chua 1kg": {"giá": 25000, "vị_trí": "Khu rau củ G1 - Tầng 1", "danh_mục": "rau củ", "mô_tả": "Cà chua tươi 1kg", "khuyến_mãi": None, "hình": "🍅", "đánh_giá": 4.2},
    "khoai tây 1kg": {"giá": 30000, "vị_trí": "Khu rau củ G1 - Tầng 1", "danh_mục": "rau củ", "mô_tả": "Khoai tây tươi 1kg", "khuyến_mãi": None, "hình": "🥔", "đánh_giá": 4.2},
    "táo fuji 1kg": {"giá": 75000, "vị_trí": "Khu trái cây G2 - Tầng 1", "danh_mục": "trái cây", "mô_tả": "Táo Fuji nhập khẩu 1kg", "khuyến_mãi": "Giảm 15%", "hình": "🍎", "đánh_giá": 4.6},
    "rau xà lách 300g": {"giá": 12000, "vị_trí": "Khu rau củ G1 - Tầng 1", "danh_mục": "rau củ", "mô_tả": "Rau xà lách tươi 300g", "khuyến_mãi": None, "hình": "🥬", "đánh_giá": 4.1},
    "chuối già 1kg": {"giá": 20000, "vị_trí": "Khu trái cây G2 - Tầng 1", "danh_mục": "trái cây", "mô_tả": "Chuối già hương 1kg", "khuyến_mãi": None, "hình": "🍌", "đánh_giá": 4.3},
    "bưởi da xanh 1 trái": {"giá": 45000, "vị_trí": "Khu trái cây G2 - Tầng 1", "danh_mục": "trái cây", "mô_tả": "Bưởi da xanh 1 trái (~1kg)", "khuyến_mãi": "Mua 2 giảm 10.000đ", "hình": "🍊", "đánh_giá": 4.5},
    "hành tây 500g": {"giá": 15000, "vị_trí": "Khu rau củ G1 - Tầng 1", "danh_mục": "rau củ", "mô_tả": "Hành tây tươi 500g", "khuyến_mãi": None, "hình": "🧅", "đánh_giá": 4.0},

    # === ĐỒ DÙNG GIA ĐÌNH ===
    "nước rửa chén sunlight 750ml": {"giá": 32000, "vị_trí": "Kệ H1 - Tầng 2", "danh_mục": "đồ dùng gia đình", "mô_tả": "Nước rửa chén Sunlight chanh 750ml", "khuyến_mãi": "Mua 1 tặng 1 (size nhỏ)", "hình": "🧴", "đánh_giá": 4.4},
    "bột giặt omo 4.5kg": {"giá": 155000, "vị_trí": "Kệ H2 - Tầng 2", "danh_mục": "đồ dùng gia đình", "mô_tả": "Bột giặt OMO Matic 4.5kg", "khuyến_mãi": "Giảm 30.000đ", "hình": "🧺", "đánh_giá": 4.6},
    "giấy vệ sinh pulppy 12 cuộn": {"giá": 65000, "vị_trí": "Kệ H3 - Tầng 2", "danh_mục": "đồ dùng gia đình", "mô_tả": "Giấy vệ sinh Pulppy 12 cuộn", "khuyến_mãi": None, "hình": "🧻", "đánh_giá": 4.3},
    "nước lau sàn vim 1l": {"giá": 28000, "vị_trí": "Kệ H1 - Tầng 2", "danh_mục": "đồ dùng gia đình", "mô_tả": "Nước lau sàn Vim hương lavender 1 lít", "khuyến_mãi": None, "hình": "🧹", "đánh_giá": 4.2},
    "kem đánh răng ps 200g": {"giá": 28000, "vị_trí": "Kệ H4 - Tầng 2", "danh_mục": "đồ dùng gia đình", "mô_tả": "Kem đánh răng PS bạc hà 200g", "khuyến_mãi": "Mua 2 giảm 15%", "hình": "🪥", "đánh_giá": 4.3},
    "dầu gội clear 650ml": {"giá": 115000, "vị_trí": "Kệ H4 - Tầng 2", "danh_mục": "đồ dùng gia đình", "mô_tả": "Dầu gội Clear bạc hà 650ml", "khuyến_mãi": "Giảm 20.000đ", "hình": "🧴", "đánh_giá": 4.5},

    # === ĐỒ ĐÔNG LẠNH ===
    "xúc xích vissan 500g": {"giá": 55000, "vị_trí": "Tủ đông lạnh I1 - Tầng 1", "danh_mục": "đông lạnh", "mô_tả": "Xúc xích tiệt trùng Vissan 500g", "khuyến_mãi": None, "hình": "🌭", "đánh_giá": 4.2},
    "há cảo đông lạnh 500g": {"giá": 65000, "vị_trí": "Tủ đông lạnh I1 - Tầng 1", "danh_mục": "đông lạnh", "mô_tả": "Há cảo tôm thịt đông lạnh 500g", "khuyến_mãi": "Giảm 10.000đ", "hình": "🥟", "đánh_giá": 4.4},
    "kem wall's 450ml": {"giá": 75000, "vị_trí": "Tủ đông lạnh I2 - Tầng 1", "danh_mục": "đông lạnh", "mô_tả": "Kem Wall's vị chocolate 450ml", "khuyến_mãi": "Mua 2 giảm 20%", "hình": "🍦", "đánh_giá": 4.6},
}

CATEGORIES = {
    "sữa": {"icon": "🥛", "mô_tả": "Sữa tươi, sữa bột, sữa chua"},
    "mì": {"icon": "🍜", "mô_tả": "Mì ăn liền, phở, bún, cháo"},
    "nước giải khát": {"icon": "🥤", "mô_tả": "Nước ngọt, trà, nước ép, cà phê"},
    "bánh kẹo": {"icon": "🍪", "mô_tả": "Bánh quy, snack, kẹo"},
    "gia vị": {"icon": "🧂", "mô_tả": "Nước mắm, dầu ăn, gia vị nấu ăn"},
    "thịt": {"icon": "🥩", "mô_tả": "Thịt heo, bò, gà"},
    "hải sản": {"icon": "🦐", "mô_tả": "Cá, tôm, mực"},
    "rau củ": {"icon": "🥬", "mô_tả": "Rau xanh, củ quả tươi"},
    "trái cây": {"icon": "🍎", "mô_tả": "Trái cây nhập khẩu & nội địa"},
    "đồ dùng gia đình": {"icon": "🧴", "mô_tả": "Chất tẩy rửa, vệ sinh cá nhân"},
    "đông lạnh": {"icon": "🧊", "mô_tả": "Thực phẩm đông lạnh, kem"},
}

STORE_MAP = {
    "Tầng 1": {
        "Kệ A1-A3": "🥛 Sữa & sản phẩm từ sữa",
        "Kệ B1-B2": "🍜 Mì ăn liền & thực phẩm khô",
        "Kệ C1-C3": "🥤 Nước giải khát & cà phê",
        "Quầy F1": "🥩 Thịt tươi",
        "Quầy F2": "🦐 Hải sản",
        "Khu G1": "🥬 Rau củ tươi",
        "Khu G2": "🍎 Trái cây",
        "Tủ I1-I2": "🧊 Thực phẩm đông lạnh",
        "Quầy thu ngân": "💳 Gần cửa ra vào",
    },
    "Tầng 2": {
        "Kệ D1-D3": "🍪 Bánh kẹo & snack",
        "Kệ E1-E2": "🧂 Gia vị & dầu ăn",
        "Kệ H1-H4": "🧴 Đồ dùng gia đình & vệ sinh",
    },
}

# === COMBO DEALS ===
COMBOS = {
    "combo lẩu": {
        "sản_phẩm": ["thịt bò úc 500g", "rau xà lách 300g", "nấm", "nước mắm nam ngư 500ml"],
        "giảm_phần_trăm": 10,
        "hình": "🍲",
        "mô_tả": "Combo Lẩu Bò Thịnh Soạn"
    },
    "combo ăn sáng": {
        "sản_phẩm": ["bánh mì sandwich kinh đô", "sữa vinamilk 1l", "sữa chua vinamilk lốc 4"],
        "giảm_phần_trăm": 8,
        "hình": "🌅",
        "mô_tả": "Combo Bữa Sáng Năng Lượng"
    },
    "combo tiệc": {
        "sản_phẩm": ["coca cola 330ml", "pepsi 330ml", "snack poca khoai tây 54g", "bánh chocopie 396g", "kem wall's 450ml"],
        "giảm_phần_trăm": 12,
        "hình": "🎉",
        "mô_tả": "Combo Tiệc Vui Vẻ"
    },
    "combo nấu phở": {
        "sản_phẩm": ["phở bò vifon", "thịt bò úc 500g", "hành tây 500g", "nước mắm nam ngư 500ml"],
        "giảm_phần_trăm": 10,
        "hình": "🍜",
        "mô_tả": "Combo Phở Bò Tại Nhà"
    },
}


# ==================== CẤU HÌNH AI ====================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
# 👇 Lấy API key miễn phí tại: https://aistudio.google.com/apikey
# GEMINI_API_KEY = "paste-your-key-here"

def build_system_prompt():
    product_info = ""
    for name, info in PRODUCTS.items():
        promo = f", KM: {info['khuyến_mãi']}" if info.get('khuyến_mãi') else ""
        product_info += f"- {name}: {info['mô_tả']}, giá {info['giá']:,}đ, tại {info['vị_trí']}{promo}, ⭐{info.get('đánh_giá', 'N/A')}\n"
    combo_info = ""
    for key, combo in COMBOS.items():
        combo_info += f"- {key}: {combo['mô_tả']}, gồm: {', '.join(combo['sản_phẩm'])}, giảm {combo['giảm_phần_trăm']}%\n"

    return f"""Bạn là trợ lý AI thân thiện của Siêu Thị ABC. Trả lời tiếng Việt, ngắn gọn, dùng emoji.

SẢN PHẨM CÓ BÁN:
{product_info}
COMBO TIẾT KIỆM:
{combo_info}
SƠ ĐỒ SIÊU THỊ:
Tầng 1: Sữa (Kệ A1-A3), Mì (B1-B2), Nước giải khát (C1-C3), Thịt (Quầy F1), Hải sản (F2), Rau củ (G1), Trái cây (G2), Đông lạnh (Tủ I1-I2), Thu ngân gần cửa ra
Tầng 2: Bánh kẹo (D1-D3), Gia vị (E1-E2), Đồ gia dụng (H1-H4)

MIỄN PHÍ SHIP đơn từ 200.000đ. Ship 25.000đ nếu dưới 200k.
Hotline: 1900-1234. Giao hàng 1-2 giờ.

QUY TẮC:
1. Trả lời ngắn gọn, thân thiện, dùng emoji phù hợp
2. Chỉ giới thiệu sản phẩm CÓ TRONG danh sách. Không bịa sản phẩm
3. Khi gợi ý SP, kèm tên chính xác + giá. Nhắc gõ 'mua [tên SP]' để mua
4. Tư vấn thông minh: nấu ăn → gợi nguyên liệu, trẻ em → gợi sữa, tiệc → gợi combo
5. Nếu hỏi ngoài siêu thị, lịch sự chuyển hướng về mua sắm
6. KHÔNG dùng markdown (**, ##, ``). Chỉ dùng emoji và text thường
7. Nhớ ngữ cảnh hội thoại trước đó
8. Nếu khách nói chung chung, hỏi thêm để tư vấn chính xác"""


ai_model = None
ai_client = None
SYSTEM_PROMPT = None
if GEMINI_API_KEY:
    try:
        ai_client = genai.Client(api_key=GEMINI_API_KEY)
        SYSTEM_PROMPT = build_system_prompt()
        ai_model = 'gemini-2.0-flash'
        print("✅ AI Gemini đã kích hoạt! Chatbot thông minh sẵn sàng.")
    except Exception as e:
        print(f"⚠️ Không thể khởi tạo AI: {e}")
        ai_client = None
else:
    print("ℹ️  Chưa có GEMINI_API_KEY. Chatbot chạy chế độ keyword.")
    print("   Lấy key miễn phí: https://aistudio.google.com/apikey")


# ==================== HTML CARD GENERATORS ====================

def html_product_card(name, info, show_buy=True):
    """Generate an HTML card for a single product."""
    stars_count = int(info.get("đánh_giá", 0))
    stars_html = "★" * stars_count + "☆" * (5 - stars_count)
    promo_html = f'<div class="pc-promo">🎁 {info["khuyến_mãi"]}</div>' if info.get("khuyến_mãi") else ""
    buy_html = f'<button class="pc-buy" onclick="quickSend(\'mua {name}\')">🛒 Thêm giỏ</button>' if show_buy else ""
    safe_name = name.replace("'", "\\'")
    return f'''<div class="product-card">
        <div class="pc-icon">{info.get("hình", "📦")}</div>
        <div class="pc-body">
            <div class="pc-name">{info["mô_tả"]}</div>
            <div class="pc-price">{format_price(info["giá"])}</div>
            <div class="pc-stars">{stars_html} <span>{info.get("đánh_giá", "")}</span></div>
            <div class="pc-loc">📍 {info["vị_trí"]}</div>
            {promo_html}
            {buy_html}
        </div>
    </div>'''


def html_product_grid(products, title="", show_buy=True):
    """Generate an HTML grid of product cards."""
    cards = "".join(html_product_card(n, i, show_buy) for n, i in products)
    title_html = f'<div class="cards-title">{title}</div>' if title else ""
    return f'{title_html}<div class="product-grid">{cards}</div>'


def html_compare_table(products):
    """Generate comparison HTML for products."""
    if len(products) < 2:
        return None
    rows = ""
    for n, i in products:
        stars = "★" * int(i.get("đánh_giá", 0)) + "☆" * (5 - int(i.get("đánh_giá", 0)))
        promo = f'<span class="cmp-promo">🎁 {i["khuyến_mãi"]}</span>' if i.get("khuyến_mãi") else '<span class="cmp-none">Không</span>'
        rows += f'''<div class="cmp-col">
            <div class="cmp-icon">{i.get("hình", "📦")}</div>
            <div class="cmp-name">{i["mô_tả"]}</div>
            <div class="cmp-price">{format_price(i["giá"])}</div>
            <div class="cmp-stars">{stars}</div>
            <div class="cmp-detail">📍 {i["vị_trí"]}</div>
            <div class="cmp-detail">{promo}</div>
            <button class="pc-buy" onclick="quickSend('mua {n}')">🛒 Mua</button>
        </div>'''
    return f'<div class="cards-title">⚖️ SO SÁNH SẢN PHẨM</div><div class="compare-grid">{rows}</div>'


def html_combo_card(combo_key, combo):
    """Generate HTML card for a combo deal."""
    items_html = ""
    total = 0
    for pname in combo["sản_phẩm"]:
        if pname in PRODUCTS:
            p = PRODUCTS[pname]
            items_html += f'<div class="combo-item">{p.get("hình", "📦")} {p["mô_tả"]} — {format_price(p["giá"])}</div>'
            total += p["giá"]
    discount = total * combo["giảm_phần_trăm"] // 100
    final = total - discount
    return f'''<div class="combo-card">
        <div class="combo-header">{combo["hình"]} {combo["mô_tả"]}</div>
        <div class="combo-items">{items_html}</div>
        <div class="combo-footer">
            <div class="combo-old">Giá gốc: <s>{format_price(total)}</s></div>
            <div class="combo-save">Tiết kiệm: -{format_price(discount)} ({combo["giảm_phần_trăm"]}%)</div>
            <div class="combo-final">💰 Chỉ còn: {format_price(final)}</div>
        </div>
        <button class="pc-buy combo-buy" onclick="quickSend('mua {combo_key}')">🛒 Mua combo</button>
    </div>'''


def html_cart(items, total):
    """Generate HTML cart display."""
    rows = ""
    for i, item in enumerate(items, 1):
        info = PRODUCTS.get(item["tên"], {})
        icon = info.get("hình", "📦")
        subtotal = item["giá"] * item["số_lượng"]
        rows += f'''<div class="cart-row">
            <span class="cart-icon">{icon}</span>
            <div class="cart-detail">
                <div class="cart-name">{item["tên"].title()} ×{item["số_lượng"]}</div>
                <div class="cart-sub">{format_price(subtotal)}</div>
            </div>
            <button class="cart-del" onclick="quickSend('xóa sp {i}')">✕</button>
        </div>'''
    ship = 0 if total >= 200000 else 25000
    ship_label = "Miễn phí ✨" if ship == 0 else format_price(ship)
    return f'''<div class="cart-card">
        <div class="cards-title">🛒 GIỎ HÀNG CỦA BẠN</div>
        {rows}
        <div class="cart-divider"></div>
        <div class="cart-total-row"><span>Tiền hàng:</span><span>{format_price(total)}</span></div>
        <div class="cart-total-row"><span>🚚 Vận chuyển:</span><span>{ship_label}</span></div>
        <div class="cart-total-row final"><span>💳 Tổng cộng:</span><span>{format_price(total + ship)}</span></div>
        <div class="cart-actions">
            <button class="pc-buy" onclick="quickSend('thanh toán')">💳 Thanh toán</button>
            <button class="cart-clear" onclick="quickSend('xóa giỏ')">🗑️ Xóa giỏ</button>
        </div>
    </div>'''


def html_checkout(items, total):
    """Generate HTML checkout confirmation."""
    rows = ""
    for i, item in enumerate(items, 1):
        info = PRODUCTS.get(item["tên"], {})
        icon = info.get("hình", "📦")
        rows += f'<div class="ck-row">{icon} {item["tên"].title()} ×{item["số_lượng"]} → {format_price(item["giá"] * item["số_lượng"])}</div>'
    ship = 0 if total >= 200000 else 25000
    return f'''<div class="checkout-card">
        <div class="ck-header">📦 XÁC NHẬN ĐƠN HÀNG</div>
        <div class="ck-items">{rows}</div>
        <div class="cart-divider"></div>
        <div class="cart-total-row"><span>Tiền hàng:</span><span>{format_price(total)}</span></div>
        <div class="cart-total-row"><span>🚚 Ship:</span><span>{"Miễn phí ✨" if ship == 0 else format_price(ship)}</span></div>
        <div class="cart-total-row final"><span>💳 THÀNH TIỀN:</span><span>{format_price(total + ship)}</span></div>
        <div class="ck-info">📍 Giao trong 1-2 giờ | 💳 COD<br>📞 Hotline: 1900-1234</div>
        <div class="ck-success">✅ Đã ghi nhận đơn hàng! Cảm ơn bạn! 🎉</div>
    </div>'''


def html_category_grid():
    """Generate HTML category grid."""
    cards = ""
    for cat, info in CATEGORIES.items():
        count = sum(1 for p in PRODUCTS.values() if p["danh_mục"] == cat)
        cards += f'''<div class="cat-card" onclick="quickSend('{cat}')">
            <span class="cat-icon">{info["icon"]}</span>
            <span class="cat-name">{cat.title()}</span>
            <span class="cat-count">{count} SP</span>
        </div>'''
    return f'<div class="cards-title">📂 DANH MỤC SẢN PHẨM</div><div class="cat-grid">{cards}</div>'


# ==================== LOGIC CHATBOT ====================

def get_cart():
    if 'cart' not in session:
        session['cart'] = []
    return session['cart']


def format_price(price):
    return f"{price:,.0f}đ".replace(",", ".")


def fuzzy_match(s1, s2, threshold=0.5):
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio() >= threshold


def search_products(keyword):
    keyword = keyword.lower().strip()
    if not keyword:
        return []
    exact = []
    fuzzy = []
    for name, info in PRODUCTS.items():
        if keyword in name or keyword in info["danh_mục"] or keyword in info["mô_tả"].lower():
            exact.append((name, info))
        elif any(fuzzy_match(keyword, word) for word in name.split()):
            fuzzy.append((name, info))
    return exact if exact else fuzzy


def get_promotions():
    return [(name, info) for name, info in PRODUCTS.items() if info["khuyến_mãi"]]


def find_product_location(keyword):
    keyword = keyword.lower().strip()
    results = []
    for name, info in PRODUCTS.items():
        if keyword in name or keyword in info["danh_mục"] or keyword in info["mô_tả"].lower():
            results.append((name, info["vị_trí"], info.get("hình", "📦")))
    return results


def add_to_cart(product_name, quantity=1):
    product_name = product_name.lower().strip()
    for name, info in PRODUCTS.items():
        if product_name in name or name in product_name:
            cart = get_cart()
            for item in cart:
                if item["tên"] == name:
                    item["số_lượng"] += quantity
                    session['cart'] = cart
                    return name, info["giá"], item["số_lượng"]
            cart.append({"tên": name, "giá": info["giá"], "số_lượng": quantity})
            session['cart'] = cart
            return name, info["giá"], quantity

    # Fallback: tolerate minor typos (e.g. hà/há) when matching product names.
    best_name = None
    best_score = 0
    for name in PRODUCTS.keys():
        score = SequenceMatcher(None, product_name, name).ratio()
        if score > best_score:
            best_score = score
            best_name = name

    if best_name and best_score >= 0.72:
        info = PRODUCTS[best_name]
        cart = get_cart()
        for item in cart:
            if item["tên"] == best_name:
                item["số_lượng"] += quantity
                session['cart'] = cart
                return best_name, info["giá"], item["số_lượng"]
        cart.append({"tên": best_name, "giá": info["giá"], "số_lượng": quantity})
        session['cart'] = cart
        return best_name, info["giá"], quantity

    return None, 0, 0


def remove_from_cart(index):
    cart = get_cart()
    if 0 <= index < len(cart):
        removed = cart.pop(index)
        session['cart'] = cart
        return removed
    return None


def get_cart_summary():
    cart = get_cart()
    if not cart:
        return None, 0
    total = sum(item["giá"] * item["số_lượng"] for item in cart)
    return cart, total


def clear_cart():
    session['cart'] = []


def get_top_products():
    return sorted(PRODUCTS.items(), key=lambda x: x[1].get("đánh_giá", 0), reverse=True)[:6]


def recommend_milk(age_text):
    match = re.search(r'(\d+)\s*(tuổi|tháng|thang|tuoi)', age_text.lower())
    if match:
        age = int(match.group(1))
        unit = match.group(2)
    else:
        match = re.search(r'(\d+)', age_text)
        if match:
            age = int(match.group(1))
            unit = "tuổi"
        else:
            return None
    if 'tháng' in unit or 'thang' in unit:
        if age <= 6:
            return [("sữa enfamil 900g", PRODUCTS["sữa enfamil 900g"])]
        elif age <= 12:
            return [("sữa enfamil 900g", PRODUCTS["sữa enfamil 900g"]),
                    ("sữa optimum gold 900g", PRODUCTS["sữa optimum gold 900g"])]
        else:
            return [("sữa optimum gold 900g", PRODUCTS["sữa optimum gold 900g"]),
                    ("sữa grow plus 900g", PRODUCTS["sữa grow plus 900g"])]
    else:
        if age <= 1:
            return [("sữa optimum gold 900g", PRODUCTS["sữa optimum gold 900g"])]
        elif age <= 2:
            return [("sữa optimum gold 900g", PRODUCTS["sữa optimum gold 900g"]),
                    ("sữa grow plus 900g", PRODUCTS["sữa grow plus 900g"])]
        elif age <= 6:
            return [("sữa grow plus 900g", PRODUCTS["sữa grow plus 900g"]),
                    ("sữa vinamilk 1l", PRODUCTS["sữa vinamilk 1l"]),
                    ("sữa th true milk 1l", PRODUCTS["sữa th true milk 1l"])]
        elif age <= 15:
            return [("sữa vinamilk 1l", PRODUCTS["sữa vinamilk 1l"]),
                    ("sữa th true milk 1l", PRODUCTS["sữa th true milk 1l"]),
                    ("sữa chua vinamilk lốc 4", PRODUCTS["sữa chua vinamilk lốc 4"])]
        else:
            return [("sữa vinamilk 1l", PRODUCTS["sữa vinamilk 1l"]),
                    ("sữa ensure 850g", PRODUCTS["sữa ensure 850g"]),
                    ("sữa đậu nành fami 1l", PRODUCTS["sữa đậu nành fami 1l"])]


def recommend_recipe(text):
    recipes = {
        "lẩu": ["thịt bò úc 500g", "rau xà lách 300g", "mì omachi xốt bò hầm", "nước mắm nam ngư 500ml"],
        "phở": ["phở bò vifon", "thịt bò úc 500g", "hành tây 500g", "nước mắm nam ngư 500ml"],
        "bún bò": ["bún bò huế vifon", "thịt bò úc 500g", "tương ớt chinsu 250ml"],
        "tiệc": ["coca cola 330ml", "pepsi 330ml", "snack poca khoai tây 54g", "bánh chocopie 396g", "kem wall's 450ml"],
        "ăn sáng": ["bánh mì sandwich kinh đô", "sữa vinamilk 1l", "cà phê g7 hộp 18 gói"],
        "nấu canh": ["cà chua 1kg", "thịt heo xay 500g", "hạt nêm knorr 400g", "nước mắm nam ngư 500ml"],
    }
    for keyword, ingredients in recipes.items():
        if keyword in text:
            items = [(ing, PRODUCTS[ing]) for ing in ingredients if ing in PRODUCTS]
            total = sum(PRODUCTS[ing]["giá"] for ing in ingredients if ing in PRODUCTS)
            text_resp = f"🍳 GỢI Ý NGUYÊN LIỆU CHO MÓN {keyword.upper()}:\n\n"
            for ing in ingredients:
                if ing in PRODUCTS:
                    info = PRODUCTS[ing]
                    text_resp += f"  {info.get('hình', '📦')} {info['mô_tả']} — {format_price(info['giá'])}\n"
            text_resp += f"\n  💰 Tổng ước tính: {format_price(total)}\n💡 Gõ 'mua [tên SP]' để thêm vào giỏ hàng!"
            html_resp = html_product_grid(items, f"🍳 Nguyên liệu: {keyword.upper()} (≈{format_price(total)})")
            return {"text": text_resp, "html": html_resp}
    return None


def budget_shopping(amount):
    """Suggest products that fit within a budget."""
    affordable = [(n, i) for n, i in sorted(PRODUCTS.items(), key=lambda x: x[1]["giá"]) if i["giá"] <= amount]
    if not affordable:
        return {"text": f"Rất tiếc, không có sản phẩm nào dưới {format_price(amount)}.", "html": None}

    # Greedy selection: pick highest-rated products that fit budget
    selected = []
    remaining = amount
    for n, i in sorted(affordable, key=lambda x: x[1].get("đánh_giá", 0), reverse=True):
        if i["giá"] <= remaining:
            selected.append((n, i))
            remaining -= i["giá"]
            if len(selected) >= 8:
                break

    total_spent = sum(i["giá"] for _, i in selected)
    text_resp = f"💰 GỢI Ý MUA SẮM VỚI {format_price(amount)}:\n\n"
    for n, i in selected:
        text_resp += f"  {i.get('hình', '📦')} {i['mô_tả']} — {format_price(i['giá'])}\n"
    text_resp += f"\n  💰 Tổng: {format_price(total_spent)} (còn dư {format_price(remaining)})"
    html_resp = html_product_grid(selected, f"💰 Gợi ý với ngân sách {format_price(amount)} (Tổng: {format_price(total_spent)})")
    return {"text": text_resp, "html": html_resp}


def compare_products_handler(text):
    """Compare products based on query."""
    # Try to find "so sánh X và Y" or "so sánh X với Y"
    match = re.search(r'so\s*sánh\s+(.+?)\s+(?:và|với|vs|va|voi)\s+(.+)', text.lower())
    if not match:
        return None
    kw1, kw2 = match.group(1).strip(), match.group(2).strip()
    results1 = search_products(kw1)
    results2 = search_products(kw2)
    if not results1 or not results2:
        missing = kw1 if not results1 else kw2
        return {"text": f"❌ Không tìm thấy '{missing}'. Thử tên khác nhé!", "html": None}
    items = [results1[0], results2[0]]
    text_resp = f"⚖️ SO SÁNH: {results1[0][1]['mô_tả']} vs {results2[0][1]['mô_tả']}\n\n"
    for n, i in items:
        text_resp += f"  {i.get('hình', '📦')} {i['mô_tả']}\n"
        text_resp += f"     💰 {format_price(i['giá'])} | ⭐ {i.get('đánh_giá', 'N/A')}\n"
        text_resp += f"     📍 {i['vị_trí']}\n"
        text_resp += f"     🎁 {i['khuyến_mãi'] or 'Không có KM'}\n\n"
    cheaper = items[0] if items[0][1]["giá"] <= items[1][1]["giá"] else items[1]
    better = items[0] if items[0][1].get("đánh_giá", 0) >= items[1][1].get("đánh_giá", 0) else items[1]
    text_resp += f"  💡 Rẻ hơn: {cheaper[1]['mô_tả']} ({format_price(cheaper[1]['giá'])})\n"
    text_resp += f"  ⭐ Đánh giá cao hơn: {better[1]['mô_tả']} ({better[1].get('đánh_giá', 0)})"
    html_resp = html_compare_table(items)
    return {"text": text_resp, "html": html_resp}


def parse_purchase_request(text):
    """Extract quantity + product name from natural purchase phrases."""
    m = re.search(r'\b(?:thêm|them|mua|đặt|dat|order|add)\b', text)
    if not m:
        return 1, ""

    tail = text[m.end():].strip()
    tail = re.sub(r'\b(?:vào giỏ|vao gio|giỏ hàng|gio hang)\b', ' ', tail)
    tail = re.sub(r'\b(?:cho mình|cho minh|cho em|giúp mình|giup minh|giúp em|giup em|với|voi|nhé|nhe)\b', ' ', tail)

    quantity = 1
    # Only parse quantity when it is a leading standalone number (avoid 500g/330ml product sizes).
    qty_match = re.match(r'^(\d+)\s*(?:x|cái|hộp|gói|chai|lon|cuộn|lốc|thùng|phần|suất)?\b', tail)
    if qty_match:
        quantity = max(1, int(qty_match.group(1)))
        tail = tail[qty_match.end():].strip()

    product_name = re.sub(r'\s+', ' ', tail).strip(" ,.;:-")
    return quantity, product_name


# ==================== AI CHAT ====================

def get_chat_history():
    if 'chat_history' not in session:
        session['chat_history'] = []
    return session['chat_history']


def add_chat_history(role, content):
    history = get_chat_history()
    history.append({"role": role, "content": content[:500]})
    if len(history) > 20:
        session['chat_history'] = history[-20:]
    else:
        session['chat_history'] = history


def ai_chat(user_input):
    """Dùng Gemini AI để trả lời thông minh."""
    if not ai_client:
        return None
    try:
        history = get_chat_history()
        messages = []
        for msg in history[-10:]:
            messages.append({"role": msg["role"], "parts": [{"text": msg["content"]}]})
        messages.append({"role": "user", "parts": [{"text": user_input}]})

        response = ai_client.models.generate_content(
            model=ai_model,
            contents=messages,
            config={"system_instruction": SYSTEM_PROMPT}
        )
        ai_text = response.text.strip()

        # Tìm sản phẩm được nhắc đến → tạo HTML cards
        mentioned = []
        ai_lower = ai_text.lower()
        for name, info in PRODUCTS.items():
            if name in ai_lower:
                mentioned.append((name, info))
        html = html_product_grid(mentioned[:6], "🤖 AI gợi ý") if mentioned else None

        return R(ai_text, html)
    except Exception as e:
        print(f"⚠️ AI Error: {e}")
        return None


# ==================== MAIN PROCESS ====================

def R(text, html=None):
    """Helper to create response dict."""
    return {"text": text, "html": html}


def process_message(user_input):
    text = user_input.lower().strip()

    # --- Chào hỏi ---
    if any(w in text for w in ["xin chào", "hello", "hi", "chào", "hey", "alo"]):
        hour = datetime.now().hour
        if hour < 12:
            greeting = "🌅 Chào buổi sáng"
        elif hour < 18:
            greeting = "☀️ Chào buổi chiều"
        else:
            greeting = "🌙 Chào buổi tối"
        return R(f"{greeting}! Tôi là trợ lý AI của Siêu Thị ABC 🛒\n\n"
                "Tôi có thể giúp bạn:\n"
                "  🔹 Tư vấn sản phẩm theo nhu cầu\n"
                "  🔹 Tra cứu giá & khuyến mãi hot\n"
                "  🔹 So sánh sản phẩm\n"
                "  🔹 Gợi ý theo ngân sách\n"
                "  🔹 Tìm vị trí trong siêu thị\n"
                "  🔹 Gợi ý nguyên liệu nấu ăn\n"
                "  🔹 Combo tiết kiệm\n"
                "  🔹 Đặt hàng online\n\n"
                "💡 Hãy thử ngay nhé!")

    # --- Cảm ơn ---
    if any(w in text for w in ["cảm ơn", "cam on", "thanks", "thank", "tks"]):
        return R("😊 Không có chi! Rất vui được hỗ trợ bạn. Cần gì thêm cứ hỏi nhé!")

    # --- So sánh ---
    if any(w in text for w in ["so sánh", "so sanh", "compare"]):
        result = compare_products_handler(text)
        if result:
            return result
        return R("💡 Để so sánh, gõ: 'so sánh [SP1] và [SP2]'\nVD: 'so sánh coca cola và pepsi'")

    # --- Ngân sách ---
    budget_match = re.search(r'(?:có|co|budget|ngân sách|ngan sach|mua được|mua duoc|trong|dưới|duoi)\s*(\d[\d.]*)\s*(?:k|K|nghìn|nghin|đ|d|đồng|dong|vnđ|vnd)?', text)
    if not budget_match:
        budget_match = re.search(r'(\d[\d.]*)\s*(?:k|K|nghìn|nghin)\b', text)
        if budget_match and any(w in text for w in ["mua", "gợi ý", "tư vấn", "có", "trong"]):
            pass
        else:
            budget_match = None
    if budget_match:
        raw = budget_match.group(1).replace(".", "")
        amount = int(raw)
        # Auto-detect: if small number, assume "nghìn"
        if amount < 1000:
            amount *= 1000
        if amount > 0:
            return budget_shopping(amount)

    # --- Combo ---
    if any(w in text for w in ["combo", "bộ", "deal"]):
        # Show specific combo or all combos
        for key, combo in COMBOS.items():
            if any(word in text for word in key.split()):
                text_resp = f"{combo['hình']} {combo['mô_tả']}:\n\n"
                total = 0
                for pname in combo["sản_phẩm"]:
                    if pname in PRODUCTS:
                        p = PRODUCTS[pname]
                        text_resp += f"  {p.get('hình', '📦')} {p['mô_tả']} — {format_price(p['giá'])}\n"
                        total += p["giá"]
                discount = total * combo["giảm_phần_trăm"] // 100
                text_resp += f"\n  💰 Giá gốc: {format_price(total)} → Giảm {combo['giảm_phần_trăm']}% → Chỉ còn {format_price(total - discount)}"
                html_resp = html_combo_card(key, combo)
                return R(text_resp, html_resp)
        # Show all combos
        text_resp = "🎉 COMBO TIẾT KIỆM:\n\n"
        html_resp = '<div class="cards-title">🎉 COMBO TIẾT KIỆM</div><div class="combo-grid">'
        for key, combo in COMBOS.items():
            total = sum(PRODUCTS[p]["giá"] for p in combo["sản_phẩm"] if p in PRODUCTS)
            discount = total * combo["giảm_phần_trăm"] // 100
            text_resp += f"  {combo['hình']} {combo['mô_tả']}\n     Giảm {combo['giảm_phần_trăm']}% → {format_price(total - discount)}\n\n"
            html_resp += html_combo_card(key, combo)
        html_resp += "</div>"
        text_resp += "💡 Gõ tên combo để xem chi tiết (VD: 'combo lẩu')"
        return R(text_resp, html_resp)

    # --- Danh mục ---
    if any(w in text for w in ["danh mục", "danh muc", "loại", "categories", "category"]):
        text_resp = "📂 DANH MỤC SẢN PHẨM:\n\n"
        for cat, info in CATEGORIES.items():
            count = sum(1 for p in PRODUCTS.values() if p["danh_mục"] == cat)
            text_resp += f"  {info['icon']} {cat.upper()} ({count} SP)\n"
        text_resp += "\n💡 Gõ tên danh mục để xem SP (VD: 'sữa', 'hải sản')"
        return R(text_resp, html_category_grid())

    # --- Sản phẩm hot ---
    if any(w in text for w in ["bán chạy", "ban chay", "hot", "phổ biến", "nổi bật", "top", "best"]):
        top = get_top_products()
        text_resp = "⭐ SẢN PHẨM ĐÁNH GIÁ CAO NHẤT:\n\n"
        for name, info in top:
            text_resp += f"  {info.get('hình', '📦')} {info['mô_tả']} — {format_price(info['giá'])} | ⭐{info.get('đánh_giá', '')}\n"
        return R(text_resp, html_product_grid(top, "⭐ SẢN PHẨM ĐÁNH GIÁ CAO"))

    # --- Gợi ý món ăn ---
    if any(w in text for w in ["nấu", "nau", "làm", "lam", "gợi ý", "goi y", "nguyên liệu", "lẩu", "phở", "bún bò", "tiệc", "ăn sáng", "canh"]):
        recipe = recommend_recipe(text)
        if recipe:
            return recipe

    # --- Tư vấn sữa ---
    if "sữa" in text and any(w in text for w in ["tuổi", "tháng", "trẻ", "bé", "con", "tuoi", "thang", "em bé", "sơ sinh", "người lớn", "già"]):
        recs = recommend_milk(text)
        if recs:
            text_resp = "🍼 Dựa trên độ tuổi, tôi gợi ý:\n\n"
            for name, info in recs:
                text_resp += f"  ✅ {info['mô_tả']} — {format_price(info['giá'])}\n"
                if info['khuyến_mãi']:
                    text_resp += f"     🎁 {info['khuyến_mãi']}\n"
            text_resp += "\n💡 Gõ 'mua [tên sữa]' để thêm giỏ hàng!"
            html_resp = html_product_grid(recs, "🍼 Sữa phù hợp theo độ tuổi")
            return R(text_resp, html_resp)
        return R("Bạn cho biết bé bao nhiêu tuổi/tháng tuổi nhé? 🤔")

    # --- Khuyến mãi ---
    if any(w in text for w in ["khuyến mãi", "khuyen mai", "giảm giá", "giam gia", "ưu đãi", "sale", "promotion", "km"]):
        promos = get_promotions()
        if promos:
            text_resp = f"🎉 KHUYẾN MÃI HÔM NAY ({len(promos)} SP):\n\n"
            for name, info in promos:
                text_resp += f"  {info.get('hình', '📦')} {info['mô_tả']} — {format_price(info['giá'])} → 🎁 {info['khuyến_mãi']}\n"
            text_resp += "\n💡 Gõ 'mua [tên SP]' để thêm giỏ hàng."
            html_resp = html_product_grid(promos, f"🎉 KHUYẾN MÃI HÔM NAY ({len(promos)} SP)")
            return R(text_resp, html_resp)
        return R("Hiện tại không có khuyến mãi nào.")

    # --- Tra giá ---
    if any(w in text for w in ["giá", "gia", "bao nhiêu", "bao nhieu", "cost", "price"]):
        text_search = text
        for kw in ["giá", "gia", "bao nhiêu", "bao nhieu", "của", "cua", "là", "la", "cost", "price", "?"]:
            text_search = text_search.replace(kw, "")
        text_search = text_search.strip()
        if text_search:
            results = search_products(text_search)
            if results:
                text_resp = "💰 Kết quả tra cứu giá:\n\n"
                for name, info in results:
                    text_resp += f"  {info.get('hình', '📦')} {info['mô_tả']} — {format_price(info['giá'])}\n"
                    if info['khuyến_mãi']:
                        text_resp += f"     🎁 {info['khuyến_mãi']}\n"
                html_resp = html_product_grid(results, "💰 Kết quả tra cứu giá")
                return R(text_resp, html_resp)
            return R(f"❌ Không tìm thấy '{text_search}'.\n💡 Gõ 'danh mục' để xem các loại SP.")
        return R("Bạn muốn tra giá sản phẩm nào? 🤔")

    # --- Tìm vị trí ---
    if any(w in text for w in ["ở đâu", "o dau", "vị trí", "vi tri", "chỗ nào", "cho nao", "nằm ở", "nam o", "tìm", "tim"]):
        text_search = text
        for kw in ["ở đâu", "o dau", "vị trí", "vi tri", "chỗ nào", "cho nao", "tìm", "tim", "nằm ở", "nam o", "của", "cua", "?"]:
            text_search = text_search.replace(kw, "")
        text_search = text_search.strip()
        if text_search:
            results = find_product_location(text_search)
            if results:
                text_resp = "📍 VỊ TRÍ TRONG SIÊU THỊ:\n\n"
                for name, loc, icon in results:
                    text_resp += f"  {icon} {name.title()} → 📍 {loc}\n"
                text_resp += "\n🗺️ Gõ 'bản đồ' để xem toàn bộ sơ đồ."
                return R(text_resp)
            return R(f"❌ Không tìm thấy '{text_search}'.\n💡 Thử từ khóa khác nhé!")
        return R("Bạn muốn tìm sản phẩm nào? 🤔")

    # --- Bản đồ ---
    if any(w in text for w in ["bản đồ", "ban do", "sơ đồ", "so do", "layout", "map"]):
        text_resp = "🗺️ SƠ ĐỒ SIÊU THỊ ABC:\n\n"
        for floor, areas in STORE_MAP.items():
            text_resp += f"━━━ 📌 {floor} ━━━\n"
            for area, desc in areas.items():
                text_resp += f"  {area}: {desc}\n"
            text_resp += "\n"
        text_resp += "💡 Gõ '[tên SP] ở đâu' để tìm vị trí cụ thể."
        return R(text_resp)

    # --- Xóa SP trong giỏ ---
    if any(w in text for w in ["xóa sp", "xoa sp", "bỏ sp", "remove"]):
        match = re.search(r'(\d+)', text)
        if match:
            removed = remove_from_cart(int(match.group(1)) - 1)
            if removed:
                return R(f"✅ Đã xóa {removed['tên'].title()} khỏi giỏ hàng.")
            return R("❌ Số thứ tự không hợp lệ.")
        return R("Nhập số thứ tự SP cần xóa (VD: 'xóa sp 1')")

    # --- Xóa giỏ ---
    if any(w in text for w in ["xóa giỏ", "xoa gio", "clear cart", "xóa hết"]):
        clear_cart()
        return R("🗑️ Đã xóa toàn bộ giỏ hàng.")

    # --- Thêm giỏ hàng / Mua combo ---
    if any(w in text for w in ["thêm", "them", "mua", "đặt", "dat", "order", "add"]):
        # Check combo first
        for key, combo in COMBOS.items():
            if key.replace("combo ", "") in text or key in text:
                total = 0
                for pname in combo["sản_phẩm"]:
                    if pname in PRODUCTS:
                        add_to_cart(pname, 1)
                        total += PRODUCTS[pname]["giá"]
                discount = total * combo["giảm_phần_trăm"] // 100
                _, cart_total = get_cart_summary()
                return R(f"✅ Đã thêm {combo['mô_tả']} vào giỏ!\n"
                         f"  💰 Tiết kiệm: {format_price(discount)}\n"
                         f"  🛒 Tổng giỏ: {format_price(cart_total)}")

        quantity, product_name = parse_purchase_request(text)
        if product_name:
            name, price, qty = add_to_cart(product_name, quantity)
            if name:
                info = PRODUCTS[name]
                _, cart_total = get_cart_summary()
                text_resp = f"✅ Đã thêm vào giỏ hàng:\n\n"
                text_resp += f"  {info.get('hình', '📦')} {name.title()} +{quantity} (tổng {qty})\n"
                text_resp += f"  💰 Tạm tính lần thêm: {format_price(price * quantity)}\n\n"
                text_resp += f"  🛒 Tổng giỏ: {format_price(cart_total)}\n"
                if cart_total >= 200000:
                    text_resp += "  🚚 Miễn phí giao hàng! ✨"
                else:
                    text_resp += f"  🚚 Thêm {format_price(200000 - cart_total)} nữa để FREE ship!"
                return R(text_resp)
            suggestions = search_products(product_name)
            if suggestions:
                text_resp = f"❌ Không tìm thấy '{product_name}'.\n\n💡 Có phải bạn muốn:\n"
                for sn, si in suggestions[:3]:
                    text_resp += f"  • {si['mô_tả']} - {format_price(si['giá'])}\n"
                html_resp = html_product_grid(suggestions[:3], f"💡 Có phải bạn tìm:")
                return R(text_resp, html_resp)
            return R(f"❌ Không tìm thấy '{product_name}'. Thử tên khác nhé!")
        return R("Bạn muốn mua sản phẩm nào? 🤔")

    # --- Giỏ hàng ---
    if any(w in text for w in ["giỏ hàng", "gio hang", "cart", "giỏ"]):
        items, total = get_cart_summary()
        if items:
            text_resp = "🛒 GIỎ HÀNG CỦA BẠN:\n\n"
            for i, item in enumerate(items, 1):
                info = PRODUCTS.get(item['tên'], {})
                icon = info.get('hình', '📦')
                text_resp += f"  {i}. {icon} {item['tên'].title()} x{item['số_lượng']} — {format_price(item['giá'] * item['số_lượng'])}\n"
            ship = 0 if total >= 200000 else 25000
            text_resp += f"\n  💰 TỔNG: {format_price(total)}\n"
            text_resp += f"  🚚 Ship: {'Miễn phí ✨' if ship == 0 else format_price(ship)}\n"
            text_resp += "\n💡 'thanh toán' | 'xóa sp [số]' | 'xóa giỏ'"
            return R(text_resp, html_cart(items, total))
        return R("🛒 Giỏ hàng trống.\n💡 VD: 'mua 2 sữa vinamilk 1l'")

    # --- Thanh toán ---
    if any(w in text for w in ["thanh toán", "thanh toan", "đặt hàng", "dat hang", "checkout", "giao hàng", "giao hang", "delivery"]):
        items, total = get_cart_summary()
        if items:
            text_resp = "📦 XÁC NHẬN ĐƠN HÀNG\n\n"
            for i, item in enumerate(items, 1):
                text_resp += f"  {i}. {item['tên'].title()} x{item['số_lượng']} → {format_price(item['giá'] * item['số_lượng'])}\n"
            ship = 0 if total >= 200000 else 25000
            text_resp += f"\n  💰 THÀNH TIỀN: {format_price(total + ship)}\n"
            text_resp += "✅ Đã ghi nhận đơn hàng! Cảm ơn bạn! 🎉"
            h = html_checkout(items, total)
            clear_cart()
            return R(text_resp, h)
        return R("🛒 Giỏ hàng trống.\nVD: 'mua 2 sữa vinamilk 1l'")

    # --- Tìm kiếm chung ---
    results = search_products(text)
    if results:
        text_resp = f"🔍 Tìm thấy {len(results)} sản phẩm:\n\n"
        for name, info in results:
            text_resp += f"  {info.get('hình', '📦')} {info['mô_tả']} — {format_price(info['giá'])} | ⭐{info.get('đánh_giá', '')}\n"
        text_resp += "\n💡 Gõ 'mua [tên SP]' để thêm giỏ hàng."
        html_resp = html_product_grid(results, f"🔍 Tìm thấy {len(results)} sản phẩm")
        return R(text_resp, html_resp)

    # --- Help ---
    if any(w in text for w in ["help", "trợ giúp", "hướng dẫn", "huong dan", "?"]):
        return R("📖 HƯỚNG DẪN SỬ DỤNG:\n\n"
                "  🔹 Tìm SP: nhập tên (VD: 'coca cola')\n"
                "  🔹 Tư vấn: 'sữa cho trẻ 2 tuổi'\n"
                "  🔹 Tra giá: 'giá mì hảo hảo'\n"
                "  🔹 KM: 'xem khuyến mãi'\n"
                "  🔹 So sánh: 'so sánh coca và pepsi'\n"
                "  🔹 Ngân sách: 'tôi có 100k mua gì'\n"
                "  🔹 Combo: 'combo lẩu'\n"
                "  🔹 Vị trí: 'nước mắm ở đâu'\n"
                "  🔹 Sơ đồ: 'bản đồ'\n"
                "  🔹 Nấu ăn: 'nấu lẩu cần gì'\n"
                "  🔹 Mua: 'mua 2 coca cola'\n"
                "  🔹 Giỏ: 'giỏ hàng'\n"
                "  🔹 Đặt: 'thanh toán'\n\n"
                "🚚 FREE ship từ 200.000đ!")

    # --- AI thông minh ---
    ai_result = ai_chat(user_input)
    if ai_result:
        return ai_result

    # --- Mặc định (khi không có AI) ---
    return R("Hmm, tôi chưa hiểu ý bạn 🤔\n\n"
            "Thử các cách sau:\n"
            "  🔹 Nhập tên SP: 'coca cola'\n"
            "  🔹 Tra giá: 'giá sữa vinamilk'\n"
            "  🔹 So sánh: 'so sánh X và Y'\n"
            "  🔹 Ngân sách: 'tôi có 200k'\n"
            "  🔹 Combo: 'combo tiệc'\n"
            "  🔹 KM: 'khuyến mãi'\n"
            "  🔹 Gõ 'help' để xem hướng dẫn")


# ==================== FLASK ROUTES ====================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    user_message = str(data.get("message", "")).strip()
    if not user_message:
        return jsonify({"reply": "Vui lòng nhập tin nhắn.", "html": None})
    result = process_message(user_message)
    add_chat_history("user", user_message)
    add_chat_history("model", result["text"])
    cart = get_cart()
    cart_count = sum(item["số_lượng"] for item in cart)
    _, cart_total = get_cart_summary()
    return jsonify({
        "reply": result["text"],
        "html": result.get("html"),
        "cart_count": cart_count,
        "cart_total": cart_total,
        "ai_active": ai_client is not None
    })


@app.route("/api/categories")
def api_categories():
    return jsonify(CATEGORIES)


@app.route("/api/products")
def api_products():
    category = request.args.get("category", "")
    if category:
        filtered = {k: v for k, v in PRODUCTS.items() if v["danh_mục"] == category.lower()}
        return jsonify(filtered)
    return jsonify(PRODUCTS)


@app.route("/api/search")
def api_search():
    q = request.args.get("q", "").strip()
    if not q or len(q) < 2:
        return jsonify([])
    results = search_products(q)
    return jsonify([{"name": n, "desc": i["mô_tả"], "price": i["giá"], "icon": i.get("hình", "📦")} for n, i in results[:5]])


if __name__ == "__main__":
    ngrok_token = os.environ.get("NGROK_AUTHTOKEN", "").strip()
    if ngrok_token:
        try:
            from pyngrok import ngrok
            ngrok.set_auth_token(ngrok_token)
            public_url = ngrok.connect(5000)
            print(f"\n{'='*50}")
            print(f"🌐 LINK PUBLIC: {public_url.public_url}")
            print(f"{'='*50}\n")
        except Exception as e:
            print(f"\n⚠️  Ngrok: {e}")
            print("   Dùng cloudflared tunnel hoặc truy cập qua LAN.\n")
    else:
        print("ℹ️  Chưa cấu hình NGROK_AUTHTOKEN. Bỏ qua link public và chạy local/LAN.\n")

    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)
