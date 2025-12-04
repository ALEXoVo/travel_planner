"""
数据库迁移脚本
添加POI优先级字段和用户活动表

执行方式：
python migrations/add_poi_priority_and_activity.py
"""
import sys
import os

# 添加父目录到路径，以便导入模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import UserPOIFavorite, UserActivity
from sqlalchemy import text


def migrate():
    """执行数据库迁移"""
    with app.app_context():
        print("开始数据库迁移...")

        # 检查数据库引擎类型
        engine = db.engine
        dialect_name = engine.dialect.name

        if dialect_name == 'sqlite':
            print("检测到SQLite数据库，执行ALTER TABLE...")

            try:
                # 为 user_poi_favorites 表添加新字段
                with engine.connect() as conn:
                    # 检查字段是否已存在
                    result = conn.execute(text("PRAGMA table_info(user_poi_favorites)"))
                    columns = [row[1] for row in result]

                    if 'source' not in columns:
                        conn.execute(text("ALTER TABLE user_poi_favorites ADD COLUMN source VARCHAR(20) DEFAULT 'user'"))
                        print("[OK] 添加 source 字段成功")
                    else:
                        print("[-] source 字段已存在，跳过")

                    if 'priority' not in columns:
                        conn.execute(text("ALTER TABLE user_poi_favorites ADD COLUMN priority VARCHAR(20) DEFAULT 'must_visit'"))
                        print("[OK] 添加 priority 字段成功")
                    else:
                        print("[-] priority 字段已存在，跳过")

                    if 'itinerary_id' not in columns:
                        conn.execute(text("ALTER TABLE user_poi_favorites ADD COLUMN itinerary_id VARCHAR(50)"))
                        print("[OK] 添加 itinerary_id 字段成功")
                    else:
                        print("[-] itinerary_id 字段已存在，跳过")

                    conn.commit()

                print("[OK] user_poi_favorites 表迁移完成")

            except Exception as e:
                print(f"[ERROR] user_poi_favorites 表迁移失败: {str(e)}")
                return False

        else:
            print(f"检测到 {dialect_name} 数据库")
            # 对于其他数据库（MySQL、PostgreSQL等），使用SQLAlchemy的批量操作
            try:
                # 这里可以添加针对其他数据库的迁移逻辑
                print("请手动执行SQL迁移，或使用Alembic等迁移工具")
            except Exception as e:
                print(f"[ERROR] 迁移失败: {str(e)}")
                return False

        # 创建 user_activities 表（如果不存在）
        try:
            print("\n检查 user_activities 表...")
            # 检查表是否存在
            inspector = db.inspect(engine)
            if 'user_activities' not in inspector.get_table_names():
                print("创建 user_activities 表...")
                db.create_all()
                print("[OK] user_activities 表创建成功")
            else:
                print("[-] user_activities 表已存在，跳过")

        except Exception as e:
            print(f"[ERROR] user_activities 表创建失败: {str(e)}")
            return False

        print("\n[SUCCESS] 数据库迁移全部完成！")
        return True


def rollback():
    """回滚迁移（仅供参考，SQLite不支持删除列）"""
    with app.app_context():
        print("开始回滚迁移...")

        engine = db.engine
        dialect_name = engine.dialect.name

        if dialect_name == 'sqlite':
            print("警告：SQLite不支持删除列，无法完全回滚")
            print("建议手动删除 user_activities 表：")
            print("  DROP TABLE user_activities;")

            try:
                # 删除 user_activities 表
                with engine.connect() as conn:
                    conn.execute(text("DROP TABLE IF EXISTS user_activities"))
                    conn.commit()
                print("[OK] user_activities 表已删除")
            except Exception as e:
                print(f"[ERROR] 删除失败: {str(e)}")

        print("回滚完成")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='数据库迁移脚本')
    parser.add_argument('action', choices=['migrate', 'rollback'], default='migrate',
                        help='执行的操作：migrate（迁移）或 rollback（回滚）')

    args = parser.parse_args()

    if args.action == 'migrate':
        success = migrate()
        sys.exit(0 if success else 1)
    elif args.action == 'rollback':
        rollback()
