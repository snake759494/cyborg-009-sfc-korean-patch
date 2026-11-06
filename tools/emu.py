"""Headless snes9x libretro harness (background, no window)."""
import ctypes as C
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
B = dict(B=0, Y=1, SELECT=2, START=3, UP=4, DOWN=5, LEFT=6, RIGHT=7, A=8, X=9, L=10, R=11)


class Info(C.Structure):
    _fields_ = [('path', C.c_char_p), ('data', C.c_void_p), ('size', C.c_size_t), ('meta', C.c_char_p)]


class Var(C.Structure):
    _fields_ = [('key', C.c_char_p), ('value', C.c_char_p)]


ENV = C.CFUNCTYPE(C.c_bool, C.c_uint, C.c_void_p)
VIDEO = C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
AUDIO = C.CFUNCTYPE(None, C.c_int16, C.c_int16)
BATCH = C.CFUNCTYPE(C.c_size_t, C.c_void_p, C.c_size_t)
POLL = C.CFUNCTYPE(None)
INPUT = C.CFUNCTYPE(C.c_int16, C.c_uint, C.c_uint, C.c_uint, C.c_uint)


class Emu:
    def __init__(self, rom, workdir=None):
        self.core = core = C.CDLL(str(HERE / 'snes9x_libretro.dll'))
        self.dirs = C.create_string_buffer(str(workdir or HERE).encode())
        self.pixfmt = 0
        self.last = None
        self.pressed = set()
        self.vars = {}

        @ENV
        def env(cmd, data):
            if cmd in (9, 30, 31):
                C.cast(data, C.POINTER(C.c_char_p))[0] = C.cast(self.dirs, C.c_char_p); return True
            if cmd == 10:
                self.pixfmt = C.cast(data, C.POINTER(C.c_int))[0]; return self.pixfmt in (0, 1, 2)
            if cmd == 15:
                v = C.cast(data, C.POINTER(Var)).contents; v.value = self.vars.get(v.key); return bool(v.value)
            if cmd == 16:
                vv = C.cast(data, C.POINTER(Var)); i = 0
                while vv[i].key:
                    self.vars[vv[i].key] = vv[i].value.split(b'; ')[-1].split(b'|')[0]; i += 1
                return True
            if cmd in (3, 17):
                C.cast(data, C.POINTER(C.c_bool))[0] = False; return True
            if cmd in (18, 37): return True
            return False

        @VIDEO
        def video(data, w, h, pitch):
            if data and data != C.c_void_p(-1).value:
                self.last = (C.string_at(data, pitch * h), w, h, pitch, self.pixfmt)

        @AUDIO
        def audio(a, b): pass

        @BATCH
        def batch(d, n): return n

        @POLL
        def poll(): pass

        @INPUT
        def inp(port, device, index, ident):
            return 1 if port == 0 and device == 1 and ident in self.pressed else 0

        self._cb = [env, video, audio, batch, poll, inp]
        for name, fn, typ in [('environment', env, ENV), ('video_refresh', video, VIDEO), ('audio_sample', audio, AUDIO),
                              ('audio_sample_batch', batch, BATCH), ('input_poll', poll, POLL), ('input_state', inp, INPUT)]:
            f = getattr(core, 'retro_set_' + name); f.argtypes = [typ]; f(fn)
        core.retro_init()
        core.retro_load_game.argtypes = [C.POINTER(Info)]; core.retro_load_game.restype = C.c_bool
        core.retro_get_memory_size.argtypes = [C.c_uint]; core.retro_get_memory_size.restype = C.c_size_t
        core.retro_get_memory_data.argtypes = [C.c_uint]; core.retro_get_memory_data.restype = C.c_void_p
        core.retro_serialize_size.restype = C.c_size_t
        core.retro_serialize.argtypes = [C.c_void_p, C.c_size_t]; core.retro_serialize.restype = C.c_bool
        core.retro_unserialize.argtypes = [C.c_void_p, C.c_size_t]; core.retro_unserialize.restype = C.c_bool
        rom = Path(rom).read_bytes()
        self._rom = C.create_string_buffer(rom)
        game = Info(b'game.sfc', C.cast(self._rom, C.c_void_p), len(rom), None)
        assert core.retro_load_game(C.byref(game))
        self.frame = 0

    def run(self, n=1, keys=()):
        self.pressed = {B[k] for k in keys}
        for _ in range(n):
            self.core.retro_run(); self.frame += 1
        self.pressed = set()

    def tap(self, key, hold=3, after=20):
        self.run(hold, [key]); self.run(after)

    def mem(self, k):
        return C.string_at(self.core.retro_get_memory_data(k), self.core.retro_get_memory_size(k))

    def wram(self):
        return self.mem(2)

    def vram(self):
        return self.mem(3)

    def save(self, path=None):
        n = self.core.retro_serialize_size(); b = C.create_string_buffer(n)
        assert self.core.retro_serialize(b, n)
        if path: Path(path).write_bytes(b.raw)
        return b.raw

    def load(self, data):
        if isinstance(data, (str, Path)): data = Path(data).read_bytes()
        b = C.create_string_buffer(data); assert self.core.retro_unserialize(b, len(data))

    def image(self):
        raw, w, h, pitch, fmt = self.last
        if fmt == 1:
            a = np.frombuffer(raw, np.uint32).reshape(h, pitch // 4)[:, :w]
            rgb = np.stack([(a >> 16) & 255, (a >> 8) & 255, a & 255], -1).astype(np.uint8)
        else:
            a = np.frombuffer(raw, np.uint16).reshape(h, pitch // 2)[:, :w].astype(np.uint32)
            if fmt == 2:
                rgb = np.stack([((a >> 11) & 31) * 255 // 31, ((a >> 5) & 63) * 255 // 63, (a & 31) * 255 // 31], -1)
            else:
                rgb = np.stack([((a >> 10) & 31) * 255 // 31, ((a >> 5) & 31) * 255 // 31, (a & 31) * 255 // 31], -1)
            rgb = rgb.astype(np.uint8)
        return Image.fromarray(rgb)

    def shot(self, path, scale=2):
        im = self.image(); im.resize((im.width * scale, im.height * scale), Image.NEAREST).save(path)

    def close(self):
        self.core.retro_unload_game(); self.core.retro_deinit()


def regs_from_state(s):
    i = s.find(b'REG:000016:') + 11
    r = s[i:i + 16]
    import struct
    PB, DB, P, A, D, S, X, Y, PC = struct.unpack('>BBHHHHHHH', r)
    return dict(PB=PB, DB=DB, P=P, A=A, D=D, S=S, X=X, Y=Y, PC=PC)
