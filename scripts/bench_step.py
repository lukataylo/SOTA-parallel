import sys, time, numpy as np
G=9.81; N2=0.015**2; dx=1.0; dt=0.1; R=1e-5
def make(xp, pad):
    def step(z,h,qx,qy):
        eta=z+h
        hfx=xp.maximum(xp.maximum(eta[...,:,:-1],eta[...,:,1:])-xp.maximum(z[...,:,:-1],z[...,:,1:]),0.)
        hfy=xp.maximum(xp.maximum(eta[...,:-1,:],eta[...,1:,:])-xp.maximum(z[...,:-1,:],z[...,1:,:]),0.)
        wx=hfx>1e-4; wy=hfy>1e-4
        sx=xp.where(wx,hfx,1.); sy=xp.where(wy,hfy,1.)
        qx=xp.where(wx,(qx-G*sx*dt*(eta[...,:,1:]-eta[...,:,:-1])/dx)/(1+G*dt*N2*xp.abs(qx)/sx**(7/3)),0.)
        qy=xp.where(wy,(qy-G*sy*dt*(eta[...,1:,:]-eta[...,:-1,:])/dx)/(1+G*dt*N2*xp.abs(qy)/sy**(7/3)),0.)
        qxp=xp.maximum(qx,0); qxm=xp.maximum(-qx,0); qyp=xp.maximum(qy,0); qym=xp.maximum(-qy,0)
        out=(pad(qxp,0,0,0,1)+pad(qxm,0,0,1,0)+pad(qyp,0,1,0,0)+pad(qym,1,0,0,0))*dt/dx
        f=xp.minimum(1.,h/(out+1e-12))
        qx=qxp*f[...,:,:-1]-qxm*f[...,:,1:]; qy=qyp*f[...,:-1,:]-qym*f[...,1:,:]
        div=pad(qx,0,0,0,1)-pad(qx,0,0,1,0)+pad(qy,0,1,0,0)-pad(qy,1,0,0,0)
        h=h-div*dt/dx+R*dt
        return h,qx,qy
    return step
def terrain(B,n):
    r=np.random.default_rng(0); x=np.linspace(0,1,n)
    z=(0.5*np.sin(6*x)[None,:]*np.cos(5*x)[:,None]+0.02*r.normal(size=(n,n))).astype(np.float32)
    return np.broadcast_to(z,(B,n,n)).copy()
which,B,n,steps=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4])
z0=terrain(B,n)
if which=="mlx":
    import mlx.core as mx
    pad=lambda a,t,b,l,r: mx.pad(a,[(0,0),(t,b),(l,r)])
    step=mx.compile(make(mx,pad))
    z=mx.array(z0); h=mx.zeros((B,n,n)); qx=mx.zeros((B,n,n-1)); qy=mx.zeros((B,n-1,n))
    def run(h,qx,qy,k):
        for i in range(k):
            h,qx,qy=step(z,h,qx,qy)
            if i%20==19: mx.eval(h,qx,qy)
        mx.eval(h,qx,qy); return h,qx,qy
    h,qx,qy=run(h,qx,qy,40); t=time.time(); h,qx,qy=run(h,qx,qy,steps); el=time.time()-t
    tot=float(h.sum())
else:
    import jax, jax.numpy as jnp
    pad=lambda a,t,b,l,r: jnp.pad(a,((0,0),(t,b),(l,r)))
    st=make(jnp,pad)
    @jax.jit
    def run(z,h,qx,qy):
        def body(s,_): return st(z,*s),None
        s,_=jax.lax.scan(body,(h,qx,qy),None,length=steps); return s
    z=jnp.array(z0); s=(jnp.zeros((B,n,n)),jnp.zeros((B,n,n-1)),jnp.zeros((B,n-1,n)))
    o=run(z,*s); o[0].block_until_ready(); t=time.time(); o=run(z,*o); o[0].block_until_ready(); el=time.time()-t
    tot=float(o[0].sum())
print(f"{which} B={B} n={n} steps={steps}: {el:.2f}s  {B*n*n*steps/el/1e6:.0f} Mcell-steps/s  mass={tot:.4f}")
