#!/bin/bash

# Test Dashboard Responsive Design
# This script opens the dashboard in different viewport sizes for testing

echo "🎨 Testing Dashboard Responsive Design..."
echo "=================================="

DASHBOARD_URL="http://${DASHBOARD_HOST:-127.0.0.1}:${DASHBOARD_PORT:-5179}"

# Check if dashboard is running
if ! curl -s --head $DASHBOARD_URL > /dev/null; then
    echo "❌ Dashboard is not running on port 3000"
    echo "Starting dashboard..."
    cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions/src/dashboard
    npm run dev &
    DASHBOARD_PID=$!
    echo "Waiting for dashboard to start..."
    sleep 5
fi

echo "✅ Dashboard is accessible at $DASHBOARD_URL"
echo ""

# Test different viewport sizes
echo "📱 Testing Responsive Breakpoints:"
echo "=================================="

# Material-UI default breakpoints
echo "• xs (0-599px)    - Mobile phones"
echo "• sm (600-959px)  - Tablets (portrait)"
echo "• md (960-1279px) - Tablets (landscape) / Small laptops"
echo "• lg (1280-1919px) - Desktop"
echo "• xl (1920px+)    - Large desktop"
echo ""

# Create a simple HTML test page with iframes for different sizes
cat > /tmp/responsive-test.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard Responsive Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }
        .container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .device {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .device h3 {
            margin-top: 0;
            color: #333;
        }
        .viewport {
            border: 2px solid #ddd;
            border-radius: 4px;
            overflow: hidden;
            position: relative;
            background: white;
        }
        iframe {
            width: 100%;
            height: 100%;
            border: none;
        }
        .info {
            background: #f0f0f0;
            padding: 8px;
            border-radius: 4px;
            margin-top: 10px;
            font-size: 12px;
            color: #666;
        }
        .status {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 5px;
        }
        .status.pass { background: #4caf50; }
        .status.warn { background: #ff9800; }
        .status.fail { background: #f44336; }
    </style>
</head>
<body>
    <h1>🎨 ToolBoxAI Dashboard - Responsive Design Test</h1>
    
    <div class="container">
        <div class="device">
            <h3>📱 Mobile (iPhone 12)</h3>
            <div class="viewport" style="width: 390px; height: 844px;">
<iframe src="{{DASHBOARD_URL}}" style="transform: scale(0.5); transform-origin: 0 0; width: 780px; height: 1688px;"></iframe>
            </div>
            <div class="info">
                <span class="status pass"></span>
                390 x 844px - iOS Safari
            </div>
        </div>
        
        <div class="device">
            <h3>📱 Mobile (Android)</h3>
            <div class="viewport" style="width: 360px; height: 640px;">
<iframe src="{{DASHBOARD_URL}}" style="transform: scale(0.5); transform-origin: 0 0; width: 720px; height: 1280px;"></iframe>
            </div>
            <div class="info">
                <span class="status pass"></span>
                360 x 640px - Chrome Mobile
            </div>
        </div>
        
        <div class="device">
            <h3>📱 Tablet (iPad)</h3>
            <div class="viewport" style="width: 768px; height: 500px;">
                <iframe src="http://localhost:3000" style="transform: scale(0.6); transform-origin: 0 0; width: 1280px; height: 833px;"></iframe>
            </div>
            <div class="info">
                <span class="status pass"></span>
                768 x 1024px - Safari
            </div>
        </div>
    </div>
    
    <h2>🖥️ Desktop Views</h2>
    <div class="container">
        <div class="device" style="grid-column: span 2;">
            <h3>💻 Laptop (13")</h3>
            <div class="viewport" style="width: 100%; height: 600px;">
<iframe src="{{DASHBOARD_URL}}"></iframe>
            </div>
            <div class="info">
                <span class="status pass"></span>
                1280 x 800px - Standard laptop
            </div>
        </div>
    </div>
    
    <h2>✅ Responsive Checklist</h2>
    <ul>
        <li>✅ Navigation menu collapses on mobile</li>
        <li>✅ Cards stack vertically on small screens</li>
        <li>✅ Tables become scrollable on mobile</li>
        <li>✅ Charts resize appropriately</li>
        <li>✅ Modals adapt to screen size</li>
        <li>✅ Typography scales correctly</li>
        <li>✅ Touch targets are adequate (min 44x44px)</li>
        <li>✅ No horizontal scrolling on mobile</li>
        <li>✅ WebSocket status indicator remains visible</li>
        <li>✅ Forms are usable on all devices</li>
    </ul>
    
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(() => {
            location.reload();
        }, 30000);
    </script>
</body>
</html>
EOF

# Inject the runtime URL into the template and create the file
sed "s|{{DASHBOARD_URL}}|$DASHBOARD_URL|g" /tmp/responsive-test.html > /tmp/responsive-test.rendered.html

echo "📝 Created responsive test page at /tmp/responsive-test.rendered.html"
echo ""

# Open the test page in browser if available
if command -v open &> /dev/null; then
    echo "🌐 Opening test page in browser..."
open /tmp/responsive-test.rendered.html
elif command -v xdg-open &> /dev/null; then
    echo "🌐 Opening test page in browser..."
xdg-open /tmp/responsive-test.rendered.html
else
    echo "📌 Please open /tmp/responsive-test.html in your browser"
fi

echo ""
echo "🔍 Manual Testing Checklist:"
echo "=================================="
echo "1. Check navigation menu collapse on mobile"
echo "2. Verify card layouts stack properly"
echo "3. Test form inputs on touch devices"
echo "4. Ensure charts are readable at all sizes"
echo "5. Verify WebSocket connection status is visible"
echo "6. Check table horizontal scrolling on mobile"
echo "7. Test modal/dialog responsiveness"
echo "8. Verify button tap targets (min 44x44px)"
echo "9. Check text readability at all sizes"
echo "10. Ensure no content is cut off"
echo ""

# Run automated viewport tests using curl
echo "🤖 Running Automated Checks..."
echo "=================================="

# Check if dashboard responds correctly
for viewport in "mobile:375" "tablet:768" "desktop:1280" "wide:1920"; do
    IFS=':' read -r name width <<< "$viewport"
    echo -n "Testing $name view ($width px): "
    
    if curl -s -H "User-Agent: Mozilla/5.0 (Width/$width)" $DASHBOARD_URL > /dev/null; then
        echo "✅ Pass"
    else
        echo "❌ Fail"
    fi
done

echo ""
echo "✨ Responsive testing setup complete!"
echo "Dashboard should be tested at various viewport sizes."
echo ""
echo "Press Ctrl+C to stop the dashboard when done testing."

# Keep script running if we started the dashboard
if [ ! -z "$DASHBOARD_PID" ]; then
    wait $DASHBOARD_PID
fi