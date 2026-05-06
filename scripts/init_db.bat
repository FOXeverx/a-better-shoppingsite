@echo off
REM Database initialization batch file
REM Run this file to initialize the database

echo Initializing database...

REM 请确保MySQL服务已启动
REM 修改以下信息为您的MySQL信息
set DB_HOST=localhost
set DB_PORT=3306
set DB_USER=root
set DB_PASS=123456
set DB_NAME=shopping_site

echo Creating database %DB_NAME%...

mysql -h%DB_HOST% -P%DB_PORT% -u%DB_USER% -p%DB_PASS% -e "CREATE DATABASE IF NOT EXISTS %DB_NAME% CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

echo Importing tables...

mysql -h%DB_HOST% -P%DB_PORT% -u%DB_USER% -p%DB_PASS% %DB_NAME% < scripts\init_db.sql

echo Database initialization completed!
pause