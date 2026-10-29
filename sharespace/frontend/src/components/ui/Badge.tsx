import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none select-none",
  {
    variants: {
      variant: {
        default:
          "border border-blue-200 bg-blue-50 text-blue-700",
        secondary:
          "border border-slate-200 bg-slate-100 text-slate-700",
        outline:
          "border border-slate-300 text-slate-700 bg-white",
        success:
          "border border-emerald-200 bg-emerald-50 text-emerald-800",
        warning:
          "border border-amber-200 bg-amber-50 text-amber-800",
        destructive:
          "border border-red-200 bg-red-50 text-red-700",
        info:
          "border border-sky-200 bg-sky-50 text-sky-800",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge }
