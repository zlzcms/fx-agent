import type { RiskReportItem } from '@vben/types';

import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn, VxeGridProps } from '#/adapter/vxe-table';

import { FILE_SIZE_LIMIT } from '@vben/constants';
import { $t } from '@vben/locales';

import { message } from 'ant-design-vue';

import { z } from '#/adapter/form';
import { RiskType } from '#/api/risk';
import { useRiskStore } from '#/store/risk';

// 风险类型配置
export interface RiskConfig {
  riskType: RiskType;
  i18nPrefix: string;
}

// 文件上传前的验证
export const beforeUpload = (file: File, i18nPrefix: string) => {
  // 检查文件类型
  const allowedTypes = ['image/png', 'image/jpg', 'image/jpeg'];
  const isValidType = allowedTypes.includes(file.type);
  if (!isValidType) {
    message.error($t(`${i18nPrefix}.invalidFileType`));
    return false;
  }

  // 检查文件大小
  const isValidSize = file.size / 1024 / 1024 < FILE_SIZE_LIMIT;
  if (!isValidSize) {
    message.error($t(`${i18nPrefix}.fileSizeExceeded`, { maxSize: FILE_SIZE_LIMIT }));
    return false;
  }

  // 检查图片尺寸（可选）
  return new Promise((resolve) => {
    const img = new Image();
    img.addEventListener('load', () => {
      const { width, height } = img;
      if (width < 100 || height < 100) {
        message.error($t(`${i18nPrefix}.imageTooSmall`));
        resolve(false);
      } else if (width > 4096 || height > 4096) {
        message.error($t(`${i18nPrefix}.imageTooBig`));
        resolve(false);
      } else {
        resolve(false); // 阻止自动上传，由表单统一处理
      }
    });
    img.addEventListener('error', () => {
      message.error($t(`${i18nPrefix}.imageReadError`));
      resolve(false);
    });
    img.src = URL.createObjectURL(file);
  });
};

export function createQuerySchema(i18nPrefix: string, riskType?: RiskType): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'member_id',
      label: $t(`${i18nPrefix}.memberID`),
      componentProps: {
        placeholder: $t(`${i18nPrefix}.enterMemberID`),
        clearable: true,
      },
    },
    {
      component: 'Input',
      fieldName: 'member_name',
      label: $t(`${i18nPrefix}.memberName`),
      componentProps: {
        placeholder: $t(`${i18nPrefix}.enterMemberName`),
        clearable: true,
      },
    },
    {
      component: 'ApiSelect',
      fieldName: 'risk_level_id',
      label: $t('@risk-customer.riskLevel'),
      componentProps: {
        placeholder: $t('@risk-customer.selectRiskLevel'),
        allowClear: true,
        mode: 'multiple',
        api: () => useRiskStore().fetchRiskLevels(),
        labelField: 'name',
        valueField: 'id',
        resultField: '',
      },
    },
    {
      component: 'ApiSelect',
      fieldName: 'risk_tags',
      label: $t('@risk-customer.riskTag'),
      componentProps: {
        placeholder: $t('@risk-customer.selectRiskTag'),
        allowClear: true,
        mode: 'multiple',
        api: async () => {
          const allTags = await useRiskStore().fetchRiskTags();
          if (riskType === RiskType.ALL_EMPLOYEE) {
            const filteredTags = allTags.filter((tag) => tag.risk_type === RiskType.ALL_EMPLOYEE);
            return filteredTags;
          } else if (riskType === RiskType.CRM_USER) {
            const filteredTags = allTags.filter((tag) => tag.risk_type === RiskType.CRM_USER);
            return filteredTags;
          } else {
            return allTags;
          }
        },
        labelField: 'name',
        valueField: 'id',
        resultField: '',
      },
    },
    {
      component: 'Select',
      fieldName: 'is_processed',
      label: $t('@risk-customer.processStatus'),
      componentProps: {
        placeholder: $t('@risk-customer.selectProcessStatus'),
        allowClear: true,
        options: [
          {
            label: $t('@risk-customer.processed'),
            value: true,
          },
          {
            label: $t('@risk-customer.unprocessed'),
            value: false,
          },
        ],
      },
    },
  ];
}

export function createColumns(
  i18nPrefix: string,
  onActionClick?: OnActionClickFn<RiskReportItem>,
): VxeGridProps['columns'] {
  return [
    // 屏蔽序号列
    // {
    //   field: 'id',
    //   width: 100,
    //   fixed: 'left',
    //   title: $t('@risk.risk-customer.seq'),
    // },
    {
      field: 'member_id',
      title: $t(`${i18nPrefix}.memberID`),
      minWidth: 120,
    },
    {
      field: 'member_name',
      title: $t(`${i18nPrefix}.memberName`),
      minWidth: 120,
      slots: {
        default: 'memberName',
      },
    },
    {
      field: 'risk_level',
      title: $t('@risk-customer.riskLevel'),
      minWidth: 120,
      slots: {
        default: 'riskLevel',
      },
    },
    {
      field: 'created_time',
      title: $t('@risk-customer.riskTime'),
      width: 160,
    },
    {
      field: 'report_tags',
      title: $t('@risk-customer.riskTag'),
      minWidth: 220,
      maxWidth: 350,
      resizable: true,
      showOverflow: false, // 禁用省略号，让内容完整显示
      slots: {
        default: 'rick_tags',
      },
    },
    {
      field: 'description',
      title: $t('@risk-customer.description'),
      minWidth: 250,
      maxWidth: 400,
      resizable: true,
      showOverflow: 'tooltip',
    },
    {
      field: 'analysis_type',
      title: $t('@risk-customer.analysisType'),
      minWidth: 120,
      showOverflow: 'tooltip',
    },
    {
      field: 'trigger_sources',
      title: $t('@risk-customer.triggerSources'),
      minWidth: 120,
      showOverflow: 'tooltip',
    },
    {
      field: 'detection_window_info',
      title: $t('@risk-customer.detectionWindowInfo'),
      minWidth: 150,
      showOverflow: 'tooltip',
    },
    {
      field: 'handle_suggestion',
      title: $t('@risk-customer.recommendedAction'),
      minWidth: 300,
      showOverflow: 'tooltip',
    },
    {
      field: 'is_processed',
      title: $t('@risk-customer.processStatus'),
      width: 120,
      slots: {
        default: 'riskStatus',
      },
    },
    {
      field: 'handle_result',
      title: $t('@risk-customer.processResult'),
      width: 150,
      slots: {
        default: 'handle_result',
      },
    },
    {
      field: 'handle_user',
      title: $t('@risk-customer.processUser'),
      width: 120,
      slots: {
        default: 'handle_user',
      },
    },
    {
      field: 'handle_time',
      title: $t('@risk-customer.processTime'),
      width: 160,
    },
    {
      field: 'operation',
      title: $t('@risk-customer.operation'),
      align: 'center',
      fixed: 'right',
      width: 240,
      cellRender: {
        attrs: {
          onClick: onActionClick,
        },
        name: 'CellOperation',
        options: [
          {
            code: 'view',
            text: $t('@risk-customer.viewReport'),
          },
          {
            code: 'prompt',
            text: $t('@risk-customer.viewLog'),
          },
          {
            code: 'operation',
            text: $t('@risk-customer.handleNow'),
            disabled: (row: RiskReportItem) => row?.is_processed || false,
          },
        ],
      },
    },
  ];
}

// 处理表单配置
export function createProcessFormSchema(_i18nPrefix: string): VbenFormSchema[] {
  return [
    {
      component: 'Textarea',
      fieldName: 'handle_result',
      label: $t('@risk-customer.processResult'),
      componentProps: {
        placeholder: $t('@risk-customer.enterProcessResult'),
        rows: 4,
        maxlength: 500,
        showCount: true,
        style: { width: '100%' },
      },
      rules: z
        .string()
        .min(1, { message: $t('@risk-customer.enterProcessResult') })
        .max(500, { message: $t('@risk-customer.processResultMaxLength') }),
    },
    // 暂时屏蔽的其他选项
    // {
    //   component: 'RadioGroup',
    //   fieldName: 'processStatus',
    //   label: $t('@risk.risk-customer.processResult'),
    //   componentProps: {
    //     options: [
    //       { label: $t('@risk.risk-customer.processed'), value: '已处理' },
    //       { label: $t('@risk.risk-customer.unprocessed'), value: '无需处理' },
    //     ],
    //   },
    //   rules: z.string().min(1, { message: $t('@risk.risk-customer.selectProcessResult') }),
    //   defaultValue: $t('@risk.risk-customer.processed'),
    // },
    // {
    //   component: 'RadioGroup',
    //   fieldName: 'processReason',
    //   label: $t('@risk.risk-customer.processReason'),
    //   componentProps: {
    //     options: [
    //       { label: $t('@risk.risk-customer.situation1'), value: '情况1' },
    //       { label: $t('@risk.risk-customer.situation2'), value: '情况2' },
    //       { label: $t('@risk.risk-customer.situation3'), value: '情况3' },
    //     ],
    //   },
    //   rules: z.string().min(1, { message: $t('@risk.risk-customer.selectProcessReason') }),
    //   defaultValue: $t('@risk.risk-customer.situation1'),
    // },
    // {
    //   component: 'Textarea',
    //   fieldName: 'processComment',
    //   label: $t('@risk.risk-customer.processComment'),
    //   componentProps: {
    //     placeholder: $t('@risk.risk-customer.processCommentPlaceholder'),
    //     rows: 4,
    //     maxlength: 500,
    //     showCount: true,
    //   },
    //   rules: z.string().min(10, { message: $t('@risk.risk-customer.processCommentMinLength') }).max(500, { message: $t('@risk.risk-customer.processCommentMaxLength') }),
    // },
    // {
    //   component: 'Upload',
    //   fieldName: 'uploadFiles',
    //   label: $t('@risk.risk-customer.uploadImages'),
    //   componentProps: {
    //     accept: '.png,.jpg,.jpeg',
    //     disabled: false,
    //     maxCount: MAX_UPLOAD_COUNT,
    //     multiple: false,
    //     showUploadList: true,
    //     listType: 'picture-card',
    //     beforeUpload: (file: File) => beforeUpload(file, i18nPrefix),
    //   },
    //   renderComponentContent: () => ({
    //     default: () => h('div', {
    //       style: {
    //         display: 'flex',
    //         flexDirection: 'column',
    //         alignItems: 'center',
    //         justifyContent: 'center',
    //         height: '100%',
    //         color: '#666',
    //         cursor: 'pointer',
    //       }
    //     }, [
    //       h('div', { style: { fontSize: '24px', marginBottom: '8px' } }, '+'),
    //       h('div', { style: { fontSize: '14px' } }, $t(`${i18nPrefix}.uploadImages`))
    //     ]),
    //   }),
    //   rules: z.array(z.any()).min(1, { message: $t(`${i18nPrefix}.uploadImagesRequired`, { maxCount: MAX_UPLOAD_COUNT, maxSize: FILE_SIZE_LIMIT }) }),
    // },
  ];
}
