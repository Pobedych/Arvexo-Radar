declare module "@phosphor-icons/react" {
  import type { ComponentType, SVGProps } from "react";

  type IconWeight = "thin" | "light" | "regular" | "bold" | "fill" | "duotone";
  type IconProps = SVGProps<SVGSVGElement> & { size?: string | number; weight?: IconWeight };
  type IconComponent = ComponentType<IconProps>;

  export const ArrowRight: IconComponent;
  export const Buildings: IconComponent;
  export const CaretDown: IconComponent;
  export const CaretRight: IconComponent;
  export const ChartBar: IconComponent;
  export const ChartLineUp: IconComponent;
  export const CheckCircle: IconComponent;
  export const Clock: IconComponent;
  export const Coins: IconComponent;
  export const Database: IconComponent;
  export const DownloadSimple: IconComponent;
  export const FileText: IconComponent;
  export const FunnelSimple: IconComponent;
  export const GearSix: IconComponent;
  export const Info: IconComponent;
  export const Lightbulb: IconComponent;
  export const List: IconComponent;
  export const MagnifyingGlass: IconComponent;
  export const Robot: IconComponent;
  export const RocketLaunch: IconComponent;
  export const SealCheck: IconComponent;
  export const Sparkle: IconComponent;
  export const SquaresFour: IconComponent;
  export const SlidersHorizontal: IconComponent;
  export const TrendDown: IconComponent;
  export const TrendUp: IconComponent;
  export const UsersThree: IconComponent;
  export const WarningCircle: IconComponent;
  export const Wrench: IconComponent;
  export const X: IconComponent;
}
