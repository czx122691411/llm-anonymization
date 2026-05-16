/**
 * SideNavigation - 侧边导航组件
 *
 * 支持展开/收起和移动端弹出菜单
 */

import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { X, Menu, ChevronLeft } from 'lucide-react';

interface NavItem {
  path: string;
  icon: string;
  label: string;
  gradient: string;
}

const NAV_ITEMS: NavItem[] = [
  { path: '/chinese-demo', icon: '🇨🇳', label: '中文演示', gradient: 'from-amber-500 to-orange-600' },
  { path: '/custom-test', icon: '✏️', label: '自定义测试', gradient: 'from-rose-500 to-pink-600' },
  { path: '/trace-rps-dashboard', icon: '🔒', label: 'TRACE-RPS', gradient: 'from-blue-600 to-purple-600' },
  { path: '/deepseek-5rounds', icon: '🎯', label: 'DeepSeek 5轮', gradient: 'from-emerald-600 to-teal-600' },
  { path: '/training-visualization', icon: '📊', label: 'Training Plots', gradient: 'bg-slate-600' },
];

interface SideNavigationProps {
  children: React.ReactNode;
}

export const SideNavigation: React.FC<SideNavigationProps> = ({ children }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const location = useLocation();

  // 路由变化时关闭移动端菜单
  useEffect(() => {
    setIsOpen(false);
  }, [location.pathname]);

  // 阻止body滚动当菜单打开时
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  const toggleMenu = () => setIsOpen(!isOpen);
  const toggleCollapse = () => setIsCollapsed(!isCollapsed);

  // 判断当前路由是否激活
  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="flex min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* 移动端顶部栏 */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
        <div className="flex items-center justify-between px-4 py-3">
          {/* 汉堡菜单按钮 */}
          <button
            onClick={toggleMenu}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            aria-label="打开菜单"
          >
            {isOpen ? <X className="w-6 h-6 text-gray-600 dark:text-gray-400" /> : <Menu className="w-6 h-6 text-gray-600 dark:text-gray-400" />}
          </button>

          {/* 标题 */}
          <h1 className="text-lg font-bold text-gray-900 dark:text-gray-100">
            LLM Anonymization
          </h1>
        </div>
      </div>

      {/* 桌面端侧边栏 */}
      <aside
        className={`
          fixed lg:static inset-y-0 left-0 z-40
          w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800
          transition-transform duration-300 ease-in-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
          lg:translate-x-0
          ${isCollapsed ? 'lg:w-20' : 'lg:w-64'}
        `}
      >
        {/* 侧边栏头部 */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-800">
          {!isCollapsed && (
            <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
              导航菜单
            </h2>
          )}
          <button
            onClick={toggleCollapse}
            className="hidden lg:flex p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            aria-label={isCollapsed ? '展开菜单' : '收起菜单'}
          >
            <ChevronLeft className={`w-5 h-5 text-gray-600 dark:text-gray-400 transition-transform ${isCollapsed ? 'rotate-180' : ''}`} />
          </button>
        </div>

        {/* 导航列表 */}
        <nav className="p-4 space-y-2">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`
                w-full px-4 py-3 rounded-lg transition-all flex items-center gap-3 text-sm font-medium
                ${isActive(item.path)
                  ? 'bg-gradient-to-r from-violet-500 to-purple-600 text-white shadow-lg'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                }
                ${isCollapsed ? 'lg:justify-center' : ''}
              `}
              onClick={() => setIsOpen(false)}
            >
              <span className={`text-lg ${isCollapsed ? 'lg:hidden' : ''}`}>{item.icon}</span>
              {!isCollapsed && <span>{item.label}</span>}
            </Link>
          ))}
        </nav>

        {/* 侧边栏底部 */}
        <div className="mt-auto p-4 border-t border-gray-200 dark:border-gray-800">
          {!isCollapsed && (
            <div className="text-xs text-gray-500 dark:text-gray-400">
              © 2026 LLM Anonymization
            </div>
          )}
        </div>
      </aside>

      {/* 移动端遮罩层 */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={toggleMenu}
          aria-hidden="true"
        />
      )}

      {/* 主内容区 */}
      <div className="flex-1 flex flex-col min-h-screen">
        {/* 桌面端头部 */}
        <header className="hidden lg:block bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
          <div className="px-8 py-6">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              LLM Anonymization Visualizer
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              探索和分析文本匿名化结果
            </p>
          </div>
        </header>

        {/* 页面内容 */}
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
};
