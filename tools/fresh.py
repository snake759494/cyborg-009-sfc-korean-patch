import sys; sys.path.insert(0,'tools')
from emu import Emu
e=Emu(sys.argv[1]); e.run(1900); e.save('st_kt.bin'); e.close()
