/**
 * Service Worker Cleanup Utility
 *
 * This script ensures any previously registered service workers are completely
 * unregistered and caches are cleared. Add this to your main.tsx temporarily
 * if you're experiencing service worker issues.
 */

export async function unregisterServiceWorkers(): Promise<void> {
  if ('serviceWorker' in navigator) {
    try {
      // Get all service worker registrations
      const registrations = await navigator.serviceWorker.getRegistrations();

      console.log(`Found ${registrations.length} service worker registration(s)`);

      // Unregister all service workers
      const unregisterPromises = registrations.map(async (registration) => {
        console.log('Unregistering service worker:', registration.scope);
        const success = await registration.unregister();
        return { scope: registration.scope, success };
      });

      const results = await Promise.all(unregisterPromises);

      // Log results
      results.forEach(({ scope, success }) => {
        if (success) {
          console.log('✅ Successfully unregistered:', scope);
        } else {
          console.warn('❌ Failed to unregister:', scope);
        }
      });

      // Clear all caches
      if ('caches' in window) {
        const cacheNames = await caches.keys();
        console.log(`Found ${cacheNames.length} cache(s) to clear`);

        const deletionPromises = cacheNames.map(async (cacheName) => {
          console.log('Deleting cache:', cacheName);
          return await caches.delete(cacheName);
        });

        await Promise.all(deletionPromises);
        console.log('✅ All caches cleared');
      }

      console.log('✅ Service worker cleanup complete');
      console.log('💡 Reload the page to ensure all changes take effect');

    } catch (error) {
      console.error('Error during service worker cleanup:', error);
    }
  } else {
    console.log('Service workers not supported in this browser');
  }
}

/**
 * Check if any service workers are registered
 */
export async function checkServiceWorkers(): Promise<void> {
  if ('serviceWorker' in navigator) {
    const registrations = await navigator.serviceWorker.getRegistrations();

    if (registrations.length === 0) {
      console.log('✅ No service workers registered');
    } else {
      console.log('⚠️ Active service workers found:');
      registrations.forEach((reg, index) => {
        console.log(`${index + 1}. Scope: ${reg.scope}`);
        console.log(`   Active: ${reg.active ? 'Yes' : 'No'}`);
        console.log(`   Installing: ${reg.installing ? 'Yes' : 'No'}`);
        console.log(`   Waiting: ${reg.waiting ? 'Yes' : 'No'}`);
      });

      console.log('💡 Run unregisterServiceWorkers() to remove them');
    }
  }
}

// Export for console debugging
if (typeof window !== 'undefined') {
  (window as any).unregisterServiceWorkers = unregisterServiceWorkers;
  (window as any).checkServiceWorkers = checkServiceWorkers;
}

