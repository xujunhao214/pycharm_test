import pymysql

# 数据库连接配置（字典）
db_config = {
    "host": "39.99.136.49",
    "port": 3306,
    "user": "root",
    "password": "xizcJWmXFkB5f4fm",
    "database": "information_schema",  # 指定要连接的数据库
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor
}

try:
    # **关键修正：创建数据库连接对象**
    conn = pymysql.connect(**db_config)

    # 使用连接对象创建游标
    with conn.cursor() as cursor:
        # 执行查询（注意：COLLATIONS 表无需参数，删除多余的 (1,)）
        sql = "SELECT * FROM COLLATIONS WHERE CHARACTER_SET_NAME = 'ascii'"
        cursor.execute(sql)
        result = cursor.fetchone()
        print("查询结果：", result)

except pymysql.Error as e:
    print(f"数据库操作失败：{e}")

finally:
    # **关键修正：关闭连接对象**
    if 'conn' in locals() and conn:
        conn.close()
        print("数据库连接已关闭")
