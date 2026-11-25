import csv,numpy as np,math,itertools
from robotek_evaluation.open_lab import Actuators
from robotek_common import vehicle
a=list(csv.DictReader(open('/tmp/v5/id/out/audit_pose.csv'))); c=list(csv.DictReader(open('/tmp/v5/id/cmd.csv')))
t=np.array([float(r['sim_time']) for r in a]); sl=np.array([float(r['steer_actual']) for r in a]); sr=np.array([float(r['steer_right_actual']) for r in a])
phys=np.arctan((np.tan(sl)+np.tan(sr))/2)
ct=np.array([float(r['sim_time']) for r in c]); cv=np.array([float(r['v']) for r in c]); cw=np.array([float(r['wz']) for r in c])
t0=ct[0]+8.0; sel=(t>t0-0.5)&(t<ct[-1]+0.5)
def run(params, dyn=None):
    act=Actuators(); act.p.update(params); dt=0.01; out=[]
    for i in range(int((ct[-1]-ct[0])/dt)):
        now=ct[0]+i*dt; k=np.searchsorted(ct,now,side='right')-1
        v=cv[k]; w=cw[k]; steer=math.atan(w*vehicle.WHEELBASE/v) if v>1e-3 else 0.0
        act.command(now,v,steer); act.step(now,dt)
        out.append((now,math.atan(math.tan(act.steer)*vehicle.WHEELBASE/0.13)))  # physical nominal from model steer
    return np.array(out)
if __name__=='__main__':
    res=[]
    for delay,rate,tau in itertools.product((0.04,0.06,0.08,0.1,0.12,0.15),(0.6,0.7,0.8,0.9,1.0,1.2,1.5),(0.0,0.02,0.04,0.06,0.1)):
        out=run(dict(steer_delay=delay,steer_rate=rate,steer_tau=max(tau,1e-6)))
        pr=np.interp(t[sel],out[:,0],out[:,1]); res.append((float(np.sqrt(np.mean((pr-phys[sel])**2))),delay,rate,tau))
    for r in sorted(res)[:8]: print([round(x,4) for x in r])
    print('current', [r for r in res if r[1:]==(0.06,1.2,0.04)] or 'n/a')
