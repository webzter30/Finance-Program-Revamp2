from sqlalchemy import create_engine, inspect

engine = create_engine("sqlite:///ONE_BIG_ACCOUNT_combined_data2024.db")
inspector = inspect(engine)

print(inspector.get_table_names())