import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"
import { AlertCircle, CheckCircle2, Info, AlertTriangle } from "lucide-react"

const alertVariants = cva(
  "relative w-full rounded-xl border p-4 text-sm [&>svg~*]:pl-7 [&>svg+div]:translate-y-[-3px] [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4",
  {
    variants: {
      variant: {
        default: "bg-slate-50 border-slate-200 text-slate-800 [&>svg]:text-slate-500",
        info: "bg-blue-50 border-blue-200 text-blue-900 [&>svg]:text-blue-600",
        success: "bg-emerald-50 border-emerald-200 text-emerald-900 [&>svg]:text-emerald-600",
        warning: "bg-amber-50 border-amber-200 text-amber-900 [&>svg]:text-amber-600",
        destructive: "bg-red-50 border-red-200 text-red-900 [&>svg]:text-red-600",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

interface AlertProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof alertVariants> {
  title?: string
}

function Alert({ className, variant, title, children, ...props }: AlertProps) {
  const Icon =
    variant === "success"
      ? CheckCircle2
      : variant === "warning"
      ? AlertTriangle
      : variant === "destructive"
      ? AlertCircle
      : Info

  return (
    <div role="alert" className={cn(alertVariants({ variant }), className)} {...props}>
      <Icon className="h-4 w-4" />
      <div>
        {title && <h5 className="mb-1 font-semibold leading-none tracking-tight">{title}</h5>}
        <div className="text-xs leading-relaxed text-inherit opacity-90">{children}</div>
      </div>
    </div>
  )
}

export { Alert }
