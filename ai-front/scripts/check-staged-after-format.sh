#!/bin/bash

# 检查格式化后是否有未暂存的文件
# 如果有，则提示用户手动添加并退出提交

set -e

# 检查是否有未暂存的修改
if ! git diff --quiet; then
    echo "⚠️  代码格式化完成，但有文件被修改后未添加到暂存区"
    echo "📝 请运行以下命令将格式化后的文件添加到提交中："
    echo ""
    echo "   git add ."
    echo "   git commit"
    echo ""
    echo "💡 或者使用以下命令查看具体修改的文件："
    echo "   git diff --name-only"
    echo ""
    exit 1
fi

echo "✅ 所有格式化的文件已正确暂存"
exit 0