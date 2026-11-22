# Pro: run this now (Sunday 05:25). Two checks, about 85 minutes, nothing else on the GPU.

```
git pull --rebase
nohup fill/final_chain.sh pro dense random > results/pro/final_chain.log 2>&1 &
```

- `dense`: the lowered half re-mapped with squares 75 m apart (225 runs). `random`: 240 dismissed what-ifs run alone.
- Lines are in `docs/G_CRITERIA.md` ("Sunday morning checks"). The chain pushes results every 10 minutes and at the end.
- Write one line in `status/pro.md` when it starts and when it ends. Change no thresholds. Do not score; the Air scores.
- If you see this after 07:30, do not start: the Air will have taken the jobs over.
