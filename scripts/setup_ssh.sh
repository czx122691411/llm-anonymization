#!/bin/bash
# WSL SSH 密钥配置脚本

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  WSL SSH 密钥配置助手"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 检查原始密钥文件
ORIGINAL_KEY="/mnt/f/daily_work/server-key/llm.pem"
SSH_KEY="$HOME/.ssh/llm_server.pem"

echo "📋 步骤 1/5: 检查密钥文件"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -f "$ORIGINAL_KEY" ]; then
    echo "❌ 错误: 原始密钥文件不存在"
    echo "   路径: $ORIGINAL_KEY"
    echo ""
    echo "请确认密钥文件路径正确！"
    exit 1
fi

echo "✅ 找到密钥文件: $ORIGINAL_KEY"
ls -lh "$ORIGINAL_KEY"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  步骤 2/5: 复制并配置密钥"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 确保 .ssh 目录存在
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# 复制密钥
cp "$ORIGINAL_KEY" "$SSH_KEY"
chmod 600 "$SSH_KEY"

echo "✅ 密钥已复制到: $SSH_KEY"
ls -lh "$SSH_KEY"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  步骤 3/5: 验证密钥"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 验证密钥格式
if openssl rsa -in "$SSH_KEY" -check -noout 2>/dev/null; then
    echo "✅ 密钥格式正确"
else
    echo "❌ 密钥格式验证失败"
    exit 1
fi

# 提取公钥
ssh-keygen -y -f "$SSH_KEY" > "$SSH_KEY.pub" 2>/dev/null

echo "📌 公钥内容:"
echo ""
cat "$SSH_KEY.pub"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  步骤 4/5: 测试SSH连接"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "🔐 尝试连接到服务器 8.147.70.110 ..."
echo ""

# 测试连接
if ssh -i "$SSH_KEY" \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -o ConnectTimeout=10 \
    -o PreferredAuthentications=publickey \
    -o IdentitiesOnly=yes \
    rooter@8.147.70.110 \
    "hostname && echo '✅ 连接成功！' && exit" 2>/dev/null; then

    echo "✅ SSH 连接成功！"
    echo ""

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  步骤 5/5: 配置完成"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "✅ 配置完成！现在可以使用以下方式连接："
    echo ""
    echo "  方法 1 - 直接使用密钥:"
    echo "  ssh -i ~/.ssh/llm_server.pem rooter@8.147.70.110"
    echo ""
    echo "  方法 2 - 使用配置别名（如果配置了）:"
    echo "  ssh cloud-server"
    echo ""

    # 创建快捷配置
    cat > ~/.ssh/config.d/cloud-server.conf << EOF
Host cloud-server
    HostName 8.147.70.110
    User rooter
    IdentityFile ~/.ssh/llm_server.pem
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
EOF

    echo "✅ 已创建 SSH 配置: ~/.ssh/config.d/cloud-server.conf"
    echo ""

else
    echo "❌ SSH 连接失败"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  ⚠️  需要在服务器端配置公钥"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "请选择以下方式之一在服务器上添加公钥："
    echo ""
    echo "方式 1 - 使用密码登录:"
    echo "  ssh rooter@8.147.70.110"
    echo "  # 然后执行下面的命令:"
    echo "  mkdir -p ~/.ssh"
    echo "  chmod 700 ~/.ssh"
    echo "  echo '$(cat $SSH_KEY.pub)' >> ~/.ssh/authorized_keys"
    echo "  chmod 600 ~/.ssh/authorized_keys"
    echo ""
    echo "方式 2 - 在 Windows 上使用密钥登录:"
    echo "  ssh -i F:\\daily_work\\server-key\\llm.pem rooter@8.147.70.110"
    echo ""
    echo "方式 3 - 通过云服务商控制台登录"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  📋 完整公钥内容（需要复制到服务器）"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    cat "$SSH_KEY.pub"
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  配置完成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📚 详细文档: docs/SSH_LOGIN_GUIDE.md"
echo "🔑 密钥位置: $SSH_KEY"
echo "🔑 公钥位置: $SSH_KEY.pub"
echo ""
