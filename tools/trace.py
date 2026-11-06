import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from cpu import from_state
def run_frames(rom,state,frames=1,maxsteps=3_000_000,on_write=None,on_step=None,on_read=None):
  c=from_state(rom,state)
  if on_read: c.m.rlog=lambda a:on_read(c,a)
  if on_write: c.m.wlog=lambda a,v:on_write(c,a,v)
  if on_step: c.trace=on_step
  hist={};nmis=0;steps=0
  last=[]
  while steps<maxsteps:
    pc=c.PB<<16|c.PC
    try: c.step()
    except StopIteration: pc=None
    steps+=1
    if pc is None or hist.get(pc,0)>2000:
      # inject NMI
      nmis+=1
      if nmis>frames: break
      c.push8(c.PB);c.push16(c.PC);c.push8(c.P);c.P|=4;c.P&=~8;c.PB=0
      c.PC=c.m.r(0xffea)|c.m.r(0xffeb)<<8; hist={}
      c.m.io[0x4210]=0x80
      continue
    hist[pc]=hist.get(pc,0)+1
  return c
