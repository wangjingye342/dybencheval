import json, math
from collections import defaultdict

rows=[json.loads(l) for l in open('annotation_results_fixed_100.jsonl',encoding='utf-8')]
models=sorted(set(m for r in rows for m in (r['model_a'],r['model_b'])))

wins=defaultdict(float); games=defaultdict(int)
for r in rows:
    a,b=r['model_a'],r['model_b']
    games[(a,b)]+=1; games[(b,a)]+=1
    if r['label']=='tie':
        wins[(a,b)]+=0.5; wins[(b,a)]+=0.5
    elif r['label']=='model_a':
        wins[(a,b)]+=1
    else:
        wins[(b,a)]+=1

# connectivity components
adj=defaultdict(set)
for (a,b),n in games.items(): adj[a].add(b)
seen=set(); comps=[]
for m in models:
    if m in seen: continue
    stack=[m]; comp=set()
    while stack:
        x=stack.pop()
        if x in seen: continue
        seen.add(x); comp.add(x)
        stack+=[y for y in adj[x] if y not in seen]
    comps.append(sorted(comp))

print("Connected comparison groups (models linked by matches):")
for i,c in enumerate(comps,1): print("  Group %d: %s"%(i,c))

print("\n=== Win rate leaderboard (tie counts 0.5) ===")
wr={}
for m in models:
    w=sum(wins[(m,o)] for o in models if (m,o) in wins)
    g=sum(games[(m,o)] for o in models if (m,o) in games)
    wr[m]=(w,g,w/g)
for rank,(m,(w,g,p)) in enumerate(sorted(wr.items(),key=lambda x:-x[1][2]),1):
    print("  %d. %-38s %5.1f%%   (%.1f/%d games)"%(rank,m,p*100,w,g))

def bradley_terry(mods):
    p={m:1.0 for m in mods}
    W={m:sum(wins.get((m,o),0) for o in mods) for m in mods}
    for _ in range(3000):
        newp={}
        for m in mods:
            denom=sum(games.get((m,o),0)/(p[m]+p[o]) for o in mods if o!=m)
            newp[m]=W[m]/denom if denom>0 else p[m]
        gm=math.exp(sum(math.log(v) for v in newp.values())/len(newp))
        p={m:newp[m]/gm for m in mods}
    return p

print("\n=== Bradley-Terry strength (fit per group; higher = stronger) ===")
for i,c in enumerate(comps,1):
    if len(c)<2:
        print("  Group %d: %s (no comparisons)"%(i,c[0])); continue
    p=bradley_terry(c)
    print("  Group %d:"%i)
    for rank,(m,v) in enumerate(sorted(p.items(),key=lambda x:-x[1]),1):
        elo=400*math.log10(v)
        print("     %d. %-38s BT=%6.3f  (Elo-scale %+6.0f)"%(rank,m,v,elo))
