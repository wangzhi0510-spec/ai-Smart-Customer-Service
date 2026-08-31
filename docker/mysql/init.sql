CREATE DATABASE IF NOT EXISTS ai_customer_service
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

ALTER DATABASE ai_customer_service
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

GRANT ALL PRIVILEGES ON ai_customer_service.* TO 'ai_customer_service'@'%';
FLUSH PRIVILEGES;
