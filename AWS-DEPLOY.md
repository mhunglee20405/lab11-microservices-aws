# LAB 10 – Deploy AWS EC2 Ubuntu 24.04

## 1. AWS Console
Launch Ubuntu 24.04 x86_64 EC2 (suggested t3.medium, gp3 20-30GB) in public subnet with public IPv4 and Internet access. Key pair PEM. Security group inbound: SSH TCP 22 from your public IP /32 and Custom TCP 8080 from your public IP /32. Outbound allow HTTPS and package downloads. Keep ports 5432 and 8000 closed. EC2 and public IPv4/EBS can incur charges.

## 2. Windows PowerShell: transfer project
Open PowerShell in the parent folder containing `microservices-lab`; update path/IP:

```powershell
ssh -i "D:\\keys\\lab10.pem" ubuntu@EC2_PUBLIC_IP
# Exit SSH, then transfer from local PowerShell:
scp -i "D:\\keys\\lab10.pem" -r .\\microservices-lab ubuntu@EC2_PUBLIC_IP:~/
```

If OpenSSH complains about PEM file permissions, restrict NTFS permissions for the key or use AWS EC2 Instance Connect instead.

## 3. SSH server: Docker
```bash
ssh -i "D:\\keys\\lab10.pem" ubuntu@EC2_PUBLIC_IP  # run on Windows, not inside Ubuntu
cd ~/microservices-lab
bash install-docker-ubuntu.sh
exit
```
Reconnect (to apply group membership), then:
```bash
cd ~/microservices-lab
docker compose config
docker compose up -d --build
docker compose ps
docker compose logs --tail=50
curl -i http://127.0.0.1:8080/health
curl http://127.0.0.1:8080/api/users
curl http://127.0.0.1:8080/api/products
curl http://127.0.0.1:8080/api/orders
```

## 4. Test from Windows PowerShell
```powershell
$base = 'http://EC2_PUBLIC_IP:8080'
Invoke-RestMethod "$base/health"
$u = Invoke-RestMethod "$base/api/users" -Method Post -ContentType 'application/json' -Body (@{name='AWS Lab User';email="aws_$(Get-Date -Format yyyyMMddHHmmss)@example.com";phone='0123456789'}|ConvertTo-Json)
$p = Invoke-RestMethod "$base/api/products" -Method Post -ContentType 'application/json' -Body (@{name='AWS Lab Product';description='Cloud lab';price=1500;stock=10}|ConvertTo-Json)
$o = Invoke-RestMethod "$base/api/orders" -Method Post -ContentType 'application/json' -Body (@{user_id=$u.id;items=@(@{product_id=$p.id;quantity=2})}|ConvertTo-Json -Depth 5)
$o
Invoke-RestMethod "$base/api/products/$($p.id)" # stock should now be 8
Invoke-RestMethod "$base/api/orders/$($o.id)"
```
On EC2:
```bash
docker compose exec user-db psql -U postgres -d userdb -c 'SELECT * FROM users;'
docker compose exec product-db psql -U postgres -d productdb -c 'SELECT * FROM products;'
docker compose exec order-db psql -U postgres -d orderdb -c 'SELECT * FROM orders;'
docker compose exec order-db psql -U postgres -d orderdb -c 'SELECT * FROM order_items;'
```

## 5. Costs and safety
This is a lab configuration; docker-compose.yml uses the example password `postgres`, so NEVER publish database ports, and limit 8080 to your IP. For real public production, replace passwords with secrets, use HTTPS, authentication, monitoring, backups, and tighter IAM. EC2 Stop halts compute charges but EBS persists and is billed. Public IPv4 addresses are charged while allocated/in use. A stopped instance typically gets a new public IP after restart. To fully delete, terminate EC2 and verify volumes, Elastic IPs, snapshots, gateways and any other billable services in AWS billing dashboard. Do not run `docker compose down -v` if you wish to keep database data.
