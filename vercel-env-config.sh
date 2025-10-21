#!/bin/bash
# Vercel Environment Variables Configuration Script
# Run this to configure all environment variables for the dashboard frontend
# Usage: bash vercel-env-config.sh

set -e

echo "🚀 Configuring Vercel Environment Variables for ToolboxAI Dashboard"
echo "=================================================================="
echo ""

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Login to Vercel (if not already logged in)
echo "📝 Please ensure you're logged in to Vercel..."
vercel whoami || vercel login

echo ""
echo "Setting environment variables for all environments (Production, Preview, Development)..."
echo ""

# Backend API Configuration
echo "🔗 Setting Backend API URLs..."
vercel env add VITE_API_BASE_URL production preview development <<EOF
https://toolboxai-solutions.onrender.com
EOF

vercel env add VITE_WS_URL production preview development <<EOF
wss://toolboxai-solutions.onrender.com
EOF

# Clerk Authentication
echo "🔐 Setting Clerk Authentication..."
vercel env add VITE_CLERK_PUBLISHABLE_KEY production preview development <<EOF
pk_test_Y2FzdWFsLWZpcmVmbHktMzkuY2xlcmsuYWNjb3VudHMuZGV2JA
EOF

vercel env add NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY production preview development <<EOF
pk_test_Y2FzdWFsLWZpcmVmbHktMzkuY2xlcmsuYWNjb3VudHMuZGV2JA
EOF

vercel env add VITE_ENABLE_CLERK_AUTH production preview development <<EOF
true
EOF

vercel env add VITE_CLERK_SIGN_IN_URL production preview development <<EOF
/sign-in
EOF

vercel env add VITE_CLERK_SIGN_UP_URL production preview development <<EOF
/sign-up
EOF

vercel env add VITE_CLERK_AFTER_SIGN_IN_URL production preview development <<EOF
/dashboard
EOF

vercel env add VITE_CLERK_AFTER_SIGN_UP_URL production preview development <<EOF
/dashboard
EOF

# Supabase Configuration
echo "🗄️ Setting Supabase Configuration..."
vercel env add VITE_SUPABASE_URL production preview development <<EOF
https://jlesbkscprldariqcbvt.supabase.co
EOF

vercel env add VITE_SUPABASE_ANON_KEY production preview development <<EOF
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpsZXNia3NjcHJsZGFyaXFjYnZ0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg0MzYzNTYsImV4cCI6MjA3NDAxMjM1Nn0.NQnqmLIM7UOwRKwTnoHUJSl440d1NzPrj1xipC2du14
EOF

vercel env add NEXT_PUBLIC_SUPABASE_URL production preview development <<EOF
https://jlesbkscprldariqcbvt.supabase.co
EOF

vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production preview development <<EOF
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpsZXNia3NjcHJsZGFyaXFjYnZ0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg0MzYzNTYsImV4cCI6MjA3NDAxMjM1Nn0.NQnqmLIM7UOwRKwTnoHUJSl440d1NzPrj1xipC2du14
EOF

# Pusher Real-time Configuration
echo "📡 Setting Pusher Real-time Configuration..."
vercel env add VITE_PUSHER_KEY production preview development <<EOF
73f059a21bb304c7d68c
EOF

vercel env add VITE_PUSHER_CLUSTER production preview development <<EOF
us2
EOF

vercel env add VITE_PUSHER_AUTH_ENDPOINT production preview development <<EOF
/pusher/auth
EOF

vercel env add VITE_ENABLE_PUSHER production preview development <<EOF
true
EOF

# Feature Flags
echo "🎛️ Setting Feature Flags..."
vercel env add VITE_ENABLE_ANALYTICS production preview development <<EOF
true
EOF

vercel env add VITE_ENABLE_DEBUG_MODE production preview development <<EOF
false
EOF

vercel env add VITE_ENABLE_WEBSOCKET production preview development <<EOF
true
EOF

# Stripe Configuration (Optional - for payments)
echo "💳 Setting Stripe Configuration..."
vercel env add VITE_STRIPE_PUBLISHABLE_KEY production preview development <<EOF
pk_test_your_stripe_publishable_key_here
EOF

echo ""
echo "✅ All environment variables configured successfully!"
echo ""
echo "📋 Next Steps:"
echo "   1. Verify variables at: https://vercel.com/grayghostdevs-projects/toolbox-production-final/settings/environment-variables"
echo "   2. Trigger a new deployment to apply changes"
echo "   3. Test the dashboard at: https://toolbox-production-final.vercel.app"
echo ""
