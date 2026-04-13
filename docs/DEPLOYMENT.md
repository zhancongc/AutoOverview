# 服务器部署配置

> 最后更新: 2026-04-13
>
> 本文档记录服务器部署相关的配置方案，包括跨服务器通信、防火墙配置等。

---

## 架构概览

```
Cloudflare
    ↓
New York (Caddy 反代)
    ↓
Shanghai (FastAPI 后端 :8006)
```

- **Cloudflare**: CDN + SSL 终止
- **New York**: `autooverview.plainkit.top`，Caddy 反代静态文件 + API
- **Shanghai**: `14.103.210.88`，FastAPI 后端服务运行在 8006 端口

---

## 方案 1：后端监听 0.0.0.0 + UFW 防火墙限制

**适用场景**: Shanghai 后端只允许 New York 服务器访问 8006 端口

### 步骤 1：修改后端监听地址

**检查当前监听状态**:
```bash
ss -tlnp | grep 8006
```

- 如果显示 `127.0.0.1:8006` → 只监听本地 ❌
- 如果显示 `0.0.0.0:8006` → 允许外部访问 ✅
- 如果没有输出 → 服务未运行 ❌

**根据启动方式修改监听地址**:

**方法 A: systemd 服务**
```bash
sudo nano /etc/systemd/system/autooverview-backend.service
```
修改 `ExecStart` 确保 `--host 0.0.0.0`:
```ini
ExecStart=/path/to/venv/bin/python /app/AutoOverview/backend/main.py --host 0.0.0.0 --port 8006
```

重启服务:
```bash
sudo systemctl daemon-reload
sudo systemctl restart autooverview-backend
```

**方法 B: supervisor**
```bash
sudo nano /etc/supervisor/conf.d/autooverview.conf
```
修改 `command`:
```ini
command=/path/to/venv/bin/python /app/AutoOverview/backend/main.py --host 0.0.0.0 --port 8006
```

重启服务:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart autooverview
```

**方法 C: 直接修改 main.py**
```python
# backend/main.py 最后一行
uvicorn.run(
    "main:app",
    host="0.0.0.0",  # 改成 0.0.0.0
    port=8006,
    reload=True,
    access_log=True,
    reload_excludes=[".venv", "*.pyc", "__pycache__"]
)
```

### 步骤 2：配置 UFW 防火墙

**在上海服务器执行**:

```bash
# 1. 确保 UFW 已安装
sudo apt install ufw -y

# 2. 设置默认策略
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 3. 允许 SSH（避免锁死）
sudo ufw allow 22/tcp

# 4. 允许 Nginx HTTPS（443）和 HTTP（80）
sudo ufw allow 443/tcp
sudo ufw allow 80/tcp

# 5. 【关键】只允许 New York 服务器访问 8006
sudo ufw allow from 23.94.5.193 to any port 8006 proto tcp

# 6. 启用防火墙
sudo ufw enable

# 7. 查看状态
sudo ufw status numbered
```

**预期输出**:
```
Status: active

     To                         Action      From
     --                         ------      ----
[ 1] 22/tcp                     ALLOW IN    Anywhere
[ 2] 443/tcp                   ALLOW IN    Anywhere
[ 3] 80/tcp                    ALLOW IN    Anywhere
[ 4] 8006/tcp                  ALLOW IN    23.94.5.193
```

### 步骤 3：验证连接

**在上海服务器验证监听地址**:
```bash
ss -tlnp | grep 8006
# 应该显示: 0.0.0.0:8006
```

**在 New York 服务器测试**:
```bash
curl http://14.103.210.88:8006/api/health
```

**预期返回**:
```json
{"status":"ok","deepseek_configured":true,"demo_task_ids":[...]}
```

**从其他 IP 测试（应该被拒绝）**:
```bash
# 用个人电脑测试，应该超时或拒绝
curl http://14.103.210.88:8006/api/health
# Connection refused / timeout
```

---

## New York Caddy 配置

**文件**: `/etc/caddy/sites/autooverview.plainkit.top.conf`

```caddy
autooverview.plainkit.top {
    tls /etc/ssl/cloudflare/plainkit.top.pem /etc/ssl/cloudflare/plainkit.top-key.pem

    encode gzip

    # API 反向代理到上海后端
    handle /api/* {
        reverse_proxy http://14.103.210.88:8006
    }

    # 静态文件服务
    handle {
        root * /opt/autooverview-en/frontend/dist-en
        
        try_files {path} /index.html
        file_server

        # 静态资源缓存
        @static path *.js *.css *.png *.jpg *.svg *.woff *.woff2
        header @static Cache-Control "public, max-age=31536000, immutable"
    
        # HTML 不缓存
        @html path *.html /
        header @html Cache-Control "no-cache, no-store, must-revalidate"
    }

    # 安全头
    header X-Content-Type-Options "nosniff"
    header X-Frame-Options "DENY"
}
```

重启 Caddy:
```bash
sudo systemctl reload caddy
# 或
sudo systemctl restart caddy
```

---

## 常见问题

### Q: 修改后仍然 502 错误

**检查清单**:
1. 上海服务器后端是否监听 `0.0.0.0:8006`
2. UFW 防火墙是否允许 NY IP 访问 8006
3. 云服务商安全组是否开放 8006 端口
4. 从 NY 服务器直接测试: `curl http://14.103.210.88:8006/api/health`

### Q: 如何查看防火墙日志

```bash
# 查看 UFW 日志
sudo tail -f /var/log/ufw.log
# 或
sudo journalctl -u ufw -f
```

### Q: 如何临时开放 8006 端口测试

```bash
# 临时允许所有 IP 访问（测试用）
sudo ufw delete 4  # 删除之前的规则编号
sudo ufw allow 8006/tcp

# 测试完成后恢复限制
sudo ufw delete allow 8006/tcp
sudo ufw allow from 23.94.5.193 to any port 8006 proto tcp
```

### Q: 云服务器安全组配置

如果使用阿里云/腾讯云等，需要在控制台配置安全组：

| 规则 | 协议 | 端口 | 来源 | 说明 |
|------|------|------|------|------|
| 入站 | TCP | 22 | 0.0.0.0/0 | SSH |
| 入站 | TCP | 80 | 0.0.0.0/0 | HTTP |
| 入站 | TCP | 443 | 0.0.0.0/0 | HTTPS |
| 入站 | TCP | 8006 | 23.94.5.193/32 | 后端 API（仅 NY 服务器） |

---

## 服务器信息

| 服务器 | IP | 用途 |
|--------|-----|------|
| Shanghai (后端) | 14.103.210.88 | FastAPI :8006 |
| New York (反代) | 23.94.5.193 | Caddy + 静态文件 |

---

## 参考文档

- [UFW 防火墙指南](https://help.ubuntu.com/community/UFW)
- [Caddy 反向代理文档](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy)
- [CLAUDE.md](../CLAUDE.md) - 项目指引
