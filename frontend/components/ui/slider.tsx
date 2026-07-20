"use client";

import * as SliderPrimitive from "@radix-ui/react-slider";
import { forwardRef } from "react";
import { cn } from "@/lib/utils";

interface SliderProps extends React.ComponentPropsWithoutRef<typeof SliderPrimitive.Root> {
  trackColor?: string;
}

export const Slider = forwardRef<React.ElementRef<typeof SliderPrimitive.Root>, SliderProps>(
  ({ className, trackColor = "#DB2777", ...props }, ref) => (
    <SliderPrimitive.Root
      ref={ref}
      className={cn("relative flex w-full touch-none select-none items-center", className)}
      {...props}
    >
      <SliderPrimitive.Track className="relative h-1.5 w-full grow overflow-hidden rounded-full bg-white/10">
        <SliderPrimitive.Range className="absolute h-full rounded-full" style={{ backgroundColor: trackColor }} />
      </SliderPrimitive.Track>
      <SliderPrimitive.Thumb
        className="block h-3.5 w-3.5 rounded-full border border-white/40 bg-white shadow transition-transform hover:scale-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
        style={{ backgroundColor: trackColor }}
      />
    </SliderPrimitive.Root>
  )
);
Slider.displayName = "Slider";
