import type { Config } from 'tailwindcss'

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  safelist: [
    'flex', 'flex-1', 'flex-col', 'items-center', 'items-start', 'justify-between',
    'justify-center', 'gap-2', 'gap-3', 'gap-4', 'gap-6', 'space-y-1', 'space-y-3',
    'space-y-4', 'space-y-6', 'space-y-8', 'grid', 'grid-cols-2', 'grid-cols-4',
    'grid-cols-5', 'col-span-2',
    'p-3', 'p-4', 'p-5', 'p-6', 'p-8', 'p-12', 'px-3', 'px-4', 'px-6', 'px-8',
    'py-1', 'py-2', 'py-2.5', 'py-3', 'py-8', 'py-12', 'py-16',
    'mt-1', 'mt-2', 'mt-3', 'mt-4', 'mt-5', 'mb-1', 'mb-2', 'mb-3', 'mb-4',
    'ml-56', 'w-full', 'w-56', 'w-8', 'w-12', 'w-64', 'h-full', 'h-8', 'h-12',
    'h-1.5', 'h-64', 'min-h-screen', 'min-w-0', 'max-w-lg', 'shrink-0',
    'text-xs', 'text-sm', 'text-base', 'text-lg', 'text-xl', 'text-2xl', 'text-3xl',
    'text-4xl', 'font-medium', 'font-semibold', 'font-bold', 'font-mono',
    'leading-relaxed', 'tracking-wider', 'uppercase', 'capitalize', 'truncate',
    'italic', 'text-left', 'text-center', 'text-right',
    'text-white', 'text-slate-300', 'text-slate-400', 'text-slate-500', 'text-slate-600',
    'text-blue-400', 'text-blue-500', 'text-green-400', 'text-red-400', 'text-orange-400',
    'text-yellow-400', 'text-yellow-300',
    'bg-blue-600', 'hover:bg-blue-500', 'bg-blue-600/20',
    'bg-green-900/20', 'bg-green-900/30', 'bg-green-900/50',
    'bg-red-900/20', 'bg-red-900/30', 'bg-red-900/50',
    'bg-orange-900/20', 'bg-yellow-900/20', 'bg-yellow-900/30',
    'bg-gray-800', 'bg-gray-900/20',
    'border', 'border-b', 'border-t', 'border-r', 'rounded', 'rounded-lg', 'rounded-xl',
    'rounded-full', 'overflow-hidden', 'overflow-x-auto',
    'border-blue-500', 'border-blue-800', 'border-green-700', 'border-green-800',
    'border-green-900/50', 'border-red-800', 'border-orange-800', 'border-yellow-700',
    'border-gray-700', 'border-white/10',
    'fixed', 'relative', 'absolute', 'z-50', 'top-0', 'left-0',
    'transition-all', 'transition-colors', 'duration-1000',
    'hover:bg-blue-500', 'hover:bg-red-900/50', 'hover:text-white', 'hover:border-slate-500',
    'disabled:opacity-40', 'disabled:cursor-not-allowed',
    'divide-y', 'divide-[#1e2a45]',
    'sr-only', 'inline-flex', 'whitespace-pre-wrap', 'resize-none',
    'accent-green-500', 'animate-spin', 'animate-pulse',
    'w-4', 'h-4', 'border-4', 'border-t-blue-500', 'border-blue-600/30',
    'bg-[#0a0e1a]', 'bg-[#0f1629]', 'bg-[#1a2238]', 'bg-[#243352]',
    'border-[#1e2a45]', 'text-[#94a3b8]', 'text-[#64748b]',
    'hover:bg-[#1a2238]', 'hover:bg-[#243352]',
  ],
  theme: {
    extend: {
      colors: {
        dark: { 900: '#0a0e1a', 800: '#0f1629', 700: '#1a2238', 600: '#1e2a45' },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      }
    },
  },
  plugins: [],
} satisfies Config