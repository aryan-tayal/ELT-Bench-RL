from pathlib import Path

import yaml

RAW_COLUMN_DESCRIPTIONS = {
    "customers": {
        "customer_id": "unique id of the customer",
        "name": "the customer's name",
        "country": "country code of the customer",
    },
    "orders": {
        "order_id": "unique id of the order",
        "customer_id": "id of the customer who placed the order",
        "amount": "order amount",
        "status": "order status, such as completed or cancelled",
    },
    "refunds": {
        "refund_id": "unique id of the refund",
        "order_id": "id of the order that was refunded",
        "amount": "refunded amount",
    },
}

DATA_MODEL = {
    "models": [
        {
            "name": "customer_summary",
            "description": "Each record represents a customer.",
            "columns": [
                {"name": "customer_id", "description": "the id of the customer"},
                {"name": "name", "description": "the name of the customer"},
                {
                    "name": "num_orders",
                    "description": "the number of completed orders of the customer, replace NULL values with 0.",
                },
                {
                    "name": "total_amount",
                    "description": "the total amount of the customer's completed orders, replace NULL values with 0.",
                },
                {
                    "name": "has_refund",
                    "description": "Set to 1 if any order of the customer has been refunded, otherwise, set to 0",
                },
                {
                    "name": "above_avg_spend",
                    "description": "Set to 1 if the customer's total_amount is greater than the average total_amount across all customers, otherwise, set to 0",
                },
            ],
        },
        {
            "name": "country_summary",
            "description": "Each record represents a country.",
            "columns": [
                {"name": "country", "description": "the country code"},
                {
                    "name": "num_customers",
                    "description": "the number of distinct customers in the country",
                },
                {
                    "name": "revenue",
                    "description": "the total amount of completed orders from customers in the country, replace NULL values with 0.",
                },
            ],
        },
    ]
}

def _write_config(task, sandbox_root: Path, db_path: Path) -> None:
    config = {
        "source_dir": str(Path(task.source_dir).resolve()),
        "destination": {
            "type": "duckdb",
            "path": str(Path(db_path).resolve()),
            "schema": task.schema,
        },
        "streams_available": sorted(task.expected_raw),
    }
    (sandbox_root / "config.yaml").write_text(yaml.safe_dump(config, sort_keys=False))