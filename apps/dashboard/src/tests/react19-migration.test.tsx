jest.setTimeout(10000);

/**
 * React 19 Migration Tests
 * Validates the migration from React 18 to React 19
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Button } from '../components/atomic/atoms/Button.react19';
import { useAction, useOptimistic, REACT_19_FEATURES } from '../config/react19';
import { renderHook, act } from '@testing-library/react';

describe('React 19 Migration Tests', () => {
  describe('Component ref handling without forwardRef', () => {
    it('should accept ref prop directly without forwardRef', () => {
      const ref = React.createRef<HTMLButtonElement>();
      render(<Button ref={ref}>Test Button</Button>);

      expect(ref.current).toBeInstanceOf(HTMLButtonElement);
      expect(ref.current?.textContent).toBe('Test Button');
    });

    it('should work with useRef hook', () => {
      const TestComponent = () => {
        const buttonRef = React.useRef<HTMLButtonElement>(null);

        React.useEffect(() => {
          if (buttonRef.current) {
            buttonRef.current.focus();
          }
        }, []);

        return <Button ref={buttonRef}>Focus Me</Button>;
      };

      render(<TestComponent />);
      const button = screen.getByText('Focus Me');
      expect(document.activeElement).toBe(button);
    });

    it('should work with callback refs', () => {
      let buttonElement: HTMLButtonElement | null = null;

      render(
        <Button
          ref={(el) => {
            buttonElement = el;
          }}
        >
          Callback Ref
        </Button>
      );

      expect(buttonElement).toBeInstanceOf(HTMLButtonElement);
    });
  });

  describe('React 19 Actions API', () => {
    it('should handle async actions with useAction hook', async () => {
      const mockAction = jest.fn().mockResolvedValue({ success: true });
      const onSuccess = jest.fn();
      const onError = jest.fn();

      const TestComponent = () => {
        return (
          <Button
            action={mockAction}
            onSuccess={onSuccess}
            onError={onError}
          >
            Execute Action
          </Button>
        );
      };

      render(<TestComponent />);
      const button = screen.getByText('Execute Action');

      fireEvent.click(button);

      await waitFor(() => {
        expect(mockAction).toHaveBeenCalled();
        expect(onSuccess).toHaveBeenCalledWith({ success: true });
      });

      expect(onError).not.toHaveBeenCalled();
    });

    it('should handle action errors properly', async () => {
      const error = new Error('Action failed');
      const mockAction = jest.fn().mockRejectedValue(error);
      const onError = jest.fn();

      render(
        <Button action={mockAction} onError={onError}>
          Failing Action
        </Button>
      );

      fireEvent.click(screen.getByText('Failing Action'));

      await waitFor(() => {
        expect(onError).toHaveBeenCalledWith(error);
      });
    });

    it('should show loading state during action execution', async () => {
      let resolveAction: (value: any) => void;
      const mockAction = jest.fn(
        () =>
          new Promise((resolve) => {
            resolveAction = resolve;
          })
      );

      render(
        <Button action={mockAction} loadingText="Processing...">
          Async Button
        </Button>
      );

      const button = screen.getByText('Async Button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(screen.getByText('Processing...')).toBeInTheDocument();
      });

      act(() => {
        resolveAction!({ done: true });
      });

      await waitFor(() => {
        expect(screen.queryByText('Processing...')).not.toBeInTheDocument();
        expect(screen.getByText('Async Button')).toBeInTheDocument();
      });
    });
  });

  describe('useAction hook', () => {
    it('should manage async operations', async () => {
      const mockAction = jest.fn().mockResolvedValue('result');

      const { result } = renderHook(() =>
        useAction(mockAction)
      );

      expect(result.current.isPending).toBe(false);
      expect(result.current.error).toBe(null);

      let actionPromise: Promise<any>;
      act(() => {
        actionPromise = result.current.execute('arg1', 'arg2');
      });

      expect(result.current.isPending).toBe(true);

      await act(async () => {
        await actionPromise;
      });

      expect(result.current.isPending).toBe(false);
      expect(mockAction).toHaveBeenCalledWith('arg1', 'arg2');
    });

    it('should handle errors in useAction', async () => {
      const error = new Error('Test error');
      const mockAction = jest.fn().mockRejectedValue(error);
      const onError = jest.fn();

      const { result } = renderHook(() =>
        useAction(mockAction, undefined, onError)
      );

      await act(async () => {
        try {
          await result.current.execute();
        } catch (e) {
          // Expected to throw
        }
      });

      expect(result.current.error).toBe(error);
      expect(onError).toHaveBeenCalledWith(error);
    });
  });

  describe('useOptimistic hook', () => {
    it('should handle optimistic updates', () => {
      const { result } = renderHook(() =>
        useOptimistic(0, (current, increment: number) => current + increment)
      );

      const [value, updateOptimistically, isPending] = result.current;

      expect(value).toBe(0);
      expect(isPending).toBe(false);

      act(() => {
        updateOptimistically(5);
      });

      const [newValue, , newIsPending] = result.current;
      expect(newValue).toBe(5);
      expect(newIsPending).toBe(true);
    });

    it('should work with complex state', () => {
      interface Todo {
        id: number;
        text: string;
        completed: boolean;
      }

      const initialTodos: Todo[] = [
        { id: 1, text: 'Task 1', completed: false },
      ];

      const { result } = renderHook(() =>
        useOptimistic(initialTodos, (todos, newTodo: Todo) => [...todos, newTodo])
      );

      act(() => {
        const [, updateOptimistically] = result.current;
        updateOptimistically({ id: 2, text: 'Task 2', completed: false });
      });

      const [todos] = result.current;
      expect(todos).toHaveLength(2);
      expect(todos[1].text).toBe('Task 2');
    });
  });

  describe('React 19 Features Configuration', () => {
    it('should have all required feature flags', () => {
      expect(REACT_19_FEATURES.useActions).toBe(true);
      expect(REACT_19_FEATURES.useSuspenseList).toBe(true);
      expect(REACT_19_FEATURES.concurrentFeatures).toBeDefined();
      expect(REACT_19_FEATURES.concurrentFeatures.useTransition).toBe(true);
      expect(REACT_19_FEATURES.concurrentFeatures.useDeferredValue).toBe(true);
    });

    it('should have server components configuration', () => {
      expect(REACT_19_FEATURES.serverComponents).toBeDefined();
      expect(REACT_19_FEATURES.serverComponents.enabled).toBeDefined();
      expect(REACT_19_FEATURES.serverComponents.apiRoute).toBe('/rsc');
    });

    it('should have asset loading configuration', () => {
      expect(REACT_19_FEATURES.assetLoading).toBeDefined();
      expect(REACT_19_FEATURES.assetLoading.prefetch).toBe(true);
      expect(REACT_19_FEATURES.assetLoading.preload).toBe(true);
    });
  });

  describe('Backwards Compatibility', () => {
    it('should still work with traditional onClick handlers', () => {
      const handleClick = jest.fn();

      render(<Button onClick={handleClick}>Traditional Click</Button>);

      fireEvent.click(screen.getByText('Traditional Click'));
      expect(handleClick).toHaveBeenCalled();
    });

    it('should work with all button variants', () => {
      const variants = ['primary', 'secondary', 'outlined', 'ghost', 'danger'] as const;

      variants.forEach((variant) => {
        const { rerender } = render(
          <Button variant={variant}>Variant {variant}</Button>
        );

        expect(screen.getByText(`Variant ${variant}`)).toBeInTheDocument();
        rerender(<></>);
      });
    });

    it('should handle loading states correctly', () => {
      const { rerender } = render(
        <Button loading loadingText="Loading...">
          Submit
        </Button>
      );

      expect(screen.getByText('Loading...')).toBeInTheDocument();
      expect(screen.queryByText('Submit')).not.toBeInTheDocument();

      rerender(
        <Button loading={false}>
          Submit
        </Button>
      );

      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
      expect(screen.getByText('Submit')).toBeInTheDocument();
    });
  });

  describe('TypeScript Support', () => {
    it('should have proper type inference', () => {
      // This test validates TypeScript compilation
      const TestComponent = () => {
        const buttonRef = React.useRef<HTMLButtonElement>(null);
        const handleAction = async (data: string): Promise<{ result: string }> => {
          return { result: data };
        };

        return (
          <Button
            ref={buttonRef}
            variant="primary"
            size="md"
            action={handleAction}
            onSuccess={(result: { result: string }) => {
              console.log(result.result);
            }}
            onError={(error: Error) => {
              console.error(error.message);
            }}
          >
            Typed Button
          </Button>
        );
      };

      render(<TestComponent />);
      expect(screen.getByText('Typed Button')).toBeInTheDocument();
    });
  });

  describe('Performance Improvements', () => {
    it('should not re-render unnecessarily', () => {
      let renderCount = 0;

      const TestComponent = React.memo(() => {
        renderCount++;
        return <Button>Memoized Button</Button>;
      });

      const { rerender } = render(
        <div>
          <TestComponent />
        </div>
      );

      expect(renderCount).toBe(1);

      rerender(
        <div>
          <TestComponent />
        </div>
      );

      expect(renderCount).toBe(1); // Should not re-render due to memo
    });
  });
});

// Integration tests
describe('React 19 Migration Integration', () => {
  it('should work with complex component hierarchies', () => {
    const ComplexComponent = () => {
      const containerRef = React.useRef<HTMLDivElement>(null);
      const buttonRef = React.useRef<HTMLButtonElement>(null);

      const handleAction = async () => {
        await new Promise((resolve) => setTimeout(resolve, 100));
        return { success: true };
      };

      return (
        <div ref={containerRef}>
          <Button
            ref={buttonRef}
            action={handleAction}
            variant="primary"
            size="lg"
            icon={<span>🚀</span>}
            iconPosition="left"
          >
            Launch Feature
          </Button>
        </div>
      );
    };

    render(<ComplexComponent />);
    expect(screen.getByText('Launch Feature')).toBeInTheDocument();
    expect(screen.getByText('🚀')).toBeInTheDocument();
  });

  it('should handle multiple actions in sequence', async () => {
    const actions: string[] = [];

    const TestComponent = () => {
      const action1 = async () => {
        actions.push('action1');
        return 'result1';
      };

      const action2 = async () => {
        actions.push('action2');
        return 'result2';
      };

      return (
        <>
          <Button action={action1}>Button 1</Button>
          <Button action={action2}>Button 2</Button>
        </>
      );
    };

    render(<TestComponent />);

    fireEvent.click(screen.getByText('Button 1'));
    fireEvent.click(screen.getByText('Button 2'));

    await waitFor(() => {
      expect(actions).toEqual(['action1', 'action2']);
    });
  });
});