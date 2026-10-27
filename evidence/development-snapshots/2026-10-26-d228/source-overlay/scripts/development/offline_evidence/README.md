# 本机离线证据核验

当前阶段已按用户选择交付离线开发版。简短中文入口：[从这里开始](../../../docs/development/offline-development-delivery-2026-10-25-rev-001/START_HERE.md)。完整主线与真实协议就绪仍未完成；下文历史增量按各自原范围保留。

第一版只支持下列保留原件/开发样本，复用已完成消费者；不联网、不安装软件，不需要购买数据或服务。

从项目根目录运行：

```sh
.venv/bin/python -I -B scripts/development/offline_evidence/cli.py demo
```

这会检查五项，输出可读结果：两份失业率PDF、GDP版本与Advance配对、八个日历例子，以及一组**合成开发绑定样本**。最后仍显示真实准入、历史认证时间和Genesis尚未建立。

支持目录、单项检查和机器可读报告：

```sh
.venv/bin/python -I -B scripts/development/offline_evidence/cli.py list
.venv/bin/python -I -B scripts/development/offline_evidence/cli.py verify u3-july-2025
.venv/bin/python -I -B scripts/development/offline_evidence/cli.py demo --json
```

## GDP 发行版变化对比

直接比较已支持的2026年Q1/Q2七条公布值声明：

```sh
.venv/bin/python -I -B scripts/development/offline_evidence/cli.py compare-gdp
.venv/bin/python -I -B scripts/development/offline_evidence/cli.py compare-gdp --json
```

可另用三份已留存的BEA新闻稿PDF交叉核对这七条声明：

```sh
.venv/bin/python -I -B scripts/development/offline_evidence/cli.py compare-gdp --news-pdfs
.venv/bin/python -I -B scripts/development/offline_evidence/cli.py compare-gdp --news-pdfs --json
.venv/bin/python -I -B scripts/development/offline_evidence/cli.py verify gdp-news-pdfs
```

可选核对绑定PDF原件哈希、发行标题/日期、页数、SAAR表头及Real GDP行，逐项匹配版本表七个数值；输出PDF页码和来源哈希。Q2第二次估计的技术说明只支持“下调小于0.1个百分点”，不补造精确未舍入修订量。任一所需文件缺失、损坏或声明不匹配，合并结果不会给出成功对比表；缺少文件不能掩盖另一类输入的硬错误。

这些PDF内的比较列是**该新闻稿对更早版本的声明**，不是更早发行日的原件或历史首次字节证据。JSON分别保留版本表日期与PDF自身发布日期，不把两者合并。默认`demo`仍检查原五项；三份GDP新闻稿PDF仅由上述明确命令核对。

按季度、发布日期列出实际GDP较前期的百分比变化率（按来源表口径），另列“较上次”和“较首次列示”两个差值，单位为**百分点**。每季度首行“较上次”为无前项，较首次列示为0；例如Q1从2变成1.6，是下降0.4个百分点。Q2的Advance与Second虽同为1.5，仍是两个版本，不合并。

这里计算的是**列示公布值之差**，没有恢复舍入前的估计。两个版本均显示1.5、差值为0，也不能据此断言底层估计完全没有修订。JSON的`difference_basis`和`unrounded_revisions`明确保留这一界限；不要把表中差值当作来源公布的精确未舍入修订量。

此命令会重新核对同样三份固定身份文件，不读取旧报告来冒充新核验；支持原有`--inputs`公共目录选项。缺失、损坏或不支持的结果不生成对比表。人类输出列出来源文件SHA256、表名和数值单元格；JSON保留原始七条声明、两次Advance配对和完整单元格引用，并新增`observations.comparison`。退出码和真实准入边界与其他命令相同。

版本表是当前留存的**回溯声明**。两份Advance归档只支持对应的声明配对，不证明当时留存了首次公布原件，也不证明完整修订历史或认证可得时间。“首次列示”仅指本工具列出的第一条，“最后列示”也不表示最终不再修订。此命令不扩大到任意季度、任意XLSX或新下载材料，不作预测或投资建议。

| case | 有限支持范围 |
|---|---|
| `u3-july-2025` | 所保留July2025当次发行PDF；实际抽值4.2 |
| `u3-november-2025` | 所保留November2025当次发行PDF；实际抽值4.6，October缺测保留None |
| `gdp-2026-vintages` | 所保留三份XLSX中的七个发行声明及两次Advance配对；同值不同发行版不合并 |
| `bea-calendar` | 所保留ICS、2025/2026年度HTML中的八个例子；不是全部应有日历 |
| `bindings-demo` | 已封存的无密钥合成IB2/TC2绑定样本；不是实际运行或真实经济数据认证 |
| `gdp-news-pdfs` | 三份留存新闻稿PDF，七条GDP声明与舍入说明；仅明确选择时运行 |
| `cpi-june-2026-copy` | 一份已供CPI用户正文副本，季调月变化与表A对应；不是发布者原字节，仅明确选择或mainline时运行 |
| `cpi-june-2026-archive` | FRASER保存的38页BLS PDF，自动消费第一页的发行及月度/同比声明；不是BLS直接取得原字节，仅明确选择或mainline时运行 |
| `calendar-predecessors-2026` | NYFed两份月历与OMB年度PDF的三项前置资料计划声明；未纳入实际来源合同，仅明确选择或mainline时运行 |

输入文件和代码都按固定身份比较。`list --json`列出23个明确文件的原相对路径、别名、大小与SHA256，其中3个GDP新闻稿PDF、1份CPI正文副本、1份CPI归档PDF和3份前置资料日历不属于默认demo。默认只读取选定项的原路径，不扫描目录、自动寻找文件、下载替代或读取私钥。

若把**已授权公共文件**另存到自己的目录，可按list显示的别名放置，再运行：

```sh
.venv/bin/python -I -B scripts/development/offline_evidence/cli.py demo --inputs /absolute/public-input-directory
```

例如July文件必须命名为`u3-july2025.pdf`；绑定七文件位于`binding/`。这个目录是你提供公共材料的位置，不是独立历史完整性或治理权限证明。不要放秘密材料。用户提供文件的扩展名相同，不代表它受支持；其他发行版、CSV、任意PDF/XLSX目前不支持，不能重新导出或编辑来冒充原件。没有自动复制全项目或任意文件读取接口。

`compare-gdp --news-pdfs --inputs ...`共需要6个明确别名：原GDP版本表和两份Advance XLSX，加`gdp1q26-3rd.pdf`、`gdp2q26-3rd.pdf`、`gdp2q26-2nd.pdf`。不会因新目录缺文件而回退到原路径。

需要已有两套环境：调用本入口的项目`.venv`提供jsonschema4.26.0；PDF调用当前用户既有bundled Python（`.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3`）及pypdf6.10.0。此版本选择的是本机已检查环境，不承诺在其他电脑自动存在。PDF环境不可用时，该类显示UNAVAILABLE，其他类仍检查，不安装或悄悄改解析器。

输出：

- `OBSERVED`：这些有限文件的局部核对已完成，**不是完整通过**。
- `MISSING`：明确输入/依赖缺少；指定新目录时不回退旧文件。
- `REJECTED`：身份不同、输入不安全、消费者拒绝或源码/共享schema改变。
- `UNAVAILABLE`：运行环境/依赖不可用。
- `UNSUPPORTED`：不在有限支持范围（CLI未知case直接显示用法错误）。

退出码0只表示选定的有限检查全部完成；1表示缺少文件/环境；2表示拒绝/不支持。查看JSON的整体结论：始终`UNRESOLVED`、`real_admission=NOT_READY`、真实G02/G03与Genesis `NOT_ESTABLISHED`、`prospective_eligible=false`、`protocol_state_change=NONE`。没有用退出码0代表协议准入。

不证明FIRST、认证available_at、完整历史/mandatory universe、独立authority/适用性、完整build/runtime、生产资格、正式时间证据或Bitcoin。不能把普通hash或来源声明提升为这些事实。原29项完整缺项和11项义务仍保留；原C01/C05/C06/G10保护没有修改。

开发者验证仅运行新入口的行为测试：

```sh
.venv/bin/python -B -m unittest discover -s scripts/development/offline_evidence -p test_cli.py -v
```

本机软件仍属开发工具；不执行真实签名消息、provider/OTS/Core、采纳、接受、冻结、资格计数、Genesis或生产动作。没有自动发布/邮件/后台任务。

## 主线开发框架

用一个命令查看现有主线模块：

```sh
.venv/bin/python -I -B scripts/development/offline_evidence/cli.py mainline
.venv/bin/python -I -B scripts/development/offline_evidence/cli.py mainline --json
```

它实际消费固定 D178 公共开发运行包的十三参输入、D177 留存的 16 个测试方法/50 条事件、已有 GDP 七条声明和八个官方日历样本。另接入 CPI 用户正文副本及已有两份失业率 PDF，覆盖三个目标的有限样例。事件经现有消费者核对，再按固定方法映射对应到五报告实际消费的同一份 R4T 原字节、事前定义、调用/尝试和结果；不二次读取 R4T，也不重跑历史测试。规则权限、资格历史、完整周期、预测资格和 G10 调用现有组件的**缺输入诊断**。十四个模块统一输出，局部成功不能覆盖缺项或拒绝；模块数不是进度百分比。

CPI 可单独运行 `verify cpi-june-2026-copy`。它从固定 2026 年 6 月正文副本解析 CPI-U 季调月变化 -0.4%，对应表 A 的 June 列；未季调同比 3.5% 单列，不混作目标值。检查发行标题/编号/日期声明、列口径、负号及 headline/表格一致性，保留正文行定位和文件摘要。该副本是用户提供的页面文字，不是原 HTML/PDF，也不证明发行日认证可得、首次原件或文档完整性。明确 `--inputs` 时别名为 `cpi-june2026-copy.txt`，缺失不回退；不需要用户重供或编辑原文件。2025 年 7 月失业率 4.2、11 月 4.6 由原 PDF 消费者读取，October 缺测保持 None。选定的不同月份只是有限开发样例，不据此选定真实 mandatory 范围。

时间模块另读 D132 固定公开 2025 Q2 GDP PDF（公共镜像）与650字节 OTS 样例：核对文件身份、31字节格式头、版本、SHA256标签及主体摘要，再完整消费585字节正文并重算40步支持的操作路径。结果包含文件声明的Bitcoin高度912095及路径根。另读D187留存的两公开服务原始响应，核对80字节区块头双SHA256身份与原Merkle字段；这项byte-binding只是已取得字节的一致性；另有D192 standalone PoW按头部声明目标/mainnet上限检查，但未验证高度归属、该高度应有难度、owner-controlled Core链、确认数或civil-time上界。完整OTS与Bitcoin仍为NOT_CHECKED；样例也不对应本项目R4T/final-SA，真实时间模块保持MISSING。损坏或不支持的正文拒绝；缺少证明/PDF时不回退，其他分支继续。适用工作流和独立留存仍缺真实材料。

这是可运行的开发框架，不是完整权威重放：固定五报告中仅一份有有限本机测试支持，其余四份仍为合成；事件对应关系只支持有限本地一致性，执行真值仍未认证。真实规则、独立全集、历史时间和完整 readiness 尚未建立。当前正常展示会退出 **1**，表示真实条件仍缺；输入被拒绝时退出 **2**，不会用退出 0 表示主线成功。

可用 `--inputs` 指定 GDP/日历的既有公共文件别名目录；`--run-inputs` 指定含 `INPUT_SET.json` 和 `inputs/` 的完整 D178 公共开发材料目录；`--execution-inputs` 指定 D177 事件目录；`--proof-inputs` 指定 D132 公开 PDF/OTS 样例目录；`--header-inputs` 指定D187公开区块头响应目录。各目录分别作用，缺失时不回退默认来源。不支持任意运行包、真实签名材料或扫描目录。运行清单先与固定身份比较，再按其中确切路径读取；事件/证明也只读代码列明的固定公共文件，原件缺失、身份变化和符号链接都会保留诊断。

只验证此框架新增行为：

```sh
.venv/bin/python -B -m unittest discover -s scripts/development/offline_evidence -p test_mainline.py -v
.venv/bin/python -B -m unittest discover -s scripts/development/offline_evidence -p test_target_inputs.py -v
```

mainline 的 execution-trace 还消费 D177 attempt2 的八份固定来源记录，实际核对22份留存加载仓库源码、七份已保留 wheel、60份包内Python成员，以及当前已导入的21份产品模块对应源码文件。它把同一 R4T/事前定义的 package/lock/runtime/source 引用与这些材料相连，并用同一快照核对运行命令和stdout/stderr原bytes。--execution-inputs 下缺少这些控制文件时不回退默认目录；缺项与替换同时保留，其他分支继续。

这是有限来源及发行物对应检查：当前导入模块的源文件相同，不证明实际内存或缓存字节码、完整解释器/stdlib/native/system/build闭包，也不认证历史执行或时间。仅支持明确仓库源码布局；其他安装布局报告不支持，不猜路径、不读取旧临时环境。

mainline 的有限产品消费另有源码快照载入保护：固定 D176 wheel 对应的21个产品Python源版本，先读完并检查原bytes，再直接compile；所选模块的导入不读取pyc，exec audit核对相同顶层code，拒绝事先已缓存于sys.modules的产品和未声明的产品代码。源码缺失与替换全部留诊断，在执行前拒绝；此时不导入未经核对的权威诊断分支，其他公共数据独立worker继续。hook在有限消费结束或失败时恢复。

selected_code_loading只是本次21个选定Python模块顶层执行代码对应观察，保留逐源码code摘要；不证明全部函数执行、第三方/原生/解释器/系统/build闭包、历史D177运行真实或实际独立适用。D183的current_loaded_bytecode_identity未建立字段继续表示一般性载入身份，新增的选定top-level观察单列，不扩大为全代码认证。

OTS正文消费者只是有限、纯本地的格式/哈希路径读取，不是完整OTS客户端或Strong verifier。支持SHA256文件摘要及SHA256/append/prepend/reverse/hexlify；Bitcoin attestation只读高度/路径根，pending URI和未知attestation只保留声明，绝不请求URL。只接受最短varuint，拒绝重复分支；比上游某些宽容解码更窄，不把未支持编码称为全局OTS无效。上限：proof1MiB、路径深度128、nodes4096、操作message/result4096byte、attestation8192byte、URI1000byte、留存attestation报告约1MiB。全部分支及EOF检查，任何失败不保留部分成功。legacy unverified_body_bytes仍为585，表示未完成完整证明/链验证，不再表示未读；body_computation.body_bytes_consumed明确表示已读范围。独立参考在ML-D186 PUBLIC_SOURCES.json，未导入或执行上游客户端，没有安装、stamp/upgrade/cache/calendar/RPC/Core或真实协议事件。

D187 header_binding单列公开字节绑定：固定四响应，两服务对应同height912095。每个hash/header都实际解码，80byte header身份双SHA256反序显示，路径digest直接比较wire Merkle字段，全部Bitcoin路径/全部header消费；错误与缺项共存时REJECTED优先。缺材料仍保留正文计算，拒绝header会标出REJECTED并正常exit2，其他经济数据分支继续。正常局部绑定OBSERVED仍exit1/真实time MISSING/NOT_READY。两个服务相同不证明独立资格、链选择或确认数；自洽伪造header也可能通过此byte-only检查，其legacy proof_of_work仍NOT_CHECKED；D192另给standalone_pow结果，链/full OTS仍NOT_CHECKED，不提供认证civil-time或项目subject绑定。执行只读留存文件，无任何网络/节点/RPC/协议动作；原公开响应来源见D187 ACQUISITION.json。

D189在原initial-authority模块加technical_signing_profile_candidate：实际消费D185固定candidate raw/full、typed schema及普通seal；纯函数另可比较所供policy3的两个profile/carrier refs。默认不供应或选择真实rule，profile内容OBSERVED、规则绑定MISSING，原public auth UNKNOWN/BLOCKED_BY_G02保持；即使开发规则两用途匹配仍UNRESOLVED/0 operational binding/NOT_READY，独立选择/权限/生效、verifier合同、其余用途及G10未建立。不构造任何签署消息或载体。旧用户CPI正文仍是正文：本轮官方PDF下载TLS失败且浏览器策略拒绝，未获取publisher原件，也未绕过。

`--profile-inputs`只指定D185技术候选目录，仍不给真实rule，也不建立权限route。缺失不回退；候选被拒绝则initial-authority父模块REJECTED/exit2，并保留原native auth UNKNOWN/BLOCKED_BY_G02，其他数据分支继续。

D191提供独立synthetic_ma3_codec.py纯API encode_synthetic_case(case_bytes,profile_bytes)，仅固定D191合成project/actor、非公钥标签digest和一组exact synthetic refs可进入编码。保留候选A的C8/U10/排除4、严格集合/版本/决定规则，复用D185/D189 canonical+profile，输出合成envelope/frame，不生成key/signature/carrier，不可供真实project输入或通过caller标志关闭合成门。默认mainline不导入/调用此编码器、不构造消息；没有真实MA3 verifier或签署入口。开发验证：`.venv/bin/python -I -B -m unittest discover -s scripts/development/offline_evidence -p test_synthetic_ma3_codec.py`。通过不建立public auth、实际profile选择/生效、完整runtime或G10；状态仍NOT_READY。

D192增加standalone_pow独立子结果：复用既有全部header响应，严格解码80byte头部、little-endian nBits及compact target，拒绝负/零/overflow/高于Bitcoin mainnet powLimit，比较双SHA256数值与该声明目标。header_binding原byte-only语义保持，新增子检查的known失败仍向主线example/time REJECTED传播，缺材料不回退，其他分支继续。正常两个原响应都OBSERVED，真实time MISSING/NOT_READY/exit1。并未核验该height必须采用的target、难度调整、累计chainwork、有效链选择/确认/Core/真实project subject或认证civil-time；该结果不是Strong、Bitcoin整体或完整OTS验证。没有挖矿/nonce搜索/节点/Core/RPC/交易/协议动作，只对留存原字节作本地计算。官方v30 compact/PoW/mainnet参数原文留存作参考，不执行。一个故障传播测试使用明确的第二次调用失败seam，不能当实际公共header PoW失败或密码学漏洞证据。


### D196：既有轻量公开观察的离线重放

`mainline`在原time子结果中读取D195固定请求记录与626byte原响应；可以用`--chain-inputs /absolute/path`指定搬迁后的同一输入集合，缺失或替换不回退默认材料。运行不联网、不启动Core、不下载区块链。没有增加顶层主线模块或真实权威入口。

公开metadata与同一已准入header核对；保留所有请求，包括Mempool四次抓取失败。原件缺失、identity拒绝和semantic矛盾分别保存，拒绝上行到time与exit2，独立经济数据仍继续。服务报告不在主链是有效负观察，不制造确认深度；服务报告在主链时也只做height算术，tip两查询不是原子快照。来源独立性、独立全链、认证时间、project subject与Strong合同均未建立，默认仍NOT_READY/exit1。

该集合只是固定开发样例与历史抓取观察，不是实时服务查询、完整mandatory universe或独立链证明；不能替代原C01/C05/C06/G10和真实协议义务。用户取消的大Core同步路线不恢复。


### D197：搬迁时限定产品源码命名空间

已准入21个产品source snapshot的上下文现在同时限定该namespace的查找，使不同root的同一源码不会被ambient安装路径抢选后拒绝。不把root/src加到sys.path；其他第三方模块仍由既有环境提供，完整runtime未建立。预载入/未登记/不同code/pyc保护保持，正常或异常退出移除本次finder并恢复原loader。

D197 finite-public-samples.zip仅带有限D178组合及公开证明样例、所需源码，原件和路径保持。它不含完整14模块/经济数据、历史event/provenance/wheel闭包或Python环境；使用已有兼容运行环境，默认exit1/NOT_READY。包内README/MANIFEST声明确切范围，外部记录archive SHA256仅为开发传输身份，不形成TrustedManifest或软件权威。用户取消的Core/完整链下载仍不恢复。

### D200：D199本地Core公开样例的留存结果接入

D199在用户另行授权的30GiB裁剪方案下已经完成，并正常停机；上文D196/D197的“未恢复Core”描述保留其历史范围。当前`mainline`会读取该次成功运行的五份固定公开文件：107段RESULT、原始PUBLIC_EVENTS、verification、控制器源码快照及配置快照。配置/源码只核字节，不执行。新增`--core-inputs /absolute/path`仅指定这些文件的目录，缺失或替换不回退默认，不启动节点、不联网或重下链。D199全部32项交付仍是历史原件，本模块只消费上述五件与同次已读取的PDF/OTS/header，共八个明确输入，不声称重放整个监督历史、全部runtime或全链。

时间模块的`public_example.retained_core_sample`单列本地节点历史观察：main/blocks972999/IBDfalse、固定height912095、hash、80byte头及verbose字段、60905个该时点确认。原事件逐份检查所有chain/network/peer结果、留存资源、唯一终止与最后观察绑定；verification的已知否定/缺项不能被成功标志盖住。复用既有OTS消费者核PDF→证明→同一header Merkle关联。首个成功后追加失败、遗漏末次观察、缺consumer、资源超界、JSON重复键/非有限数均不能得到局部OBSERVED。

该结果是留存解析后RPC观察的一致性核对，不是当前实时RPC、认证历史执行或原始传输字节验证；控制器exit0来自固定本地留存记录，离线消费不会重新观察过去进程。Publisher PGP仍未独立核验，host/header时间不作认证civil-time，紧凑材料不能独立重放Bitcoin全链。原passive消费者的NOT_CHECKED/NOT_ESTABLISHED标志保持；公开GDP不是本项目R4T/final-SA，项目Strong、三provider、资格历史、独立规则/完整范围和适用工作流仍缺证。真实time模块保持MISSING，默认主线仍exit1/UNRESOLVED/NOT_READY；坏D199输入上行REJECTED/exit2，同时保留其他经济数据和缺项。

定向验证：`.venv/bin/python -I -B -m unittest discover -s scripts/development/offline_evidence -p test_core_sample.py -v`。D197旧搬迁包未更新，不能据此声称该旧包已带D200能力。

D202进一步把留存RESULT的argv、memory_policy和read_retry_policy绑定到D199固定历史profile：程序/conf/datadir/network及完整参数列表、保护阈值、HTTP单次重试条件与限额均须精确且类型相同，True不能当1、5.0不能当5。声明矛盾与缺证明同时保留。历史路径仅作字符串比较，不读取该主机目录或执行程序；此检查不认证过去实际载入配置或代码。固定CLI pin仍先拒绝被修改的文件，新增语义检查针对纯API的内部一致性缺口，未证明默认CLI绕过。


### D203：CPI归档PDF与原正文的有限声明对应

`verify cpi-june-2026-archive`消费FRASER独立托管的固定502033字节归档PDF（SHA256 `dd9288175bd38ef9c05b1e5d5ce03ea6c6032a1c2900355208905f78f94aea81`），复用已有bundled Python及pypdf 6.10.0，不安装包、不联网。检查38页/未加密结构，解析第1页USDL-26-1191、July 14发行声明和June口径，分开输出季调月变化−0.4%及未季调同比3.5%。Table A在第2页为栅格图片，已人工视觉核对，但自动消费者不解析或核验其数值；输出明确保留NOT_CHECKED_RASTER_TABLE。

现有inflation-data模块保留原用户正文result，再实际消费archive_carrier并给carrier_comparison。八个共享发行/测量声明必须相同，缺项不借另一载体补齐，拒绝与缺项同时保留且拒绝优先。仍为14个顶层模块；这不是两独立统计来源，不证明完整表格/发行历史、历史首次原件或认证可得时间。旧正文源类别保持，不因新PDF升级。明确--inputs时新别名为`cpi-june2026-fraser.pdf`，缺失、替换或symlink不回退默认路径。

归档地址及取得过程见D203的ACQUISITION_ARCHIVE_FILE.json。此前BLS源站浏览授权拒绝仍有效；本包未向该源站发请求，未使用代理或绕过访问控制。FRASER的/docs两次超时保留，独立/files/docs存储成功。运行核验完全离线，不访问PDF内链接；真实主线继续UNRESOLVED/NOT_READY。

### D208：三项前置资料的日历声明

```sh
.venv/bin/python -I -B scripts/development/offline_evidence/cli.py verify calendar-predecessors-2026
.venv/bin/python -I -B scripts/development/offline_evidence/cli.py verify calendar-predecessors-2026 --json
```

复用D207留存的NYFed October/December 2026月历HTML与OMB 2026年度日历PDF，共495920字节。逐份核身份后，绑定同一日单元格的指标链接及其紧邻时刻，并核对OMB对应月份列和参考期声明：GDP 2026Q3 Advance计划于2026-10-29、U3与CPI 2026-11分别计划于2026-12-04及2026-12-10公布，三项时刻均声明08:30 Eastern Time。NYFed声明日程暂定、可能立即变化；参考期来自OMB季度标签或“previous month”注释，未冒称NYFed直接列出参考期。

`mainline`在原official-calendar模块内分别运行既有BEA八例和新predecessor_research；任一拒绝或缺项均保留，另一份通过不能遮盖失败。顶层仍14模块、默认demo仍5项。显式`--inputs`所需新别名为`nyfed-oct2026.html`、`nyfed-dec2026.html`、`omb-2026-pfei.pdf`，缺失、替换或symlink不回退默认原件。新解析器源码也按固定身份核对，复用既有bundled PDF环境，不联网或安装。

这三项仅是官方汇编中的有限计划声明，不能证明来源独立性、实际发布、公布值、认证可得时间或完整mandatory universe。NYFed/OMB未被当前BLS/BEA限定的实际来源合同准入；未修改合同或选择实际范围。2027Q1六条CPI/U3时刻仍未供应，也未计算UTC、信息截止或执行期限。D204搬迁ZIP保留其历史快照，未带本次增量；当前工作区支持本命令。主线仍UNRESOLVED/NOT_READY，协议状态不变。

新消费者定向测试需已有pypdf环境：`/Users/sage/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -I -B -m unittest discover -s scripts/development/offline_evidence -p test_predecessor_calendar.py -v`。

### D211：第三个signing用途的隔离合同消费

`verifier_contract.py`新增纯API：

```python
consume(contract_bytes, profile_bytes, rule_bytes=None, artifact_bytes=None)
```

它消费D211固定技术候选及八份明确公共材料的bytes：adapter、run_binding、build_observations、source_manifest、configuration、pre_run、dependency_audit、native_binary。确切路径、大小和SHA256在`docs/development/verifier-contract-consumption-2026-10-25-rev-001/ARTIFACT_INPUTS.json`；合同和schema也在该目录。只读取原生库字节核身份，不加载或执行。函数内部不读文件，也不接收key、message、signature、carrier、backend或验签结果。

复用D189实际profile/rule消费，保留原两个用途；可选供应的开发policy3还须使verifier_contract_ref与本合同exact ref相同。合同结构、普通seal、raw/full身份、semantic ID及所有八份身份都核对。没有rule时整体MISSING；全供给的合成规则局部匹配可为OBSERVED，verdict始终UNRESOLVED、实际绑定0、NOT_READY/NONE。缺项不回退，已知失败不被兄弟缺项或成功掩盖。

该候选描述现有CryptoResult状态和接口，不实现结果归一化或验证真实签名。八份身份不等于完整backend gate、全部源码依赖或runtime；旧C入口未声明消息大小上限，message_resource_policy与execution_contract_complete继续NOT_ESTABLISHED。不会借Go的1MiB或合成样本限制补齐，不截断或改验摘要。公共认证入口保持UNKNOWN，mainline/CLI/catalog及D204历史ZIP没有接入本增量。

定向检查使用现有项目环境：

```sh
.venv/bin/python -I -B -m unittest discover -s scripts/development/offline_evidence -p test_verifier_contract.py -v
```

### D214：验签合同消费接入现有主线诊断

`mainline`现在在初始规则与权限模块内实际调用D211消费者，并列保留原D189 profile结果和新增`technical_verifier_contract_candidate`。两者共用一次读取的同一份profile原字节，默认不供应任何真实或合成rule。正常显示合同内容/八材料身份局部OBSERVED、规则绑定MISSING，原public-auth仍UNKNOWN/BLOCKED_BY_G02；主线仍exit1/NOT_READY。顶层14模块、目录9case/23输入与默认5demo保持。

可把同一份已授权公共合同及八材料按下列别名搬到独立目录：

```sh
.venv/bin/python -I -B scripts/development/offline_evidence/cli.py mainline --verifier-inputs /absolute/public-verifier-directory
```

| 角色 | 明确别名 |
|---|---|
| 合同候选 | `CONTRACT_CANDIDATE.json` |
| adapter | `public_verifier.py` |
| run_binding | `run_binding.py` |
| build_observations | `BUILD_OBSERVATIONS.json` |
| source_manifest | `SOURCE_MANIFEST.json` |
| configuration | `config.h` |
| pre_run | `PRE_RUN.json` |
| dependency_audit | `evidence/DEPENDENCY_AUDIT.json` |
| native_binary | `native/fp_public_verify.dylib` |

原`--profile-inputs`仍只控制D185 profile目录，两个目录分别作用。明确目录缺失、替换或symlink不回退默认原件；只读这些固定别名，不扫描目录或读取其他rule/key文件。代码/schema/catalog仍为固定仓库依赖。新source载入失败时仍独立核对旧profile；任何已知拒绝上行到initial-authority和exit2，并保留兄弟缺项，经济数据等其他模块继续。

输入文件准入与纯内容消费分别记录：`read_admission`及`input_findings`保存实际拒绝/缺项；身份被拒绝的bytes不交解析器，内容显示NOT_CHECKED而非伪称通过或仅缺失。消费者源码先核身份后直接compile，不用pyc替换。这里不会加载或执行材料中的adapter/dylib，不运行D212 gate、验签或构造消息/载体，也不认证历史执行、完整runtime、资源规则或实际权限。D211纯API及旧技术候选未改，D204历史ZIP没有本次增量。

固定导入依赖也先通过同一被动读取准入：D189源、canonical源、rule/profile schema，以及新contract schema/catalog。导入只使用已核对的不可变字节快照；拒绝或缺依赖时跳过对应消费者，已拒绝路径不会再被导入代码打开。D189仅在自身四依赖有效时独立核对。快照读取只在隔离worker的单线程导入范围内生效并恢复，不是通用并发加载库或完整宿主防护。

定向验证：`.venv/bin/python -I -B -m unittest discover -s scripts/development/offline_evidence -p test_mainline_verifier.py -v`。


### D218：用户选定2027Q1的只读评估

用户已选择按公布日期2027-01-01至03-31，GDP Advance/CPI/U3及既有last-observed-value方法，作为只读评估对象。`verify q1-2027-read-only-assessment`复用D206留存OMB2027 PDF/BEA2027 HTML/规划清单及本次选择记录；不联网、不新建forecast/cycle/slot或采纳规则。mainline在原official-calendar内实际消费该子结果，旧BEA/前置资料研究仍分别保留，14模块不增；catalog10cases/27inputs，默认demo5不变。

输出9条日历声明：7个目标发行候选及2个GDP修订参考；7条紧前首次发行依赖中4条在窗内、3条为窗外资料需求。GDP三行时钟仅取BEA本行，六条CPI/U3时刻保持null；未取得时区/实际值/认证availability，不计算UTC截止。三来源/控制一致不证明独立必需全集；只读选择不等于实际governing scope，不豁免季度外持续义务。

显式`--inputs`所需新别名为omb-2027-pfei.pdf、bea-2027-next-year.html、q1-2027-planning-inventory.json、q1-2027-read-only-scope.json；缺失、替换或symlink不回退默认。使用既有bundledPython/pypdf6.10.0。来源合同准入、真实规则/权限/C06/G10仍未建立，NOT_READY/NONE；D215历史ZIP不含D217/D218增量且不重建。

### D219：同次运行的窗外前置日历对应

`mainline` 在原 official-calendar 内将已消费的 D218 三项窗外参考期与 D208 计划声明对应，不再读取或解析原件。`predecessor_calendar_binding` 保留每条需要方、计划日期/时刻/时区、原单元格位置及来源身份；核对固定三项、七条依赖及阶段，缺项/拒绝/环境失败分别保留，已知失败不被兄弟缺项遮蔽。该函数只供现有汇总组合使用，不能独立认证任意调用者提供的观察结果。

GDP 2026-Q3、U3/CPI 2026-11 得到的仍是暂定计划声明，不是首次发行值或认证可得证据。六条2027年CPI/U3时刻、独立必需全集、来源合同准入和真实就绪状态均未补齐；原子结果、catalog10/27、默认demo5、14模块及D215历史ZIP保持。定向检查：`test_predecessor_binding.py`。

### D220：同次声明输入身份检查

`mainline` 的 initial-authority 新增独立 `technical_verifier_identity_gate`，准入D212声明的64个公共快照，实际复用固定adapter中的hash/PRE_RUN检查逻辑，核对其63个声明gate输入。默认复用D214同路径同身份的八份快照；已拒绝路径也不会重读。原D211纯API、两个技术候选结果和signing_candidates默认两返回值保持；直接调用该旧函数而不提供gate_output不会执行本检查。

可选 `--verifier-gate-inputs DIR` 只控制64条固定相对路径的镜像根目录，确切布局见 `docs/development/mainline-verifier-gate-integration-2026-10-25-rev-001/GATE_INPUTS.json`。它和原 `--verifier-inputs` 的九别名目录分别作用，缺失、替换、符号链接无默认回退；任何硬拒绝上行到模块及exit2，同时保留兄弟缺项和经济数据结果。

这里只编译已核adapter源码的检查定义，以已准入字节替代文件读取，未导入ctypes、载入native、执行验签/语料或认证完整环境。它是固定声明集身份消费，不是原始文件系统gate环境或独立软件/runtime全集证明；旧八锚点消费者的full/runtime字段保持未立。实际权限、消息资源策略、G10和真实就绪仍未建立，NOT_READY/NONE；14模块和历史ZIP不变。定向检查：`test_verifier_gate.py`。

### D222：缺依赖时保留环境不可用

主线产品导入缺少模块或发行包时输出 `UNAVAILABLE / MISSING_DEPENDENCY`，而非将未执行的检查记成材料拒绝。独立时间材料检查和公共经济数据仍继续，已知源码准入拒绝或坏材料仍上行 `REJECTED`；兼容环境下的结果不变，不安装依赖或认证完整runtime。D221历史ZIP保持原样，缺jsonschema时的旧错误分类及单文件修正说明见 `docs/development/mainline-runtime-availability-2026-10-26-rev-001/`。


### Exact archival U3 A-1 support (2026-10-26)

`verify u3-july-2025-a1 --json` and `verify u3-november-2025-a1 --json` consume the same two retained PDF editions via the admitted existing summary observer and new exact Table A-1 TOTAL/SA parser. Nine column identities distinguish three NSA from six SA columns; the last SA total rate is selected. November October absence stays absent. Mainline adds `target_table_support` plus a same-edition/selector/value comparison to each existing unemployment module. Legacy observations remain unchanged; failed/missing exact support is retained and affects the module verdict.

The catalog now has12 finite cases/29 input references (some aliases/raw identities shared), demo remains5, mainline remains14 modules. No new PDF/network, installed package, actual source admission, historical FIRST, authenticated availability, governing applicability, real report or readiness is established. Existing D221 ZIP/D222 single-worker overlay do not contain this increment; keep them frozen and use their exact documented scope. This is public archival declaration support only, not a full Table A-1 product parser or arbitrary PDF certification.


### Exact archival CPI Table 1 support (2026-10-26)

`verify cpi-june-2026-table1 --json` consumes the retained FRASER PDF page9 Table1 All items row, selecting the ninth numeric column: seasonally adjusted May-to-June2026 monthly change -0.4%. The unadjusted monthly -0.3% and yearly3.5% remain distinct. It reuses the existing admitted headline observer on the same immutable bytes and binds the new row to the already-consumed carrier declarations. Mainline inflation-data adds only `target_table_support`; original copy/headline/comparison results remain intact. Rejection or missing exact support affects the module verdict. Table A remains an unverified raster table.

Catalog13 cases/30 input references, demo5 and14 mainline modules. This is one archived table row, not original-publisher bytes, historical FIRST, authenticated availability, actual source admission, complete table/document/runtime/universe or real readiness. No new download, installation, fee, protocol or Git action. Use D228's six-file verified overlay against frozen D221 ZIP; it includes unchanged D227 A1 and D222 runtime fixes.
