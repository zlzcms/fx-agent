export const extraMenu = [

  // 一级菜单:ai助理
  {
    id: '100',
    name: 'Aiassistant',
    path: 'Aiassistant',
    sort: 100,
    type: 0,
    perms: null,
    remark: null,
    parent_id: null,
    created_time: "2025-06-11T06:08:20.926046Z",
    updated_time: null,
    meta: {
      title: 'AI助理',
      icon: "ant-design:reddit-outlined",
      iframeSrc: "",
      link: "",
      keepAlive: true,
      hideInMenu: false,
      menuVisibleWithForbidden: false
    },
    children: [
      {
        id: 101,
        name: 'AiassistantQa',
        path: 'Aiassistant-qa',
        component: '/aiassistant/qa/index',
        sort: 0,
        type: 1,
        parent_id: 100,
        meta: {
          title: 'AI问答',
          hideInMenu: false,
          menuVisibleWithForbidden: false,
        },
      },
      {
        id: 102,
        name: 'AiassistantReports',
        path: 'Aiassistant-reports',
        component: '/aiassistant/reports/index',
        sort: 1,
        parent_id: 100,
        type: 1,
        meta: {
          title: 'AI报告',
          hideInMenu: false,
          menuVisibleWithForbidden: false,
        },
      },
      {
        id: 201,
        name: 'ReportsFinance',
        path: 'reports-finance',
        component: '/aiassistant/reports/index2',
        sort: 0,
        type: 1,
        parent_id: 200,
        meta: {
          title: '财务报表',
          hideInMenu: false,
          menuVisibleWithForbidden: false,
        },
      },
      {
        id: 202,
        name: 'AIReportDetail',
        path: '/aiassistant/reports/detail',
        component: '/aiassistant/reports/index3',
        meta: {
          title: '财务报表详情',
          hideInMenu: false,
          menuVisibleWithForbidden: false,
        },
      },
    ],
  }
]
