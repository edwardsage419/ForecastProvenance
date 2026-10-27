# 已验证的公开时间演练：离线重放交付

这是一次已获准、已结束的非预测演练材料。实际4次请求：2份服务回应通过验签，另1家2次超时；失败和后续退避状态保留。没有新增费用，没有生产资格、规则采纳或Genesis动作。完整项目仍未就绪。

**证明主体是原公开FILES.json，不是这个后来整理的ZIP。** 本包不能证明新ZIP或新代码在原回应时间以前就已存在；不能把该非预测证据改成预测记录。

下载并核验public-time-event-replay.zip：2742486bytes，SHA256：

    6f8b62c87aba43d5bb044061b6e5884fc2c1db4eab77e4ab224b2033353e89ba

仅展开到全新目录。内部82个安全普通文件，81条成员身份清单，展开4871129bytes；不包含Go安装包、私钥/测试私钥、venv、钱包或Core数据。固定上游许可原件和来源说明已随包保留。验证外部SHA及内部manifest以后，使用已有兼容Python，在新目录中运行：

    /absolute/path/to/existing/python -I -S -B scripts/development/offline_evidence/roughtime_event.py

预期exit0/OBSERVED只表示47份原件与既有审计匹配；本命令不联网或重新运行native，结果仍NOT_READY/NONE。原生数学重放仅在darwin/arm64下按包内README的network-deny命令运行，使用已有Python3.12.3与包内固定二进制；不安装新环境。它重验2份原回应及4个public signature/nonce反例，状态递推一致。已有输出/软链接拒绝，最终排他创建结果，不覆盖其他结果。

本机和新目录实际重放结果逐byte相同；8项运输/覆盖保护测试通过，独立review P2已修复并定向复验关闭。REVIEW.md保留初查，RECHECK.md为最终结论。native/publicpacket验证不建立完整软件信任、控制独立性、生产许可、完整历史/规则/报告/Strong/workflow；本地解析地址也不是运营方公网路由证明。

原始授权仅本次事件，已consumed；不得再次执行历史联网脚本、归零state或自动启动新事件。发布本包只保存可核验原件，不做正式采纳、资格变化、Acceptance/Freeze/Genesis或生产。
