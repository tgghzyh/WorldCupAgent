# WorldCupAgent 服务器部署技术报告

## 1. 部署结论

WorldCupAgent 已部署至阿里云轻量应用服务器，并可通过 HTTP 对外访问。当前服务器部署的是项目的静态 Next.js 前端，展示仓库中 `frontend/public/data/snapshots/latest.json` 对应的预测快照；服务器不运行 Python 数据流水线，也不在运行时调用 LLM。

最初计划是在服务器中使用 Node.js 容器构建并运行 Next.js。由于所选实例仅有 2 vCPU 和 1 GiB 内存，生产构建在 Next.js 编译阶段持续超过 40 分钟，无法满足稳定部署要求。最终方案改为在本地完成静态构建、将构建产物提交到 GitHub，再由服务器中的轻量 Nginx 容器提供网站服务。

## 2. 服务器环境

| 项目 | 配置 |
| --- | --- |
| 云产品 | 阿里云轻量应用服务器 |
| 操作系统 | Alibaba Cloud Linux 3.2104 U10（OpenAnolis Edition） |
| CPU 与内存 | 2 vCPU、1 GiB RAM |
| 系统盘 | 30 GiB ESSD |
| 容器运行时 | Docker 26.1.3 |
| Swap | 2 GiB 持久化交换文件 |
| 对外服务端口 | TCP 80 |

服务器通过具备 `sudo` 权限的 `admin` 账号维护。GitHub 私有仓库使用服务器专属、只读的 SSH Deploy Key 访问，不使用 GitHub 账号密码或个人访问令牌。

## 3. 最终架构

```text
本地开发机
  -> npm run build
  -> frontend/out 静态导出文件
  -> 推送到 GitHub main 分支
  -> 服务器 git pull --ff-only
  -> Docker Compose 启动 Nginx 容器
  -> TCP 80 对外提供网站
```

该架构将 Node.js 编译从服务器移出。Nginx 仅托管生成后的 HTML、JavaScript、CSS、图片和快照 JSON 文件，内存占用更低，启动和更新行为也更可预期。

## 4. 部署配置变更

| 文件 | 作用 |
| --- | --- |
| `frontend/next.config.ts` | 设置 `output: "export"`，将站点导出至 `frontend/out`；远程图片不再依赖 Next.js 服务端图片优化。 |
| `frontend/out/` | 由 `npm run build` 生成并纳入版本控制的静态站点文件。 |
| `frontend/Dockerfile` | 基于 `nginx:1.27-alpine` 构建镜像，将 `frontend/out` 复制到 Nginx 网站根目录。 |
| `docker-compose.yml` | 启动 `worldcup-agent-web` 容器、配置自动重启，并映射服务器 TCP 80 至容器 TCP 80。 |

关键 Git 提交：

| 提交 | 说明 |
| --- | --- |
| `4545f73` | 初始 Node.js 22 Docker 部署配置。 |
| `7edfb17` | 当前生产使用的静态导出和 Nginx 部署配置。 |

## 5. 服务器初始化

### 5.1 Swap 配置

1 GiB 物理内存不足以承担偶发的构建或运维峰值，因此创建 2 GiB Swap 并写入 `/etc/fstab`：

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile swap swap defaults 0 0' | sudo tee -a /etc/fstab
free -h
```

### 5.2 GitHub 仓库访问

服务器使用 `ssh-keygen` 创建 Ed25519 密钥，将公钥添加到 GitHub 仓库的 **Settings -> Deploy keys**，且只授予只读权限。完成后可安全克隆私有仓库：

```bash
git clone git@github.com:tgghzyh/WorldCupAgent.git
```

### 5.3 防火墙

阿里云轻量服务器防火墙需允许入站 TCP 80，以提供公开 HTTP 访问。TCP 22 用于远程管理，应按实际管理来源收紧；在配置 HTTPS 前，无需开放 TCP 443。

## 6. 部署与验证

首次克隆仓库后，在服务器执行：

```bash
cd ~/WorldCupAgent
git pull --ff-only
sudo docker compose up --build -d
```

验证容器和本地 HTTP 服务：

```bash
sudo docker compose ps
sudo docker compose logs --tail=50 web
curl -I http://127.0.0.1
```

最后一条命令应返回 HTTP `200`。云防火墙规则生效后，可使用服务器公网 IP 通过 HTTP 访问网站。

## 7. 后续更新流程

每次修改前端代码或预测快照数据后，先在本地重新生成静态站点，再推送：

```bash
cd frontend
npm run build
cd ..
git add frontend/out frontend/next.config.ts frontend/public/data/snapshots/latest.json
git commit -m "Update published site"
git push origin main
```

随后在服务器更新：

```bash
cd ~/WorldCupAgent
git pull --ff-only
sudo docker compose up --build -d
```

更新时服务器不需要执行 `npm install` 或 `npm run build`。
