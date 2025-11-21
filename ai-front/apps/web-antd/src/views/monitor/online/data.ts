import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn, VxeGridProps } from '#/adapter/vxe-table';
import type { OnlineMonitorResult } from '#/api';

import { $t } from '@vben/locales';

export const querySchema: VbenFormSchema[] = [
  {
    component: 'Input',
    fieldName: 'username',
    label: $t('views.monitor.online.username'),
  },
];

export function useColumns(
  onActionClick?: OnActionClickFn<OnlineMonitorResult>,
): VxeGridProps['columns'] {
  return [
    {
      field: 'seq',
      title: $t('page.table.id'),
      type: 'seq',
      width: 50,
    },
    { field: 'session_uuid', title: $t('views.monitor.online.sessionUuid'), width: 280 },
    { field: 'username', title: $t('views.monitor.online.username') },
    { field: 'nickname', title: $t('views.monitor.online.nickname') },
    { field: 'ip', title: $t('views.monitor.online.ipAddress') },
    { field: 'os', title: $t('views.monitor.online.operatingSystem') },
    { field: 'browser', title: $t('views.monitor.online.browser') },
    { field: 'device', title: $t('views.monitor.online.device') },
    {
      field: 'status',
      title: $t('views.monitor.online.status'),
      cellRender: {
        name: 'CellTag',
        options: [
          { color: 'success', label: $t('views.monitor.online.online'), value: 1 },
          { color: 'warning', label: $t('views.monitor.online.offline'), value: 0 },
        ],
      },
    },
    { field: 'last_login_time', title: $t('views.monitor.online.lastLoginTime') },
    { field: 'expire_time', title: $t('views.monitor.online.expireTime') },
    {
      field: 'operation',
      title: $t('page.table.operation'),
      align: 'center',
      fixed: 'right',
      width: 130,
      cellRender: {
        attrs: {
          nameField: 'nickname',
          onClick: onActionClick,
        },
        name: 'CellOperation',
        options: [
          {
            code: 'delete',
            text: $t('views.monitor.online.forceOffline'),
          },
        ],
      },
    },
  ];
}
