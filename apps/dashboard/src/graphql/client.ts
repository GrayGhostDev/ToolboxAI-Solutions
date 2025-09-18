/**
 * Apollo Client configuration for GraphQL
 */

import {
  ApolloClient,
  InMemoryCache,
  createHttpLink,
  split,
  ApolloLink,
} from '@apollo/client';
import { setContext } from '@apollo/client/link/context';
import { WebSocketLink } from '@apollo/client/link/ws';
import { getMainDefinition } from '@apollo/client/utilities';
import { onError } from '@apollo/client/link/error';

// Get GraphQL endpoint from environment
const GRAPHQL_ENDPOINT = import.meta.env.VITE_GRAPHQL_ENDPOINT || 'http://localhost:8008/graphql';
const GRAPHQL_WS_ENDPOINT = import.meta.env.VITE_GRAPHQL_WS_ENDPOINT || 'ws://localhost:8008/graphql';

// HTTP link for queries and mutations
const httpLink = createHttpLink({
  uri: GRAPHQL_ENDPOINT,
  credentials: 'include',
});

// WebSocket link for subscriptions
const wsLink = new WebSocketLink({
  uri: GRAPHQL_WS_ENDPOINT,
  options: {
    reconnect: true,
    connectionParams: () => {
      const token = localStorage.getItem('token');
      return {
        authorization: token ? `Bearer ${token}` : '',
      };
    },
  },
});

// Auth link to add authorization header
const authLink = setContext((_, { headers }) => {
  const token = localStorage.getItem('token');
  return {
    headers: {
      ...headers,
      authorization: token ? `Bearer ${token}` : '',
    },
  };
});

// Error link for error handling
const errorLink = onError(({ graphQLErrors, networkError, operation, forward }) => {
  if (graphQLErrors) {
    graphQLErrors.forEach(({ message, locations, path, extensions }) => {
      console.error(
        `[GraphQL error]: Message: ${message}, Location: ${locations}, Path: ${path}`
      );

      // Handle specific error codes
      if (extensions?.code === 'UNAUTHENTICATED') {
        // Redirect to login or refresh token
        localStorage.removeItem('token');
        window.location.href = '/login';
      }

      if (extensions?.code === 'RATE_LIMITED') {
        // Show rate limit message to user
        const retryAfter = extensions.retry_after;
        console.warn(`Rate limited. Retry after ${retryAfter} seconds`);
      }
    });
  }

  if (networkError) {
    console.error(`[Network error]: ${networkError}`);
  }
});

// Split link to route requests to appropriate transport
const splitLink = split(
  ({ query }) => {
    const definition = getMainDefinition(query);
    return (
      definition.kind === 'OperationDefinition' &&
      definition.operation === 'subscription'
    );
  },
  wsLink,
  authLink.concat(httpLink)
);

// Combine error link with split link
const link = ApolloLink.from([errorLink, splitLink]);

// Configure cache
const cache = new InMemoryCache({
  typePolicies: {
    User: {
      keyFields: ['id'],
    },
    Course: {
      keyFields: ['id'],
    },
    Lesson: {
      keyFields: ['id'],
    },
    Quiz: {
      keyFields: ['id'],
    },
    Query: {
      fields: {
        users: {
          // Pagination merge strategy
          keyArgs: ['filter', 'sort'],
          merge(existing, incoming, { args }) {
            if (!existing) return incoming;

            const merged = {
              ...incoming,
              nodes: [...(existing.nodes || []), ...(incoming.nodes || [])],
            };

            return merged;
          },
        },
        courses: {
          keyArgs: ['filter', 'sort'],
          merge(existing, incoming) {
            if (!existing) return incoming;

            const merged = {
              ...incoming,
              nodes: [...(existing.nodes || []), ...(incoming.nodes || [])],
            };

            return merged;
          },
        },
      },
    },
  },
});

// Create Apollo Client instance
export const apolloClient = new ApolloClient({
  link,
  cache,
  defaultOptions: {
    watchQuery: {
      fetchPolicy: 'cache-and-network',
      errorPolicy: 'all',
    },
    query: {
      fetchPolicy: 'cache-first',
      errorPolicy: 'all',
    },
    mutate: {
      errorPolicy: 'all',
    },
  },
  connectToDevTools: import.meta.env.DEV,
});