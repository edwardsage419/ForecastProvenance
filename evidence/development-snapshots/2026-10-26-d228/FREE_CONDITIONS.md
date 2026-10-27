# 当前有限快照的费用与容量边界

核查日期：2026-10-26，使用GitHub官方文档。只判断这组约17MB开发成果，不能把未来未知事件量或生命周期增长填0。

| 事实 | 本批影响 | 官方依据 |
|---|---|---|
| GitHub Free个人账户可使用不限数量公开仓库 | 现有公开仓库可作本批拟用位置，不必新购计划 | https://docs.github.com/en/get-started/learning-about-github/githubs-plans |
| 普通文件>50MiB有警告，>100MiB阻止；网页添加每文件至多25MiB | 最大15,024,382byte低于三者，不需要LFS；不采用网页手工逐一上传80文件作为推荐操作 | https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github |
| repository-limits给出.git盘占用10GB、目录宽3000、深50等性能建议，单对象推荐1MB但硬限100MB | 15MB ZIP高于1MB推荐而低于硬限；仅保留一份基础包加小增量，不频繁重复提交大二进制。建议不是免费网盘配额 | https://docs.github.com/en/repositories/creating-and-managing-repositories/repository-limits |
| 另一large-files文档仍给出仓库理想<1GB、强烈建议<5GB | 两页建议数值不同，均如实记录；当前小批次明显更小，不能据此保证整个远端.git精确体积或无限容量 | 同上两页 |
| 官方备份文档区分Git历史、LFS与额外元数据；迁移archive有恢复局限 | 此批采用普通文件，不以Actions artifact/Packages/wiki或migration archive作为唯一保存层 | https://docs.github.com/en/repositories/archiving-a-github-repository/backing-up-a-repository |

方案仅使用现有电脑/宽带/存储和普通公开Git仓库。不会启用LFS、Packages、Actions、Codespaces、外购对象存储、付费备份或新增额度。现有仓库的公开性已由连接器只读核对；没有读取支付配置，也不需要它来开展本批静态准备。

本批文件门槛：检查全部文件实际身份、无目标碰撞，每文件<25MiB；远端仓库存在不等于本批已保存在远端。项目代码/资料的可公开范围按确切白名单审阅，不能把选择公开可见性理解为任意文件都可上传。

增长处理：基础包只保留一份，后续只列有新依据的增量；对每次发布重算实际文件量，不按7个发行候选乘一个臆造事件数估全年流量。若接近仓库健康建议或出现费用提示，停新增发布并提出保留完整义务的免费替代/窗口方案，不自动删历史或付款。

GitHub单点服务、账号控制和现有本机不能自动构成lifelong保证。还需真实上传后按固定commit重新取回核验，保留独立于GitHub的已知索引身份及现有本地原件；用户统筹维护与故障恢复。当前完整项目免费路线仍UNKNOWN，没有证明必须付费，也未证明所有服务/事件都免费可用。
