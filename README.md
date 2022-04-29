# ctfd-matrix-scoreboard
## Usage

在`CTFd`的`CTFd/plugins`目录下

```bash
git clone https://github.com/Ephemeral1y/ctfd-matrix-scoreboard
docker restart ctfd_ctfd_1
```

一些参数的修改

`__init__.py`

```python
NumberOfChallenges = 40 # 题目最大数量

if(solve.date == top[0].date):
	solvenum = solve.challenge_id
	score = score + int(cvalue * 1.1)   #一血加成10%
	blood[solve.challenge_id].append(1)
elif(solve.date == top[1].date):
	solvenum = solve.challenge_id
	score = score + int(cvalue * 1.05)  #二血加成5%
	blood[solve.challenge_id].append(2)
elif(solve.date == top[2].date):
	solvenum = solve.challenge_id
	score = score + int(cvalue * 1.03)  #三血加成3%
	blood[solve.challenge_id].append(3)
else:
	solvenum = solve.challenge_id
	score = score + int(cvalue * 1)
	blood[solve.challenge_id].append(0)
```

目前只支持`reverse`,`pwn`,`web`,`misc`,`crypto`五个方向的前端显示，有需要的可以自行修改源码
