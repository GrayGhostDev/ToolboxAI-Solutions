// Ambient module declarations for Mantine components

declare module '*.svg' {
  const content: any;
  export default content;
}

declare module '*.png' {
  const content: any;
  export default content;
}

declare module '*.jpg' {
  const content: any;
  export default content;
}

declare module '*.css' {
  const content: any;
  export default content;
}

declare module '*.scss' {
  const content: any;
  export default content;
}

// Global type extensions
declare global {
  interface Window {
    [key: string]: any;
  }

  interface EventListener {
    (evt: any): void;
  }
}

export {};
