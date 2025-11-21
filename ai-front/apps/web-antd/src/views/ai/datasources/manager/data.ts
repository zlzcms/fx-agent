/**
 * @Author: zhujinlong
 * @Date:   2025-06-12 13:56:21
 * @Last Modified by:   zhujinlong
 * @Last Modified time: 2025-06-12 17:16:56
 */
import type { DatabaseTreeNode } from '#/api';

import { h } from 'vue';
import { Tag } from 'ant-design-vue';

/**
 * 获取类型标签组件
 */
export function getTypeTag(type: 'database' | 'table' | 'field') {
  const tagConfig = {
    database: { color: 'blue', text: '数据库' },
    table: { color: 'green', text: '表' },
    field: { color: 'orange', text: '字段' },
  };

  const config = tagConfig[type];
  return h(Tag, { color: config.color }, () => config.text);
}

/**
 * 获取类型图标
 */
export function getTypeIcon(type: 'database' | 'table' | 'field') {
  const iconMap = {
    database: '🗄️',
    table: '📋',
    field: '📝',
  };
  return iconMap[type];
}

/**
 * 树形表格列配置
 */
export function useDatabaseTreeColumns(): any[] {
  return [
    {
      type: 'seq',
      width: 60,
      fixed: 'left',
    },
    {
      field: 'name',
      title: '数据',
      minWidth: 200,
      treeNode: true,
      slots: {
        default: ({ row }: { row: DatabaseTreeNode }) => {
          return h('div', { class: 'flex items-center gap-2' }, [
            h('span', { class: 'text-lg' }, getTypeIcon(row.type)),
            h('span', row.name),
          ]);
        },
      },
    },
    {
      field: 'type',
      title: '类型',
      width: 100,
      slots: {
        default: ({ row }: { row: DatabaseTreeNode }) => getTypeTag(row.type),
      },
    },
    {
      field: 'description',
      title: '描述',
      minWidth: 300,
      editRender: {
        name: 'input',
        props: {
          placeholder: '请输入描述信息...',
        },
      },
      slots: {
        default: ({ row }: { row: DatabaseTreeNode }) => {
          return row.description || h('span', { class: 'text-gray-400' }, '暂无描述');
        },
      },
    },
    {
      field: 'field_type',
      title: '字段类型',
      width: 120,
      visible: false, // 默认隐藏，只在字段级别显示
      slots: {
        default: ({ row }: { row: DatabaseTreeNode }) => {
          if (row.type === 'field' && row.field_type) {
            return h(Tag, { color: 'purple' }, () => row.field_type);
          }
          return '-';
        },
      },
    },
    {
      field: 'table_rows',
      title: '数据量',
      width: 120,
      visible: false, // 默认隐藏，只在表级别显示
      slots: {
        default: ({ row }: { row: DatabaseTreeNode }) => {
          if (row.type === 'table' && row.table_rows !== undefined) {
            return new Intl.NumberFormat('zh-CN').format(row.table_rows);
          }
          return '-';
        },
      },
    },
  ];
}

/**
 * 构建树形数据结构
 */
export function buildTreeData(flatData: DatabaseTreeNode[]): DatabaseTreeNode[] {
  const treeData: DatabaseTreeNode[] = [];
  const nodeMap = new Map<string, DatabaseTreeNode>();

  // 首先将所有节点放入map中
  flatData.forEach(node => {
    nodeMap.set(node.id, { ...node, children: [] });
  });

  // 构建树形结构
  flatData.forEach(node => {
    const treeNode = nodeMap.get(node.id)!;
    if (node.parent_id) {
      const parent = nodeMap.get(node.parent_id);
      if (parent) {
        parent.children!.push(treeNode);
      }
    } else {
      treeData.push(treeNode);
    }
  });

  return treeData;
}

/**
 * 展开所有节点的ID列表（默认只展开数据库级别）
 */
export function getDefaultExpandedRowKeys(treeData: DatabaseTreeNode[]): string[] {
  const expandedKeys: string[] = [];
  
  function traverse(nodes: DatabaseTreeNode[], depth: number = 0) {
    nodes.forEach(node => {
      // 只默认展开数据库级别，不展开表和字段级别
      if (node.type === 'database') {
        expandedKeys.push(node.id);
      }
      if (node.children && node.children.length > 0) {
        traverse(node.children, depth + 1);
      }
    });
  }
  
  traverse(treeData);
  return expandedKeys;
}

/**
 * 将树形结构转换为扁平数组
 */
function flattenTreeData(treeData: DatabaseTreeNode[]): DatabaseTreeNode[] {
  const flatData: DatabaseTreeNode[] = [];
  
  function traverse(nodes: DatabaseTreeNode[]) {
    nodes.forEach(node => {
      // 创建节点副本，不包含children属性
      const { children, ...nodeWithoutChildren } = node;
      flatData.push(nodeWithoutChildren as DatabaseTreeNode);
      
      if (children && children.length > 0) {
        traverse(children);
      }
    });
  }
  
  traverse(treeData);
  return flatData;
}

/**
 * 获取修改的描述信息
 */
export function getChangedDescriptions(
  originalData: DatabaseTreeNode[], 
  currentData: DatabaseTreeNode[]
): Array<{ id: string; type: 'database' | 'table' | 'field'; description: string }> {
  const changes: Array<{ id: string; type: 'database' | 'table' | 'field'; description: string }> = [];
  
  // 如果currentData是树形结构，先转换为扁平数组
  const flatCurrentData = Array.isArray(currentData) && currentData.length > 0 && currentData[0]?.children !== undefined
    ? flattenTreeData(currentData)
    : currentData;
  
  function compareNodes(original: DatabaseTreeNode[], current: DatabaseTreeNode[]) {
    const originalMap = new Map(original.map(node => [node.id, node]));
    
    current.forEach(node => {
      const originalNode = originalMap.get(node.id);
      if (originalNode && originalNode.description !== node.description) {
        changes.push({
          id: node.id,
          type: node.type,
          description: node.description || '',
        });
      }
    });
  }
  
  compareNodes(originalData, flatCurrentData);
  return changes;
} 