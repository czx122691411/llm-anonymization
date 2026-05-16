/**
 * PageHeader - 统一的页面头部组件
 *
 * 包含面包屑导航、页面标题、描述和操作按钮
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { Breadcrumb, BreadcrumbItem } from './Breadcrumb';

interface PageHeaderProps {
  title: string;
  description?: string;
  breadcrumbs?: BreadcrumbItem[];
  showBackButton?: boolean;
  backPath?: string;
  actions?: React.ReactNode;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  description,
  breadcrumbs,
  showBackButton = true,
  backPath = -1,
  actions
}) => {
  const navigate = useNavigate();

  const handleBack = () => {
    if (typeof backPath === 'number' && backPath === -1) {
      navigate(-1);
    } else {
      navigate(backPath as string);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
        {/* 面包屑和返回按钮 */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-4">
            {showBackButton && (
              <button
                onClick={handleBack}
                className="flex items-center text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800 px-3 py-2 rounded-lg transition-colors"
                aria-label="返回"
              >
                <ArrowLeft className="w-4 h-4 mr-1" />
                <span className="text-sm">返回</span>
              </button>
            )}

            {breadcrumbs && (
              <div className="hidden sm:block">
                <Breadcrumb items={breadcrumbs} />
              </div>
            )}
          </div>

          {actions && (
            <div className="flex items-center gap-2">
              {actions}
            </div>
          )}
        </div>

        {/* 页面标题和描述 */}
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-slate-100">
            {title}
          </h1>
          {description && (
            <p className="mt-1 text-base text-slate-600 dark:text-slate-400">
              {description}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
