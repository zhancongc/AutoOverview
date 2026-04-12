# 法律文档合规性分析报告

**生成日期**: 2026-04-12
**分析范围**: Terms & Conditions, Privacy Policy, Refund Policy vs 实际功能实现

---

## 🔴 严重问题：缺失承诺的功能

### 1. Privacy Policy 承诺但未实现的功能

#### ❌ 账户关闭功能 (8.6 Account Closure)
**承诺**: "You may close your account at any time through your profile settings or by contacting us."

**实际状态**: 
- 前端 ProfilePage 没有"关闭账户"按钮
- 后端没有 `/api/account/close` 或类似API
- 无法通过用户界面自行关闭账户

**风险等级**: 🔴 高 (GDPR/CCPA 合规要求)

**建议**: 
- 添加账户关闭功能到 ProfilePage
- 实现后端 API 支持账户删除/停用
- 提供 30 天冷静期（可恢复）

---

#### ❌ 数据访问/导出功能 (8.1 Access & Portability)
**承诺**: "You can request a copy of your personal data in a structured format."

**实际状态**:
- 没有"导出我的数据"功能
- 没有 `/api/data/export` API
- 用户无法下载自己的所有数据

**风险等级**: 🔴 高 (GDPR 第15条 - 数据访问权)

**建议**:
- 添加"导出数据"按钮到 ProfilePage
- 实现后端 API 打包用户数据（JSON/ZIP格式）
- 包含：账户信息、生成记录、支付记录、使用日志

---

#### ❌ 数据更正功能 (8.2 Correction)
**承诺**: "You can update or correct inaccurate information through your account settings."

**实际状态**:
- ProfilePage 只显示，不允许编辑用户信息
- 没有更改邮箱、昵称的界面
- 后端没有 `/api/user/update` API

**风险等级**: 🟡 中

**建议**:
- 添加编辑个人信息的表单
- 实现后端更新API

---

#### ❌ 数据删除功能 (8.3 Deletion)
**承诺**: "You can request deletion of your personal data... We will delete your data within 30 days"

**实际状态**:
- 没有"删除我的数据"功能
- 没有数据删除请求系统
- 没有 30 天删除流程

**风险等级**: 🔴 高 (GDPR 第17条 - 被遗忘权)

**建议**:
- 实现数据删除请求API
- 建立删除工单系统
- 30 天内完成删除并发送确认

---

#### ❌ 营销退出功能 (8.5 Opt-Out)
**承诺**: "You can opt-out of marketing communications at any time."

**实际状态**:
- 没有营销邮件系统
- 没有订阅/取消订阅功能
- 没有 unsubscribe 链接

**风险等级**: 🟢 低 (目前未发送营销邮件)

**建议**: 
- 如果未来发送营销邮件，必须实现 unsubscribe 功能
- 在邮件底部添加取消订阅链接

---

#### ❌ Cookie 偏好管理 (2.3 Cookies)
**承诺**: "You can manage cookie preferences through your browser settings."

**实际状态**:
- 没有 Cookie 同意横幅
- 没有 Cookie 偏好设置界面

**风险等级**: 🟡 中 (GDPR Cookie 合规)

**建议**:
- 添加 Cookie 同意横幅
- 实现 Cookie 偏好管理

---

### 2. Refund Policy 承诺但未实现的功能

#### ❌ 退款请求系统 (8. Requesting a Refund)
**承诺**: 
- "To request a refund, contact us at service@snappicker.com"
- "Refund requests are typically reviewed within 5-10 business days"
- "refunds will be processed within 14 business days"

**实际状态**:
- 没有退款请求表单
- 没有退款工单系统
- 没有退款状态跟踪
- 邮箱 service@snappicker.com 可能未配置

**风险等级**: 🟡 中

**建议**:
- 在 ProfilePage 添加"请求退款"按钮
- 实现退款工单系统
- 配置 service@snappicker.com 邮箱
- 建立退款处理流程

---

#### ❌ 技术故障退款流程 (3.1 Technical Failures)
**承诺**: "We will investigate the issue and may offer a credit replacement or partial refund"

**实际状态**:
- `refund_credit()` 函数存在但只用于任务失败
- 没有用户可见的"报告问题"功能
- 没有技术故障退款申请流程

**风险等级**: 🟡 中

**建议**:
- 添加"报告问题"功能到 ReviewPage
- 实现技术故障退款申请API
- 建立人工审核流程

---

### 3. Terms & Conditions 承诺的功能实现情况

#### ✅ 服务描述 (2. Service Description)
**承诺**: 
- 自动搜索学术数据库 ✅
- AI生成文献综述 ✅
- 多格式导出 ✅
- 基于额度的使用系统 ✅

**实际状态**: 已实现

---

#### ✅ 支付处理 (5.2 Payment Terms)
**承诺**: "Payments are processed securely through Paddle"

**实际状态**: 已实现 Paddle 集成

---

#### ⚠️ 账户暂停/终止 (8. Account Suspension & Termination)
**承诺**: "We reserve the right to suspend or terminate your account"

**实际状态**:
- 后端有封禁用户功能
- 但没有用户界面查看账户状态

**风险等级**: 🟢 低

---

## 📊 合规性评分

| 法律文档 | 合规度 | 严重问题数 | 建议优先级 |
|---------|--------|-----------|-----------|
| Privacy Policy | 40% | 5 | 🔴 高 |
| Refund Policy | 60% | 2 | 🟡 中 |
| Terms & Conditions | 85% | 1 | 🟢 低 |

---

## 🚨 立即行动建议

### 优先级 1（GDPR/CCPA 合规必须）
1. **实现账户关闭功能**
   - 前端：ProfilePage 添加"关闭账户"按钮
   - 后端：`DELETE /api/account` API
   - 数据库：软删除（保留数据用于法律要求）

2. **实现数据导出功能**
   - 前端：ProfilePage 添加"导出数据"按钮
   - 后端：`GET /api/data/export` API
   - 格式：JSON 包含所有用户数据

3. **实现数据删除请求功能**
   - 前端：ProfilePage 添加"删除数据"按钮
   - 后端：`POST /api/data/deletion-request` API
   - 流程：30天内完成删除

### 优先级 2（用户体验改进）
4. **添加个人信息编辑功能**
   - 前端：ProfilePage 添加编辑表单
   - 后端：`PUT /api/user/profile` API

5. **实现退款请求系统**
   - 前端：ProfilePage 添加"请求退款"链接
   - 后端：退款工单系统
   - 邮件：配置 service@snappicker.com

### 优先级 3（法律完善）
6. **更新法律文档**
   - 如果无法实现某些功能，应更新文档
   - 添加"我们正在努力实现这些功能"的说明
   - 或删除无法实现的承诺

---

## ⚖️ 法律风险提示

1. **GDPR 违规风险**: 
   - 缺少数据访问权、删除权、可移植权的实现
   - 可能面临罚款（最高 2000 万欧元或全球营业额 4%）

2. **CCPA 违规风险**:
   - 缺少加州居民的隐私权利实现
   - 可能面临每条记录 $2500-$7500 的民事罚款

3. **虚假宣传风险**:
   - 法律文档承诺了不存在的功能
   - 可能构成误导性商业行为

---

## 📝 后续步骤

1. **立即**: 更新法律文档，删除无法实现的承诺
2. **短期** (1-2周): 实现账户关闭、数据导出功能
3. **中期** (1个月): 实现数据删除、退款系统
4. **长期**: 建立完整的隐私合规体系

---

**免责声明**: 此分析基于当前代码状态，不构成法律建议。建议咨询隐私律师确保完全合规。
