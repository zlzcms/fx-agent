# Backend 文件恢复总结

## 问题概述

backend 目录下的所有文件被误删除。

## 恢复过程

### 1. 发现问题
- backend 目录变成空目录
- Git 显示所有文件处于 "deleted" 状态

### 2. 恢复文件
使用 Git 恢复命令：
```bash
git restore backend/
```

### 3. 验证恢复
- ✅ 所有文件已恢复
- ✅ alembic 目录恢复（70 个迁移文件）
- ✅ 环境配置文件恢复

## 当前状态

### 目录结构
```
backend/
├── .env.local            # 本地环境配置
├── .env.production       # 生产环境配置
├── alembic/             # 迁移文件目录
│   ├── env.py
│   └── versions/        # 70 个迁移文件
├── app/                 # 应用代码
├── common/              # 公共模块
├── database/            # 数据库连接
└── ...
```

### Git 状态
- 所有文件已恢复
- 工作目录干净（除了新创建的脚本）

## 数据库迁移

### 问题
之前遇到的迁移问题：
- 表 `sys_recommended_questions` 已存在
- Alembic 版本未同步

### 解决方案

#### 方案 1: 使用新创建的脚本（推荐）
```bash
./update_db.sh
```

此脚本会：
1. 自动加载环境变量
2. 显示当前版本
3. 执行数据库迁移

#### 方案 2: 手动更新数据库版本
```bash
# 连接数据库
docker exec -it fba_postgres psql -U postgres -d fba

# 更新版本
UPDATE alembic_version SET version_num = 'edd6636a4f4f';

# 验证
SELECT * FROM alembic_version;
\q
```

#### 方案 3: 手动执行迁移
```bash
cd /home/user/www/ai-backend
source .venv/bin/activate

# 加载环境变量
export $(cat backend/.env.local | grep -v '^#' | xargs)

# 查看当前版本
alembic current

# 执行迁移
alembic upgrade head
```

## 预防措施

1. **定期提交代码**
   ```bash
   git add .
   git commit -m "描述"
   git push
   ```

2. **删除文件前先确认**
   - 使用 `git status` 查看将要删除的文件
   - 重要操作前先备份

3. **使用 .gitignore**
   - 确保不该删除的文件不会被误操作

## 相关文件

- `update_db.sh` - 数据库更新脚本
- `backend/.env.local` - 本地环境配置
- `backend/.env.production` - 生产环境配置
- `alembic.ini` - Alembic 配置文件

## 注意事项

1. 环境变量文件（`.env.*`）包含敏感信息，不要提交到 Git
2. 数据库迁移前建议先备份数据库
3. 生产环境操作需要格外小心

## 下一步

1. 运行 `./update_db.sh` 更新数据库
2. 验证应用是否正常运行
3. 如有问题，查看日志排查
