const routes = [
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'), // исправлено на MainLayout
    children: [
      { path: '', component: () => import('pages/IndexPage.vue') },
    ]
  },
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue')
  }
]

export default routes
