# D228入口

先读REPORT.md和VERIFICATION.json（最终保存时生成），然后按需查PLAN.md、PROGRESS.md、REVIEW.md。ACTUAL_RESULTS.json是五次实际进程退出码/身份；MAINLINE_A/B和MIXED_BAD_AND_MISSING是原始输出；RELOCATED_A/B及DIFFERENCES文件保留两个新目录重放边界。

SCOPED_DIFF.patch、SOURCE_IDENTITIES.json及before-source仅覆盖本包修改，PUBLIC_INPUT.json与CANDIDATE_SELECTOR_IDENTITY.json固定公共输入/历史selector。overlay和OVERLAY.json仅适用于指定冻结D221 ZIP的新核验解包；replay_exact.py不会覆盖现有未知checkout，不发起网络/协议动作。

整条真实主线未完成NOT_READY/NONE。本包不授权Git写入或新目标。
