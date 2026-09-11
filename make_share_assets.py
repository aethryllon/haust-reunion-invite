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
    W, H = 1080, 1700
    im = vgrad(W, H, NAVY1, NAVY0)
    from PIL import ImageChops
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    ImageDraw.Draw(glow).ellipse([W//2-500, -380, W//2+500, 320], fill=(60, 48, 14))
    im = ImageChops.add(im, glow)
    gold_dots(im, 90)
    d = ImageDraw.Draw(im, "RGBA")
    boxes = {}

    d.rounded_rectangle([28, 28, W-28, H-28], radius=18, outline=GOLD, width=3)
    d.rounded_rectangle([44, 44, W-44, H-44], radius=12, outline=(217,180,92,110), width=1)

    cx = W // 2
    logo = Image.open("logo.png").convert("RGBA")
    lw = 420; lh = int(logo.height * lw / logo.width)
    logo = logo.resize((lw, lh), Image.LANCZOS)
    im.paste(logo, (cx - lw//2, 92), logo)
    boxes['校徽'] = [92, 92+lh]
    d = ImageDraw.Draw(im, "RGBA")

    f_title = font(KAI, 145)
    center_text(d, cx, 230, "科大廿载", f_title, GOLD_B, ls=26); boxes['标题1'] = [230, 375]
    center_text(d, cx, 400, "青春再聚", f_title, GOLD_B, ls=26); boxes['标题2'] = [400, 545]

    y = 600
    d.line([cx-230, y, cx-30, y], fill=GOLD, width=2)
    d.line([cx+30, y, cx+230, y], fill=GOLD, width=2)
    d.polygon([cx, y-8, cx+8, y, cx, y+8, cx-8, y], fill=GOLD_B)
    boxes['分隔线'] = [y, y]

    center_text(d, cx, 636, "机电工程学院机制025班", font(KAI, 54), INK, ls=8); boxes['副题1'] = [636, 690]
    center_text(d, cx, 718, "毕业二十周年同学聚会", font(KAI, 44), (200,190,160), ls=14); boxes['副题2'] = [718, 762]

    by = 816
    box = [150, by, W-150, by+210]
    d.rounded_rectangle(box, radius=14, outline=(217,180,92,160), width=2)
    d.rounded_rectangle([box[0]+8, box[1]+8, box[2]-8, box[3]-8], radius=10, outline=(217,180,92,70), width=1)
    center_text(d, cx, by+28, "谨定于 2026年10月2日 — 10月4日", font(YHB, 44, 0), GOLD_B)
    center_text(d, cx, by+96, "洛阳 · 河南科技大学西苑校区", font(YHB, 44, 0), INK)
    center_text(d, cx, by+158, "（涧西区西苑路48号）", font(YH, 32, 0), (170, 165, 148))
    boxes['信息框'] = [by, by+210]

    qr = make_qr("https://haust-reunion.surge.sh/", 400)
    qy = 1074; pad = 24
    card = Image.new("RGB", (qr.width+pad*2, qr.height+pad*2), (255, 253, 246))
    card.paste(qr, (pad, pad))
    mask = Image.new("L", card.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0,0,card.width,card.height], radius=20, fill=255)
    im.paste(card, (cx - card.width//2, qy), mask)
    d = ImageDraw.Draw(im, "RGBA")
    boxes['二维码'] = [qy, qy+card.height]

    ty = qy + card.height + 26
    center_text(d, cx, ty, "长按识别二维码 · 开启邀请函", font(KAI, 40), GOLD_B, ls=6)
    boxes['码说明'] = [ty, ty+46]

    sy = 1612
    center_text(d, cx, sy, "机电工程学院机制025班 · 筹备组 敬邀", font(YH, 30, 0), (150, 146, 132))
    boxes['落款'] = [sy, sy+36]
    ss = 84; sx = W-176; syy = 1568
    d.rounded_rectangle([sx, syy, sx+ss, syy+ss], radius=10, fill=(200, 52, 52, 235))
    f_stamp = font(KAI, 33)
    for i, ch in enumerate("青春再聚"):
        d.text((sx + 11 + (i%2)*32, syy + 6 + (i//2)*40), ch, font=f_stamp, fill=(255, 242, 228))
    boxes['印章'] = [syy, syy+ss]

    # 自检：所有元素必须在边框(44..H-44)内，且二维码不得与文字重叠
    border_top, border_bottom = 44, H-44
    ok = True
    for name, (t, b) in boxes.items():
        if t < border_top or b > border_bottom:
            print(f"  ✗ {name} 越界: y{t}-{b}"); ok = False
    qrt, qrb = boxes['二维码']
    for name in ('落款','码说明','印章','信息框','副题2'):
        t, b = boxes[name]
        if not (b <= qrt or t >= qrb):
            print(f"  ✗ {name} 与二维码重叠"); ok = False
    print("  ✓ 全部元素坐标自检:", "通过" if ok else "未通过")
    for k, v in boxes.items(): print(f"  {k}: y{v[0]}-{v[1]}")
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
