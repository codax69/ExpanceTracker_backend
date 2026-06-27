-- docker/mysql/init.sql
-- Runs once when the MySQL container is first created.
-- Ensures the database exists and sets character set/collation.

CREATE DATABASE IF NOT EXISTS `expensetracker`
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- Grant full privileges to the app user
GRANT ALL PRIVILEGES ON `expensetracker`.* TO 'expenseuser'@'%';
FLUSH PRIVILEGES;
