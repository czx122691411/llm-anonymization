# 响应式侧边导航菜单设计文档

## 功能特性

### 1. 移动端 (默认隐藏)

```
┌─────────────────────────────────┐
│ ☰  LLM Anonymization          │ ← 汉堡菜单按钮
└─────────────────────────────────┘
         ↓ 点击菜单
┌─────────────────────────────────┐
│ ☰  LLM Anonymization          │
├─────────────────────────────────┤
│ ╱─────────────────────────────╲
│  │ 🇨🇳 中文演示                 │
│  │ ✏️  自定义测试               │
│  │ 🔒 TRACE-RPS                 │
│  │ 🎯 DeepSeek 5轮               │
│  │ 📊 Training Plots             │
│  ╲─────────────────────────────╱
└─────────────────────────────────┘
    遮罩层(点击关闭)
```

**特点**：
- 默认隐藏侧边栏，节省屏幕空间
- 点击左上角汉堡菜单滑入
- 点击遮罩层或导航项自动关闭
- 路由跳转时自动关闭

### 2. 桌面端 (始终显示)

#### 展开状态 (默认)
```
┌─────────────────────────────────────────────────────┐
│  ┌──────────────┐  LLM Anonymization Visualizer     │
│  │ 导航菜单     │  探索和分析文本匿名化结果          │
│  │              │                                  │
│  │ 🇨🇳 中文演示 │                                  │
│  │ ✏️ 自定义测试 │  [页面内容区域]                   │
│  │ 🔒 TRACE-RPS  │                                  │
│  │ 🎯 DeepSeek 5轮│                                  │
│  │ 📊 Training   │                                  │
│  │              │  [← 可点击收起]                  │
│  └──────────────┘                                  │
└─────────────────────────────────────────────────────┘
      264px 固定宽度
```

#### 收起状态
```
┌─────────────────────────────────────────────────────┐
│  ┌──┐  LLM Anonymization Visualizer                  │
│  │🇨│  探索和分析文本匿名化结果                       │
│  │✏│                                           [页面内容]│
│  │🔒│                                           │
│  │🎯│                                           │
│  │📊│                                           │
│  └──┘  [← 可点击展开]                              │
└─────────────────────────────────────────────────────┘
    80px 收起宽度
```

## 交互设计

### 移动端交互流程

1. **打开菜单**
   - 点击左上角汉堡图标 (☰)
   - 侧边栏从左侧滑入
   - 背景添加半透明黑色遮罩
   - 禁止body滚动

2. **关闭菜单**
   - 点击遮罩层
   - 点击任一导航项
   - 点击X按钮
   - 侧边栏滑出，遮罩消失

### 桌面端交互

1. **收起/展开**
   - 点击右上角箭头按钮 (←)
   - 侧边栏宽度在 264px ↔ 80px 之间切换
   - 图标始终可见，文字根据空间显示/隐藏

2. **当前页面高亮**
   - 活跃路由使用紫色渐变背景
   - 非活跃路由使用灰色背景

## 技术实现

### 组件位置
- **组件**: `frontend/src/components/SideNavigation.tsx`
- **使用**: `frontend/src/main.tsx`

### 状态管理
```tsx
const [isOpen, setIsOpen] = useState(false);        // 移动端菜单开关
const [isCollapsed, setIsCollapsed] = useState(false); // 桌面端收起状态
```

### 响应式断点
- **移动端**: 默认 (hidden)
- **平板端**: `sm:` (640px+)
- **桌面端**: `lg:` (1024px+)

### CSS Transition
```css
transition-transform duration-300 ease-in-out
```

### 动画类
- 滑入/滑出: `translate-x-0` ↔ `-translate-x-full`
- 收起/展开: `w-64` ↔ `w-20`

## API 文档

### Props
```tsx
interface SideNavigationProps {
  children: React.ReactNode;  // 页面内容
}
```

### 使用示例
```tsx
<SideNavigation>
  <Routes>
    <Route path="/" element={<Dashboard />} />
    <Route path="/custom-test" element={<CustomTestPage />} />
  </Routes>
</SideNavigation>
```

## 用户体验优化

### 1. 性能优化
- 使用 `transform` 而非 `left/right` 属性，获得GPU加速
- 遮罩层使用 `fixed` 定位，避免回流

### 2. 可访问性
- 添加 `aria-label` 描述按钮功能
- 遮罩层添加 `aria-hidden="true"`
- 键盘导航支持 (Tab/Shift+Tab)

### 3. 视觉反馈
- 活跃路由：紫色渐变背景 + 阴影
- 悬停效果：灰色背景高亮
- 焦点状态：ring outline

### 4. 防止滚动冲突
```tsx
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
```

## 扩展建议

### 未来增强功能
1. **记忆用户偏好**：使用 localStorage 保存侧边栏状态
2. **快捷键支持**：
   - `Ctrl+B` - 切换侧边栏
   - `Esc` - 关闭移动端菜单
3. **过渡动画优化**：
   - 弹性缓动函数
   - 卡片式菜单展开
4. **主题切换**：
   - 深色/浅色模式切换按钮
   - 跟随系统偏好

### 自定义配置
```tsx
interface SideNavigationConfig {
  defaultCollapsed?: boolean;    // 默认收起状态
  collapsible?: boolean;          // 是否允许收起
  breakpoint?: 'sm' | 'md' | 'lg'; // 响应式断点
  animationDuration?: number;     // 动画时长(ms)
}
```

## 浏览器兼容性

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- 移动端浏览器 (iOS Safari 14+, Chrome 90+)

## 性能指标

- 首次绘制时间: < 100ms
- 交互延迟: < 50ms
- 动画帧率: 60fps
