## Chatbot sieu thi (Flask)

Ung dung chatbot ho tro:
- Tu van san pham (vi du: "sua nao tot cho tre 2 tuoi?")
- Tra cuu gia va khuyen mai
- Tim vi tri san pham trong sieu thi
- Ho tro dat hang online / giao hang tan nha

## Chay local

1. Cai thu vien:
	pip install -r requirements.txt
2. Chay app:
	python chat.py
3. Mo trinh duyet:
	http://127.0.0.1:5000

## Lay link web tu GitHub (Render)

Du an da co file `render.yaml`, `requirements.txt`, `runtime.txt` de deploy truc tiep tu GitHub.

1. Push code len nhanh `main` tren GitHub.
2. Vao Render, chon New + -> Blueprint.
3. Chon repo GitHub nay.
4. Render tu dong doc `render.yaml` va tao web service.
5. Sau khi deploy xong, ban nhan link dang:
	https://<ten-service>.onrender.com

Luu y:
- GitHub Pages khong chay duoc Flask backend.
- Neu muon chatbot AI Gemini, them bien moi truong `GEMINI_API_KEY` trong Render.
