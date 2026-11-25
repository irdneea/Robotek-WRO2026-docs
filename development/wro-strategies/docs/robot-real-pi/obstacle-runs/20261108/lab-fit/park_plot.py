import sys, math, numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
d=np.load(sys.argv[1]); out=sys.argv[2]
rs,a,track=d['rs'],d['a'],[list(t) for t in d['track']]
x,y,th=track[-1]
ok=np.isfinite(rs)&(rs>0.05)&(rs<3)
OUT=1.5; L,D,END=0.3495,0.20,0.48; T=0.02
FRONT,REAR,HW=0.14699,0.08591,0.0738
fig,axs=plt.subplots(1,2,figsize=(14,6.5))
for ax,(name,sgn) in zip(axs,(('CCW (lote x 0,13..0,48)',1),('CW, marco espejado (lote x -0,48..-0,13)',-1))):
    px=x+rs[ok]*np.cos(th+sgn*a[ok]); py=y+rs[ok]*np.sin(th+sgn*a[ok])
    ax.scatter(px,py,s=4,c='tab:blue',label='LiDAR (último barrido)')
    tr=np.array(track); ax.plot(tr[:,0],tr[:,1],'-',c='0.6',lw=1,label='pose de la estrategia')
    xa,xb=(END-L,END) if sgn>0 else (-END,-END+L)
    ax.add_patch(plt.Rectangle((xa,-OUT),L,D,fill=False,ec='tab:green',lw=2,ls='--',label='lote del reglamento'))
    for lx in (xa-T,xb): ax.add_patch(plt.Rectangle((lx,-OUT),T,D,color='tab:green',alpha=.5))
    ax.axhline(-OUT,c='k',lw=2,label='muro exterior (y -1,5)')
    c,s=math.cos(th),math.sin(th)
    box=[(FRONT,HW),(FRONT,-HW),(-REAR,-HW),(-REAR,HW),(FRONT,HW)]
    ax.plot([x+u*c-v*s for u,v in box],[y+u*s+v*c for u,v in box],'r-',lw=2,label='coche (contorno, pose final)')
    ax.arrow(x,y,0.1*c,0.1*s,head_width=0.02,color='r')
    ax.set_xlim(-0.9,0.9); ax.set_ylim(-1.65,-0.7); ax.set_aspect('equal'); ax.grid(alpha=.3)
    ax.set_title(name); ax.set_xlabel('x (m)'); ax.set_ylabel('y (m)')
axs[0].legend(loc='upper left',fontsize=8)
fig.suptitle('Aparcamiento fijo 23:25: pose final x %.3f y %.3f rumbo %.2f rad (%.0f°)'%(x,y,th,math.degrees(th)))
fig.tight_layout(); fig.savefig(out,dpi=110)
print(x,y,th)
