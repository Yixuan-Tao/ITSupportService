from pathlib import Path
import zipfile, textwrap, json, os

base = Path("e:/agent/source/it_support_data")
base.mkdir(exist_ok=True)

files = {}

files["README.md"] = """
# 企业内部 IT 支持 AI Agent 背景信息文件包

这是一套为“企业内部 IT 支持 AI Agent”准备的模拟知识库与规则文件，可直接作为：
- RAG 知识库初始语料
- Agent 系统提示词的业务背景
- Jira 工单分类/优先级/升级规则输入
- Demo 演示数据

## 文件结构

### 01_knowledge_base
面向员工的制度、流程、排障、FAQ 文档。

### 02_policy_and_rules
面向 Agent 的业务规则、工单分类、优先级、升级策略。

### 03_seed_data
示例部门、常见软件、设备类型、测试问句。

## 使用建议
1. 先将 `01_knowledge_base` 中的 md 文件导入向量库。
2. 将 `02_policy_and_rules` 中的规则文件作为 system prompt 或 tool routing 参考。
3. 将 `03_seed_data` 中的数据用于测试、评估和 demo。
4. 后续可替换为你自己的真实/半真实企业文档。

## 注意
本文件包为项目演示用虚构企业资料，适合简历项目、课程项目与本地 demo，不适合直接用于真实企业生产环境。
"""

kb = base / "01_knowledge_base"
rules = base / "02_policy_and_rules"
seed = base / "03_seed_data"
for d in [kb, rules, seed]:
    d.mkdir(exist_ok=True)

docs = {
"01_knowledge_base/KB_001_公司IT支持总览.md": """
# 公司 IT 支持服务总览

## 服务范围
IT 支持团队负责以下事项：
- 账号与权限问题
- VPN 与远程办公接入
- 邮箱与单点登录（SSO）
- 办公电脑与外设故障
- 打印机与会议室设备基础问题
- 常用办公软件安装与授权申请
- 网络连接与 Wi-Fi 访问问题

## 服务时间
- 工作日：09:00 - 18:00
- 紧急故障支持：工作日 18:00 前提交高优先级工单
- 非工作时间：仅处理 P1 级别故障

## 联系方式
- AI Agent：公司内部支持门户
- Jira 服务台：IT 项目 `IT`
- 紧急联系电话：400-800-1234（仅 P1）

## 不在支持范围内
- 个人设备的非工作用途故障
- 非授权软件安装
- 非公司批准的外部账号申请
- 与工作无关的网络问题
""",
"01_knowledge_base/KB_002_VPN连接与远程办公指南.md": """
# VPN 连接与远程办公指南

## 适用场景
适用于员工在公司外部访问内网服务，如代码仓库、内部 Wiki、财务系统、HR 门户等。

## 连接前检查
1. 确认账号未被锁定
2. 确认已完成 MFA 绑定
3. 确认本地网络可正常访问互联网
4. 确认已安装公司标准 VPN 客户端
5. 确认当前时间与系统时间正确

## 标准连接步骤
1. 打开公司 VPN 客户端
2. 输入公司邮箱账号
3. 选择 `Corporate-Remote`
4. 输入密码
5. 完成 MFA 验证
6. 连接成功后访问内部系统进行确认

## 常见报错与处理
### 报错：Authentication Failed
可能原因：
- 密码错误
- 账号锁定
- MFA 未通过
处理方式：
- 先确认密码是否正确
- 尝试在 SSO 门户登录验证账号状态
- 如连续失败 5 次，等待 15 分钟后重试
- 如仍失败，提交“账号/权限”类工单

### 报错：Gateway Timeout
可能原因：
- 本地网络不稳定
- VPN 网关异常
处理方式：
- 切换网络（如手机热点）
- 关闭并重开客户端
- 5 分钟后重试
- 若多人同时异常，可能为平台侧故障，提交“网络/VPN”工单

### 报错：MFA Verification Failed
处理方式：
- 确认手机时间正确
- 确认 MFA App 未切换账号
- 尝试重新发起验证
- 若设备遗失，提交“MFA 重置”请求

## 提交工单时需要提供的信息
- 设备类型（笔记本/台式机）
- 操作系统版本
- VPN 客户端版本
- 报错截图
- 问题发生时间
- 当前所在网络环境（家庭宽带/公共 Wi-Fi/手机热点）
""",
"01_knowledge_base/KB_003_账号密码与MFA管理.md": """
# 账号、密码与 MFA 管理

## 密码策略
- 长度至少 12 位
- 必须包含大小写字母、数字和特殊字符中的至少三类
- 不得与最近 5 次密码重复
- 建议每 180 天更新一次

## 密码重置
### 自助重置适用条件
- 账号未锁定
- 已绑定 MFA
- 能访问注册邮箱或手机

### 自助重置步骤
1. 进入 SSO 门户
2. 点击“忘记密码”
3. 输入邮箱账号
4. 通过 MFA 或邮箱验证码验证身份
5. 设置新密码

## 账号锁定
连续 5 次密码错误将触发锁定，默认锁定 15 分钟。

## MFA 绑定
新员工须在入职首日完成 MFA 绑定：
- 推荐使用 Microsoft Authenticator 或 Google Authenticator
- 绑定后请保存恢复码
- 更换手机前请先解绑旧设备

## MFA 丢失处理
如手机遗失或无法访问 MFA：
- 提交“MFA 重置”工单
- 提供员工编号与部门信息
- IT 人员将在身份核验后处理
""",
"01_knowledge_base/KB_004_邮箱与SSO常见问题.md": """
# 邮箱与 SSO 常见问题

## 邮箱无法登录
检查顺序：
1. 确认密码是否过期
2. 确认 MFA 是否正常
3. 确认邮箱地址是否输入完整
4. 确认浏览器是否缓存异常，可尝试无痕模式

## SSO 登录后跳转失败
常见原因：
- 浏览器 Cookie 被禁用
- 旧登录缓存冲突
- 账号权限未同步
处理方式：
- 清理浏览器缓存与 Cookie
- 使用 Chrome 最新版本
- 如首次开通系统，等待 10 分钟后重试
- 仍失败则提交“账号/权限”工单

## 邮箱附件无法发送
可能原因：
- 超过大小限制（25MB）
- 包含敏感文件类型
- 网络中断
建议：
- 大文件改用企业网盘链接
- 检查文件命名
- 如内部邮件频繁失败，附截图提交工单
""",
"01_knowledge_base/KB_005_软件安装与授权申请流程.md": """
# 软件安装与授权申请流程

## 默认可自助安装的软件
- Chrome
- Zoom
- 企业微信
- Office 套件
- VS Code
- 7-Zip

## 需要审批的软件
- Adobe 系列
- JetBrains 商业授权
- 数据库客户端
- 设计类软件
- 抓包/调试工具
- 远程控制工具

## 标准申请流程
1. 在支持门户选择“软件安装/授权申请”
2. 填写软件名称、版本、用途、紧急程度
3. 如为收费软件，需填写成本中心
4. 审批通过后由 IT 安装或下发授权

## 安装失败排查
- 是否具备本地管理员权限
- 是否被杀毒或安全策略阻止
- 是否与现有版本冲突
- 是否系统版本不兼容

## 工单需提供的信息
- 软件名称
- 版本号
- 设备资产编号
- 操作系统版本
- 错误截图
""",
"01_knowledge_base/KB_006_电脑与外设故障排查.md": """
# 电脑与外设故障排查

## 电脑无法开机
1. 检查电源适配器与插座
2. 长按电源键 10 秒后重试
3. 拔掉外接设备后重启
4. 若仍无反应，提交“硬件故障”工单

## 蓝屏或频繁死机
建议提供：
- 错误代码
- 最近安装的软件
- 发生频率
- 是否连接外设
- 是否系统更新后出现

## 键盘、鼠标异常
- 更换 USB 接口
- 蓝牙设备重新配对
- 确认电量充足
- 在其他设备上交叉测试

## 显示器无信号
- 检查电源与视频线
- 切换输入源
- 重插 HDMI/DP 线
- 笔记本请尝试 Win + P 切换显示模式
""",
"01_knowledge_base/KB_007_打印机与会议室设备支持.md": """
# 打印机与会议室设备支持

## 打印机无法打印
排查步骤：
1. 确认打印机在线
2. 检查纸张和墨粉状态
3. 确认选择了正确打印机
4. 清空打印队列后重试
5. 重启打印机

## 会议室投屏失败
- 确认线缆连接正常
- 确认选择正确输入源
- 重启投屏盒子
- 尝试无线投屏或备用线缆

## 视频会议无声音
- 确认系统输出设备
- 确认会议软件麦克风/扬声器设置
- 重启会议室主机
- 更换 USB 音频设备
""",
"01_knowledge_base/KB_008_WiFi与办公网络问题.md": """
# Wi-Fi 与办公网络问题

## 无法连接公司 Wi-Fi
1. 确认选择正确 SSID：`Corp-WiFi`
2. 使用公司邮箱账号登录
3. 确认设备已通过安全策略检查
4. 忘记该网络后重新连接

## 网络速度慢
建议先确认：
- 是否仅个别网站慢
- 是否仅当前工位异常
- 是否多人同时异常
- 是否使用了 VPN

## 有线网络不可用
- 检查网线与接口灯状态
- 更换工位网口测试
- 确认是否使用了扩展坞
- 仍异常则提交“网络问题”工单
""",
"01_knowledge_base/KB_009_入职设备与账号开通流程.md": """
# 入职设备与账号开通流程

## 标准开通项
- 邮箱账号
- SSO 账号
- VPN 访问
- 基础办公软件
- 企业 IM
- 共享盘基础权限

## 开通时点
- 正式入职前 1 个工作日完成基础准备
- 高权限系统须由直属经理单独审批

## 新员工首日检查项
1. 首次登录邮箱
2. 修改初始密码
3. 绑定 MFA
4. 测试 VPN
5. 测试 IM 与共享盘
""",
"01_knowledge_base/KB_010_离职回收与权限关闭流程.md": """
# 离职回收与权限关闭流程

## 离职处理范围
- 回收笔记本、显示器、门禁卡
- 关闭邮箱与 SSO
- 吊销 VPN 与系统权限
- 转移共享文件归属

## 标准流程
1. HR 提交离职单
2. IT 在最后工作日 18:00 前关闭账号
3. 设备由行政/IT 验收
4. 数据交接由直属经理确认

## 紧急离职
如为即时离职，IT 可在收到授权通知后立即冻结账号。
""",
"01_knowledge_base/KB_011_工单提交规范与示例.md": """
# 工单提交规范与示例

## 好工单应包含的信息
- 问题现象
- 出现时间
- 影响范围
- 设备与系统信息
- 报错信息
- 是否紧急
- 截图或录屏

## 示例：高质量工单
标题：Windows 11 笔记本 VPN 登录提示 Authentication Failed  
描述：2026-03-20 09:10 开始出现问题。公司笔记本，Windows 11，VPN 客户端 5.2.1。密码确认无误，MFA 正常。已重启客户端与电脑，仍失败。附报错截图。影响今日远程办公。

## 示例：低质量工单
标题：电脑坏了  
描述：连不上，快帮我看看
""",
"01_knowledge_base/KB_012_内部知识文档使用说明.md": """
# 内部知识文档使用说明

## 文档优先级
当多个文档内容冲突时，按以下优先级使用：
1. 最新发布的正式制度/SOP
2. 由 IT 团队维护的标准知识库
3. 常见问题 FAQ
4. 历史工单经验总结

## 文档使用原则
- Agent 回答时优先引用正式制度与 SOP
- 无明确文档支持时，不应编造解决方案
- 涉及安全、权限、财务系统时必须谨慎处理
"""
}

rule_docs = {
"02_policy_and_rules/RULE_001_工单分类规则.md": """
# 工单分类规则

## 一级分类
- 网络/VPN
- 账号/权限
- 邮箱/SSO
- 软件安装/授权
- 硬件故障
- 打印/会议室设备
- 入职/离职支持
- 其他

## 分类示例
- “VPN 连不上” → 网络/VPN
- “邮箱登不上” → 邮箱/SSO
- “需要安装 Adobe” → 软件安装/授权
- “电脑黑屏” → 硬件故障
- “会议室无法投屏” → 打印/会议室设备
""",
"02_policy_and_rules/RULE_002_优先级判定规则.md": """
# 优先级判定规则

## P1
业务中断、多人受影响、无法替代、需要立即处理
示例：
- 公司 VPN 全员无法连接
- 邮箱系统全面不可用
- 核心业务系统无法访问

## P2
单人或小范围严重受影响，短时间内需要处理
示例：
- 员工无法登录 VPN 且当天必须远程办公
- 关键软件授权失效影响交付

## P3
一般性问题，有替代方案，不影响核心业务连续性
示例：
- 常规软件安装申请
- 单个打印机异常

## P4
咨询类、低影响、计划性请求
示例：
- 流程咨询
- 非紧急权限申请
""",
"02_policy_and_rules/RULE_003_人工升级规则.md": """
# 人工升级规则

以下情况必须转人工：
1. 涉及账号冻结、权限越权、安全告警
2. 涉及财务、法务、HR 敏感系统
3. 检索不到明确知识文档支持
4. 用户连续两轮反馈“仍未解决”
5. 模型无法确认分类或优先级
6. 同一问题可能影响多人或全公司
""",
"02_policy_and_rules/RULE_004_Jira字段映射规则.md": """
# Jira 字段映射规则

## 基本字段
- project.key = IT
- issuetype.name = Task

## 业务映射
- summary = 工单标题
- description = 结构化问题描述
- priority = 优先级
- labels = 分类标签
- customfield_device_type = 设备类型
- customfield_os = 操作系统
- customfield_urgency = 紧急程度

## description 结构建议
1. 用户信息
2. 问题现象
3. 影响范围
4. 已尝试步骤
5. 设备与系统信息
6. 附件说明
""",
"02_policy_and_rules/RULE_005_Agent回答约束.md": """
# Agent 回答约束

1. 必须优先基于知识文档回答
2. 没有依据时不得编造制度、流程或权限
3. 遇到安全/权限高风险问题必须建议提交工单或转人工
4. 需要工单时，先尽量补全关键信息
5. 回复应清晰、简洁、步骤化
6. 优先给出员工可自行执行的安全操作
7. 涉及管理员权限操作时，需明确标注“需 IT 协助”
"""
}

seed_docs = {
"03_seed_data/SEED_001_部门与角色样例.md": """
# 部门与角色样例

## 部门
- Engineering
- Product
- Design
- HR
- Finance
- Operations
- Marketing
- Sales

## 角色
- 员工
- 部门经理
- IT 支持工程师
- IT 管理员
- HR 专员
""",
"03_seed_data/SEED_002_设备与系统样例.md": """
# 设备与系统样例

## 设备类型
- 公司笔记本
- 台式机
- 测试机
- 会议室主机
- 打印机
- 显示器
- 扩展坞

## 操作系统
- Windows 10
- Windows 11
- macOS 14
- Ubuntu 22.04
""",
"03_seed_data/SEED_003_常见软件清单.md": """
# 常见软件清单

## 默认常用软件
- Chrome
- Edge
- Office
- Zoom
- 企业微信
- VS Code
- 7-Zip

## 审批类软件
- Adobe Photoshop
- Adobe Acrobat Pro
- IntelliJ IDEA Ultimate
- DataGrip
- Navicat
- Figma Desktop
- Wireshark
""",
"03_seed_data/SEED_004_测试问句样例.md": """
# 测试问句样例

## FAQ 类
- VPN 连不上怎么办？
- 我怎么申请安装 Adobe？
- 新员工第一天要做哪些 IT 设置？
- 离职时账号什么时候关闭？

## 报障类
- 我电脑今天早上突然蓝屏了
- 邮箱登不上，一直让我重新验证
- 打印机在线但打印不出来
- 公司 Wi-Fi 连上了但上不了网

## 查询类
- 我昨天提交的软件安装工单现在到哪一步了？
- 我想看一下我的工单状态

## 高风险类
- 能不能直接给我管理员权限？
- 帮我绕过 MFA 登录一下
"""
}

all_docs = {}
all_docs.update(docs)
all_docs.update(rule_docs)
all_docs.update(seed_docs)

for rel, content in all_docs.items():
    p = base / rel
    p.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")

# create a compact index
index = {
    "project": "企业内部 IT 支持 AI Agent",
    "total_files": len(all_docs) + 1,
    "knowledge_base_files": len(docs),
    "rule_files": len(rule_docs),
    "seed_files": len(seed_docs),
    "folders": ["01_knowledge_base", "02_policy_and_rules", "03_seed_data"]
}
(base / "file_index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

zip_path = Path("e:/agent/source/it_support_data.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for p in base.rglob("*"):
        z.write(p, p.relative_to(base.parent))

print(f"Created: {base}")
print(f"Zip: {zip_path}")
print(f"Total files: {len(list(base.rglob('*')))}")