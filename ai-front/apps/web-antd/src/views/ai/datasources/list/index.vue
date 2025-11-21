<script setup lang="ts">
import type { VbenFormProps } from '@vben/common-ui';

import type {
  // OnActionClickParams,
  VxeTableGridOptions,
} from '#/adapter/vxe-table';
// 导入API和类型
import type { BatchCreateDataSourceParams, BatchCreateDataSourceResponse, DataSource } from '#/api';

import { nextTick, onMounted, ref } from 'vue';

import { Page, useVbenModal } from '@vben/common-ui';
// import { MaterialSymbolsAdd } from '@vben/icons';
import { $t } from '@vben/locales';

import { message } from 'ant-design-vue';

import { useVbenForm } from '#/adapter/form';
import { useVbenVxeGrid } from '#/adapter/vxe-table';
import {
  batchCreateDataSourceApi,
  deleteDataSourceApi,
  getDataSourceApi,
  getDataSourceListApi,
  updateDataSourceApi,
} from '#/api';
import { pagerPresets } from '#/configs/pager';

import {
  addDataSource,
  clearSelectedDataSources,
  databaseOptions,
  isLoadingFields,
  loadDatabaseOptions,
  loadTableFields,
  loadTableOptions,
  querySchema,
  removeDataSource,
  selectedDataSources,
  tableOptions,
  updateDataSourceDescription,
  useAddSchema,
  useColumns,
} from './data';

/**
 * 表格配置
 */
const formOptions: VbenFormProps = {
  collapsed: true,
  showCollapseButton: true,
  submitButtonOptions: {
    content: $t('page.form.query'),
  },
  schema: querySchema,
};

const gridOptions: VxeTableGridOptions<DataSource> = {
  rowConfig: {
    keyField: 'id',
  },
  checkboxConfig: {
    highlight: true,
  },
  columnConfig: {
    resizable: true,
    useKey: true,
  },
  height: 'auto',
  exportConfig: {},
  printConfig: {},
  toolbarConfig: {
    export: true,
    print: true,
    refresh: { code: 'query' },
    custom: true,
    zoom: true,
  },
  pagerConfig: pagerPresets.standard,
  columns: useColumns(),
  proxyConfig: {
    ajax: {
      query: async ({ page }, formValues) => {
        try {
          const params = {
            ...formValues,
            page: page.currentPage,
            size: page.pageSize,
          };

          const response = await getDataSourceListApi(params);

          return {
            items: response.items || [],
            total: response.total || 0,
          };
        } catch (error) {
          console.error(`${$t('views.ai.datasources.getListFailed')}:`, error);
          message.error($t('views.ai.datasources.getListFailed'));
          return {
            items: [],
            total: 0,
          };
        }
      },
    },
  },
};

const [Grid, gridApi] = useVbenVxeGrid({ formOptions, gridOptions });

function onRefresh() {
  gridApi.query();
}

// function onActionClick({ code, row }: OnActionClickParams<DataSource>) {
//   switch (code) {
//     case 'delete': {
//       // 直接执行删除操作，VXE表格会自动显示确认对话框
//       return new Promise(async (resolve, reject) => {
//         try {
//           await deleteDataSourceApi([row.id]);
//           message.success(
//             $t('views.ai.datasources.deleteCollectionSuccess', { name: row.collection_name }),
//           );
//           onRefresh();
//           resolve(true);
//         } catch (error) {
//           console.error($t('views.ai.datasources.deleteCollectionFailed') + ':', error);
//           message.error($t('views.ai.datasources.deleteCollectionFailed'));
//           reject(error);
//         }
//       });
//     }
//     case 'edit': {
//       // 实现编辑集合功能
//       editDataSource.value = row.id;
//       editModalApi.open();
//       break;
//     }
//     case 'view': {
//       // 实现查看集合详情功能
//       viewDataSource.value = row.id;
//       viewModalApi.open();
//       break;
//     }
//   }
// }

/**
 * 编辑表单
 */
const [EditForm, editFormApi] = useVbenForm({
  showDefaultActions: false,
  schema: [
    {
      component: 'Input',
      fieldName: 'collection_name',
      label: $t('views.ai.datasources.collectionName'),
      componentProps: {
        placeholder: $t('views.ai.datasources.enterCollectionName'),
      },
    },
    {
      component: 'Textarea',
      fieldName: 'collection_description',
      label: $t('views.ai.datasources.collectionDescription'),
      componentProps: {
        placeholder: $t('views.ai.datasources.enterCollectionDescription'),
        rows: 3,
      },
    },
    {
      component: 'Switch',
      fieldName: 'status',
      label: $t('views.ai.datasources.enableStatus'),
    },
  ],
});

const editDataSource = ref<string>('');
const editDetail = ref<any>(null);
const editDataSources = ref<any[]>([]);
const deletedDataSourceIds = ref<string[]>([]);

// 从编辑列表中移除数据源
const removeEditDataSource = (index: number) => {
  const removedDs = editDataSources.value[index];
  if (removedDs && removedDs.id) {
    // 记录要删除的数据源ID
    deletedDataSourceIds.value.push(removedDs.id);
  }
  // 从编辑列表中移除
  editDataSources.value.splice(index, 1);
};

// 在编辑模态框中添加数据源
const addEditDataSource = async (databaseName: string, tableName: string) => {
  const exists = editDataSources.value.some(
    (ds) => ds.database_name === databaseName && ds.table_name === tableName,
  );

  if (!exists) {
    const tableInfo = tableOptions.value.find((t) => t.value === tableName);
    const newDataSource = {
      id: null, // 新添加的数据源没有ID
      database_name: databaseName,
      table_name: tableName,
      description: tableInfo?.description || '',
      originalDescription: '', // 新数据源的原始描述为空
      selected_field: '',
      fields: [],
    };

    editDataSources.value.push(newDataSource);

    // 自动加载该表的字段
    const fields = await loadTableFields(databaseName, tableName);
    const addedDs = editDataSources.value.find(
      (ds) => ds.database_name === databaseName && ds.table_name === tableName && !ds.id,
    );
    if (addedDs) {
      addedDs.fields = fields;
      if (fields.length > 0 && fields[0]) {
        addedDs.selected_field = fields[0].field_name;
      }
    }
  }
};

// 编辑模态框中的数据库和表选择
const editCurrentDatabase = ref<string>('');
const editCurrentTable = ref<string>('');

// 处理编辑模态框中的数据库选择变化
const handleEditDatabaseChange = (databaseName: string) => {
  editCurrentDatabase.value = databaseName;
  editCurrentTable.value = '';
  loadTableOptions(databaseName);
};

// 处理编辑模态框中的添加数据表
const handleEditAddTable = async () => {
  if (editCurrentDatabase.value && editCurrentTable.value) {
    if (
      editDataSources.value.length > 0 &&
      editDataSources.value[0]?.database_name !== editCurrentDatabase.value
    ) {
      message.error($t('views.ai.datasources.onlySameDatabase'));
      return;
    }
    await addEditDataSource(editCurrentDatabase.value, editCurrentTable.value);
    editCurrentTable.value = ''; // 清空选择

    // 添加数据源后，滚动到底部
    nextTick(() => {
      const scrollContainer = document.querySelector('.editModal .space-y-3.max-h-60');
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    });
  }
};

const [editModal, editModalApi] = useVbenModal({
  destroyOnClose: true,
  class: 'w-4/5',
  title: $t('views.ai.datasources.editCollection'),
  async onConfirm() {
    const { valid } = await editFormApi.validate();
    if (valid) {
      editModalApi.lock();
      try {
        const formData = (await editFormApi.getValues()) as {
          collection_description?: string;
          collection_name?: string;
          status?: boolean;
        };

        // 更新集合信息
        await updateDataSourceApi(editDataSource.value, {
          collection_name: formData.collection_name,
          description: formData.collection_description,
          status: formData.status,
        });

        // 更新每个数据源的描述
        for (const ds of editDataSources.value) {
          if (ds.id && (ds.originalDescription !== ds.description || ds.selected_field)) {
            await updateDataSourceApi(ds.id, {
              description: ds.description,
              relation_field: ds.selected_field,
            });
          }
        }

        // 创建新添加的数据源
        const newDataSources = editDataSources.value.filter((ds) => !ds.id);
        if (newDataSources.length > 0) {
          const batchData: BatchCreateDataSourceParams = {
            collection_name: formData.collection_name || editDetail.value.collection_name,
            collection_description: formData.collection_description,
            status: formData.status ?? editDetail.value.status,
            data_sources: newDataSources.map((ds) => ({
              database_name: ds.database_name,
              table_name: ds.table_name,
              description: ds.description,
              relation_field: ds.selected_field,
            })),
          };
          await batchCreateDataSourceApi(batchData);
        }

        // 删除被移除的数据源
        if (deletedDataSourceIds.value.length > 0) {
          await deleteDataSourceApi(deletedDataSourceIds.value);
        }

        await editModalApi.close();
        message.success($t('views.ai.datasources.updateCollectionSuccess'));
        onRefresh();
      } catch (error) {
        console.error(`${$t('views.ai.datasources.updateCollectionFailed')}:`, error);
        message.error($t('views.ai.datasources.updateCollectionFailed'));
      } finally {
        editModalApi.unlock();
      }
    }
  },
  async onOpenChange(isOpen) {
    if (isOpen && editDataSource.value) {
      try {
        // 获取集合详情
        const detail = await getDataSourceApi(editDataSource.value);
        editDetail.value = detail;

        // 初始化可编辑的数据源列表
        editDataSources.value = (detail?.datasources || []).map((ds: any) => ({
          ...ds,
          originalDescription: ds.description || '',
          selected_field: ds.relation_field || '', // 从后端获取已保存的关联字段
          fields: [],
        }));

        // 为现有数据源加载字段信息
        for (const ds of editDataSources.value) {
          if (ds.database_name && ds.table_name) {
            ds.fields = await loadTableFields(ds.database_name, ds.table_name);
          }
        }

        // 重置删除列表和编辑表单变量
        deletedDataSourceIds.value = [];
        if (editDataSources.value.length > 0 && editDataSources.value[0]) {
          handleEditDatabaseChange(editDataSources.value[0].database_name);
        } else {
          handleEditDatabaseChange('');
        }

        await editFormApi.setValues({
          collection_name: detail.collection_name || '',
          collection_description: detail.collection_description || '',
          status: detail.status || false,
        });
      } catch {
        console.error($t('views.ai.datasources.getDetailFailed'));
        message.error($t('views.ai.datasources.getDetailFailed'));
        editModalApi.close();
      }
    }
  },
});

/**
 * 查看详情
 */
const viewDataSource = ref<string>('');
const viewDetail = ref<any>(null);

const [viewModal, viewModalApi] = useVbenModal({
  destroyOnClose: true,
  class: 'w-4/5',
  title: $t('views.ai.datasources.viewCollection'),
  async onOpenChange(isOpen) {
    if (isOpen && viewDataSource.value) {
      try {
        // 获取集合详情
        const detail = await getDataSourceApi(viewDataSource.value);
        viewDetail.value = detail;
      } catch {
        console.error($t('views.ai.datasources.getDetailFailed'));
        message.error($t('views.ai.datasources.getDetailFailed'));
        viewModalApi.close();
      }
    }
  },
});

/**
 * 添加表单 - 集合创建
 */
const [AddForm, addFormApi] = useVbenForm({
  showDefaultActions: false,
  schema: useAddSchema(),
});

// 当前选择的数据库
const currentDatabase = ref<string>('');
// 当前选择的数据表
const currentTable = ref<string>('');

const [addModal, addModalApi] = useVbenModal({
  destroyOnClose: true,
  class: 'w-4/5',
  title: $t('views.ai.datasources.createDataSourceCollection'),
  async onConfirm() {
    if (selectedDataSources.value.length === 0) {
      message.error($t('views.ai.datasources.pleaseSelectAtLeastOneTable'));
      return;
    }

    const { valid } = await addFormApi.validate();
    if (valid) {
      addModalApi.lock();
      const formData = (await addFormApi.getValues()) as {
        collection_description?: string;
        collection_name: string;
        status: boolean;
      };

      try {
        // 使用批量创建API
        const batchData: BatchCreateDataSourceParams = {
          collection_name: formData.collection_name,
          collection_description: formData.collection_description,
          status: formData.status,
          data_sources: selectedDataSources.value.map((ds) => ({
            database_name: ds.database_name,
            table_name: ds.table_name,
            description: ds.description,
            relation_field: ds.selected_field,
          })),
        };

        const result: BatchCreateDataSourceResponse = await batchCreateDataSourceApi(batchData);
        await addModalApi.close();
        message.success(
          $t('views.ai.datasources.createCollectionSuccess', {
            name: result.collection_name,
            count: result.created_count,
          }),
        );
        onRefresh();
        clearSelectedDataSources();
      } finally {
        addModalApi.unlock();
      }
    }
  },
  onOpenChange(isOpen) {
    if (isOpen) {
      addFormApi.resetForm();
      clearSelectedDataSources();
      currentDatabase.value = '';
      currentTable.value = '';
    }
  },
});

// 处理数据库选择变化
const handleDatabaseChange = (databaseName: string) => {
  currentDatabase.value = databaseName;
  currentTable.value = '';
  loadTableOptions(databaseName);
};

// 处理添加数据表
const handleAddTable = () => {
  if (currentDatabase.value && currentTable.value) {
    if (
      selectedDataSources.value.length > 0 &&
      selectedDataSources.value[0]?.database_name !== currentDatabase.value
    ) {
      message.error($t('views.ai.datasources.onlySameDatabase'));
      return;
    }
    addDataSource(currentDatabase.value, currentTable.value);
    currentTable.value = ''; // 清空选择

    // 添加数据源后，滚动到底部
    nextTick(() => {
      const scrollContainer = document.querySelector('.space-y-3.max-h-60');
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    });
  }
};

onMounted(() => {
  // 初始化数据库选项
  loadDatabaseOptions();
});
</script>

<template>
  <Page auto-content-height>
    <Grid>
      <template #toolbar-actions>
        <!-- <VbenButton @click="() => addModalApi.open()">
          <MaterialSymbolsAdd class="size-5" />
          {{ $t('views.ai.datasources.createCollection') }}
        </VbenButton> -->
      </template>
    </Grid>

    <!-- 编辑模态框 -->
    <editModal>
      <div class="space-y-6">
        <!-- 基本信息表单 -->
        <div class="border-b pb-4">
          <h3 class="text-lg font-medium mb-4">{{ $t('views.ai.datasources.collectionInfo') }}</h3>
          <EditForm />
        </div>

        <!-- 包含的数据源列表 -->
        <div>
          <h3 class="text-lg font-medium mb-4">
            {{ $t('views.ai.datasources.includedDataSources') }}
            <span class="text-sm text-gray-500"
              >({{ $t('views.ai.datasources.total', { count: editDataSources.length }) }})</span
            >
          </h3>

          <div v-if="editDataSources.length === 0" class="text-center py-8 text-gray-500">
            <p>{{ $t('views.ai.datasources.noDataSources') }}</p>
          </div>

          <div v-else class="space-y-3 max-h-60 overflow-y-auto">
            <div
              v-for="(ds, index) in editDataSources"
              :key="ds.id"
              class="flex items-center space-x-4 p-3 border rounded-lg bg-gray-50"
            >
              <!-- 数据库和表名 -->
              <div class="flex-shrink-0 min-w-0 flex-1">
                <div class="font-medium text-sm">{{ ds.database_name }}.{{ ds.table_name }}</div>
              </div>

              <!-- 描述 -->
              <div class="flex-1">
                <a-input
                  v-model:value="ds.description"
                  :placeholder="$t('views.ai.datasources.enterDescription')"
                  size="small"
                />
              </div>

              <!-- 删除按钮 -->
              <div class="flex-shrink-0">
                <a-button type="text" danger size="small" @click="removeEditDataSource(index)">
                  {{ $t('common.delete') }}
                </a-button>
              </div>
            </div>
          </div>
        </div>

        <!-- 编辑模式下的字段关联配置 -->
        <div v-if="editDataSources.length > 0" class="border-t pt-4">
          <h3 class="text-lg font-medium mb-4 flex items-center">
            <span class="mr-2">{{ $t('views.ai.datasources.fieldRelationConfig') }}</span>
            <a-tag color="blue" size="small">
              {{ editDataSources.length }} {{ $t('views.ai.datasources.table') }}
            </a-tag>
          </h3>
          <p class="text-sm text-gray-600 mb-4">
            {{ $t('views.ai.datasources.pleaseSelectFieldForEachTable') }}
          </p>

          <!-- 工作流展示区域 -->
          <div class="bg-white border border-gray-200 rounded-lg p-4">
            <div class="flex flex-wrap items-center gap-4">
              <template
                v-for="(ds, index) in editDataSources"
                :key="`edit_field_${ds.database_name}_${ds.table_name}`"
              >
                <!-- 数据源节点 -->
                <div class="flex flex-col items-center">
                  <!-- 表信息 -->
                  <div class="bg-blue-50 border border-blue-200 rounded-lg p-3 min-w-48">
                    <div class="font-medium text-sm text-blue-800 mb-2">
                      {{ ds.database_name }}.{{ ds.table_name }}
                    </div>

                    <!-- 字段选择 -->
                    <div class="space-y-2">
                      <label class="block text-xs font-medium text-gray-700">关联字段</label>
                      <div
                        v-if="isLoadingFields(ds.database_name, ds.table_name)"
                        class="flex items-center justify-center py-2"
                      >
                        <a-spin size="small" />
                        <span class="ml-2 text-xs text-gray-500">{{
                          $t('views.ai.datasources.loadingFields')
                        }}</span>
                      </div>
                      <a-radio-group
                        v-else-if="ds.fields && ds.fields.length > 0"
                        :value="ds.selected_field"
                        size="small"
                        @change="
                          (e: any) => {
                            ds.selected_field = e.target.value;
                          }
                        "
                        class="w-full"
                      >
                        <div class="max-h-32 overflow-y-auto space-y-1">
                          <div
                            v-for="field in ds.fields"
                            :key="field.field_name"
                            class="flex items-center"
                          >
                            <a-radio :value="field.field_name" class="text-xs">
                              <span class="font-mono">{{ field.field_name }}</span>
                              <span class="text-gray-500 ml-1">({{ field.field_type }})</span>
                            </a-radio>
                          </div>
                        </div>
                      </a-radio-group>
                      <div v-else class="text-xs text-gray-500 text-center py-2">
                        {{ $t('views.ai.datasources.noFieldInfo') }}
                      </div>
                    </div>
                  </div>

                  <!-- 选中的字段标签 -->
                  <div
                    v-if="ds.selected_field"
                    class="mt-2 px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium"
                  >
                    {{ ds.selected_field }}
                  </div>
                </div>

                <!-- 箭头连接线 -->
                <div v-if="index < editDataSources.length - 1" class="flex items-center">
                  <div class="flex flex-col items-center">
                    <!-- 水平线 -->
                    <div class="w-8 h-0.5 bg-gray-300"></div>
                    <!-- 箭头 -->
                    <div
                      class="w-0 h-0 border-l-4 border-l-transparent border-r-4 border-r-transparent border-t-4 border-t-gray-400 mt-1"
                    ></div>
                    <!-- 关联标签 -->
                    <div class="mt-1 text-xs text-gray-500 whitespace-nowrap">关联</div>
                  </div>
                </div>
              </template>
            </div>

            <!-- 关联说明 -->
            <div v-if="editDataSources.length > 1" class="mt-4 p-3 bg-gray-50 rounded-lg">
              <div class="flex items-start space-x-2">
                <div
                  class="flex-shrink-0 w-4 h-4 bg-blue-500 rounded-full flex items-center justify-center mt-0.5"
                >
                  <span class="text-white text-xs">i</span>
                </div>
                <div class="text-sm text-gray-700">
                  <p class="font-medium mb-1">
                    {{ $t('views.ai.datasources.relationDescriptionTitle') }}
                  </p>
                  <p>{{ $t('views.ai.datasources.relationExplanation') }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 添加新数据源 -->
        <div class="border-t pt-4">
          <h3 class="text-lg font-medium mb-4">
            {{ $t('views.ai.datasources.addNewDataSource') }}
          </h3>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium mb-2">{{
                $t('views.ai.datasources.database')
              }}</label>
              <a-select
                v-model:value="editCurrentDatabase"
                :placeholder="$t('views.ai.datasources.selectDatabase')"
                class="w-full"
                :dropdown-style="{ maxWidth: '400px' }"
                :disabled="editDataSources.length > 0"
                @change="handleEditDatabaseChange"
              >
                <a-select-option
                  v-for="db in databaseOptions"
                  :key="db.value"
                  :value="db.value"
                  :title="`${db.label}${db.description ? ` (${db.description})` : ''}`"
                >
                  <div class="truncate">
                    {{ db.label }}
                    <template v-if="db.description">（{{ db.description }}）</template>
                  </div>
                </a-select-option>
              </a-select>
            </div>
            <div>
              <label class="block text-sm font-medium mb-2">{{
                $t('views.ai.datasources.table')
              }}</label>
              <div class="flex gap-2">
                <a-select
                  v-model:value="editCurrentTable"
                  :placeholder="$t('views.ai.datasources.selectTableFirst')"
                  class="flex-1"
                  :disabled="!editCurrentDatabase"
                  :dropdown-style="{ maxWidth: '400px' }"
                >
                  <a-select-option
                    v-for="table in tableOptions"
                    :key="table.value"
                    :value="table.value"
                    :title="`${table.label}${table.description ? ` (${table.description})` : ''}`"
                  >
                    <div class="truncate">
                      {{ table.label }}
                      <template v-if="table.description">（{{ table.description }}）</template>
                    </div>
                  </a-select-option>
                </a-select>
                <a-button type="primary" :disabled="!editCurrentTable" @click="handleEditAddTable">
                  {{ $t('views.ai.datasources.addDataSource') }}
                </a-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </editModal>

    <!-- 查看详情模态框 -->
    <viewModal>
      <div v-if="viewDetail" class="space-y-6">
        <!-- 基本信息 -->
        <div class="border-b pb-4">
          <h3 class="text-lg font-medium mb-4">{{ $t('views.ai.datasources.collectionInfo') }}</h3>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700">{{
                $t('views.ai.datasources.collectionName')
              }}</label>
              <div class="mt-1 text-sm text-gray-900">{{ viewDetail.collection_name || '-' }}</div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">{{
                $t('views.ai.datasources.status')
              }}</label>
              <div class="mt-1">
                <a-tag :color="viewDetail.status ? 'green' : 'red'">
                  {{ viewDetail.status ? '启用' : '禁用' }}
                </a-tag>
              </div>
            </div>
            <div class="col-span-2">
              <label class="block text-sm font-medium text-gray-700">{{
                $t('views.ai.datasources.collectionDescription')
              }}</label>
              <div class="mt-1 text-sm text-gray-900">
                {{ viewDetail.collection_description || '-' }}
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">{{
                $t('views.ai.datasources.dataSourceCount')
              }}</label>
              <div class="mt-1 text-sm text-gray-900">
                {{ viewDetail.data_sources_count || 0 }}
                {{ $t('views.ai.datasources.dataSourceCountUnit') }}
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">{{
                $t('common.createdTime')
              }}</label>
              <div class="mt-1 text-sm text-gray-900">{{ viewDetail.created_time || '-' }}</div>
            </div>
          </div>
        </div>

        <!-- 包含的数据源列表 -->
        <div>
          <h3 class="text-lg font-medium mb-4">
            {{ $t('views.ai.datasources.includedDataSources') }}
            <span class="text-sm text-gray-500"
              >({{
                $t('views.ai.datasources.total', { count: viewDetail.datasources?.length || 0 })
              }})</span
            >
          </h3>

          <div
            v-if="!viewDetail.datasources || viewDetail.datasources.length === 0"
            class="text-center py-8 text-gray-500"
          >
            <p>{{ $t('views.ai.datasources.noDataSources') }}</p>
          </div>

          <div v-else class="space-y-3 max-h-60">
            <div
              v-for="ds in viewDetail.datasources"
              :key="ds.id"
              class="flex items-center space-x-4 p-3 border rounded-lg bg-gray-50"
            >
              <!-- 数据库和表名 -->
              <div class="flex-shrink-0 min-w-0 flex-1">
                <div class="font-medium text-sm">{{ ds.database_name }}.{{ ds.table_name }}</div>
              </div>

              <!-- 描述 -->
              <div class="flex-1">
                <div class="text-sm text-gray-600">
                  {{ ds.description || $t('views.ai.datasources.noDescription') }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </viewModal>

    <!-- 添加模态框 - 集合创建 -->
    <addModal>
      <div class="space-y-6">
        <!-- 基本信息表单 -->
        <div class="border-b pb-4">
          <h3 class="text-lg font-medium mb-4">{{ $t('views.ai.datasources.collectionInfo') }}</h3>
          <AddForm />
        </div>

        <!-- 数据库和表选择 -->
        <div class="border-b pb-4">
          <h3 class="text-lg font-medium mb-4">
            {{ $t('views.ai.datasources.selectDataSource') }}
            <span class="text-sm text-gray-500"
              >({{
                $t('views.ai.datasources.selectedCount', { count: selectedDataSources.length })
              }})</span
            >
          </h3>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium mb-2">{{
                $t('views.ai.datasources.database')
              }}</label>
              <a-select
                v-model:value="currentDatabase"
                :placeholder="$t('views.ai.datasources.selectDatabase')"
                class="w-full"
                :dropdown-style="{ maxWidth: '400px' }"
                :disabled="selectedDataSources.length > 0"
                @change="handleDatabaseChange"
              >
                <a-select-option
                  v-for="db in databaseOptions"
                  :key="db.value"
                  :value="db.value"
                  :title="`${db.label}${db.description ? ` (${db.description})` : ''}`"
                >
                  <div class="truncate">
                    {{ db.label }}
                    <template v-if="db.description">（{{ db.description }}）</template>
                  </div>
                </a-select-option>
              </a-select>
            </div>
            <div>
              <label class="block text-sm font-medium mb-2">{{
                $t('views.ai.datasources.table')
              }}</label>
              <div class="flex gap-2">
                <a-select
                  v-model:value="currentTable"
                  :placeholder="$t('views.ai.datasources.selectTableFirst')"
                  class="flex-1"
                  :disabled="!currentDatabase"
                  :dropdown-style="{ maxWidth: '400px' }"
                >
                  <a-select-option
                    v-for="table in tableOptions"
                    :key="table.value"
                    :value="table.value"
                    :title="`${table.label}${table.description ? ` (${table.description})` : ''}`"
                  >
                    <div class="truncate">
                      {{ table.label }}
                      <template v-if="table.description">（{{ table.description }}）</template>
                    </div>
                  </a-select-option>
                </a-select>
                <a-button type="primary" :disabled="!currentTable" @click="handleAddTable">
                  {{ $t('views.ai.datasources.addDataSource') }}
                </a-button>
              </div>
            </div>
          </div>
        </div>

        <!-- 已选择的数据源列表 -->
        <div>
          <h3 class="text-lg font-medium mb-4">
            {{ $t('views.ai.datasources.selectedDataSources') }}
          </h3>

          <div v-if="selectedDataSources.length === 0" class="text-center py-8 text-gray-500">
            <p>{{ $t('views.ai.datasources.pleaseSelectTableAsDataSource') }}</p>
            <p class="text-sm mt-2">{{ $t('views.ai.datasources.atLeastOneTable') }}</p>
          </div>

          <div v-else class="space-y-3 max-h-60 overflow-y-auto">
            <div
              v-for="(ds, index) in selectedDataSources"
              :key="`${ds.database_name}_${ds.table_name}`"
              class="flex items-center space-x-4 p-3 border rounded-lg bg-gray-50"
            >
              <!-- 数据库和表名 -->
              <div class="flex-shrink-0 min-w-0 flex-1">
                <div class="font-medium text-sm">{{ ds.database_name }}.{{ ds.table_name }}</div>
              </div>

              <!-- 描述输入框 -->
              <div class="flex-1">
                <a-input
                  :value="ds.description"
                  :placeholder="$t('views.ai.datasources.enterDescription')"
                  size="small"
                  @input="
                    (e: Event) =>
                      updateDataSourceDescription(index, (e.target as HTMLInputElement).value)
                  "
                />
              </div>

              <!-- 删除按钮 -->
              <div class="flex-shrink-0">
                <a-button type="text" danger size="small" @click="removeDataSource(index)">
                  {{ $t('common.delete') }}
                </a-button>
              </div>
            </div>
          </div>
        </div>

        <!-- 字段关联配置 -->
        <div v-if="selectedDataSources.length > 0" class="border-t pt-6">
          <h3 class="text-lg font-medium mb-4 flex items-center">
            <span class="mr-2">{{ $t('views.ai.datasources.fieldRelationConfig') }}</span>
            <a-tag color="blue" size="small">
              {{ selectedDataSources.length }} {{ $t('views.ai.datasources.table') }}
            </a-tag>
          </h3>
          <p class="text-sm text-gray-600 mb-4">
            {{ $t('views.ai.datasources.pleaseSelectFieldForEachTable') }}
          </p>

          <!-- 工作流展示区域 -->
          <div class="bg-white border border-gray-200 rounded-lg p-4">
            <div class="flex flex-wrap items-center gap-4">
              <template
                v-for="(ds, index) in selectedDataSources"
                :key="`field_${ds.database_name}_${ds.table_name}`"
              >
                <!-- 数据源节点 -->
                <div class="flex flex-col items-center">
                  <!-- 表信息 -->
                  <div class="bg-blue-50 border border-blue-200 rounded-lg p-3 min-w-48">
                    <div class="font-medium text-sm text-blue-800 mb-2">
                      {{ ds.database_name }}.{{ ds.table_name }}
                    </div>

                    <!-- 字段选择 -->
                    <div class="space-y-2">
                      <label class="block text-xs font-medium text-gray-700">关联字段</label>
                      <div
                        v-if="isLoadingFields(ds.database_name, ds.table_name)"
                        class="flex items-center justify-center py-2"
                      >
                        <a-spin size="small" />
                        <span class="ml-2 text-xs text-gray-500">{{
                          $t('views.ai.datasources.loadingFields')
                        }}</span>
                      </div>
                      <a-radio-group
                        v-else-if="ds.fields && ds.fields.length > 0"
                        :value="ds.selected_field"
                        size="small"
                        @change="
                          (e: any) => {
                            ds.selected_field = e.target.value;
                          }
                        "
                        class="w-full"
                      >
                        <div class="max-h-32 overflow-y-auto space-y-1">
                          <div
                            v-for="field in ds.fields"
                            :key="field.field_name"
                            class="flex items-center"
                          >
                            <a-radio :value="field.field_name" class="text-xs">
                              <span class="font-mono">{{ field.field_name }}</span>
                              <span class="text-gray-500 ml-1">({{ field.field_type }})</span>
                            </a-radio>
                          </div>
                        </div>
                      </a-radio-group>
                      <div v-else class="text-xs text-gray-500 text-center py-2">
                        {{ $t('views.ai.datasources.noFieldInfo') }}
                      </div>
                    </div>
                  </div>

                  <!-- 选中的字段标签 -->
                  <div
                    v-if="ds.selected_field"
                    class="mt-2 px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium"
                  >
                    {{ ds.selected_field }}
                  </div>
                </div>

                <!-- 箭头连接线 -->
                <div v-if="index < selectedDataSources.length - 1" class="flex items-center">
                  <div class="flex flex-col items-center">
                    <!-- 水平线 -->
                    <div class="w-8 h-0.5 bg-gray-300"></div>
                    <!-- 箭头 -->
                    <div
                      class="w-0 h-0 border-l-4 border-l-transparent border-r-4 border-r-transparent border-t-4 border-t-gray-400 mt-1"
                    ></div>
                    <!-- 关联标签 -->
                    <div class="mt-1 text-xs text-gray-500 whitespace-nowrap">关联</div>
                  </div>
                </div>
              </template>
            </div>

            <!-- 关联说明 -->
            <div v-if="selectedDataSources.length > 1" class="mt-4 p-3 bg-gray-50 rounded-lg">
              <div class="flex items-start space-x-2">
                <div
                  class="flex-shrink-0 w-4 h-4 bg-blue-500 rounded-full flex items-center justify-center mt-0.5"
                >
                  <span class="text-white text-xs">i</span>
                </div>
                <div class="text-sm text-gray-700">
                  <p class="font-medium mb-1">
                    {{ $t('views.ai.datasources.relationDescriptionTitle') }}
                  </p>
                  <p>{{ $t('views.ai.datasources.relationExplanation') }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </addModal>
  </Page>
</template>
