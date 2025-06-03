const routes = [
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'), // исправлено на MainLayout
    children: [
      { path: '', component: () => import('pages/IndexPage.vue') },
      { path: 'test-list', component: () => import('src/components/TestList.vue') } // рекомендуем использовать kebab-case для URL
    ]
  },
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue')
  }
]

export default routes
