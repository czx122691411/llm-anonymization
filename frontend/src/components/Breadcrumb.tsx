/**
 * Breadcrumb - 面包屑导航组件
 *
 * 显示当前页面路径，支持快速返回上级页面
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';

export interface BreadcrumbItem {
  label: string;
  path: string;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
  homePath?: string;
  homeLabel?: string;
}

export const Breadcrumb: React.FC<BreadcrumbProps> = ({
  items,
  homePath = '/',
  homeLabel = '首页'
}) => {
  // 确保首页在路径开头
  const allItems = items[0]?.path === homePath
    ? items
    : [{ label: homeLabel, path: homePath }, ...items];

  return (
    <nav className="flex items-center space-x-1 text-sm" aria-label="面包屑导航">
      {allItems.map((item, index) => (
        <React.Fragment key={item.path}>
          {index > 0 && (
            <ChevronRight className="w-4 h-4 text-slate-400 flex-shrink-0" />
          )}

          {index === allItems.length - 1 ? (
            // 当前页面
            <span className="text-slate-900 dark:text-slate-100 font-medium">
              {item.label}
            </span>
          ) : (
            // 可点击的路径
            <Link
              to={item.path}
              className="flex items-center text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 transition-colors"
            >
              {index === 0 && (
                <Home className="w-4 h-4 mr-1" />
              )}
              <span>{item.label}</span>
            </Link>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
};
