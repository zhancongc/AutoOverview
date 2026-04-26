# 推广邮件系统 & 分享截图审核

> 详细文档，CLAUDE.md 中只保留简要指引。

## 推广邮件系统

### 数据表
- `email_contacts` — 字段：name, email, position, source_url, status(pending/sent/failed), unsubscribed, sent_at, error, created_at
- 模型：`backend/authkit/models/email_campaign.py` → `EmailContact`

### 导入联系人
```bash
cd backend && python3 scripts/import_contacts.py contacts.csv          # 追加导入
cd backend && python3 scripts/import_contacts.py contacts.csv --reset  # 清空后重新导入
```
CSV 格式：`name,email,position,source_url`

### 发送邮件
```bash
cd backend && python3 scripts/send_promo_emails.py                        # 发送所有 pending
cd backend && python3 scripts/send_promo_emails.py --limit 10             # 只发 10 封
cd backend && python3 scripts/send_promo_emails.py --dry-run              # 预览不发送
cd backend && python3 scripts/send_promo_emails.py --position "PhD"       # 按 position 筛选
cd backend && python3 scripts/send_promo_emails.py --email xxx@ac.uk      # 指定邮箱
cd backend && python3 scripts/send_promo_emails.py --limit 50 --delay 5   # 每封间隔 5 秒
```

自动跳过已发送（status=sent）和已退订（unsubscribed=true）的用户。

### 相关文件
| 文件 | 说明 |
|------|------|
| `backend/scripts/import_contacts.py` | CSV 导入脚本 |
| `backend/scripts/send_promo_emails.py` | 批量发送脚本 |
| `backend/scripts/university_domains.py` | 邮箱域名→大学名称 |
| `backend/authkit/templates/promo_email.py` | 邮件模板（Jinja2） |
| `backend/authkit/routers/email_unsubscribe.py` | 退订功能（HMAC token） |
| `backend/authkit/services/email_service.py` | 通用邮件服务 |

### SMTP 配置
在 `.env.auth` 中配置：`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, `SMTP_FROM_NAME`

---

## 分享截图审核系统

### 流程
用户上传截图 → 写入 `credit_logs`（reason=share_reward_pending）→ 管理员在 `/david/approve` 审核 → 通过则发 2 积分，拒绝则删除记录

### API
| 接口 | 说明 |
|------|------|
| `POST /api/share-reward` | 用户上传截图（不自动发积分） |
| `GET /api/david/share-proofs` | 列出待审核截图（自动清理 >30 天文件） |
| `POST /api/david/share-proofs/{filename}/approve` | 通过：发放 2 积分 + 删除截图 |
| `POST /api/david/share-proofs/{filename}/reject` | 拒绝：删除记录 + 删除截图 |

审核接口受 David whitelist 保护。

### 文件存储
- 截图目录：`backend/uploads/share_proofs/`
- 静态访问：`/share-proofs/{filename}`

### 前端
- 审核页面：`DavidApprovePage.tsx`（路由 `/david/approve`，DavidRoute 保护）
- 海报弹窗分享按钮触发 `ShareRewardModal`（中文站：微信/上传截图，英文站：X(@JadeZhan0822)/上传截图）
- 适用页面：ReviewPage、ReviewPageInternational、ComparisonMatrixViewer
