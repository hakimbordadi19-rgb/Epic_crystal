#!/usr/bin/env python3
"""EPIC crystal intro  -  Apkhack929
 0.0-7.0s  floating blue/red crystal shards + bokeh; a blue and a red crystal
           sphere rush towards each other with energy streams and lightning
 7.0s      huge explosion: flash, shock rings, rays, sparks, camera shake
 7.4-13.5s the debris turns into diamonds that form the name (blue / red)

Termux:  pkg install python python-pillow ffmpeg
  python epic_apkhack.py --res fhd                 # 1080p (anti-aliased)
  python epic_apkhack.py --res fhd --portrait      # phone vertical
  python epic_apkhack.py --res 4k
  python epic_apkhack.py --res hd --ss 1           # fast test
  python epic_apkhack.py --music song.mp3
  python epic_apkhack.py --snap 7.3                # one PNG frame (test)
"""
import argparse
import math
import os
import random
import subprocess
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

RES = {"hd": (1280, 720), "fhd": (1920, 1080), "4k": (3840, 2160), "8k": (7680, 4320)}
DEFAULT_SS = {"hd": 3, "fhd": 2, "4k": 1, "8k": 1}
FPS = 30
T_SPHERES = 1.5
T_BOOM = 7.0
T_FORM = 2.8
T_DIA = T_BOOM + 0.35
TOTAL = 13.5

DEFAULT_NAME = "Apkhack929"
SEGMENTS = [("Apk", 0), ("hack", 1), ("929", 0)]      # 0 blue, 1 red

KEYPAL = {0: ((5, 25, 115), (130, 205, 255)), 1: ((95, 5, 22), (255, 125, 105))}
DIA_L, DIA_D = [(70, 160, 255), (255, 95, 110)], [(15, 50, 215), (180, 10, 40)]
SPH = {0: ((3, 18, 100), (70, 165, 255)), 1: ((85, 4, 16), (255, 100, 85))}
HOT_L, HOT_D = (255, 238, 175), (255, 140, 40)
BLUE_STREAM = [(60, 150, 255), (120, 210, 255), (200, 240, 255), (40, 100, 255)]
FIRE_STREAM = [(255, 90, 25), (255, 160, 50), (255, 225, 120), (255, 60, 40)]
SPARK_COLS = [(255, 215, 100), (255, 255, 255), (110, 180, 255), (255, 85, 70)]
BOKEH_COLS = [(40, 120, 255), (90, 200, 255), (255, 70, 70), (255, 190, 80), (255, 255, 255)]

FONTS = ["/system/fonts/Roboto-Black.ttf", "/system/fonts/Roboto-Bold.ttf",
         "/system/fonts/DroidSans-Bold.ttf",
         "/data/data/com.termux/files/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
         "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"]


# ----------------------------------------------------------------- helpers
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def mix(c1, c2, t):
    return (int(c1[0] + (c2[0] - c1[0]) * t), int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t))


def shade(c, k):
    return (max(0, min(255, int(c[0] * k))), max(0, min(255, int(c[1] * k))),
            max(0, min(255, int(c[2] * k))))


def ease_out(x):
    return 1 - (1 - x) ** 3


def smooth(x):
    return x * x * (3 - 2 * x)


def find_font(user):
    if user:
        return user
    for p in FONTS:
        if os.path.isfile(p):
            return p
    return None


def load_font(path, size):
    return ImageFont.truetype(path, size) if path else ImageFont.load_default(size)


def icosphere(rng):
    t = (1 + 5 ** 0.5) / 2
    v = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t),
         (0, -1, -t), (0, 1, -t), (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    f = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4),
         (11, 10, 2), (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8),
         (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]

    def nrm(p):
        l = math.sqrt(p[0] ** 2 + p[1] ** 2 + p[2] ** 2)
        return (p[0] / l, p[1] / l, p[2] / l)

    v = [nrm(p) for p in v]
    cache = {}

    def mid(a, b):
        k = (min(a, b), max(a, b))
        if k not in cache:
            v.append(nrm(((v[a][0] + v[b][0]) / 2, (v[a][1] + v[b][1]) / 2,
                          (v[a][2] + v[b][2]) / 2)))
            cache[k] = len(v) - 1
        return cache[k]

    nf = []
    for a, b, c in f:
        ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
        nf += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
    v = [(p[0] * s, p[1] * s, p[2] * s) for p in v
         for s in [rng.uniform(0.92, 1.04)]]          # irregular = real crystal
    return v, nf


# ------------------------------------------------- name -> diamond points
def split_lines(name, portrait):
    if not portrait or len(name) < 4:
        return [name]
    if name == DEFAULT_NAME:
        return ["Apk", "hack", "929"]
    h = (len(name) + 1) // 2
    return [name[:h], name[h:]]


def colour_key(name, idx):
    if name == DEFAULT_NAME:
        n = 0
        for seg, key in SEGMENTS:
            n += len(seg)
            if idx < n:
                return key
        return 0
    return idx % 2


def build_points(name, fpath, W, H, portrait):
    lines = split_lines(name, portrait)
    n = len(lines)
    size = int(H * 0.26)
    while True:
        f = load_font(fpath, size)
        wmax = max(f.getlength(l) for l in lines)
        lh = size * 1.18
        if (wmax <= W * 0.84 and n * lh <= H * 0.62) or size < 20:
            break
        size = int(size * 0.95)
    stroke = max(1, int(size * 0.03))
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    info, off = [], 0
    for k, line in enumerate(lines):
        cy = H / 2 + (k - (n - 1) / 2) * lh
        md.text((W / 2, cy), line, font=f, fill=255, anchor="mm",
                stroke_width=stroke, stroke_fill=255)
        x0 = W / 2 - f.getlength(line) / 2
        bounds = [x0 + f.getlength(line[:i + 1]) for i in range(len(line))]
        info.append((cy, bounds, off, line))
        off += len(line)
    step = max(5, int(size * 0.045))
    px = mask.load()
    pts, row, y = [], 0, step / 2
    while y < H - 1:
        x = step / 2 if row % 2 else 0.0
        while x < W - 1:
            if px[int(x), int(y)] > 128:
                k = min(range(n), key=lambda j: abs(info[j][0] - y))
                cy, bounds, o, line = info[k]
                idx = next((i for i, bb in enumerate(bounds) if x <= bb), len(line) - 1)
                pts.append((x, y, o + idx))
            x += step
        y += step / 2
        row += 1
    return pts, step, [(cy, colour_key(name, o)) for (cy, _, o, _) in info]


# ------------------------------------------------------------------- scene
class Epic:
    def __init__(self, W, H, name, fpath, ss, portrait):
        self.W, self.H, self.ss, self.portrait = W, H, ss, portrait
        self.U = min(W, H)
        self.cx, self.cy = W / 2, H / 2
        self.ax = (0.0, 1.0) if portrait else (1.0, 0.0)
        rng = random.Random(929)

        g = ImageOps.invert(Image.radial_gradient("L")).resize((W, H), Image.BILINEAR)
        self.bg = ImageOps.colorize(g, black=(1, 2, 9), white=(10, 16, 46))
        self.vig = (Image.radial_gradient("L").resize((W, H), Image.BILINEAR)
                    .point(lambda v: int(255 - 0.6 * v)).convert("RGB"))
        self.white = Image.new("RGB", (W, H), (255, 255, 255))
        self.black = Image.new("RGB", (W, H), (0, 0, 0))

        self.stars = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0, 6.28))
                      for _ in range(110)]
        self.shards = []
        for _ in range(32):
            z = rng.random()
            nv = rng.randint(6, 8)
            verts = sorted((rng.uniform(0, 6.283), rng.uniform(0.55, 1.0)) for _ in range(nv))
            self.shards.append(dict(
                x0=rng.uniform(-0.1, 1.1), y0=rng.uniform(-0.1, 1.1),
                vx=rng.uniform(-0.02, 0.02), vy=rng.uniform(-0.015, 0.015), z=z,
                size=0.03 + 0.055 * z + rng.uniform(0, 0.02), rot0=rng.uniform(0, 6.28),
                spin=rng.uniform(-0.9, 0.9), ph=rng.uniform(0, 6.28),
                key=0 if rng.random() < 0.6 else 1, el=rng.uniform(0.6, 1.0),
                c=(rng.uniform(-0.2, 0.2), rng.uniform(-0.2, 0.2)), verts=verts,
                foff=[rng.uniform(-1, 1) for _ in verts],
                sp=[rng.random() < 0.14 for _ in verts]))
        self.bokeh = [(rng.uniform(0, 1), rng.uniform(0, 1), rng.uniform(-0.02, 0.02),
                       rng.uniform(-0.015, 0.015), rng.uniform(0.012, 0.055),
                       rng.choice(BOKEH_COLS), rng.uniform(0, 6.28)) for _ in range(40)]
        self.ico = icosphere(random.Random(7))
        self.frf = [random.Random(i).uniform(0.8, 1.2) for i in range(len(self.ico[1]))]
        self.sparks = [(rng.uniform(0, 6.283), rng.uniform(0.25, 1.5), rng.uniform(1.0, 2.6),
                        rng.randrange(4), rng.uniform(0, 6.28)) for _ in range(280)]
        self.ray_j = [rng.uniform(-0.08, 0.08) for _ in range(28)]
        self.ray_l = [rng.uniform(0.6, 1.2) for _ in range(28)]

        pts, self.step, self.lines = build_points(name, fpath, W, H, portrait)
        self.half = self.step / 2 * 0.94
        self.dia = []
        for (x, y, idx) in pts:
            self.dia.append((x, y, rng.uniform(0, 6.28), math.sqrt(rng.random()) * self.U * 0.09,
                             colour_key(name, idx), rng.uniform(0.82, 1.15),
                             rng.uniform(0, 1.0), rng.uniform(-0.3, 0.3),
                             rng.uniform(0, 6.28), rng.random() < 0.07))
        print(f"      {len(self.dia)} diamonds", flush=True)

    # ---- small drawing helpers
    def star(self, d, x, y, s, k):
        c = (int(255 * k),) * 3
        w = max(1, int(s / 6))
        d.line([(x - s, y), (x + s, y)], fill=c, width=w)
        d.line([(x, y - s), (x, y + s)], fill=c, width=w)

    def shard_pos(self, s, t):
        W, H = self.W, self.H
        tt = min(t, T_BOOM)
        x = s["x0"] + s["vx"] * tt + 0.01 * math.sin(tt * 0.7 + s["ph"])
        y = s["y0"] + s["vy"] * tt + 0.012 * math.cos(tt * 0.6 + s["ph"])
        x = ((x + 0.15) % 1.3 - 0.15) * W
        y = ((y + 0.15) % 1.3 - 0.15) * H
        u = smooth(clamp((tt - 4.5) / 2.5)) * 0.3          # pulled towards the centre
        x += (self.cx - x) * u
        y += (self.cy - y) * u
        if t > T_BOOM:                                      # blown away by the explosion
            age = t - T_BOOM
            dx, dy = x - self.cx, y - self.cy
            ln = math.hypot(dx, dy) + 1e-6
            sp = self.U * (0.5 + 0.9 * s["z"])
            e = (1 - math.exp(-age * 1.8)) / 1.8
            x += dx / ln * sp * e
            y += dy / ln * sp * e
        return x, y

    def draw_shard(self, d, s, x, y, f, t, bright):
        size = s["size"] * self.U * f
        sx = 0.55 + 0.45 * abs(math.cos(s["spin"] * t * 0.7 + s["ph"]))
        ang = s["rot0"] + s["spin"] * t
        ca, sa = math.cos(ang), math.sin(ang)

        def tr(px, py):
            return (x * f + px * ca - py * sa, y * f + px * sa + py * ca)

        pts = [tr(math.cos(th) * rf * size * sx * s["el"], math.sin(th) * rf * size)
               for th, rf in s["verts"]]
        cp = tr(s["c"][0] * size, s["c"][1] * size)
        dark, light = KEYPAL[s["key"]]
        la = t * 0.8
        n = len(pts)
        for i in range(n):
            v = 0.5 + 0.5 * math.cos(s["verts"][i][0] + ang - la + s["foff"][i] * 3)
            v = clamp(v * 0.9 + (0.55 if s["sp"][i] else 0.0))
            d.polygon([cp, pts[i], pts[(i + 1) % n]], fill=shade(mix(dark, light, v), bright))
        edge = shade(mix(light, (255, 255, 255), 0.6), bright * 0.9)
        d.line(pts + [pts[0]], fill=edge, width=max(1, int(size / 60)))
        for i in range(0, n, 2):
            d.line([cp, pts[i]], fill=shade(light, bright * 0.45), width=1)

    def draw_sphere(self, img, cx, cy, r, t, key, fade, spin):
        V, F = self.ico
        size = int(r * 2.5)
        c = size / 2
        ay, ax = t * 0.9 * spin, 0.45 + 0.25 * math.sin(t * 0.5)
        ca, sa, cxa, sxa = math.cos(ay), math.sin(ay), math.cos(ax), math.sin(ax)
        rv = []
        for (x, y, z) in V:
            x1, z1 = x * ca + z * sa, -x * sa + z * ca
            rv.append((x1, y * cxa - z1 * sxa, y * sxa + z1 * cxa))
        dark, light = SPH[key]
        L = (-0.45, -0.55, 0.70)
        ln = math.sqrt(sum(q * q for q in L))
        L = tuple(q / ln for q in L)
        Hv = (L[0], L[1], L[2] + 1)
        hn = math.sqrt(sum(q * q for q in Hv))
        Hv = tuple(q / hn for q in Hv)
        fl = []
        for fi, (a, b, cc) in enumerate(F):
            A, B, C = rv[a], rv[b], rv[cc]
            ux, uy, uz = B[0] - A[0], B[1] - A[1], B[2] - A[2]
            vx, vy, vz = C[0] - A[0], C[1] - A[1], C[2] - A[2]
            n = (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)
            m = math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2) + 1e-9
            n = (n[0] / m, n[1] / m, n[2] / m)
            g = ((A[0] + B[0] + C[0]) / 3, (A[1] + B[1] + C[1]) / 3, (A[2] + B[2] + C[2]) / 3)
            if n[0] * g[0] + n[1] * g[1] + n[2] * g[2] < 0:
                n = (-n[0], -n[1], -n[2])
            fl.append((g[2], fi, n, A, B, C))
        fl.sort(key=lambda q: q[0])
        layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        lw = max(1, int(r / 110))
        for gz, fi, n, A, B, C in fl:
            poly = [(c + P[0] * r, c + P[1] * r) for P in (A, B, C)]
            diff = max(0.0, n[0] * L[0] + n[1] * L[1] + n[2] * L[2])
            if n[2] > 0:
                spec = max(0.0, n[0] * Hv[0] + n[1] * Hv[1] + n[2] * Hv[2]) ** 30
                col = mix(dark, light, clamp(0.22 + 0.9 * diff * self.frf[fi]))
                col = mix(col, (255, 255, 255), clamp(spec * 0.8))
                d.polygon(poly, fill=col + (205,))
                d.line(poly + [poly[0]], fill=mix(light, (255, 255, 255), 0.5) + (235,), width=lw)
            else:
                col = shade(mix(dark, light, 0.25 + 0.3 * diff), 0.7)
                d.polygon(poly, fill=col + (110,))
        if fade < 1:
            layer.putalpha(layer.split()[3].point(lambda v: int(v * fade)))
        img.paste(layer, (int(cx - c), int(cy - c)), layer)

    def streams(self, fd, c, dv, key, t, u, fade, rs):
        U = self.U
        L = U * (0.12 + 0.55 * u)
        cols = BLUE_STREAM if key == 0 else FIRE_STREAM
        px, py = -dv[1], dv[0]
        rnd = random.Random(int(t * FPS) * 7 + key)
        for k in range(18):
            off = (k - 9) * U * 0.006
            col = cols[k % len(cols)]
            pts = []
            for j in range(13):
                q = j / 12
                wob = (math.sin(t * 9 + k * 1.7 + j * 0.9) * U * 0.028
                       + math.sin(t * 17 + k * 2.3 - j * 1.3) * U * 0.012) * q
                sx = c[0] + dv[0] * (rs * 0.8 + L * q) + px * (off * (1 - q * 0.4) + wob)
                sy = c[1] + dv[1] * (rs * 0.8 + L * q) + py * (off * (1 - q * 0.4) + wob)
                pts.append((sx * 0.5, sy * 0.5))
            fd.line(pts, fill=shade(col, fade * (0.55 + 0.45 * math.sin(t * 12 + k))),
                    width=max(1, int(U * 0.0022)))
        for _ in range(34):
            q = rnd.random()
            sx = c[0] + dv[0] * (rs + L * q) + px * rnd.uniform(-1, 1) * U * 0.05 * q
            sy = c[1] + dv[1] * (rs + L * q) + py * rnd.uniform(-1, 1) * U * 0.05 * q
            rr = max(1, U * 0.004 * (1 - q * 0.5))
            fd.ellipse([sx * 0.5 - rr, sy * 0.5 - rr, sx * 0.5 + rr, sy * 0.5 + rr],
                       fill=shade(cols[2], fade))

    def lightning(self, fd, p0, p1, t, k):
        U = self.U
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        ln = math.hypot(dx, dy) + 1e-6
        px, py = -dy / ln, dx / ln
        cols = [(230, 240, 255), (90, 190, 255), (255, 150, 60)]
        for a in range(3):
            pts = []
            for j in range(15):
                q = j / 14
                n = (math.sin(t * 27 + a * 2.1 + j * 1.9) + math.sin(t * 41 + a * 5 - j * 2.7)) * 0.5
                off = n * U * 0.045 * math.sin(math.pi * q)
                pts.append(((p0[0] + dx * q + px * off) * 0.5, (p0[1] + dy * q + py * off) * 0.5))
            fd.line(pts, fill=shade(cols[a], k), width=max(1, int(U * (0.003 if a == 0 else 0.0018))))

    def diamonds(self, d, t):
        half = self.half
        sweep = ((t - T_DIA - T_FORM) * self.W * 0.55) % (self.W * 1.9) - self.W * 0.3
        sw_w = self.W * 0.12
        for (tx, ty, a, rr, key, j, delay, sw, ph, sp) in self.dia:
            sx, sy = self.cx + math.cos(a) * rr, self.cy + math.sin(a) * rr
            tt = t - T_DIA - delay
            e = ease_out(clamp(tt / (T_FORM - 1.0)))
            dx, dy = tx - sx, ty - sy
            x = sx + dx * e - dy * sw * math.sin(math.pi * e)
            y = sy + dy * e + dx * sw * math.sin(math.pi * e)
            r = half * (0.35 + 0.65 * clamp(tt / 0.5 + 0.2))
            ec = smooth(e)
            lc, dc = mix(HOT_L, DIA_L[key], ec), mix(HOT_D, DIA_D[key], ec)
            k = j
            if e >= 1:
                sh = max(0.0, 1 - abs((tx + ty * 0.5) - sweep) / sw_w)
                k = j * (0.95 + 0.1 * math.sin(t * 3 + ph))
                if sh > 0:
                    lc = mix(lc, (255, 255, 255), sh * 0.5)
                    dc = mix(dc, (255, 255, 255), sh * 0.3)
            d.polygon([(x, y - r), (x - r, y), (x, y + r)], fill=shade(lc, k))
            d.polygon([(x, y - r), (x + r, y), (x, y + r)], fill=shade(dc, k))
            if sp and e >= 1:
                s = max(0.0, math.sin(t * 4 + ph * 2)) ** 12
                if s > 0.25:
                    self.star(d, x, y, r * 3.2 * s, s)

    # ---- one frame
    def render(self, t):
        W, H, U, cx, cy = self.W, self.H, self.U, self.cx, self.cy
        ax = self.ax
        age = t - T_BOOM
        boom = age >= 0
        img = self.bg.copy()
        d = ImageDraw.Draw(img)
        for (x, y, ph) in self.stars:
            c = int(160 * (0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * 1.5 + ph))))
            d.rectangle([x, y, x + self.ss, y + self.ss], fill=(c, c, int(c * 1.1)))

        # --- crystal shards, 3 depth layers (far / mid blurred = depth of field)
        far = Image.new("RGB", (W // 4, H // 4))
        mid = Image.new("RGB", (W // 2, H // 2))
        dfar, dmid = ImageDraw.Draw(far), ImageDraw.Draw(mid)
        near = []
        appear = smooth(clamp(t / 1.2))
        for s in self.shards:
            fade = appear * ((1 - clamp(age / 2.4)) if boom else 1.0)
            if fade <= 0.02:
                continue
            x, y = self.shard_pos(s, t)
            br = (0.30 + 0.7 * s["z"]) * fade * 1.1
            if s["z"] < 0.33:
                self.draw_shard(dfar, s, x, y, 0.25, t, br)
            elif s["z"] < 0.66:
                self.draw_shard(dmid, s, x, y, 0.5, t, br)
            else:
                near.append((s, x, y, br))
        far = far.filter(ImageFilter.GaussianBlur(max(1, int(U * 0.25 * 0.012))))
        mid = mid.filter(ImageFilter.GaussianBlur(max(1, int(U * 0.5 * 0.004))))
        img = ImageChops.add(img, far.resize((W, H), Image.BILINEAR))
        img = ImageChops.add(img, mid.resize((W, H), Image.BILINEAR))

        fx = Image.new("RGB", (W // 2, H // 2))
        fd = ImageDraw.Draw(fx)
        gl = Image.new("RGB", (W // 4, H // 4))
        gd = ImageDraw.Draw(gl)
        glow_disc = lambda x, y, r, col: gd.ellipse(
            [x / 4 - max(r / 4, 0), y / 4 - max(r / 4, 0), x / 4 + max(r / 4, 0), y / 4 + max(r / 4, 0)], fill=col)

        # --- the two crystal spheres rushing together
        if t >= T_SPHERES and not boom:
            sf = smooth(clamp((t - T_SPHERES) / 1.0))
            rs = U * 0.12
            u = clamp((t - T_SPHERES) / (T_BOOM - T_SPHERES))
            dist0 = (H if self.portrait else W) * 0.36
            dist = 1.96 * rs + (dist0 - 1.96 * rs) * (1 - u ** 2.2)
            cb = (cx - ax[0] * dist / 2, cy - ax[1] * dist / 2)
            cr = (cx + ax[0] * dist / 2, cy + ax[1] * dist / 2)
            glow_disc(cb[0], cb[1], rs * 2.0, shade((20, 70, 235), 0.55 * sf))
            glow_disc(cr[0], cr[1], rs * 2.0, shade((235, 40, 40), 0.55 * sf))
            self.streams(fd, cb, (-ax[0], -ax[1]), 0, t, u, sf, rs)
            self.streams(fd, cr, ax, 1, t, u, sf, rs)
            if u > 0.3 and dist > 2.05 * rs:
                k = smooth((u - 0.3) / 0.7)
                p0 = (cb[0] + ax[0] * rs * 0.95, cb[1] + ax[1] * rs * 0.95)
                p1 = (cr[0] - ax[0] * rs * 0.95, cr[1] - ax[1] * rs * 0.95)
                self.lightning(fd, p0, p1, t, k)
            self.draw_sphere(img, cb[0], cb[1], rs, t, 0, sf, 1)
            self.draw_sphere(img, cr[0], cr[1], rs, t, 1, sf, -1)

        d = ImageDraw.Draw(img)
        for (s, x, y, br) in near:
            self.draw_shard(d, s, x, y, 1.0, t, br)

        # --- explosion
        if boom:
            a = math.exp(-age * 1.7)
            r = U * (0.10 + 0.55 * ease_out(clamp(age / 1.1)))
            glow_disc(cx, cy, r, shade((255, 170, 90), 0.9 * a))
            glow_disc(cx, cy, r * 0.55, shade((255, 245, 220), a))
            for sgn, col in ((-1, (40, 110, 255)), (1, (255, 50, 50))):
                glow_disc(cx + sgn * ax[0] * r * 0.9, cy + sgn * ax[1] * r * 0.9, r * 0.8,
                          shade(col, 0.8 * a))
            for i, (dl, col) in enumerate([(0, (120, 190, 255)), (0.12, (255, 90, 80)),
                                           (0.25, (255, 255, 255))]):
                aa = age - dl
                if 0 < aa < 1.7:
                    rr = U * 1.6 * ease_out(aa / 1.7) * 0.5
                    kk = 1 - aa / 1.7
                    fd.ellipse([cx / 2 - rr, cy / 2 - rr, cx / 2 + rr, cy / 2 + rr],
                               outline=shade(col, kk), width=max(2, int(U * 0.008 * kk * 0.5) + 1))
            if age < 1.4:
                rc = [(120, 190, 255), (255, 110, 90), (255, 215, 120)]
                for i in range(28):
                    an = i * 2 * math.pi / 28 + self.ray_j[i]
                    ln = U * (0.15 + 1.3 * ease_out(clamp(age / 0.9))) * self.ray_l[i]
                    w = U * 0.012 * (1 - clamp(age / 1.4))
                    ex, ey = cx + math.cos(an) * ln, cy + math.sin(an) * ln
                    px, py = -math.sin(an), math.cos(an)
                    fd.polygon([((cx + px * w) / 2, (cy + py * w) / 2), (ex / 2, ey / 2),
                                ((cx - px * w) / 2, (cy - py * w) / 2)],
                               fill=shade(rc[i % 3], (1 - age / 1.4) * 0.9))
            for (an, spd, life, ci, ph) in self.sparks:
                if age > life:
                    continue
                e = (1 - math.exp(-age * 2.4)) / 2.4
                dx, dy = math.cos(an), math.sin(an)
                x = cx + dx * spd * U * e
                y = cy + dy * spd * U * e + 0.08 * U * age * age
                tail = spd * U * math.exp(-age * 2.4) * 0.045
                fd.line([(x / 2, y / 2), ((x - dx * tail) / 2, (y - dy * tail) / 2)],
                        fill=shade(SPARK_COLS[ci], 1 - age / life), width=max(1, int(U * 0.0025)))

        # --- the diamonds that form the name
        if t >= T_DIA:
            self.diamonds(d, t)
            form = smooth(clamp((t - T_DIA) / T_FORM))
            if form > 0:
                if len(self.lines) == 1:
                    for fxp, c in ((0.32, (30, 80, 255)), (0.68, (255, 25, 60))):
                        bx = W * fxp + math.sin(t * 0.8 + fxp * 5) * W * 0.04
                        rr = W * 0.17
                        gd.ellipse([bx / 4 - rr / 4, cy / 4 - rr * 0.15, bx / 4 + rr / 4, cy / 4 + rr * 0.15],
                                   fill=shade(c, 0.45 * form))
                else:
                    for (ly, key) in self.lines:
                        c = (255, 25, 60) if key else (30, 80, 255)
                        bx, rr = W / 2 + math.sin(t * 0.8 + ly) * W * 0.03, W * 0.34
                        gd.ellipse([bx / 4 - rr / 4, ly / 4 - rr * 0.105, bx / 4 + rr / 4, ly / 4 + rr * 0.105],
                                   fill=shade(c, 0.4 * form))
            done = t - (T_DIA + T_FORM)
            if 0 <= done < 1.2:
                rr = U * 0.9 * ease_out(done / 1.2) * 0.5
                fd.ellipse([cx / 2 - rr, cy / 2 - rr, cx / 2 + rr, cy / 2 + rr],
                           outline=shade((150, 200, 255), 0.8 * (1 - done / 1.2)),
                           width=max(2, int(U * 0.004)))

        # --- bloom (two scales) + crisp fx
        sw, sh = W // 4, H // 4
        small = ImageChops.add(img.resize((sw, sh), Image.BILINEAR), gl)
        small = ImageChops.add(small, fx.resize((sw, sh), Image.BILINEAR))
        b1 = small.filter(ImageFilter.GaussianBlur(max(2, W // 240)))
        b2 = (small.resize((sw // 2, sh // 2), Image.BILINEAR)
              .filter(ImageFilter.GaussianBlur(max(2, W // 700)))
              .resize((sw, sh), Image.BILINEAR))
        bloom = ImageChops.add(b1, b2).resize((W, H), Image.BILINEAR).point(lambda v: int(v * 0.38))
        img = ImageChops.add(img, bloom)
        img = ImageChops.add(img, fx.filter(ImageFilter.GaussianBlur(1)).resize((W, H), Image.BILINEAR))

        # --- bokeh balls
        bk = Image.new("RGB", (sw, sh))
        bd = ImageDraw.Draw(bk)
        flare = 1 + 1.5 * math.exp(-age * 2) if boom else 1.0
        dim = 1 - 0.55 * smooth(clamp((t - T_DIA) / T_FORM))
        for (x0, y0, vx, vy, rad, col, ph) in self.bokeh:
            x = (((x0 + vx * t) + 0.1) % 1.2 - 0.1) * sw
            y = (((y0 + vy * t) + 0.1) % 1.2 - 0.1) * sh
            rr = rad * U / 4
            k = (0.25 + 0.2 * (0.5 + 0.5 * math.sin(t * 1.3 + ph))) * flare * dim * appear
            bd.ellipse([x - rr, y - rr, x + rr, y + rr], fill=shade(col, k))
        bk = bk.filter(ImageFilter.GaussianBlur(max(1, int(rad_blur(U)))))
        img = ImageChops.add(img, bk.resize((W, H), Image.BILINEAR))

        img = ImageChops.multiply(img, self.vig)

        if boom:
            fl = math.exp(-age * 8) * 1.05
            if fl > 0.03:
                img = Image.blend(img, self.white, min(0.92, fl))
            if age < 0.9:
                amp = U * 0.012 * math.exp(-age * 5)
                img = ImageChops.offset(img, int(amp * math.sin(age * 70)), int(amp * math.cos(age * 83)))
        done = t - (T_DIA + T_FORM)
        if 0 <= done < 0.4:
            img = Image.blend(img, self.white, 0.25 * (1 - done / 0.4))
        ft = smooth(clamp(t / 0.8))
        if ft < 1:
            img = Image.blend(self.black, img, ft)
        return img


def rad_blur(U):
    return max(1, U * 0.0012)


# -------------------------------------------------------------------- main
def sound_expr():
    e = ("0.12*sin(2*PI*55*t)*min(1,t/2)"
         "+0.2*sin(2*PI*(150*t+45*t*t))*lt(t,7)*(t/7)"
         "+0.9*sin(2*PI*48*(t-7))*exp(-1.8*(t-7))*gte(t,7)"
         "+0.6*(2*random(0)-1)*exp(-5*(t-7))*gte(t,7)"
         "+0.04*sin(2*PI*2200*t)*gte(t,9.5)*exp(-0.4*(t-9.5))")
    return e.replace(",", "\\,")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", choices=list(RES) + ["16k", "32k"], default="fhd")
    ap.add_argument("--portrait", action="store_true")
    ap.add_argument("--name", default=DEFAULT_NAME)
    ap.add_argument("--music")
    ap.add_argument("--font")
    ap.add_argument("--ss", type=int, choices=[1, 2, 3, 4], help="anti-aliasing level")
    ap.add_argument("--out", default="epic_apkhack.mp4")
    ap.add_argument("--snap", type=float, help="save PNG of one moment (seconds)")
    a = ap.parse_args()

    res = a.res
    if res in ("16k", "32k"):
        print(f"{res} cannot be played or encoded by any phone/player (HEVC max is 8192x4320, "
              f"one {res} frame needs gigabytes of RAM).\n"
              f"Using 8k instead. For extra sharpness use --ss.")
        res = "8k"
    W, H = RES[res]
    if a.portrait:
        W, H = H, W
    ss = a.ss or DEFAULT_SS[res]
    fpath = find_font(a.font)
    if not fpath:
        print("No TTF font found; pass --font file.ttf for best letters.")

    print(f"[1/3] Building scene {W}x{H} (anti-aliasing x{ss}) ...", flush=True)
    sc = Epic(W * ss, H * ss, a.name, fpath, ss, a.portrait)

    def frame(t):
        im = sc.render(t)
        return im.reduce(ss) if ss > 1 else im

    if a.snap is not None:
        frame(a.snap).save("snap.png")
        print("saved snap.png")
        return

    n = int(TOTAL * FPS)
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if a.music:
        cmd += ["-i", a.music, "-af", f"afade=t=out:st={TOTAL - 1.5}:d=1.5"]
    else:
        cmd += ["-f", "lavfi", "-i", f"aevalsrc={sound_expr()}:s=44100:d={TOTAL}"]
    if res in ("4k", "8k"):
        vc = ["-c:v", "libx265", "-preset", "veryfast", "-crf", "20", "-tag:v", "hvc1"]
    else:
        vc = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "16"]
    cmd += ["-map", "0:v", "-map", "1:a", *vc, "-pix_fmt", "yuv420p", "-ac", "2",
            "-c:a", "aac", "-b:a", "192k", "-t", f"{TOTAL:.2f}", "-movflags", "+faststart", a.out]

    print(f"[2/3] Rendering {n} frames -> {a.out}", flush=True)
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for i in range(n):
            p.stdin.write(frame(i / FPS).tobytes())
            if i % 15 == 0:
                print(f"      {i * 100 // n}%", flush=True)
        p.stdin.close()
        p.wait()
    except BrokenPipeError:
        sys.exit("ffmpeg stopped early (see error above)")
    print(f"[3/3] Done: {a.out}")


if __name__ == "__main__":
    main()
