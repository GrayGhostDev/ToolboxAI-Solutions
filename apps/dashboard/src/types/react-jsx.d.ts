// Extend the JSX namespace to include MUI components
declare namespace JSX {
  interface IntrinsicElements {
    // Add any HTML elements if needed
  }
}

// React 18 JSX transformation fixes
declare module 'react/jsx-runtime' {
  export const jsx: any;
  export const jsxs: any;
  export const Fragment: any;
}

declare module 'react/jsx-dev-runtime' {
  export const jsx: any;
  export const jsxs: any;
  export const Fragment: any;
}

// Fix for React component typing
declare global {
  namespace React {
    type FC<P = {}> = React.FunctionComponent<P>;
    type ReactElement<P = any, T extends string | JSXElementConstructor<any> = string | JSXElementConstructor<any>> = {
      type: T;
      props: P;
      key: React.Key | null;
    };
  }
}

export {};