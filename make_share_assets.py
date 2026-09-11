# -*- coding: utf-8 -*-
"""生成微信分享海报(带二维码)与链接卡片缩略图"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import qrcode, random, math

NAVY0, NAVY1 = (7, 11, 28), (19, 27, 66)
GOLD, GOLD_B, GOLD_D = (217, 180, 92), (245, 217, 138), (154, 117, 46)
INK = (236, 229, 210)
RED = (179, 39, 45)

KAI = r"C:\Windows\Fonts\simkai.ttf"
YH = r"C:\Windows\Fonts\msyh.ttc"
YHB = r"C:\Windows\Fonts\msyhbd.ttc"

def font(path, size, idx=0):
    return ImageFont.truetype(path, size, index=idx)

def vgrad(w, h, c0, c1):
    im = Image.new("RGB", (w, h), c0)
    px = im.load()
    for y in range(h):
        t = y / h
        r = int(c0[0] + (c1[0] - c0[0]) * t)
        g = int(c0[1] + (c1[1] - c0[1]) * t)
        b = int(c0[2] + (c1[2] - c0[2]) * t)
        for x in range(w):
            px[x, y] = (r, g, b)
    return im

def gold_dots(im, n, seed=7):
    rnd = random.Random(seed)
    d = ImageDraw.Draw(im, "RGBA")
    for _ in range(n):
        x, y = rnd.uniform(0, im.width), rnd.uniform(0, im.height)
        r = rnd.uniform(1.2, 3.4)
        a = rnd.randint(28, 80)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 218, 138, a))

def center_text(d, cx, y, s, f, fill, ls=0):
    """居中写一行，ls为额外字距"""
    if ls:
        widths = [d.textlength(ch, font=f) + ls for ch in s]
        total = sum(widths) - ls
        x = cx - total / 2
        for ch, w in zip(s, widths):
            d.text((x, y), ch, font=f, fill=fill)
            x += w
    else:
        w = d.textlength(s, font=f)
        d.text((cx - w / 2, y), s, font=f, fill=fill)

def make_qr(url, box=860, border=2):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=20, border=border)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color=(20, 26, 54), back_color=(255, 253, 246)).convert("RGB")
    return img.resize((box, box), Image.NEAREST)

def make_poster(path):
    W, H = 1080, 1560
    im = vgrad(W, H, NAVY1, NAVY0)  # 顶部稍亮
    # 顶部金色光晕
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W//2-500, -380, W//2+500, 320], fill=(60, 48, 14))
    im = Image.blend(im, Image.blend(im, glow, 0.0), 0.0)  # placeholder
    im = Image.composite(Image.new("RGB",(W,H),(0,0,0)), im, Image.new("L",(W,H),0))
    # 用加法混合光晕
    from PIL import ImageChops
    im = ImageChops.add(im, glow)
    gold_dots(im, 90)
    d = ImageDraw.Draw(im, "RGBA")

    # 双金边框
    d.rounded_rectangle([28, 28, W-28, H-28], radius=18, outline=GOLD, width=3)
    d.rounded_rectangle([44, 44, W-44, H-44], radius=12, outline=(217,180,92,110), width=1)

    cx = W // 2
    # 校徽
    logo = Image.open("logo.png").convert("RGBA")
    lw = 420
    lh = int(logo.height * lw / logo.width)
    logo = logo.resize((lw, lh), Image.LANCZOS)
    im.paste(logo, (cx - lw//2, 96), logo)
    d = ImageDraw.Draw(im, "RGBA")

    # 主标题
    y = 250
    f_title = font(KAI, 150)
    center_text(d, cx, y, "科大廿载", f_title, GOLD_B, ls=26)
    y += 185
    center_text(d, cx, y, "青春再聚", f_title, GOLD_B, ls=26)

    # 分隔线
    y += 205
    d.line([cx-230, y, cx-30, y], fill=GOLD, width=2)
    d.line([cx+30, y, cx+230, y], fill=GOLD, width=2)
    d.polygon([cx, y-8, cx+8, y, cx, y+8, cx-8, y], fill=GOLD_B)

    # 副标题
    y += 36
    f_sub = font(KAI, 56)
    center_text(d, cx, y, "机电工程学院机制025班", f_sub, INK, ls=8)
    y += 92
    center_text(d, cx, y, "毕业二十周年同学聚会", font(KAI, 46), (200, 190, 160), ls=14)

    # 信息框
    y += 105
    box = [150, y, W-150, y+250]
    d.rounded_rectangle(box, radius=14, outline=(217,180,92,160), width=2)
    d.rounded_rectangle([box[0]+8, box[1]+8, box[2]-8, box[3]-8], radius=10, outline=(217,180,92,70), width=1)
    f_info = font(YHB, 46, 0)
    center_text(d, cx, y+34, "谨定于 2026年10月2日 — 10月4日", f_info, GOLD_B)
    center_text(d, cx, y+108, "洛阳 · 河南科技大学西苑校区", f_info, INK)
    center_text(d, cx, y+178, "（涧西区西苑路48号）", font(YH, 34, 0), (170, 165, 148))

    # 二维码
    qr = make_qr("https://haust-reunion.surge.sh/", 400)
    qy = box[3] + 66
    pad = 24
    qw, qh = qr.size
    card = Image.new("RGB", (qw+pad*2, qh+pad*2), (255, 253, 246))
    card.paste(qr, (pad, pad))
    r = 20
    mask = Image.new("L", card.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0,0,card.width,card.height], radius=r, fill=255)
    im.paste(card, (cx - card.width//2, qy), mask)
    d = ImageDraw.Draw(im, "RGBA")

    # 二维码说明
    ty = qy + card.height + 26
    center_text(d, cx, ty, "长按识别二维码 · 开启邀请函", font(KAI, 42), GOLD_B, ls=6)

    # 底部落款 + 红印章
    by = H - 118
    center_text(d, cx-70, by, "机电工程学院机制025班 · 筹备组 敬邀", font(YH, 30, 0), (150, 146, 132))
    # 印章
    ss = 86
    sx, sy = W-206, H-246
    d.rounded_rectangle([sx, sy, sx+ss, sy+ss], radius=10, fill=(200, 52, 52, 235))
    f_stamp = font(KAI, 34)
    for i, ch in enumerate("青春再聚"):
        d.text((sx + 12 + (i%2)*32, sy + 7 + (i//2)*40), ch, font=f_stamp, fill=(255, 242, 228))

    im.save(path, quality=92)
    print("海报:", path, im.size)

def make_thumb(path):
    W, H = 500, 400
    im = vgrad(W, H, NAVY1, NAVY0)
    from PIL import ImageChops
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    ImageDraw.Draw(glow).ellipse([W//2-320, -260, W//2+320, 200], fill=(52, 42, 12))
    im = ImageChops.add(im, glow)
    gold_dots(im, 40, seed=3)
    d = ImageDraw.Draw(im, "RGBA")
    d.rounded_rectangle([14, 14, W-14, H-14], radius=12, outline=GOLD, width=2)
    cx = W // 2
    logo = Image.open("logo.png").convert("RGBA")
    lw = 300
    lh = int(logo.height * lw / logo.width)
    logo = logo.resize((lw, lh), Image.LANCZOS)
    im.paste(logo, (cx - lw//2, 44), logo)
    d = ImageDraw.Draw(im, "RGBA")
    center_text(d, cx, 138, "科大廿载 · 青春再聚", font(KAI, 62), GOLD_B, ls=6)
    center_text(d, cx, 236, "毕业二十周年同学聚会", font(KAI, 40), INK, ls=6)
    d.line([cx-140, 306, cx+140, 306], fill=(217,180,92,150), width=1)
    center_text(d, cx, 322, "2026.10.02 — 10.04 · 洛阳", font(YHB, 32, 0), (255, 226, 150))
    im.save(path, quality=88)
    print("缩略图:", path, im.size)

if __name__ == "__main__":
    import os
    os.chdir(os.path.join(os.environ.get("TEMP", r"C:\Users\徐毅力\AppData\Local\Temp"), "poster"))
    make_poster(r"C:\Users\徐毅力\ZCodeProject\reunion-invitation\share-poster.jpg")
    make_thumb(r"C:\Users\徐毅力\ZCodeProject\reunion-invitation\share-thumb.jpg")
