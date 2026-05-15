/**
 * DataCard - A reusable metric card component with icon, value, and trend
 * Displays key metrics with smooth number animations
 */

import React, { useEffect, useRef, useState } from 'react';
import { LucideIcon } from 'lucide-react';

interface DataCardProps {
  /** Card title */
  title: string;
  /** Main value to display */
  value: number | string;
  /** Unit suffix (e.g., '%', 's', '$') */
  unit?: string;
  /** Icon component */
  icon?: LucideIcon;
  /** Trend percentage (positive or negative) */
  trend?: number;
  /** Color theme */
  color?: 'blue' | 'green' | 'purple' | 'amber' | 'red' | 'emerald';
  /** Additional subtitle */
  subtitle?: string;
  /** Whether to animate the number */
  animate?: boolean;
  /** Custom className */
  className?: string;
}

const colorStyles = {
  blue: {
    bg: 'bg-blue-50 dark:bg-blue-900/20',
    iconBg: 'bg-blue-100 dark:bg-blue-900/30',
    iconColor: 'text-blue-600 dark:text-blue-400',
    textColor: 'text-blue-700 dark:text-blue-300',
  },
  green: {
    bg: 'bg-green-50 dark:bg-green-900/20',
    iconBg: 'bg-green-100 dark:bg-green-900/30',
    iconColor: 'text-green-600 dark:text-green-400',
    textColor: 'text-green-700 dark:text-green-300',
  },
  purple: {
    bg: 'bg-purple-50 dark:bg-purple-900/20',
    iconBg: 'bg-purple-100 dark:bg-purple-900/30',
    iconColor: 'text-purple-600 dark:text-purple-400',
    textColor: 'text-purple-700 dark:text-purple-300',
  },
  amber: {
    bg: 'bg-amber-50 dark:bg-amber-900/20',
    iconBg: 'bg-amber-100 dark:bg-amber-900/30',
    iconColor: 'text-amber-600 dark:text-amber-400',
    textColor: 'text-amber-700 dark:text-amber-300',
  },
  red: {
    bg: 'bg-red-50 dark:bg-red-900/20',
    iconBg: 'bg-red-100 dark:bg-red-900/30',
    iconColor: 'text-red-600 dark:text-red-400',
    textColor: 'text-red-700 dark:text-red-300',
  },
  emerald: {
    bg: 'bg-emerald-50 dark:bg-emerald-900/20',
    iconBg: 'bg-emerald-100 dark:bg-emerald-900/30',
    iconColor: 'text-emerald-600 dark:text-emerald-400',
    textColor: 'text-emerald-700 dark:text-emerald-300',
  },
};

/**
 * Animated number component with easing
 */
const AnimatedNumber: React.FC<{ value: number; duration?: number; decimals?: number }> = ({
  value,
  duration = 300,
  decimals = 1,
}) => {
  const [displayValue, setDisplayValue] = useState(0);
  const startTimeRef = useRef<number>();
  const startValueRef = useRef(0);
  const animationFrameRef = useRef<number>();

  useEffect(() => {
    startTimeRef.current = performance.now();
    startValueRef.current = displayValue;

    const animate = (currentTime: number) => {
      if (!startTimeRef.current) return;

      const elapsed = currentTime - startTimeRef.current;
      const progress = Math.min(elapsed / duration, 1);

      // Easing function: easeOutQuart
      const easeOut = 1 - Math.pow(1 - progress, 4);

      const current = startValueRef.current + (value - startValueRef.current) * easeOut;
      setDisplayValue(current);

      if (progress < 1) {
        animationFrameRef.current = requestAnimationFrame(animate);
      }
    };

    animationFrameRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [value, duration]);

  return <span>{displayValue.toFixed(decimals)}</span>;
};

export const DataCard: React.FC<DataCardProps> = ({
  title,
  value,
  unit = '',
  icon: Icon,
  trend,
  color = 'blue',
  subtitle,
  animate = true,
  className = '',
}) => {
  const styles = colorStyles[color];

  return (
    <div
      className={`
        relative overflow-hidden rounded-xl border border-gray-200 dark:border-gray-800
        bg-white dark:bg-gray-900 p-6 shadow-sm hover:shadow-md
        transition-all duration-300 ease-in-out
        ${className}
      `}
    >
      {/* Background gradient accent */}
      <div className={`absolute top-0 right-0 w-32 h-32 ${styles.bg} rounded-full blur-3xl opacity-50 -translate-y-1/2 translate-x-1/2`} />

      <div className="relative">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            {Icon && (
              <div className={`p-2.5 rounded-lg ${styles.iconBg} transition-transform duration-300 hover:scale-110`}>
                <Icon className={`w-5 h-5 ${styles.iconColor}`} />
              </div>
            )}
            <div>
              <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</h3>
              {subtitle && <p className="text-xs text-gray-500 dark:text-gray-500 mt-0.5">{subtitle}</p>}
            </div>
          </div>
        </div>

        {/* Value */}
        <div className="flex items-baseline gap-2 mb-2">
          <span className={`text-3xl font-bold ${styles.textColor}`}>
            {animate && typeof value === 'number' ? (
              <AnimatedNumber value={value} />
            ) : (
              value
            )}
            {unit && <span className="text-xl ml-1">{unit}</span>}
          </span>
        </div>

        {/* Trend */}
        {trend !== undefined && (
          <div className="flex items-center gap-1.5">
            <span
              className={`text-sm font-medium flex items-center gap-1 transition-colors duration-300 ${
                trend > 0 ? 'text-green-600 dark:text-green-400' : trend < 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-500'
              }`}
            >
              {trend > 0 ? '↑' : trend < 0 ? '↓' : '−'}
              {Math.abs(trend).toFixed(1)}%
            </span>
            <span className="text-xs text-gray-500 dark:text-gray-400">vs 上期</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default DataCard;
