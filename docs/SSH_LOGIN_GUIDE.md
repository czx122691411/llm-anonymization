# WSL SSH 密钥对登录完整指南

## 🎯 目标
使用密钥对从 WSL 登录到云服务器 `8.147.70.110`

---

## 📋 完整步骤

### 第一步：在 WSL 中准备密钥

```bash
# 1. 复制密钥到 SSH 目录
cp /mnt/f/daily_work/server-key/llm.pem ~/.ssh/llm_server.pem

# 2. 设置正确权限（非常重要！）
chmod 600 ~/.ssh/llm_server.pem

# 3. 验证密钥
ls -lh ~/.ssh/llm_server.pem
# 应该显示: -rw------- 1 rooter rooter

# 4. 测试密钥格式
openssl rsa -in ~/.ssh/llm_server.pem -check -noout
# 应该显示: RSA key ok

# 5. 提取公钥
ssh-keygen -y -f ~/.ssh/llm_server.pem > ~/.ssh/llm_server.pub
cat ~/.ssh/llm_server.pub
```

### 第二步：在服务器端配置公钥

**重要：** 需要先通过其他方式（密码/控制台）登录服务器，然后配置公钥。

#### 方法 A：如果你有 SSH 密码

```bash
# 1. 使用密码登录（一次性）
ssh rooter@8.147.70.110
# 输入密码

# 2. 登录后在服务器上执行以下命令
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# 3. 添加公钥（复制下面的完整公钥内容）
echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDRdvEeBXjwZjxGF45YHpv4H74l7XK6O966YCPpS4HPMi8kSeFXWF1trOfxtm2864hwWF3h7gJir/DN9f4yxxR4mDlufx9oIUTvJSkgKSYsLSAvuJOyjs8mlViZ7/sMDuSYVuxSSP+GrtVA1dwr5GVfduDj/D9O8QUWqJaRTVp8nnJnsI5aWLzNskfpaO6f2PfzBP4sOCK4MLGWR8O76MflA8rivuzFRLG/gJeGKz+BjacJo1GGuzHLKh6aN9a/VKXIuACV7X7F9MdSgPWVa6xpCfRiPkgXJOtnKutfKg213PojTVPboYbqei1tKMaRz9hsmy/wqrhKYw8SlVyVnVDl' >> ~/.ssh/authorized_keys

# 4. 设置正确的权限
chmod 600 ~/.ssh/authorized_keys

# 5. 验证配置
cat ~/.ssh/authorized_keys

# 6. 退出服务器
exit
```

#### 方法 B：从 Windows 使用密钥登录

```powershell
# 在 Windows PowerShell 或 CMD 中执行
ssh -i F:\daily_work\server-key\llm.pem rooter@8.147.70.110

# 登录后执行同样的命令配置公钥（见方法 A）
```

#### 方法 C：使用云服务商控制台

如果你的云服务商提供 Web 控制台/VNC：

1. 登录控制台
2. 打开终端
3. 执行方法 A 中的命令

### 第三步：从 WSL 使用密钥登录

服务器配置好公钥后，在 WSL 中执行：

```bash
# 方法 1：直接指定密钥文件
ssh -i ~/.ssh/llm_server.pem rooter@8.147.70.110

# 方法 2：添加到 SSH 配置文件
cat >> ~/.ssh/config << 'EOF'

Host cloud-server
    HostName 8.147.70.110
    User rooter
    IdentityFile ~/.ssh/llm_server.pem
    StrictHostKeyChecking no
EOF

# 然后可以这样连接
ssh cloud-server

# 方法 3：使用完整命令
ssh -i ~/.ssh/llm_server.pem \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    rooter@8.147.70.110
```

### 第四步：验证连接

```bash
# 测试连接并显示服务器信息
ssh -i ~/.ssh/llm_server.pem rooter@8.147.70.110 << 'ENDSSH'
echo "✅ SSH 连接成功！"
hostname
whoami
pwd
uptime
df -h
free -h
ENDSSH
```

---

## 🔧 故障排查

### 问题 1: Permission denied (publickey)

**原因**: 服务器端没有配置公钥

**解决**: 先通过密码或其他方式登录服务器，添加公钥到 `~/.ssh/authorized_keys`

### 问题 2: Warning: UNPROTECTED PRIVATE KEY FILE!

**原因**: 密钥文件权限过于开放

**解决**:
```bash
chmod 600 ~/.ssh/llm_server.pem
```

### 问题 3: Load key: invalid format

**原因**: 密钥文件损坏或格式错误

**解决**: 重新从原始位置复制密钥文件

---

## 📝 快速命令参考

```bash
# 一键设置密钥
cp /mnt/f/daily_work/server-key/llm.pem ~/.ssh/llm_server.pem && \
chmod 600 ~/.ssh/llm_server.pem && \
ls -lh ~/.ssh/llm_server.pem

# 连接命令
ssh -i ~/.ssh/llm_server.pem rooter@8.147.70.110

# 查看公钥
cat ~/.ssh/llm_server.pub
```

---

## ✅ 成功连接后的示例操作

```bash
# 查看服务器状态
ssh -i ~/.ssh/llm_server.pem rooter@8.147.70.110 "
    echo '=== 系统信息 ==='
    hostname
    uptime
    df -h
    free -h
    python3 --version
"

# 执行远程命令
ssh -i ~/.ssh/llm_server.pem rooter@8.147.70.110 "ls -la /root"

# 传输文件
scp -i ~/.ssh/llm_server.pem local_file.txt rooter@8.147.70.110:/root/
```

---

**重要提示**:
1. 必须先在服务器端配置公钥
2. 密钥文件权限必须是 600
3. 用户名是 `rooter`，服务器 IP 是 `8.147.70.110`
