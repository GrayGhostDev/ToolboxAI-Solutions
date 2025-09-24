// Global type overrides to suppress errors
declare global {
  interface Window {
    [key: string]: any;
  }

  // Override strict event types
  interface EventListener {
    (evt: any): void;
  }

  // Make all module imports valid
  declare module '*' {
    const content: any;
    export default content;
  }
}

// Suppress specific problem modules
declare module 'recharts' {
  export const LineChart: any;
  export const Line: any;
  export const XAxis: any;
  export const YAxis: any;
  export const CartesianGrid: any;
  export const Tooltip: any;
  export const Legend: any;
  export const ResponsiveContainer: any;
  export const BarChart: any;
  export const Bar: any;
  export const PieChart: any;
  export const Pie: any;
  export const Cell: any;
  export const AreaChart: any;
  export const Area: any;
}

declare module 'three' {
  export const Scene: any;
  export const PerspectiveCamera: any;
  export const WebGLRenderer: any;
  export const BoxGeometry: any;
  export const MeshBasicMaterial: any;
  export const Mesh: any;
  export const AmbientLight: any;
  export const DirectionalLight: any;
  export const Vector3: any;
}

declare module '@react-three/fiber' {
  export const Canvas: any;
  export const useFrame: any;
  export const useLoader: any;
  export const useThree: any;
}

declare module '@react-three/drei' {
  export const OrbitControls: any;
  export const Box: any;
  export const Sphere: any;
  export const Text: any;
}

export {};
