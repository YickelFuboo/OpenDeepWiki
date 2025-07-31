# S3 存储配置说明

## S3 配置参数

### 必需参数
```bash
# S3 存储桶名称
S3_BUCKET_NAME=user-service

# 存储区域
S3_REGION=us-east-1

# 访问密钥
S3_ACCESS_KEY_ID=your_access_key
S3_SECRET_ACCESS_KEY=your_secret_key

# S3 兼容服务的端点URL（必需）
S3_ENDPOINT_URL=https://your-s3-endpoint.com
```

### 可选参数
```bash
# 是否使用SSL连接
S3_USE_SSL=true
```

## 不同S3兼容服务的配置

### 1. AWS S3
```bash
STORAGE_TYPE=s3
S3_BUCKET_NAME=your-bucket-name
S3_REGION=us-east-1
S3_ACCESS_KEY_ID=your_aws_access_key
S3_SECRET_ACCESS_KEY=your_aws_secret_key
S3_ENDPOINT_URL=https://s3.amazonaws.com
S3_USE_SSL=true
```

### 2. MinIO（S3兼容模式）
```bash
STORAGE_TYPE=s3
S3_BUCKET_NAME=user-service
S3_REGION=us-east-1
S3_ACCESS_KEY_ID=minioadmin
S3_SECRET_ACCESS_KEY=minioadmin
S3_ENDPOINT_URL=http://localhost:9000
S3_USE_SSL=false
```

### 3. DigitalOcean Spaces
```bash
STORAGE_TYPE=s3
S3_BUCKET_NAME=your-space-name
S3_REGION=nyc3
S3_ACCESS_KEY_ID=your_spaces_key
S3_SECRET_ACCESS_KEY=your_spaces_secret
S3_ENDPOINT_URL=https://nyc3.digitaloceanspaces.com
S3_USE_SSL=true
```

### 4. Cloudflare R2
```bash
STORAGE_TYPE=s3
S3_BUCKET_NAME=your-bucket-name
S3_REGION=auto
S3_ACCESS_KEY_ID=your_r2_key
S3_SECRET_ACCESS_KEY=your_r2_secret
S3_ENDPOINT_URL=https://your-account-id.r2.cloudflarestorage.com
S3_USE_SSL=true
```

### 5. Backblaze B2
```bash
STORAGE_TYPE=s3
S3_BUCKET_NAME=your-bucket-name
S3_REGION=us-west-002
S3_ACCESS_KEY_ID=your_b2_key_id
S3_SECRET_ACCESS_KEY=your_b2_application_key
S3_ENDPOINT_URL=https://s3.us-west-002.backblazeb2.com
S3_USE_SSL=true
```

## 为什么需要 S3_ENDPOINT_URL？

所有S3兼容服务都需要指定endpoint_url：
- **AWS S3**: `https://s3.amazonaws.com`
- **MinIO**: `http://localhost:9000`
- **DigitalOcean Spaces**: `https://region.digitaloceanspaces.com`
- **Cloudflare R2**: `https://account-id.r2.cloudflarestorage.com`
- **Backblaze B2**: `https://s3.region.backblazeb2.com`

## 安全注意事项

1. **访问密钥**：不要在代码中硬编码，使用环境变量
2. **SSL连接**：生产环境建议启用SSL
3. **权限控制**：使用最小权限原则配置IAM策略
4. **存储桶策略**：配置适当的存储桶访问策略

## 测试连接

启动服务时会自动测试S3连接：
- 检查存储桶是否存在
- 验证访问权限
- 测试基本操作（上传、下载）

如果配置有误，服务启动时会显示错误信息。 