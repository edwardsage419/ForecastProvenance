# 待单独授权的确切GitHub发布动作

只允许审阅本方案；本轮未执行以下动作。当前AGENTS.md规定：`Do not perform git commit, push, merge, rebase, force push, reset, clean, stash, or discard unknown changes unless explicitly authorized for that specific operation.` 选择公开GitHub与普通开发连续授权不自行扩大为这些具体Git写入。

拟执行：在现有`edwardsage419/ForecastProvenance`公开仓库，以最新核对的main commit为parent，新建`codex/public-evidence-d228`分支；仅新增FILES.json白名单79项及索引本身，共80文件；建立一份提交并推送/等效GitHub API写入，创建一份草稿PR供用户查看。内容只放`evidence/development-snapshots/2026-10-26-d228/`，不改产品入口、主分支、仓库公开性或现有目录，不执行merge。新分支已存在、parent/目标目录变动或白名单身份改变时停止并保存具体差异，不覆盖重写。

发布前必须固定本地FILES.json身份，逐项重新核对79条，重新读取main和目标目录；不读取/处理未知dirty，不使用`git add .`或全目录扫描。推荐通过精确tree/blob写入独立分支，避免本地未知index/worktree状态；API提交/分支写入与Git提交同样需要这份具体授权，不能借工具绕过。

发布后只读核对提交tree内80路径/尺寸/对象身份，逐项按固定commit重新取回可获得的原字节，核对SHA256；连接器不支持二进制时不能用metadata/hash-of-pointer冒充ZIP取回验证。可另用已授权普通公开HTTPS GET读取固定commit的普通公共文件，不提交provider/OTS请求。保存远端核验结果；若取回失败保留未决，不说已完成远端恢复，不启动付费替代。

草稿PR标题建议：`Preserve bounded development snapshot through D228`。说明应明确：这是有限开发归档，不是实际规则采纳、完整公共协议证据、资格/Acceptance/Freeze/Genesis或生产就绪；保留未决与错误尝试，零新增费用，不合并。发布没有赋予这些文档规范效力，也不把公开时间认证为历史首次时间。

这份动作方案不包含任何私钥、待签消息、provider事件、Core/native/RPC、真实信任或规则动作。用户可以只批准这份确切发布动作，不必再次解释历史或确认已经记录的业务方向。若暂不批准，保留本地成果并继续其他有依据且在主线内的工作；不重复造发布工具或副本模型。
