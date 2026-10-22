$ErrorActionPreference = 'Stop'
$base = 'http://localhost:8080'
$stamp = Get-Date -Format 'yyyyMMddHHmmss'
Write-Host '1. Gateway health:' -ForegroundColor Cyan
Invoke-RestMethod "$base/health"
Write-Host '2. Create user:' -ForegroundColor Cyan
$userBody = @{ name = 'Alice'; email = "alice.$stamp@example.com"; phone = '1234567890' } | ConvertTo-Json
$user = Invoke-RestMethod -Method Post -Uri "$base/api/users" -ContentType 'application/json' -Body $userBody
$user | Format-List
Write-Host '3. Create product:' -ForegroundColor Cyan
$productBody = @{ name = 'iPhone 15'; description = 'Demo product'; price = 999.99; stock = 50 } | ConvertTo-Json
$product = Invoke-RestMethod -Method Post -Uri "$base/api/products" -ContentType 'application/json' -Body $productBody
$product | Format-List
Write-Host '4. Create order (2 units):' -ForegroundColor Cyan
$orderBody = @{ user_id = $user.id; items = @(@{ product_id = $product.id; quantity = 2 }) } | ConvertTo-Json -Depth 5
$order = Invoke-RestMethod -Method Post -Uri "$base/api/orders" -ContentType 'application/json' -Body $orderBody
$order | Format-List
Write-Host '5. Check product stock (expected 48):' -ForegroundColor Cyan
$updated = Invoke-RestMethod "$base/api/products/$($product.id)"
$updated | Format-List
if ($updated.stock -ne 48) { throw "Incorrect stock: $($updated.stock)" }
Write-Host '6. Order detail:' -ForegroundColor Cyan
Invoke-RestMethod "$base/api/orders/$($order.id)" | ConvertTo-Json -Depth 6
Write-Host 'PASS: Gateway, User, Product, Order and REST communication.' -ForegroundColor Green
