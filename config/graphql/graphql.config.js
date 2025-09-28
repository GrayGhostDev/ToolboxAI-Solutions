module.exports = {
  schema: ['schema/**/*.graphql'],
  documents: ['apps/dashboard/src/**/*.{graphql,tsx,ts}'],
  extensions: {
    endpoints: {
      default: {
        url: 'http://localhost:8008/graphql',
        headers: {
          Authorization: 'Bearer ${env:AUTH_TOKEN}',
        },
      },
    },
    introspection: {
      enable: true,
    },
    validation: {
      rules: ['require-id-when-available', 'no-unused-fragments', 'known-type-names'],
    },
  },
};
