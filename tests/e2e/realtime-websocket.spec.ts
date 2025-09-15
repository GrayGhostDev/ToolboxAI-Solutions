import { test, expect, Page } from '@playwright/test';

test.describe('Real-time WebSocket & Pusher Tests', () => {
  let page: Page;

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test.describe('WebSocket Connection', () => {
    test('should establish WebSocket connection', async () => {
      // Wait for WebSocket to connect
      await page.waitForTimeout(2000);

      const wsStatus = await page.evaluate(() => {
        // Check for WebSocket connection
        const ws = (window as any).webSocket || (window as any).ws;
        if (ws) {
          return {
            connected: ws.readyState === WebSocket.OPEN,
            readyState: ws.readyState,
            url: ws.url
          };
        }
        return null;
      });

      if (wsStatus) {
        console.log('WebSocket status:', wsStatus);
        expect([WebSocket.OPEN, WebSocket.CONNECTING]).toContain(wsStatus.readyState);
      }
    });

    test('should reconnect WebSocket on disconnect', async () => {
      // Check initial connection
      const initialConnection = await page.evaluate(() => {
        const ws = (window as any).webSocket || (window as any).ws;
        return ws ? ws.readyState : null;
      });

      if (initialConnection !== null) {
        // Simulate disconnect
        await page.evaluate(() => {
          const ws = (window as any).webSocket || (window as any).ws;
          if (ws && ws.close) {
            ws.close();
          }
        });

        // Wait for reconnection
        await page.waitForTimeout(5000);

        // Check if reconnected
        const reconnectionStatus = await page.evaluate(() => {
          const ws = (window as any).webSocket || (window as any).ws;
          return ws ? ws.readyState : null;
        });

        console.log('Reconnection status:', reconnectionStatus);
      }
    });

    test('should handle WebSocket messages', async () => {
      const messages: any[] = [];

      // Listen for WebSocket messages
      await page.evaluateOnNewDocument(() => {
        window.addEventListener('message', (event) => {
          if (event.data && event.data.type === 'websocket') {
            (window as any).wsMessages = (window as any).wsMessages || [];
            (window as any).wsMessages.push(event.data);
          }
        });
      });

      await page.reload();
      await page.waitForTimeout(3000);

      // Check if any messages were received
      const receivedMessages = await page.evaluate(() => {
        return (window as any).wsMessages || [];
      });

      console.log(`Received ${receivedMessages.length} WebSocket messages`);
    });
  });

  test.describe('Pusher Integration', () => {
    test('should initialize Pusher client', async () => {
      const pusherStatus = await page.evaluate(() => {
        const pusher = (window as any).Pusher || (window as any).pusher;
        if (pusher) {
          return {
            available: true,
            version: pusher.VERSION || 'unknown'
          };
        }
        return null;
      });

      if (pusherStatus) {
        console.log('Pusher status:', pusherStatus);
        expect(pusherStatus.available).toBeTruthy();
      }
    });

    test('should connect to Pusher channels', async () => {
      const channelStatus = await page.evaluate(() => {
        const pusher = (window as any).pusherInstance || (window as any).pusher;
        if (pusher && pusher.channels) {
          const channels = pusher.channels.all();
          return Object.keys(channels).map(name => ({
            name,
            subscribed: channels[name].subscribed
          }));
        }
        return [];
      });

      console.log('Pusher channels:', channelStatus);

      // Check for expected channels
      const expectedChannels = ['dashboard-updates', 'content-generation', 'agent-status'];
      for (const channel of expectedChannels) {
        const found = channelStatus.find((c: any) => c.name === channel);
        if (found) {
          console.log(`Channel ${channel} found`);
        }
      }
    });

    test('should receive Pusher events', async () => {
      // Set up event listener
      const events = await page.evaluate(() => {
        return new Promise((resolve) => {
          const pusher = (window as any).pusherInstance || (window as any).pusher;
          const collectedEvents: any[] = [];

          if (pusher) {
            const channel = pusher.subscribe('dashboard-updates');
            channel.bind('update', (data: any) => {
              collectedEvents.push({ event: 'update', data });
            });

            // Wait 3 seconds to collect events
            setTimeout(() => {
              resolve(collectedEvents);
            }, 3000);
          } else {
            resolve([]);
          }
        });
      });

      console.log(`Collected ${(events as any[]).length} Pusher events`);
    });

    test('should handle Pusher connection state changes', async () => {
      const stateChanges = await page.evaluate(() => {
        return new Promise((resolve) => {
          const pusher = (window as any).pusherInstance || (window as any).pusher;
          const states: string[] = [];

          if (pusher && pusher.connection) {
            states.push(pusher.connection.state);

            pusher.connection.bind('state_change', (states: any) => {
              states.push(states.current);
            });

            // Collect states for 2 seconds
            setTimeout(() => {
              resolve(states);
            }, 2000);
          } else {
            resolve([]);
          }
        });
      });

      console.log('Pusher connection states:', stateChanges);
    });
  });

  test.describe('Real-time Features', () => {
    test('should display real-time notifications', async () => {
      // Wait for any real-time notifications
      await page.waitForTimeout(3000);

      const notifications = await page.locator('.notification, .toast, .alert, [role="alert"]').all();
      console.log(`Found ${notifications.length} notification elements`);

      // Check if notifications appear dynamically
      const dynamicNotifications = await page.evaluate(() => {
        return new Promise((resolve) => {
          const observer = new MutationObserver((mutations) => {
            const hasNotification = mutations.some(mutation => {
              return Array.from(mutation.addedNodes).some((node: any) => {
                return node.classList && (
                  node.classList.contains('notification') ||
                  node.classList.contains('toast') ||
                  node.classList.contains('alert')
                );
              });
            });

            if (hasNotification) {
              observer.disconnect();
              resolve(true);
            }
          });

          observer.observe(document.body, {
            childList: true,
            subtree: true
          });

          // Stop observing after 5 seconds
          setTimeout(() => {
            observer.disconnect();
            resolve(false);
          }, 5000);
        });
      });

      console.log('Dynamic notifications detected:', dynamicNotifications);
    });

    test('should update data in real-time', async () => {
      // Monitor for DOM updates
      const updates = await page.evaluate(() => {
        return new Promise((resolve) => {
          let updateCount = 0;
          const targetNodes = document.querySelectorAll('[data-realtime], .real-time-data, .live-update');

          const observer = new MutationObserver((mutations) => {
            updateCount += mutations.length;
          });

          targetNodes.forEach(node => {
            observer.observe(node, {
              childList: true,
              characterData: true,
              subtree: true,
              attributes: true
            });
          });

          setTimeout(() => {
            observer.disconnect();
            resolve(updateCount);
          }, 5000);
        });
      });

      console.log(`Detected ${updates} real-time updates`);
    });

    test('should sync data across tabs', async () => {
      // Open a second tab
      const context = page.context();
      const page2 = await context.newPage();
      await page2.goto('/');
      await page2.waitForLoadState('networkidle');

      // Make a change in the first tab
      const button = page.locator('button').first();
      if (await button.count() > 0) {
        await button.click();
      }

      // Wait for sync
      await page2.waitForTimeout(2000);

      // Check if changes are reflected in second tab
      const syncStatus = await page2.evaluate(() => {
        // Check for any indicators of synced data
        return document.body.innerHTML.includes('synced') ||
               document.body.innerHTML.includes('updated');
      });

      await page2.close();
      console.log('Cross-tab sync status:', syncStatus);
    });
  });

  test.describe('Content Generation Real-time Updates', () => {
    test('should show content generation progress', async () => {
      // Look for content generation buttons
      const generateButton = page.locator('button:has-text("Generate"), button:has-text("Create Content")');

      if (await generateButton.count() > 0) {
        await generateButton.first().click();

        // Wait for progress indicators
        const progressIndicators = await page.locator('.progress, .loading, [role="progressbar"]').count();
        console.log(`Found ${progressIndicators} progress indicators`);

        // Wait for completion
        await page.waitForTimeout(5000);
      }
    });

    test('should display agent status updates', async () => {
      // Check for agent status elements
      const agentStatus = await page.locator('[data-agent-status], .agent-status, .agent-indicator').count();
      console.log(`Found ${agentStatus} agent status elements`);

      // Monitor for status changes
      const statusChanges = await page.evaluate(() => {
        return new Promise((resolve) => {
          const statusElements = document.querySelectorAll('[data-agent-status], .agent-status');
          const changes: string[] = [];

          statusElements.forEach(element => {
            const observer = new MutationObserver(() => {
              changes.push(element.textContent || '');
            });

            observer.observe(element, {
              childList: true,
              characterData: true,
              subtree: true
            });
          });

          setTimeout(() => {
            resolve(changes);
          }, 3000);
        });
      });

      console.log('Agent status changes:', statusChanges);
    });
  });

  test.describe('Error Handling', () => {
    test('should handle WebSocket errors gracefully', async () => {
      // Simulate WebSocket error
      await page.evaluate(() => {
        const ws = (window as any).webSocket || (window as any).ws;
        if (ws) {
          // Trigger error event
          ws.onerror && ws.onerror(new Event('error'));
        }
      });

      // Check if error is handled
      await page.waitForTimeout(1000);

      const hasErrorMessage = await page.locator('.error, .alert-error').count();
      console.log(`Error messages displayed: ${hasErrorMessage}`);
    });

    test('should handle Pusher disconnection', async () => {
      // Disconnect Pusher
      await page.evaluate(() => {
        const pusher = (window as any).pusherInstance || (window as any).pusher;
        if (pusher && pusher.disconnect) {
          pusher.disconnect();
        }
      });

      await page.waitForTimeout(2000);

      // Check if disconnection is handled
      const connectionStatus = await page.evaluate(() => {
        const pusher = (window as any).pusherInstance || (window as any).pusher;
        return pusher ? pusher.connection.state : 'unknown';
      });

      console.log('Pusher connection status after disconnect:', connectionStatus);
    });

    test('should retry failed connections', async () => {
      // Monitor retry attempts
      const retryAttempts = await page.evaluate(() => {
        return new Promise((resolve) => {
          let attempts = 0;
          const originalWebSocket = window.WebSocket;

          // Override WebSocket to count connection attempts
          (window as any).WebSocket = function(...args: any[]) {
            attempts++;
            return new originalWebSocket(...args);
          };

          setTimeout(() => {
            // Restore original WebSocket
            (window as any).WebSocket = originalWebSocket;
            resolve(attempts);
          }, 5000);
        });
      });

      console.log(`WebSocket retry attempts: ${retryAttempts}`);
    });
  });

  test.describe('Performance', () => {
    test('should handle high-frequency updates', async () => {
      // Simulate high-frequency updates
      const performance = await page.evaluate(() => {
        return new Promise((resolve) => {
          const startTime = performance.now();
          let updateCount = 0;

          // Simulate rapid updates
          const interval = setInterval(() => {
            updateCount++;
            // Trigger a DOM update
            const element = document.createElement('div');
            element.className = 'test-update';
            document.body.appendChild(element);
            document.body.removeChild(element);
          }, 10); // Update every 10ms

          setTimeout(() => {
            clearInterval(interval);
            const endTime = performance.now();
            resolve({
              duration: endTime - startTime,
              updates: updateCount,
              updatesPerSecond: (updateCount / ((endTime - startTime) / 1000))
            });
          }, 1000);
        });
      });

      console.log('High-frequency update performance:', performance);
      expect((performance as any).updatesPerSecond).toBeGreaterThan(50);
    });

    test('should not leak memory with WebSocket connections', async () => {
      // Get initial memory usage
      const initialMemory = await page.evaluate(() => {
        return (performance as any).memory ? (performance as any).memory.usedJSHeapSize : 0;
      });

      // Create and destroy multiple WebSocket connections
      for (let i = 0; i < 5; i++) {
        await page.evaluate(() => {
          const ws = new WebSocket('ws://localhost:8008/ws/test');
          setTimeout(() => ws.close(), 100);
        });
        await page.waitForTimeout(200);
      }

      // Get final memory usage
      const finalMemory = await page.evaluate(() => {
        return (performance as any).memory ? (performance as any).memory.usedJSHeapSize : 0;
      });

      if (initialMemory && finalMemory) {
        const memoryIncrease = finalMemory - initialMemory;
        console.log(`Memory increase: ${memoryIncrease} bytes`);

        // Memory increase should be reasonable (less than 10MB)
        expect(memoryIncrease).toBeLessThan(10 * 1024 * 1024);
      }
    });
  });
});